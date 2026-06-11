# szcport 接口深度分析

## 接口信息

```
POST https://exp.szcport.cn:8282/NEWabl/carInfoQuery.action
Content-Type: application/x-www-form-urlencoded

queryBean1.queryInput1=车牌号&id=车牌号
```

## 支持范围

| 车牌类型 | 支持 | 备注 |
|----------|------|------|
| 香港车牌（如 FR497） | ✅ | 返回关联的内地车牌和备案信息 |
| 内地车牌（如 粤ADU0650） | ❌ | 始终返回"无此数据" |

## 返回数据结构

### 有数据时（香港车牌）

HTML 包含 2 个 table：
- Table 0: 表头行（"内地/香港车牌号码"）
- Table 1: 数据行（交替格式：表头, 值, 表头, 值...）

cells 数组示例：
```
cells[0] = "车辆备案编号"       （表头）
cells[1] = "5740225423"         （值）
cells[2] = "国内车牌号码"       （表头）
cells[3] = "粤ADU0650"          （值）
cells[4] = "车辆备案有效期"     （表头）
cells[5] = "2027-06-05 00:00:00"（值）
cells[6] = "电子车牌制卡时间"   （表头）
cells[7] = "1900-01-01 00:05:43"（值）
```

### 无数据时（内地车牌或未备案）

HTML 只有 1 个 table（表头行），cells 为空或只有表头。

## 判断逻辑

**不能仅用返回码判断**：
- code=1 + cells 有数据 → 已备案（香港车牌的正常返回）
- code=1 + cells 只有表头 → 未备案
- 连接失败/空响应 → 服务器不可达，需重试

正确方式：**检查 cells 是否有实际数据行（len > 2）**

## 服务器稳定性

- 外网间歇性不可达
- 表现为 `Remote end closed connection without response` 或 `Empty reply from server`
- 等待 5-30 秒后重试通常可恢复
- 建议重试 3 次，间隔 5 秒

## 已测试的参数组合（全部无效）

以下字段名组合均无法查询内地车牌：
- `queryBean1.queryInput1` / `queryBean1.queryInput2`
- `domesticLicense` / `domesticLisenceNo`
- `licenseNo` / `plateNo` / `carNo`
- `hkPlate` / `cnPlate`
- `type` / `carType` / `licenseType`

结论：**接口本身不支持内地车牌查询**，不是参数问题。

## 单一窗口 WAF 分析

- 域名：swapp.singlewindow.cn
- 浏览器能打开页面但 JS 资源被拦截（验证码图片、查询 JS 等）
- 验证码接口返回 400（WAF 拦截）
- 无法通过自动化方式查询
