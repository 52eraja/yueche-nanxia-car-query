# szcport 服务器连接问题记录

## 症状

1. **间歇性断开连接**：`Remote end closed connection without response`
2. **空响应**：`Empty reply from server`（curl 返回）
3. **浏览器也无法访问**：`net::ERR_EMPTY_RESPONSE`
4. **恢复时间不定**：有时几秒，有时几分钟

## 观察

- 服务器 IP：`123.58.64.85:8282`
- TLS 握手成功，但服务器在应用层关闭连接
- 连接恢复后，香港车牌（FR497）可正常查询
- 连接恢复后，内地车牌（粤ADU0650）仍然查不到 → **不是连接问题，是接口限制**

## 已确认的限制

| 限制 | 详情 |
|------|------|
| 仅支持香港车牌 | urllib POST 内地车牌始终返回"无此数据" |
| 间歇性断连 | 外网不稳定，需要重试机制 |
| 无验证码 | 接口本身不需要验证码 |

## 重试策略

脚本已实现自动重试（默认 3 次，间隔 5 秒）：

```bash
# 默认重试 3 次
python3 query_car.py FR497

# 自定义重试 5 次
python3 query_car.py FR497 --retry 5
```

## 建议

- 请求间隔 ≥ 3 秒
- 如果连续失败，用 Playwright 方式重试
- 清除缓存后重试：`rm -rf ~/.hermes/cache/car-query/`
