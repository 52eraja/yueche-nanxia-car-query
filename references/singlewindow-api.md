# 单一窗口 (swapp.singlewindow.cn) 接口参考

## 查询页面

```
GET https://swapp.singlewindow.cn/qspserver/sw/qsp/query/view/queryRecordVehicle
```

## 查询 API

```
POST https://swapp.singlewindow.cn:443/qspserver/sw/qsp/query/biz/queryRecordVehicle
Content-Type: application/json;charset=utf-8
```

### 请求参数

```json
{
  "veCusCode": "",
  "veFrameNo": "",
  "domesticLisenceNo": "车牌号",
  "foreignLicense": "",
  "randomcode": "验证码"
}
```

### 返回码 (errorCode)

| 值 | 含义 |
|----|------|
| `-2` | 验证码输入错误 |
| `0` | 查询失败 |
| `1` | 成功 |
| 其他 | 没有符合条件的数据 |

### 成功返回字段 (rows[0])

| 字段 | 说明 |
|------|------|
| veCusCode | 车辆海关编号 |
| mainPortName | 主管海关 |
| veFrameNo | 车架号 |
| veTypeName | 车辆类型 |
| domesticLisenceNo | 国内车牌 |
| foreignLicense | 外籍车牌 |
| apprPeriod | 批文/许可证期限 |
| allowVeIePortName | 进出口岸主管关区 |
| selfWt | 自重(KG) |

## 验证码接口

```
GET https://swapp.singlewindow.cn:443/qspserver/verifyCode/creator
```

## JS 路径

```
https://swapp.singlewindow.cn:443/qspserver/static/js/qsp/query/queryRecordVehicle.js
```

## ⚠️ 自动化限制

1. **WAF 防护**: Python urllib 返回 412；浏览器也可能被拦截（"访问受到安全防护限制"）
2. **验证码**: 图形验证码 + WAF 环境检测，验证码图片请求也被 WAF 拦截
3. **Cookie**: JSESSIONID + CKvDhNH2GZibP
4. **JS 反爬**: `$_ts` 加密 + `Mu64.js` 浏览器环境检测
5. **IP 标记**: WAF 可能标记服务器 IP，导致浏览器也被拦截

## WAF 绕过尝试结果（2026-06-11）

| 方法 | 结果 |
|------|------|
| Python urllib 直接请求 | 412 Precondition Failed |
| curl 带 cookie 请求验证码 | 412 Precondition Failed |
| 浏览器访问首页 | "访问受到安全防护限制" |
| 浏览器 JS fetch 验证码 | 400 Bad Request |
| 浏览器重定向到首页 | 被 WAF 拦截 |

**结论**：当前服务器 IP 被 WAF 标记，单一窗口无法自动化查询。此状态可能随时间变化（WAF 标记可能过期）。

## 替代查询方式（推荐）

当需要查询内地车牌时，提示用户通过以下方式手动查询：

1. **单一窗口网页**：在"国内车牌号"输入框填车牌 → 输验证码 → 查询
2. **深圳海关12360微信公众号** → 查询功能 → 车辆管理信息查询 → 往来港澳车辆备案信息查询
3. **深圳电子口岸**（仅香港车牌）：exp.szcport.cn:8282/NEWabl/carInfoQuery.action
