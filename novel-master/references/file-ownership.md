# file-ownership.md

> 用途：定义每个 Skill 的文件读写权限边界，路径校验脚本必须与此表一致。
> 读取时机：所有 Skill 在确定目标路径或执行写入前，通过 SKILL.md 中的相对链接读取。
> 来源：冻结契约 §3.3。

## 所有权总表

| 文件区域 | 主要负责人（可写） | 其他组件权限 |
|----------|-------------------|-------------|
| `project.yaml` | novel-master | 子 Skill 只读 |
| `project_brief.md` | novel-brief | 只读或 Proposal |
| `architecture/` | story-architect / STORY | 只读或 Proposal |
| `characters/` | story-architect / CHARACTER | 只读或人物状态 Proposal |
| `world/` | story-architect / WORLD | 只读或设定 Proposal |
| `outline/` | story-architect / PLOT | chapter-planner 只读 |
| `chapters/plans/` | chapter-planner | chapter-writer 只读 |
| `chapters/drafts/` | chapter-writer | 其他子 Skill 只读 |
| `reviews/` | novel-reviewer | 其他子 Skill 只读 |
| `state/` | continuity-keeper | 禁止直接写入 |
| `workflow/` | novel-master | 子 Skill 只能通过结果字段提交内容 |

## 各 Skill 权限明细

### novel-master
- 可写：`project.yaml`、`workflow/`
- 可读：全部
- 禁止：直接生成简报、架构、章节卡、正文、评审报告、Canon 更新

### novel-brief
- 可写：`project_brief.md`
- 可读：全部（只读）
- 禁止：写大纲、世界百科、正文、擅自确定结局

### story-architect / STORY
- 可写：`architecture/`
- 可读：`project_brief.md`、`characters/`、`world/`、`outline/`
- 禁止：写正文、写状态、跨模式写入

### story-architect / CHARACTER
- 可写：`characters/`
- 可读：`project_brief.md`、`architecture/`、`world/`
- 禁止：写正文、写状态、跨模式写入

### story-architect / WORLD
- 可写：`world/`
- 可读：`project_brief.md`、`architecture/`、`characters/`
- 禁止：写正文、写状态、跨模式写入

### story-architect / PLOT
- 可写：`outline/`
- 可读：`architecture/`、`characters/`、`world/`
- 禁止：写正文、写状态、跨模式写入

### chapter-planner
- 可写：`chapters/plans/chapter_*.md`
- 可读：`outline/`、`state/`、`architecture/`、`characters/`、`world/`
- 禁止：修改总纲、写正文、写状态、增加未授权规则

### chapter-writer
- 可写：`chapters/drafts/chapter_*.md`
- 可读：`chapters/plans/`、`state/`（通过 ContextPack）、`characters/`、`world/`
- 禁止：修改总纲、写 `state/`、写 `outline/`、超出 max_edit_level

### novel-reviewer
- 可写：`reviews/*.md`（仅 artifact_persistence_allowed: true 时）
- 可读：全部（只读）
- 禁止：修改评审对象、写 `state/`、直接重写正文

### continuity-keeper
- 可写：`state/` 中与当前模式对应的文件
- 可读：全部
- 禁止：创造剧情、修改正文、把 Proposal 自动提交为 Canon、删除冲突记录

## 跨区域拆分规则

1. 同一调用不得同时写入两个不同主要负责人区域。
2. 跨区域任务必须由 novel-master 拆分为多次调用。
3. 每次调用只激活一个模式（story-architect 尤其注意）。
4. 未声明模式、声明多个模式或目标路径跨越多个所有权区域时，返回 `BLOCKED / INVALID_SKILL_MODE`。

## 路径校验规则

- 所有目标路径必须位于 `project.yaml` 的 `root_path` 内。
- 跨项目读取或写入必须拒绝并返回 `BLOCKED / PATH_OUTSIDE_PROJECT`。
- 单次 TaskEnvelope 只能引用一个 project_id。
- 写入前校验目标路径是否属于当前 Skill 的可写区域，否则返回 `OWNERSHIP_VIOLATION`。
