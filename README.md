# 粤车南下来往港澳车辆备案信息查询

查询广东省车辆经港珠澳大桥入出香港的备案信息。支持香港车牌查询，返回备案编号、关联内地车牌、有效期等信息。

## 功能说明

- **香港车牌查询**：输入香港车牌号（如 FR497），返回备案编号、关联内地车牌、备案有效期
- **数据来源**：深圳电子口岸（szcport.cn）
- **缓存机制**：查询结果缓存 24 小时，避免重复请求

## 使用方法

### 安装

```bash
git clone https://github.com/52eraja/yueche-nanxia-car-query.git
cd yueche-nanxia-car-query/scripts
```

### 查询车牌

```bash
python3 query_car.py FR497
python3 query_car.py FR497 --no-cache
python3 query_car.py FR497 --retry 5
```

## 示例

```
📋 车牌：FR497
✅ 已备案
备案编号：5740225423
国内车牌号码：粤ADU0650
备案有效期：2027-06-05
```

## 注意事项

- 请求间隔 ≥ 3 秒
- 服务器外网间歇性不可达
- 缓存有效期 24 小时
- 仅支持香港车牌查询
