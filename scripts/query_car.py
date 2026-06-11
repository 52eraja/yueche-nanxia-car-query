#!/usr/bin/env python3
"""
粤车南下来往港澳车辆备案信息查询脚本 v1.0
支持两个查询源：
  1. 深圳电子口岸 (exp.szcport.cn:8282) - 无需验证码，外网间歇性可用
  2. 广东单一窗口 (swapp.singlewindow.cn) - 需要验证码+WAF，自动化查不了

用法:
  python3 query_car.py 车牌号
  python3 query_car.py 车牌号 --source szcport
  python3 query_car.py 车牌号 --json
  python3 query_car.py 车牌号 --no-cache
  python3 query_car.py 车牌号 --retry 3
"""

import sys
import os
import json
import re
import ssl
import time
import hashlib
import argparse
import urllib.request
import urllib.parse
import http.cookiejar
from pathlib import Path
from datetime import datetime, timedelta

# ─── 配置 ───────────────────────────────────────────────

CACHE_DIR = Path.home() / '.hermes' / 'cache' / 'car-query'
CACHE_TTL_HOURS = 24
MAX_RETRIES = 3
RETRY_DELAY = 5

# ─── 工具函数 ───────────────────────────────────────────

def _ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(plate: str) -> str:
    return hashlib.md5(plate.encode()).hexdigest()


def _cache_get(plate: str) -> dict | None:
    _ensure_cache_dir()
    path = CACHE_DIR / f'{_cache_key(plate)}.json'
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        cached_at = datetime.fromisoformat(data.get('cached_at', '2000-01-01'))
        if datetime.now() - cached_at > timedelta(hours=CACHE_TTL_HOURS):
            return None
        return data
    except Exception:
        return None


def _cache_set(plate: str, result: dict):
    _ensure_cache_dir()
    path = CACHE_DIR / f'{_cache_key(plate)}.json'
    data = {'cached_at': datetime.now().isoformat(), 'plate': plate, 'result': result}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def _is_hk_plate(plate: str) -> bool:
    """判断是否为香港车牌（非粤开头）"""
    return not plate.startswith('粤')


# ─── 查询源 1：深圳电子口岸 ────────────────────────────

