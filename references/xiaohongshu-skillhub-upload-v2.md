# 小红书 SkillHub 上传流程调研

## 结论（2026-06-11 更新）

上传 Skill 到小红书 SkillHub **无法纯自动化完成**，核心卡点是 OAuth 授权必须通过小红书 App。

## 架构总览

```
用户手机(小红书App) ←xhsopen://→ skillhub-upload CLI → edith.xiaohongshu.com API
         ↑                              ↑
    扫码/授权                      Linux服务器(CI+打包+上传)
```

CLI 能做的：打包、上传、提交。**做不到**：打开 xhsopen:// 授权链接。

## skillhub-upload CLI 流程

1. `skillhub-upload login --agent` → 输出 `PROMPT:{authorizeUrl, userCode, expiresInSeconds}`
2. authorizeUrl 是 `xhsopen://` 协议 → **只能小红书 App 打开**
3. 用户在 App 授权 → CLI 自动轮询 → 写入 `~/.skillhub-upload/credentials.json`
4. `skillhub-upload publish <path> --agent --source original --tag 标签1,标签2` → 上传+提交

## 创作者平台登录风控（新发现）

**短信验证码**：从服务器 IP（非住宅 IP）发送验证码可能被小红书风控拦截，表现为点击「获取验证码」后无响应、无倒计时、无错误提示。

**解决方案**：用二维码扫码登录。步骤：
1. 打开 https://creator.xiaohongshu.com/login
2. 点击二维码图标切换到扫码模式
3. 用小红书 App 扫描
4. 二维码 base64 可通过浏览器控制台提取：`document.querySelectorAll('img')[1].src`

## 已知限制（灰度测试阶段）

- 仅支持 Markdown 和 TXT 格式
- YAML 配置及 Python/Node 脚本无法上传
- 仅部分创作者有上传权限（粉丝≥1000、注册≥6个月、实名认证）
- 审核通过后才能挂载到笔记

## 手动上传步骤（备用方案）

当 CLI 授权无法完成时：
1. 浏览器打开 https://creator.xiaohongshu.com/login
2. 二维码扫码登录（优先）或短信验证码（可能被拦截）
3. 左侧菜单 →「Red Skill」→「上传 Skill」
4. 上传 SKILL.md 或文件夹
5. 填写名称、简介、标签
6. 提交审核

## 微信发送限制

发送图片到微信可能被限流（rate limited, errcode=-2）。备选方案：
- 把图片 base64 编码后让用户自行解码
- 上传到图床后发 URL
- 用 ASCII 二维码替代（需要 Pillow：`pip install Pillow`，但当前环境 pip 不可用）

## npm 安装注意事项

在 Linux 服务器上，`npm install -g` 可能因权限问题失败（root 拥有的缓存目录、无 sudo）。解决方案：
```bash
npm install -g "<package-url>" --cache /opt/data/.npm-cache --prefix /opt/data/tools
```
安装后 CLI 路径：`/opt/data/tools/bin/skillhub-upload`

## 失败记录

| 失败场景 | 现象 | 原因 |
|---------|------|------|
| xhsopen:// 在浏览器打开 | ERR_NAME_NOT_RESOLVED | 浏览器不支持自定义协议 |
| xhsopen:// 在手机浏览器打开 | 无法跳转 | 缺少 App 关联 |
| 短信验证码 | 点击后无任何响应 | 服务器 IP 被风控 |
| npm install -g | EACCES | root 拥有的缓存目录 |
| JS 注入 Cookie | SecurityError: Access is denied | 浏览器安全策略阻止跨域 Cookie |
| whoami 无输出 | 命令成功但无输出 | 未授权/无 credentials.json |
| 二维码发送 | 微信 rate limit errcode=-2 | 微信图片发送限流 |

## Cookie 注入尝试（失败）

尝试通过浏览器 JS 注入创作者平台 Cookie 来绕过登录：

```js
document.cookie = 'web_session=xxx; domain=.xiaohongshu.com; path=/';
```

**结果**：失败。浏览器安全策略阻止 JS 设置跨域 Cookie（SecurityError: Access is denied for this document）。

即使成功设置 `document.cookie`，页面刷新后仍然跳转到登录说明 Cookie 需要正确的 domain/path/secure 标志，且浏览器可能通过其他机制（如 HttpOnly）保护认证 Cookie。

**结论**：Cookie 注入不可行。创作者平台登录必须通过正常流程（扫码或短信验证码）。
- 苏米客: https://www.xmsumi.com/detail/3358
- 网易: https://www.163.com/dy/article/KUVSLOGM0511DSSR.html
- 腾讯新闻: https://news.qq.com/rain/a/20260525A086DE00
