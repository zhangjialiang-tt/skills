# Output Risk Profile — smart-commit

> 此技能主要失败模式与防御策略。内容短小，聚焦可防可控的风险。

## 风险矩阵

| # | 失败模式 | 后果 | 防御 | 严重度 |
|---|---------|------|------|--------|
| 1 | 暂存区为空但未检测到 | git diff --cached 返回空但被误判为有内容，执行空提交 | 必须显式检查 `--name-only` 输出是否为空字符串 | 高 |
| 2 | Type 选择过于宽泛 | refactoring 被标为 feat 或 chore，commit log 误导 | 优先选最具体 type；参考 type-mapping 表的"使用场景"列 | 中 |
| 3 | Emoji 与 type 不匹配 | header 如 `fix: ✨ resolve bug` 自相矛盾 | 严格对照 type-emoji 映射表，不可自创组合 | 中 |
| 4 | Summary 使用陈述语气 | "Fixed memory leak" 而非 "fix memory leak" | 强制祈使语气规则，生成后自检 | 低 |
| 5 | Summary 超过 50 chars | header 在 `git log --oneline` 中被截断 | 生成后计数字符并截断/改写 | 低 |
| 6 | Body 写成叙事段落 | 难以在列表中快速扫描变更 | 仅使用 `- ` 项目符号格式，每项一行 | 低 |
| 7 | 未征求确认直接执行 git commit | 用户对提交内容不知情，信任崩塌 | 默认只生成 message；仅用户明确授权才执行 git commit | 高 |
| 8 | `git diff --cached` 输出过大导致分析失真 | 大规模变更时类型判断不准 | 超大 diff（>20 文件或 >2000 行）优先用 `--stat` / `--name-status` 分层总结 | 中 |
| 9 | Git hook (pre-commit) 阻断提交 | 提交失败但无提示 | 捕获 commit 退出码，失败时显示 stderr | 中 |
| 10 | **敏感信息进入提交历史** | token/私钥/密码泄露，且难以从历史清除 | 提交前扫描 diff 关键词与私钥块；命中即**停止提交**并提醒用户 | 严重 |
| 11 | **提交到错误/保护分支** | 直接污染 main/master/release | 先 `git branch --show-current`；保护分支需额外明确授权才提交 | 高 |
| 12 | **二进制/lock/生成文件被过度解读** | message 出现无根据的"业务逻辑"推断 | 二进制靠文件名/路径/大小判断；lock 仅说明"依赖更新"，不逐行推断 | 中 |
| 13 | **用户只想要 message 却被自动提交** | agent 把"生成/写一下"误读为"提交" | 默认 generate-only；仅 "执行提交/commit it/提交吧" 等明确指令才执行 | 高 |
| 14 | **不相关变更合并为单条提交** | 历史难以 bisect/回滚 | 命中拆分信号（代码+文档大改、功能+修复、格式化+逻辑、多无关模块、依赖+功能）即建议拆分 | 中 |

## 自检清单

执行完成后逐项验证：

- [ ] `git rev-parse --is-inside-work-tree` 成功（在仓库内）
- [ ] 已显示当前分支；保护分支提交需额外授权
- [ ] `git diff --cached --name-only` 确认非空
- [ ] 大 diff 已用 `--stat` / `--name-status` 分层，未强行通读
- [ ] 敏感信息扫描通过，或已拦截并提醒
- [ ] 多类不相关变更已建议拆分
- [ ] header 格式：`<type>(<scope>?): <emoji> <imperative lower-case summary>`
- [ ] summary ≤ 50 chars, header ≤ 72 chars
- [ ] type 从映射表中选择，非自由发挥
- [ ] emoji 与 type 一致
- [ ] 语言统一：header 默认英文、body 默认中文（除非用户要中文提交）
- [ ] **默认未自动执行 `git commit`**（仅用户明确授权才执行）
- [ ] （若执行）commit 成功，显示了最终 hash；失败则展示 stderr