def query_szcport(plate: str, max_retries: int = MAX_RETRIES) -> dict:
    """
    通过深圳电子口岸查询。
    URL: https://exp.szcport.cn:8282/NEWabl/carInfoQuery.action
    
    注意：
    - 仅支持香港车牌（非粤开头）直接查询
    - 内地车牌（粤开头）查询时接口返回"无此数据"，这是接口限制
    - 服务器外网间歇性不可达，需要重试
    """
    url = 'https://exp.szcport.cn:8282/NEWabl/carInfoQuery.action'
    
    for attempt in range(max_retries):
        data = urllib.parse.urlencode({
            'queryBean1.queryInput1': plate,
            'id': plate
        }).encode('utf-8')

        req = urllib.request.Request(url, data=data, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })

        try:
            resp = urllib.request.urlopen(req, context=_ssl_ctx(), timeout=15)
            raw = resp.read()
            break  # 成功，跳出重试循环
        except Exception as e:
            error_msg = str(e)
            # 连接被关闭或空响应，等待后重试
            if 'Remote end closed' in error_msg or 'Empty reply' in error_msg or 'Connection reset' in error_msg:
                if attempt < max_retries - 1:
                    print(f'[WARN] szcport 连接失败 (尝试 {attempt+1}/{max_retries}): {error_msg}，{RETRY_DELAY}秒后重试...', file=sys.stderr)
                    time.sleep(RETRY_DELAY)
                    continue
            return {'source': 'szcport', 'plate': plate, 'registered': None, 'error': error_msg}
    else:
        # 所有重试都失败
        return {'source': 'szcport', 'plate': plate, 'registered': None, 'error': f'连接失败，已重试{max_retries}次'}

    # 解码
    text = None
    for enc in ['gb18030', 'gbk', 'gb2312', 'utf-8']:
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return {'source': 'szcport', 'plate': plate, 'registered': None, 'error': 'decode error'}

    # 提取所有 td 数据
    tds = re.findall(r'<td[^>]*>(.*?)</td>', text, re.DOTALL)
    cells = []
    for td in tds:
        clean = re.sub(r'<[^>]+>', '', td).strip()
        if clean and clean != '内地/香港车牌号码':
            cells.append(clean)

    # 检查是否有"无此数据"提示
    no_data_hint = '无此数据' in text

    if cells and len(cells) > 2:
        # 有数据（cells 包含表头+值对，超过2个说明有实际数据）
        result = {
            'source': 'szcport',
            'plate': plate,
            'registered': True,
            'data': {'raw_cells': cells},
        }
        # 解析字段：cells 是 [表头, 值, 表头, 值, ...] 的交替格式
        for i in range(0, len(cells) - 1, 2):
            header = cells[i]
            value = cells[i + 1]
            if '备案编号' in header:
                result['data']['备案编号'] = value
            elif '国内车牌' in header:
                result['data']['国内车牌号码'] = value
            elif '有效期' in header:
                result['data']['备案有效期'] = value.split(' ')[0]
            elif '制卡时间' in header:
                result['data']['电子车牌制卡时间'] = value
        # 如果查询的是香港车牌（非粤开头），标注为香港车牌
        if _is_hk_plate(plate):
            result['data']['香港车牌'] = plate
        return result

    if no_data_hint:
        # 明确提示无数据 = 未备案
        return {'source': 'szcport', 'plate': plate, 'registered': False, 'data': None}

    # code=1 且 cells 只有表头 = 未备案
    return {'source': 'szcport', 'plate': plate, 'registered': False, 'data': None}


# ─── 查询源 2：广东单一窗口 ────────────────────────────

