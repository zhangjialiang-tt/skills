# 四类卡片约定

## 目录与动作白名单

| `card_type` | 目录 | 允许动作 | 限制 |
|---|---|---|---|
| `log` | `10-Daily/YYYY-MM-DD.md` | `list`、`read`、`create`、`append` | 按日期定位；禁止静默改写历史 |
| `task` | `20-Tasks/active/*.md`、`20-Tasks/done/*.md` | `list`、`search`、`read`、`create`、`update`、`archive` | 创建在 `active/`；归档到 `done/` |
| `project` | `30-Projects/*.md` | `list`、`search`、`read`、`create`、`update` | 排除 `project-template.md` 写入 |
| `knowledge` | `70-Knowledge/*.md` | `list`、`search`、`read`、`create`、`update` | 不提供删除或归档 |

只读治理文件：

- `AGENTS.md`
- `50-Agents/agent-rules.md`
- `20-Tasks/task-template.md`
- `30-Projects/project-template.md`

治理文件只提供约束和模板，不扩大目录白名单，也不得由本 skill 修改。

明确禁止：

- `.workbuddy/`
- `.obsidian/`
- `.git/`
- `00-Inbox/`、`40-Prompts/`、`60-Reviews/`、`90-Archive/`、`docs/`
- vault 外部路径和解析后逃逸白名单的链接或路径

## 路由规则

| 请求线索 | `card_type` | 默认动作 |
|---|---|---|
| 活跃任务、任务卡、完成任务、归档任务 | `task` | 按动词选择 |
| 知识卡、知识库、知识条目 | `knowledge` | 按动词选择 |
| 日志卡、今日日志、今天干了什么、写工作日志 | `log` | 读取或追加 |
| 项目卡、项目状态、项目文件、项目记忆 | `project` | 读取或更新 |

兼容旧说法：

- “查项目状态” → 读取项目卡。
- “更新项目文件” → 更新项目卡。
- “更新项目记忆” → 更新项目卡的已验证结论、待验证假设、关键决策或常见问题；不访问旧记忆目录。
- “查今日日志”“看今天干了什么” → 读取当日日志卡。
- “查工作台”“工作台同步”“记录到工作台”没有其他卡片线索 → 先询问卡片类型，不访问文件。

以下请求不产生 vault 写入：

- 完成代码修改、构建或验证，但用户没有明确要求写入。
- 纯聊天、普通知识问答、未落地方案讨论。
- 只读查询。

## 自动联动

自动联动只发生在用户明确授权主写入之后。

| 主写入 | 日志卡联动 | 项目卡联动 |
|---|---|---|
| 创建、推进或归档任务卡 | 追加动作摘要 | 仅当任务已明确关联项目，且改变项目状态、目标、阻塞、已验证结论、关键决策或下一步 |
| 创建或更新项目卡 | 追加动作摘要 | 无 |
| 创建或更新知识卡 | 追加动作摘要 | 无 |
| 创建或追加日志卡 | 无 | 无 |

细则：

1. 在写入前列出主目标和所有联动目标。
2. 当日日志不存在时，允许创建后追加。
3. 任务未明确关联项目时，只联动日志，不搜索或创建项目卡。
4. 关联项目卡不存在时，跳过项目联动并报告；不得自动创建。
5. 联动内容已存在时不重复追加。
6. 读取操作永不联动。

## 文件命名

- 日志卡：`YYYY-MM-DD.md`
- 任务卡：`YYYY-MM-DD-<lowercase-kebab-slug>.md`
- 项目卡：`<lowercase-kebab-slug>.md`
- 知识卡：`<lowercase-kebab-slug>.md`

创建前检查同目录中的同名和语义相近卡片。无法确认是否重复时先询问。

## 模板

### 日志卡

```markdown
# YYYY-MM-DD

## 今天做了什么

## 今天推进了哪些项目

## 今天遇到的问题

## 今天形成的结论

## 明天最重要的一件事
```

只填写能够确认的内容，不添加“无”“暂无”“待定”等占位条目。

### 任务卡

创建前优先读取 `20-Tasks/task-template.md`，并保持其当前字段和章节。至少包含：

```yaml
---
created: YYYY-MM-DD
status: active
tags: [task]
---
```

归档时：

1. 确认最终结果和剩余风险已经记录。
2. 将 `status` 改为 `resolved`。
3. 将文件移至 `20-Tasks/done/`。
4. 追加当日日志。

### 项目卡

创建前优先读取 `30-Projects/project-template.md`，并保持其当前字段和章节。至少包含：

```yaml
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [project]
---
```

更新时只修改与本次事件对应的状态、目标、阻塞、结论、决策、下一步或更新记录。

### 知识卡

```markdown
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: maintained
tags: [knowledge, <topic>]
aliases: []
---

# <标题>

## 适用范围

## 核心内容

## 已验证结论

## 使用示例

## 注意事项
```

只沉淀可复用内容。项目当前进度写项目卡，单次过程写任务卡，时间线动作写日志卡。
