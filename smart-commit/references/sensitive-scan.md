# Sensitive Information Scan

在生成 message 之前扫描暂存 diff，防止密钥/密码进入提交历史（一旦进历史很难清除）。这是"降误提交风险"最关键的一环。SKILL.md 第 1 步的脚本即执行本规则；脚本不可用时按本文件手动扫描。

## 扫描对象

扫描 `git diff --cached` 的文本**与**文件名，命中以下任一即视为疑似敏感信息：

### 关键词（文本中）
- `token`、`password`、`passwd`、`secret`、`api_key`、`apikey`、`access_key`
- `private_key`、`client_secret`、`credential`、`.env`（非 `.env.example`）

### 形态
- 以 `-----BEGIN ... PRIVATE KEY-----` 开头的私钥块
- `id_rsa` / `id_ed25519` 等 SSH key 文件名
- `.pem` / `.key` / `.crt` / `.p12` / `.pfx` 证书/密钥文件
- 长串 Base64 / 十六进制且上下文像密钥的字段（如 `= "aZ91...=="`）

## 处理流程

1. **命中疑似敏感信息** → **停止提交**。
2. 告知用户："暂存区 diff 疑似包含敏感信息（列出命中的关键词/文件名）"。
3. 建议用户确认来源，必要时用 `git reset` 移除或加入 `.gitignore`。
4. **仍只生成 message，不执行 `git commit`**——等用户处理完再决定是否提交。
5. **未命中** → 继续生成。

## 注意事项

- 无需复杂安全引擎，关键词 + 形态即可，但要覆盖上面清单。
- 不要把扫描本身输出到提交历史或公开位置；只在本机提示用户。
- 命中后绝不在 message 中复述密钥内容。
