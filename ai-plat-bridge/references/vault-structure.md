# 目录结构与基础约定

## 目录结构

| 路径 | 用途 |
|------|------|
| `10-Daily/YYYY-MM-DD.md` | 每日动作日志 |
| `20-Tasks/active/*.md` | 进行中的任务卡片 |
| `20-Tasks/done/*.md` | 已完成的任务卡片 |
| `30-Projects/*.md` | 项目文件（含 YAML frontmatter） |
| `40-Prompts/*.md` | 6 个核心 Prompt 模板 |
| `50-Agents/agent-rules.md` | Agent 治理规则 |
| `60-Reviews/review-template.md` | 周复盘模板 |
| `.workbuddy/memory/MEMORY.md` | 项目级长期记忆 |
| `.workbuddy/memory/YYYY-MM-DD.md` | 项目级每日记忆日志 |
| `AGENTS.md` | 仓库级指导文件 |

## 基础约定

1. **YAML frontmatter**：所有项目/任务文件需含 `created`、`status`、`tags` 字段。
2. **日期格式**：`YYYY-MM-DD`。
3. **中文输出**：所有写入内容使用中文。
4. **最小修改**：只更新与本次工作相关的节，不改变文件其他部分的结构或内容。
5. **只写有实质内容**：不为了"记录"而记录空壳信息。没有值得写的结论就跳过对应节。
