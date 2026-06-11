# 小红书 SkillHub 上传流程调研

## 结论（2026-06-11）

上传 Skill 到小红书 SkillHub **无法纯自动化完成**，需要人工登录创作者平台。

## 已知信息

### 上传入口
- **PC端**: 小红书创作服务平台 → 左侧菜单「Red Skill」
  - URL: `https://creator.xiaohongshu.com/` （需登录）
- **手机端**: 发笔记 → 组件 → Red Skill

### 上传方式
1. **网页上传**: 上传 SKILL.md 文件或包含 Markdown 的文件夹，系统自动解析名称/简介/内容
2. **对话上传**: 复制专属口令发给 AI 助手（OpenClaw/Claude Code/Codex），AI 自动完成上传
   - 口令来源: `https://redskill.xiaohongshu.net/uploader.md`（外网不可达）

### 技术细节
- RedSkill CLI **没有 upload 命令**，只有 install/search/list/uninstall/upgrade/self-upgrade
- `redskill.xiaohongshu.net` 域名外网不可达（DNS 解析失败 / ERR_ABORTED）
- 后端 API 在 `edith.xiaohongshu.com/api/sns/v1/creator/red_skill/`，需要 SSO Cookie
- 上传需要创作者账号登录（手机号 + 短信验证码）

### 当前限制（灰度测试阶段）
- 仅支持 Markdown 和 TXT 格式
- YAML 配置及 Python/Node 脚本无法上传
- 仅部分科技类创作者有上传权限
- 审核通过后才能挂载到笔记

## 实操步骤

1. 打开 `https://creator.xiaohongshu.com/login`
2. 手机号 + 短信验证码登录
3. 左侧菜单找到「Red Skill」
4. 上传 SKILL.md 或文件夹
5. 填写 Skill 名称、简介、场景标签
6. 提交审核
7. 审核通过后发笔记时添加 Red Skill 组件挂载

## 参考文章
- 苏米客: https://www.xmsumi.com/detail/3358
- 网易: https://www.163.com/dy/article/KUVSLOGM0511DSSR.html
- 腾讯新闻: https://news.qq.com/rain/a/20260525A086DE00
- SimonAKing: https://simonaking.com/blog/red-skill/
