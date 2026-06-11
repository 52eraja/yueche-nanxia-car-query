# 粤车南下来往港澳车辆备案信息查询

查询广东省车辆经港珠澳大桥入出香港的备案信息。

## 快速开始

```bash
# 查询香港车牌
python3 scripts/query_car.py FR497

# 禁用缓存
python3 scripts/query_car.py FR497 --no-cache

# 增加重试
python3 scripts/query_car.py FR497 --retry 5
```

## 功能

- 香港车牌查询（FR497、FT3406 等）
- 返回备案编号、关联内地车牌、有效期
- 自动缓存 24 小时
- 服务器不可达时自动重试

## 数据源

深圳电子口岸 (exp.szcport.cn)

## License

MIT
