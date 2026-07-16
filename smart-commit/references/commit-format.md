# Commit Message Format

智能提交使用的 header / body 规范。SKILL.md 只引用本文件，细节在此维护。

## Header Format

```
<type>(<scope>): <emoji> <short summary>
```

- `scope` **可选**，但当变更明显属于某个模块时**建议加上**，让历史更易检索。
- 工程类项目的常见 scope：`gvsp`、`axi`、`collector`、`cooler`、`skill`、`skills`、`docs`、`readme`、`ci` 等。

## Type & Emoji Mapping

| Type | Emoji | Description | 使用场景 |
|------|-------|-------------|----------|
| `feat` | ✨ | New feature | 新增功能、特性 |
| `fix` | 🐛 | Bug fix | 修复 bug |
| `docs` | 📝 | Documentation | 文档变更、注释更新 |
| `style` | 🎨 | Code style | 代码格式化、无功能变更 |
| `refactor` | ♻️ | Refactoring | 重构代码、无功能变更 |
| `perf` | ⚡️ | Performance | 性能优化 |
| `test` | ✅ | Tests | 测试相关 |
| `chore` | 🔧 | Maintenance | 工具配置、依赖更新 |
| `ci` | 👷 | CI/CD | 持续集成/部署配置 |
| `build` | 📦 | Build system | 构建系统、依赖管理 |
| `revert` | ⏪ | Revert | 回退提交 |

选 type 时取**最具体**的类别（如测试相关优先 `test` 而非 `chore`）；emoji 严格对照上表，不可自创组合。

## Header 指南

- **type**：根据变更性质选择最具体类型。
- **scope**：明显属于某模块时加上，如 `fix(gvsp)`、`docs(readme)`。
- **emoji**：使用对应类型的 emoji。
- **short summary**：
  - 祈使语气（"add" 而非 "added"）
  - 首字母小写
  - 不超过 **50** 个字符（注意 scope 会占用字符预算，scope 越长 summary 越短）
  - 直接描述变更内容

## Body 指南（可选）

变更复杂时追加 body：

- 解释 **WHAT** 改变了和 **WHY**（不只是 how）
- 用项目符号 `- ` 列出多个变更点，避免叙事段落
- 每行不超过 **72** 个字符
- **默认中文**（便于团队理解）

## 语言策略（统一，避免中英混杂）

- **header summary 默认英文**，保持 `git log` 简洁统一。
- **body 默认中文**，便于团队理解。
- **例外**：若用户明确要求中文提交（如"用中文 commit"），则 header 与 body 都用中文。
- 不要出现"英文 header 里夹中文"或"中文 body 里夹半句英文 summary"的混搭。

## 示例

```text
# 带 scope 的功能提交
feat(gvsp): ✨ add retransmit timeout backoff

# Bug 修复 + scope
fix(gvsp): 🐛 correct packet length calculation

# 重构
refactor(skill): ♻️ tighten commit workflow contract

# 文档
docs(readme): 📝 update setup guide

# 带 body
fix(collector): 🐛 avoid double-count on reconnect

- 重连后重置已上报游标，避免重复统计
- 补充单测覆盖断线重连路径
```