def query_singlewindow(plate: str, captcha_code: str = None) -> dict:
    """
    通过广东单一窗口查询。
    注意：WAF 防护 + 验证码，自动化查询通常被拦截。
    """
    base_url = 'https://swapp.singlewindow.cn:443/qspserver'
    query_url = f'{base_url}/sw/qsp/query/biz/queryRecordVehicle'

    if not captcha_code:
        return {
            'source': 'singlewindow',
            'plate': plate,
            'registered': None,
            'need_captcha': True,
            'captcha_url': f'{base_url}/verifyCode/creator',
            'message': '需要验证码，且 WAF 可能拦截自动化请求',
        }

    payload = json.dumps({
        'veCusCode': '',
        'veFrameNo': '',
        'domesticLisenceNo': plate,
        'foreignLicense': '',
        'randomcode': captcha_code,
    }).encode('utf-8')

    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=_ssl_ctx()),
        urllib.request.HTTPCookieProcessor(cookie_jar),
    )

    try:
        home_req = urllib.request.Request(
            'https://swapp.singlewindow.cn/qspserver/sw/qsp/query/view/queryRecordVehicle',
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        opener.open(home_req, timeout=15)
    except Exception:
        pass

    req = urllib.request.Request(query_url, data=payload, headers={
        'Content-Type': 'application/json;charset=utf-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://swapp.singlewindow.cn/qspserver/sw/qsp/query/view/queryRecordVehicle',
        'Origin': 'https://swapp.singlewindow.cn',
    })

    try:
        resp = opener.open(req, timeout=15)
        result = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {'source': 'singlewindow', 'plate': plate, 'registered': None, 'error': str(e)}

    error_code = result.get('errorCode')

    if error_code in ('-2', '-1'):
        return {
            'source': 'singlewindow', 'plate': plate, 'registered': None,
            'need_captcha': True, 'message': result.get('errorMessage', '验证码无效'),
        }
    if error_code == '0':
        return {
            'source': 'singlewindow', 'plate': plate, 'registered': False,
            'data': None, 'message': result.get('errorMessage', '查询失败'),
        }
    if error_code == '1':
        rows = result.get('rows', [])
        if not rows:
            return {'source': 'singlewindow', 'plate': plate, 'registered': False, 'data': None}
        row = rows[0]
        return {
            'source': 'singlewindow', 'plate': plate, 'registered': True,
            'data': {
                '车辆海关编号': row.get('veCusCode', '--'),
                '主管海关': row.get('mainPortName', '--'),
                '车架号': row.get('veFrameNo', '--'),
                '车辆类型': row.get('veTypeName', '--'),
                '国内车牌': row.get('domesticLisenceNo', '--'),
                '外籍车牌': row.get('foreignLicense', '--'),
                '批文/许可证期限': row.get('apprPeriod', '--').replace(' 00:00:00', ''),
                '进出口岸主管关区': row.get('allowVeIePortName', '--'),
            },
        }
    return {
        'source': 'singlewindow', 'plate': plate, 'registered': False,
        'data': None, 'message': result.get('errorMessage', '没有符合条件的数据'),
    }


# ─── 主查询逻辑 ────────────────────────────────────────

def query_car(plate: str, source: str = 'auto', use_cache: bool = True, max_retries: int = MAX_RETRIES) -> dict:
    plate = plate.strip().upper()

    if use_cache:
        cached = _cache_get(plate)
        if cached:
            cached['result']['from_cache'] = True
            return cached['result']

    result = None

    if source in ('auto', 'szcport'):
        result = query_szcport(plate, max_retries=max_retries)
        # szcport 不可用时尝试单一窗口
        if result and result.get('registered') is None and source == 'auto':
            error = result.get('error', '')
            if error:
                print(f'[INFO] szcport 不可用: {error}，尝试单一窗口...', file=sys.stderr)
                result = query_singlewindow(plate)
    elif source == 'singlewindow':
        result = query_singlewindow(plate)

    if result and result.get('registered') is not None:
        _cache_set(plate, result)

    return result


# ─── 格式化输出 ────────────────────────────────────────

def format_result(result: dict) -> str:
    plate = result.get('plate', '?')
    source = result.get('source', '?')
    registered = result.get('registered')
    data = result.get('data')

    lines = [f'📋 车牌：{plate}']
    source_name = {'szcport': '深圳电子口岸', 'singlewindow': '广东单一窗口'}.get(source, source)
    if 'Playwright' in source:
        source_name = '深圳电子口岸（Playwright）'
    lines.append(f'🔍 数据源：{source_name}')

    if result.get('from_cache'):
        lines.append('💾 来自缓存')
    if result.get('error'):
        lines.append(f'⚠️ 查询出错：{result["error"]}')
        return '\n'.join(lines)
    if result.get('need_captcha'):
        lines.append(f'🔐 {result.get("message", "需要验证码")}')
        return '\n'.join(lines)

    if registered is False:
        lines.append('❌ 未备案（无此数据）')
    elif registered is True and data:
        lines.append('✅ 已备案\n')
        for k, v in data.items():
            if k != 'raw_cells':
                lines.append(f'  {k}：{v}')
    else:
        lines.append('⚠️ 未知状态')

    return '\n'.join(lines)


# ─── CLI ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='粤车南下来往港澳车辆备案信息查询 v1.0')
    parser.add_argument('plate', help='车牌号')
    parser.add_argument('--source', choices=['auto', 'szcport', 'singlewindow'], default='auto')
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    parser.add_argument('--no-cache', action='store_true', help='禁用缓存')
    parser.add_argument('--captcha', help='验证码（单一窗口）')
    parser.add_argument('--retry', type=int, default=MAX_RETRIES, help=f'重试次数（默认{MAX_RETRIES}）')

    args = parser.parse_args()
    result = query_car(args.plate, source=args.source, use_cache=not args.no_cache, max_retries=args.retry)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_result(result))


if __name__ == '__main__':
    main()
