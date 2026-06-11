# carInfoQuery 接口参考

## 接口地址

```
POST https://exp.szcport.cn:8282/NEWabl/carInfoQuery.action
Content-Type: application/x-www-form-urlencoded
```

**⚠️ 注意**：是 `carInfoQuery.action`（不带 `1`），不带 1 的才是真正查询接口。

## 页面信息

- **标题**: 来往港澳车辆备案信息查询
- **编码**: GB18030（返回内容需 GBK/GB18030 解码）
- **访问**: 内网系统，外网间歇性可用

## 表单结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `queryBean1.queryInput1` | text input | 内地/香港车牌号码输入框（真正的查询参数） |
| `id` | hidden | session/token（需与 queryInput1 同时提交） |

## 查询方式

**必须 POST**，GET 请求只返回默认页面（`-1`）：

```python
import urllib.request, urllib.parse, ssl, re

def query(plate):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url = 'https://exp.szcport.cn:8282/NEWabl/carInfoQuery.action'
    data = urllib.parse.urlencode({'queryBean1.queryInput1': plate, 'id': plate}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0',
    })
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    text = resp.read().decode('gb18030')
    
    code = re.search(r'<span id="hidden_pageindex">(-?\d+)', text)
    return_code = code.group(1) if code else None
    
    if return_code == '0':
        tds = re.findall(r'<td[^>]*>(.*?)</td>', text, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', td).strip() for td in tds 
                 if re.sub(r'<[^>]+>', '', td).strip() and re.sub(r'<[^>]+>', '', td).strip() != '内地/香港车牌号码']
        return {'registered': True, 'cells': cells}
    else:
        return {'registered': False, 'cells': []}
```

服务器有频率限制，请求间隔建议 ≥ 3 秒。

## 返回码

| 返回码 | 含义 |
|--------|------|
| `-1` | 页面默认状态（未查询） |
| `0` | 查询成功，有数据行 = 已备案 |
| `1` | 查询完成，无数据 = 未备案 |

## 返回结果结构

### 已备案车辆

返回 GBK/GB18030 编码 HTML 表格，包含以下字段：

| 字段 | 示例值 | 说明 |
|------|--------|------|
| 车辆备案编号 | 5740225423 | 唯一备案 ID（纯数字） |
| 国内车牌号码 | 粤ADU0650 | 内地车牌号 |
| 车辆备案有效期 | 2027-06-05 | 备案到期时间 |

### 未备案车辆

返回码 `1`，页面显示"无此数据，请检查查询条件是否正确。"

## JS 来源分析

页面加载后，`buttons.js` 中的 `dealQuery(title)` 函数会将 form action 设为 `{title}Query.action`（即 `carInfoQuery.action`），然后提交表单。

所以正确的查询 URL 是 `carInfoQuery.action`，不是 `carInfoQuery1.action`。
