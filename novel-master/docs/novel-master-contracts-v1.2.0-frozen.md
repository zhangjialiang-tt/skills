---
title: novel-master V1.2 契约手册
document_id: NM-CONTRACT
version: 1.2.0
status: FROZEN
frozen_at: 2026-07-25
supersedes: novel-master-contracts-v1.1.0-frozen.md
applies_to: novel-master V1.2 章节生产与质量契约
companion: novel-master-architecture-v1.2.0-frozen.md
---

# novel-master V1.2 契约手册

## 1. 文档定位

本文是 `novel-master` V1 的可执行契约参考，规定项目目录、文件所有权、统一数据结构、路由规则、子 Skill 契约、异常处理和降级策略。

系统目标、设计理由、实施计划和验收策略见
[《`novel-master` 工业级网文创作 Skill 架构总纲》](novel-master-architecture-v1.2.0-frozen.md)。

若两份冻结文档发生语义冲突：

1. 权限、不变量和风险控制以架构总纲为准。
2. 字段、枚举、路径、路由和 I/O 以本手册为准。
3. 无法按上述规则解决时，停止相关写操作并登记文档缺陷。

### 1.1 目录

- 1. 文档定位
- 2. V1 组件与模式
- 3. 项目目录与所有权
- 4. 信息状态、章节生命周期与来源
- 5. 统一输入契约：`TaskEnvelope`
- 6. 统一输出契约：`SkillResult`
- 7. 授权契约：`ApprovalRef`
- 8. 状态提交事务：`ChangeSet`
- 9. 上下文包契约：`ContextPack`
- 10. `novel-master` 路由算法
- 11. 模糊用户意图处理
- 12. V1 子 Skill 契约
- 13. 异常与降级策略
- 14. 编排器输出：`MasterResult`
- 15. 契约一致性检查清单
- 16. V1 到目标架构的兼容要求
- 17. 变更记录

### 1.2 架构决策引用

本手册实现以下冻结决策：

- [ADR 6.1：Canon 单一写入者](novel-master-architecture-v1.2.0-frozen.md#nm-arch-decision-single-writer)
- [ADR 6.2：`chapter-writer` 不修改 Canon](novel-master-architecture-v1.2.0-frozen.md#nm-arch-decision-writer-no-canon)
- [ADR 6.3：评审和修改分离](novel-master-architecture-v1.2.0-frozen.md#nm-arch-decision-review-edit)
- [ADR 6.4：最小上下文包](novel-master-architecture-v1.2.0-frozen.md#nm-arch-decision-min-context)

## 2. V1 组件与模式

### 2.1 编排器

`novel-master` 负责：

- 识别用户意图、项目阶段、影响范围和风险。
- 选择最小必要路由。
- 构造 `TaskEnvelope`。
- 校验子 Skill 返回的 `SkillResult`。
- 处理越权、冲突和待决策项。
- 汇总 `MasterResult`。

`novel-master` 禁止直接生成项目简报、故事架构、章节卡、正式正文、评审报告或 Canon 更新。

### 2.2 V1 子 Skill

| Skill               | 模式                                                                                                                                                                                                                       |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `novel-brief`       | `DEFAULT`                                                                                                                                                                                                                  |
| `story-architect`   | `STORY`、`CHARACTER`、`WORLD`、`PLOT`                                                                                                                                                                                      |
| `novel-style`       | `DEFAULT`                                                                                                                                                                                                                  |
| `chapter-planner`   | `DEFAULT`                                                                                                                                                                                                                  |
| `chapter-writer`    | `WRITE`、`CONTINUE`、`EDIT`                                                                                                                                                                                                |
| `novel-reviewer`    | `DEFAULT`                                                                                                                                                                                                                  |
| `continuity-keeper` | `EXTRACT_CONTEXT`、`CHECK_CONTRADICTIONS`、`COMMIT_CHAPTER_STATE`、`COMMIT_CANON`、`IMPACT_ANALYSIS`、`GENERATE_SUMMARY`、`RESTORE_PROJECT / EXTRACT_EVIDENCE`、`RESTORE_PROJECT / REBUILD_STATE`、`REBUILD_DERIVED_STATE` |

## 3. 项目目录与所有权

### 3.1 标准目录

```text
<project-root>/
├─ project.yaml
├─ project_brief.md
├─ style_guide.md
│
├─ architecture/
│  ├─ story_architecture.md
│  ├─ themes.md
│  └─ story_promises.md
│
├─ characters/
│  ├─ protagonist.md
│  ├─ antagonist.md
│  ├─ supporting_cast.md
│  └─ relationship_map.md
│
├─ world/
│  ├─ world_overview.md
│  ├─ factions.md
│  ├─ power_system.md
│  ├─ locations.md
│  └─ glossary.md
│
├─ outline/
│  ├─ master_outline.md
│  ├─ volume_01.md
│  └─ subplot_tracker.md
│
├─ chapters/
│  ├─ plans/
│  │  └─ chapter_001.md
│  └─ drafts/
│     └─ chapter_001.md
│
├─ reviews/
│  └─ chapter_001_review.md
│
├─ state/
│  ├─ canon.md
│  ├─ timeline.md
│  ├─ character_state.md
│  ├─ chapter_summaries.md
│  ├─ foreshadowing.md
│  ├─ open_loops.md
│  ├─ knowledge_state.md
│  ├─ contradictions.md
│  └─ archives/
│     └─ summary_volume_01.md
│
└─ workflow/
   ├─ route_log.md
   ├─ pending_decisions.md
   └─ change_log.md
```

### 3.2 项目标识

`project.yaml` 至少包含：

```yaml
schema_version: "1.0"
project_id: string
title: string
language: zh-CN
root_path: string
current_volume: string | null
current_chapter: string | null
created_at: string
updated_at: string
```

约束：

- `project_id` 在本地工作区内必须唯一。
- `root_path` 必须指向当前项目根目录。
- 单次 `TaskEnvelope` 只能引用一个 `project_id`。
- 所有目标路径必须位于 `root_path` 内。
- 跨项目读取或写入必须拒绝并返回 `BLOCKED`。

### 3.3 文件所有权

| 文件区域           | V1 主要负责人                 | 其他组件权限                      |
| ------------------ | ----------------------------- | --------------------------------- |
| `project.yaml`     | `novel-master`                | 子 Skill 只读                     |
| `project_brief.md` | `novel-brief`                 | 只读或 Proposal                   |
| `architecture/`    | `story-architect / STORY`     | 只读或 Proposal                   |
| `characters/`      | `story-architect / CHARACTER` | 只读或人物状态 Proposal           |
| `world/`           | `story-architect / WORLD`     | 只读或设定 Proposal               |
| `outline/`         | `story-architect / PLOT`      | `chapter-planner` 只读            |
| `style_guide.md`   | `novel-style`                 | 只读或 Proposal                   |
| `chapters/plans/`  | `chapter-planner`             | `chapter-writer` 只读             |
| `chapters/drafts/` | `chapter-writer`              | 其他子 Skill 只读                 |
| `reviews/`         | `novel-reviewer`              | 其他子 Skill 只读                 |
| `state/`           | `continuity-keeper`           | 禁止直接写入                      |
| `workflow/`        | `novel-master`                | 子 Skill 只能通过结果字段提交内容 |

同一调用不得同时写入两个不同主要负责人区域。跨区域任务必须由 `novel-master` 拆分调用。

## 4. 信息状态、章节生命周期与来源

所有事实类内容必须标记为：

```text
CANON
PROPOSAL
DEPRECATED
UNKNOWN
```

### 4.1 状态转换

允许：

```text
UNKNOWN → PROPOSAL
PROPOSAL → CANON          仅在有授权且经 continuity-keeper 提交时
CANON → DEPRECATED        仅在影响分析、用户确认后
DEPRECATED → PROPOSAL     仅作为恢复旧方案的候选
```

禁止：

```text
UNKNOWN → CANON           无证据直接确认
PROPOSAL → CANON          子 Skill 自行确认
DEPRECATED → CANON        静默恢复旧设定
CANON → 删除              抹除历史
```

### 4.2 来源要求

每个 Canon 或状态更新至少包含：

```yaml
id: string
statement: string
source:
  type: user_decision | project_file | chapter | approved_plan
  ref: string
effective_from: string | null
status: CANON
```

无法定位来源时，只能标记为 `UNKNOWN` 或 `PROPOSAL`。

<a id="nm-contract-chapter-lifecycle"></a>

### 4.3 章节生命周期

章节计划或正文交付物必须携带：

```yaml
chapter_lifecycle:
  status: PLANNED | DRAFT | REVIEWED | ACCEPTED | SUPERSEDED | DEPRECATED | PUBLISHED
  accepted_by: user | approved_workflow | null
  acceptance_ref: string | null
  published_ref: string | null
```

字段约束：

- `accepted_by` 只在 `ACCEPTED` 或 `PUBLISHED` 时非空。
- `acceptance_ref` 必须引用有效的 `ApprovalRef.approval_id`。
- `published_ref` 只在 `PUBLISHED` 时必填，指向用户提供的发布记录。
- 生命周期元数据必须绑定具体 `deliverable_id`、`revision` 和 `content_hash`。

允许的状态转换：

| 转换                    | 触发条件                                       |
| ----------------------- | ---------------------------------------------- |
| `PLANNED → DRAFT`       | `chapter-writer` 基于章节卡产出正文            |
| `DRAFT → REVIEWED`      | 完成自动或人工评审，评审对象 revision 未变化   |
| `DRAFT → ACCEPTED`      | 用户直接接受，或命中允许跳过评审的自动接受授权 |
| `REVIEWED → DRAFT`      | 根据评审修改后产生新 revision                  |
| `REVIEWED → ACCEPTED`   | 用户明确接受，或命中自动接受工作流             |
| `ACCEPTED → SUPERSEDED` | 新版本被接受并替换当前版本                     |
| `ACCEPTED → DEPRECATED` | 用户明确废弃该章节                             |
| `ACCEPTED → PUBLISHED`  | 用户标记为已发布并提供发布引用                 |

未列出的转换全部禁止。`SUPERSEDED`、`DEPRECATED` 和 `PUBLISHED` 是 V1 终态；后续修改必须创建新 `deliverable_id` 或新 revision。

只有 `ACCEPTED` 或 `PUBLISHED` 章节可以作为 `COMMIT_CHAPTER_STATE` 的来源。章节处于 `DRAFT` 或 `REVIEWED` 时，`chapter_report` 中的变化只能进入 `state_change_proposals`。

### 4.4 来源优先级

来源冲突时按以下规则从高到低比较：

```yaml
source_priority:
  rules:
    - priority: 6
      source_type: user_decision
      condition: 最新且仍有效的显式用户确认
    - priority: 5
      source_type: chapter
      condition: ACCEPTED 或 PUBLISHED 的正文
    - priority: 4
      source_type: canon
      condition: 当前有效且非 Deprecated 的 Canon
    - priority: 3
      source_type: approved_plan
      condition: 已批准但尚未执行的计划
    - priority: 2
      source_type: chapter
      condition: DRAFT 或 REVIEWED 的正文
    - priority: 1
      source_type: proposal
      condition: AI Proposal
    - priority: 0
      source_type: inference
      condition: 推断

  exceptions:
    - 未 ACCEPTED 的后写正文不能自动覆盖旧 Canon
    - 用户显式声明“以 X 为准”时，该来源在批准范围内临时提升为最高
    - 任一来源冲突都必须保留双方证据并登记 contradictions.md
```

高优先级来源不是静默覆盖许可。若覆盖会导致 Retcon、废弃 Canon 或多章返工，仍必须执行影响分析和授权流程。

## 5. 统一输入契约：`TaskEnvelope`

```yaml
task_envelope:
  schema_version: "1.0"
  request_id: string
  project:
    project_id: string
    root_path: string

  user_request: string

  task:
    type: enum
    scope: enum
    mode: enum
    risk_level: enum
    target_skill: string
    target_skill_mode: string
    skill_mode: string
    semantic_impact:
      fact_change: boolean
      state_change: boolean
      plot_outcome_change: boolean
      downstream_scope: NONE | SCENE | CHAPTER | MULTI_CHAPTER

  authority:
    operation: enum
    canon_change_allowed: boolean
    structural_change_allowed: boolean
    prose_change_allowed: boolean
    source_mutation_allowed: boolean
    artifact_persistence_allowed: boolean
    state_mutation_allowed: boolean
    max_edit_level: NONE | L1 | L2 | L3 | L4
    user_confirmation_ref: string | null
    approval_ref: object | null

  context:
    required_files:
      - path: string
        revision: string
        hash: string | null
    optional_files:
      - path: string
        revision: string
        hash: string | null
    context_pack: object | null
    base_revision: object | null

  constraints:
    must_preserve: []
    must_include: []
    must_avoid: []
    target_length: string | null
    target_style: string | null
    viewpoint: string | null

  output:
    expected_deliverables: []
    target_paths: []
```

### 5.1 文件引用：`FileRef`

```yaml
file_ref:
  path: string
  revision: string
  hash: string | null
```

- `revision` 是项目内单调变化的文件版本标识。
- `hash` 推荐使用 SHA-256；未提供 hash 时仍必须校验 revision。
- V1.0 的纯路径字符串输入可在兼容期读取，但 1.0.1 写出方必须产生完整 `FileRef`。
- 文件内容变化时必须更新 revision 和 hash。

### 5.2 `task.type`

```text
INIT_PROJECT
REFINE_BRIEF
DESIGN_STORY
DESIGN_CHARACTER
DESIGN_WORLD
PLAN_PLOT
PLAN_VOLUME
PLAN_CHAPTER
WRITE_CHAPTER
CONTINUE_CHAPTER
REVIEW_TEXT
EDIT_TEXT
CHECK_CONTINUITY
UPDATE_CANON
RETCON
RESUME_PROJECT
BRAINSTORM
SUMMARIZE_STATE
```

### 5.3 `task.scope`

```text
SNIPPET
SCENE
CHAPTER
MULTI_CHAPTER
ARC
VOLUME
PROJECT
```

### 5.4 `task.mode`

| 模式       | 语义                                         |
| ---------- | -------------------------------------------- |
| `FAST`     | 低风险、最短链路；默认不评审、不提交正式状态 |
| `STANDARD` | 日常创作；执行必要一致性检查和状态提交       |
| `STRICT`   | 关键内容；增加评审、扩大一致性检查           |
| `ADVISORY` | 只提供建议，不写正式项目文件和状态           |

### 5.5 `task.risk_level`

```text
LOW
MEDIUM
HIGH
```

<a id="nm-contract-authority"></a>

### 5.6 `authority` 与 `operation`

```text
READ_ONLY
CREATE_DRAFT
EDIT_DRAFT
PROPOSE_CHANGE
COMMIT_STATE
```

权限约束：

- `COMMIT_STATE` 的 `target_skill` 必须是 `continuity-keeper`。
- `READ_ONLY` 必须令 `source_mutation_allowed: false` 和 `state_mutation_allowed: false`。
- `READ_ONLY` 可以在 `artifact_persistence_allowed: true` 时向独立报告路径写入产物；该产物必须标记为“未改变原项目源文件或状态”。
- `artifact_persistence_allowed: false` 时，`READ_ONLY` 的 `target_paths` 必须为空。
- `ADVISORY` 不得使用 `COMMIT_STATE`。
- `canon_change_allowed: true` 时必须提供有效 `approval_ref`；`user_confirmation_ref` 仅作为 1.0.0 兼容字段保留。
- `EDIT_DRAFT` 必须声明 `max_edit_level`。
- `task.skill_mode` 是 1.0.1 的规范模式字段；`target_skill_mode` 作为 1.0.0 兼容字段保留，两者同时存在时必须相同。
- 旧的 `canon_change_allowed`、`structural_change_allowed` 和 `prose_change_allowed` 字段继续保留，但不得授予超出三个细粒度权限字段的能力。

权限组合：

| 用户表达             | `source_mutation_allowed` | `artifact_persistence_allowed` | `state_mutation_allowed` |
| -------------------- | ------------------------- | ------------------------------ | ------------------------ |
| “只分析这一章”       | `false`                   | `true`                         | `false`                  |
| “不要修改任何东西”   | `false`                   | `false`                        | `false`                  |
| “检查问题并生成报告” | `false`                   | `true`                         | `false`                  |
| “校对一下”           | `true`，仅 L1             | `true`                         | `false`                  |

“只分析这一章”的报告落盘是默认解释；如果用户同时说“不保存”“不要修改任何东西”或等价表达，`artifact_persistence_allowed` 必须降为 `false`。

<a id="nm-contract-risk-derivation"></a>

### 5.7 编辑风险推导

```yaml
risk_level_derivation:
  - condition: L1
    result: LOW
  - condition: L2 and no fact/state/plot outcome change
    result: MEDIUM
  - condition: L3 and downstream_scope == SCENE and no fact/state/plot outcome change
    result: MEDIUM
  - condition: L3 and any fact/state/plot outcome change
    result: HIGH
  - condition: L4
    result: HIGH
```

- `HIGH` 风险编辑必须先完成 `IMPACT_ANALYSIS` 并提供有效 `ApprovalRef`。
- 执行中实际语义影响高于预估时，停止扩大修改，返回 `NEEDS_DECISION` 并重新推导风险。

## 6. 统一输出契约：`SkillResult`

```yaml
skill_result:
  schema_version: "1.0"
  skill: string
  skill_mode: string
  request_id: string
  status: enum

  summary: string

  deliverables:
    - type: string
      path: string | null
      content_summary: string
      status: draft | confirmed | revised
      deliverable_id: string
      revision: string
      content_hash: string
      supersedes: string | null
      chapter_lifecycle_status: PLANNED | DRAFT | REVIEWED | ACCEPTED | SUPERSEDED | DEPRECATED | PUBLISHED | null

  state_change_proposals:
    - type: canon_candidate | state_update | deprecation | contradiction
      description: string
      evidence: string
      source_ref: string
      risk_level: LOW | MEDIUM | HIGH
      requires_user_confirmation: boolean

  proposals:
    - description: string
      rationale: string
      impact_scope: string
      recommended: boolean
      requires_user_confirmation: boolean
      proposal_type: creative_option | structural_change | canon_change | workflow_change
      source_ref: string

  issues:
    - severity: info | warning | blocker
      category: string
      description: string
      affected_files: []
      suggested_resolution: string

  handoff:
    recommended_next_skill: string | null
    recommended_next_mode: string | null
    reason: string | null
    required_context: []

  completion:
    criteria_met: []
    criteria_unmet: []
```

### 6.1 `status`

```text
COMPLETED
COMPLETED_WITH_WARNINGS
NEEDS_DECISION
BLOCKED
FAILED
```

语义：

- `COMPLETED`：全部完成标准满足。
- `COMPLETED_WITH_WARNINGS`：交付物可用，但存在非阻塞风险。
- `NEEDS_DECISION`：低风险部分已尽量完成，高风险部分等待用户决定。
- `BLOCKED`：缺少必要输入、权限或存在未解决阻塞冲突。
- `FAILED`：执行异常，交付物不可作为正式结果。

子 Skill 不得用 `COMPLETED` 掩盖 `criteria_unmet`。

`deliverables.status` 是 1.0.0 兼容字段，继续使用小写 `draft | confirmed | revised`；章节的规范状态由 `chapter_lifecycle_status` 表达。非章节交付物的生命周期字段为 `null`。除该兼容字段和 `issues.severity` 外，风险与工作流枚举统一使用大写。

<a id="nm-contract-approval"></a>

## 7. 授权契约：`ApprovalRef`

```yaml
approval:
  approval_id: string
  request_id: string
  approved_by: user
  approved_at: string
  operation: COMMIT_CANON | RETCON | EDIT_L3 | EDIT_L4 | ACCEPT_CHAPTER | INIT_PROJECT
  approved_scope:
    files: []
    items: []
  based_on_revision: string
  expires_after_use: boolean
  status: ACTIVE | USED | EXPIRED | REVOKED
```

约束：

- `approved_at` 使用 ISO 8601。
- `based_on_revision` 必须指向批准时用户审阅的具体文件或交付物 revision。
- 目标内容、hash 或 revision 发生变化后，旧授权自动变为 `EXPIRED`。
- `L4` 和 `RETCON` 必须使用 `expires_after_use: true` 的一次性授权。
- `EDIT_L3` 只有在风险为 `HIGH` 时强制授权。
- 自动日更可以使用 `ACCEPT_CHAPTER` 持续授权，但必须限定项目、章节范围、允许偏离程度和失效条件。
- 授权使用后，`expires_after_use: true` 的状态改为 `USED`。
- `user_confirmation_ref` 在兼容期保存 `approval_id`；不能用自由文本替代完整 ApprovalRef。

### 7.1 授权有效性检查

执行前必须同时满足：

1. `status: ACTIVE`。
2. `request_id` 或批准范围覆盖当前请求。
3. `operation` 与实际操作一致；`INIT_PROJECT` 可以在同一初始化范围内授权一次初始 `COMMIT_CANON`。
4. `approved_scope` 覆盖所有目标文件和条目。
5. `based_on_revision` 与当前内容一致。
6. 授权没有被使用、撤销或过期。

任一条件不满足时返回 `BLOCKED / INVALID_APPROVAL`。

### 7.2 初始化确认闸门

```yaml
approval_gate:
  required: true
  approval_scope:
    - project_brief
    - story_architecture
    - principal_characters
    - core_world_rules
    - active_plot_plan
    - style_guide
  confirmation_format: structured_summary | full_review
```

`INITIALIZATION_REVIEW` 必须输出上述六类内容的摘要、对应 revision、待确认项和冲突。用户确认或明确自动授权后，生成 `operation: INIT_PROJECT` 的 ApprovalRef，再允许 `COMMIT_CANON`。

<a id="nm-contract-changeset"></a>

## 8. 状态提交事务：`ChangeSet`

```yaml
change_set:
  change_set_id: string
  request_id: string
  source_ref: string
  base_revision: object
  target_updates:
    - target_file: string
      operation: ADD | MODIFY | DELETE
      content: string
  status: PREPARED | VALIDATED | COMMITTED | ROLLED_BACK | FAILED
  created_at: string
  committed_at: string | null
```

### 8.1 提交协议

```text
1. PREPARE：生成包含全部目标文件的完整 ChangeSet
2. VALIDATE：校验来源、章节生命周期、权限、冲突、ApprovalRef 和 base_revision
3. APPLY：将所有结果写入同目录 `*.tmp` 临时文件
4. VERIFY：重新读取临时文件并校验格式、内容和交叉一致性
5. COMMIT：原子替换正式文件，更新 change_log 和文件 revision
6. 任一步骤失败：标记 ROLLED_BACK，清理临时文件，正式文件保持提交前状态
```

约束：

- 所有 `state_mutation_allowed: true` 的操作都必须使用 ChangeSet，包括 `COMMIT_CHAPTER_STATE`、`COMMIT_CANON`、`RESTORE_PROJECT / REBUILD_STATE`、`REBUILD_DERIVED_STATE`，以及会写入 `state/` 的冲突登记或摘要生成。
- `base_revision` 必须覆盖本次读取和写入的全部状态文件。
- 提交前当前 revision 与 `base_revision` 不一致时返回 `BLOCKED / STALE_CONTEXT`。
- `DELETE` 不得删除 Canon 或审计历史；对历史项使用 `DEPRECATED`。删除只用于无历史语义的派生条目或临时错误产物。
- `change_log.md` 与状态文件属于同一事务；日志更新失败则整个事务回滚。
- 回滚失败时返回 `FAILED / ROLLBACK_FAILED`，停止所有后继写操作并保留诊断信息。

### 8.2 提交输入

```yaml
commit_input:
  source_deliverable:
    deliverable_id: string
    revision: string
    content_hash: string
    chapter_lifecycle_status: ACCEPTED | PUBLISHED | null
  approval_ref: object | null
  base_revision:
    state/canon.md: string
    state/timeline.md: string
    state/character_state.md: string
    state/knowledge_state.md: string
    state/foreshadowing.md: string
    state/open_loops.md: string
  change_set: object
```

`COMMIT_CHAPTER_STATE` 的 `chapter_lifecycle_status` 不得为 `null`，且必须是 `ACCEPTED` 或 `PUBLISHED`。

## 9. 上下文包契约：`ContextPack`

```yaml
context_pack:
  schema_version: "1.0"
  generated_for_request: string
  project_snapshot:
    project_id: string
    title: string
    genre: string
    current_volume: string
    current_chapter: string
    current_story_phase: string

  current_state:
    time: string | UNKNOWN
    location: string | UNKNOWN
    active_conflict: string | UNKNOWN
    protagonist_goal: string | UNKNOWN

  relevant_characters:
    - name: string
      current_status: string
      current_goal: string
      known_information: []
      relationship_changes: []
      source_refs: []

  relevant_canon:
    - id: string
      statement: string
      source_ref: string

  active_open_loops:
    - id: string
      description: string
      urgency: low | medium | high
      source_ref: string

  active_foreshadowing:
    - id: string
      status: planted | reinforced | partially_revealed
      usage_constraint: string
      source_ref: string

  timeline_constraints: []
  prohibited_conflicts: []
  style_constraints: []
  unknowns: []
  source_refs: []
  omitted_context_refs: []
  budget:
    substantive_characters: integer
    estimated_tokens: integer
    truncated: boolean
```

约束：

- 只包含当前任务直接相关信息。
- 事实必须附来源，未知信息必须进入 `unknowns`。
- 实质内容目标不超过 2,000 个中文字符，完整结果不超过 4,000 tokens。
- 超限时按“硬约束 → Canon → 当前状态 → 知识范围 → 活跃伏笔 → 风格提示”保留。
- 被省略但可能相关的内容进入 `omitted_context_refs`。

## 10. `novel-master` 路由算法

### 10.1 决策顺序

```text
1. 识别显式操作与禁止项
2. 定位 project_id 和项目阶段
3. 判断任务类型、范围、模式和风险
4. 检查必要输入、revision、授权与 Canon 冲突
5. 选择最小必要子 Skill
6. 高风险时插入影响分析和用户确认
7. 章节写作后执行接受闸门
8. 只有 ACCEPTED/PUBLISHED 内容产生事实变化时插入状态提交
9. 校验结果、处理越权并汇总
```

### 10.2 项目阶段

| 项目状态                        | 默认下一步                               |
| ------------------------------- | ---------------------------------------- |
| 项目不存在                      | `novel-brief`                            |
| 有简报，无故事结构              | `story-architect / STORY`                |
| 有故事结构，缺必要人物/世界规则 | 对应 `CHARACTER` / `WORLD`               |
| 有结构，无可执行大纲            | `story-architect / PLOT`                 |
| 有大纲，无章节卡                | `chapter-planner`                        |
| 有章节卡，无正文                | `chapter-writer / WRITE`，产物为 `DRAFT` |
| 有正文                          | 根据请求进入评审、编辑或状态流程         |

只补齐当前任务的必要上游，不自动执行整个初始化链。

### 10.3 路由优先级

从高到低：

1. 用户显式禁止项和只读要求。
2. 安全、项目隔离和权限边界。
3. Canon 冲突与高风险影响分析。
4. 上游必要依赖。
5. 用户显式指定的操作。
6. 最小路由原则。
7. 默认工作流。

### 10.4 总路由表

#### 新书与设计

| 用户意图           | 主路由                                                                                                                    | 状态处理                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| 从想法创建新书     | `novel-brief → STORY`                                                                                                     | 只生成设计产物，不直接提交 Canon                  |
| 完整新书初始化     | `novel-brief → STORY → CHARACTER → WORLD → PLOT → novel-style → INITIALIZATION_REVIEW → 用户确认/自动授权 → COMMIT_CANON` | ApprovalRef 必须覆盖全部初始化范围和当前 revision |
| 修改作品定位       | `novel-brief → IMPACT_ANALYSIS`                                                                                           | 高风险时待用户确认                                |
| 设计主线/结局方向  | `STORY`                                                                                                                   | 重大变化只作为 Proposal                           |
| 设计人物/关系      | `CHARACTER`                                                                                                               | 正式采用后提交 Canon                              |
| 设计世界/力量体系  | `WORLD → CHECK_CONTRADICTIONS`                                                                                            | 新规则先作为候选                                  |
| 生成整书/分卷大纲  | `STORY → PLOT` 或仅 `PLOT`                                                                                                | 已确认结构可提交                                  |
| 确立或修订风格指南 | `novel-style`（定位/基调变化时前置 `IMPACT_ANALYSIS`）                                                                    | 高风险时待用户确认                                |

#### 章节生产

| 用户意图                 | 主路由                                                                                            | 状态处理                         |
| ------------------------ | ------------------------------------------------------------------------------------------------- | -------------------------------- |
| 规划下一章               | `EXTRACT_CONTEXT → chapter-planner`                                                               | 不提交已发生状态                 |
| 根据大纲写一章，默认协作 | `EXTRACT_CONTEXT → chapter-planner → WRITE → 输出 proposals → 用户 ACCEPT → COMMIT_CHAPTER_STATE` | 未接受前保持 DRAFT               |
| 根据大纲写一章，自动日更 | `EXTRACT_CONTEXT → chapter-planner → WRITE → REVIEW（可选）→ 自动 ACCEPT → COMMIT_CHAPTER_STATE`  | 必须有覆盖当前 revision 的预授权 |
| 已有完整章节卡           | `EXTRACT_CONTEXT → WRITE → ACCEPT → COMMIT_CHAPTER_STATE`                                         | 不重复规划；接受闸门不可省略     |
| 续写未完成章节           | `EXTRACT_CONTEXT → CONTINUE`                                                                      | 续写结果为新 DRAFT，接受后才提交 |
| 连写多章                 | `PLOT → 每章规划/写作/接受/提交循环`                                                              | 每章独立 revision 和增量提交     |
| 试写片段                 | `WRITE / ADVISORY`                                                                                | 不进入正式正文或状态             |

#### 评审与修改

| 用户意图                       | 主路由                                                         | 状态处理                                                 |
| ------------------------------ | -------------------------------------------------------------- | -------------------------------------------------------- |
| 只分析、不修改原文             | `novel-reviewer`                                               | 正文和状态不变；仅在允许时保存独立报告                   |
| 校对错字/标点                  | `EDIT L1`                                                      | 通常不更新状态                                           |
| 润色文风                       | `EDIT L2`                                                      | 含义变化则转检查                                         |
| 调整场景节奏，不改变事实或结果 | `novel-reviewer → EDIT L3`                                     | `semantic_impact.plot_outcome_change == false`，`MEDIUM` |
| 调整场景节奏，改变状态或结果   | `novel-reviewer → IMPACT_ANALYSIS → EDIT L3`                   | `semantic_impact` 任一变化为真，`HIGH`，需要 ApprovalRef |
| 修改章节剧情                   | `novel-reviewer → IMPACT_ANALYSIS → chapter-planner → EDIT L4` | 提交变化                                                 |
| 重写整章                       | `novel-reviewer → chapter-planner → WRITE`                     | 旧版 Deprecated                                          |
| 卷末复盘                       | `novel-reviewer → GENERATE_SUMMARY → PLOT`                     | 调整下一卷规划                                           |

#### 连续性与恢复

| 用户意图                         | 主路由                                                                                         |
| -------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------ |
| 检查前后矛盾                     | `CHECK_CONTRADICTIONS`                                                                         |
| 生成章节、卷或项目摘要           | `GENERATE_SUMMARY`                                                                             | 只写摘要目标，不重建派生索引   |
| 重建人物、时间线、知识或伏笔索引 | `REBUILD_DERIVED_STATE`                                                                        | 只基于已确认来源，不创建 Canon |
| 从正文建立档案                   | `RESTORE_PROJECT / EXTRACT_EVIDENCE → RecoveryReport → 按所有权路由 → 用户确认 → COMMIT_CANON` |
| 修改 Canon / 推翻设定            | `IMPACT_ANALYSIS → 用户确认 → 对应设计模式 → COMMIT_CANON`                                     |
| 断更后恢复                       | `RESTORE_PROJECT / EXTRACT_EVIDENCE → RecoveryReport → 必要时 REBUILD_STATE → chapter-planner` |

#### 低风险灵感

| 用户意图       | 路由                     | 约束             |
| -------------- | ------------------------ | ---------------- |
| 情节方向       | `STORY / ADVISORY`       | Proposal         |
| 人物名字       | `CHARACTER / FAST`       | 不建正式人物档案 |
| 世界设定灵感   | `WORLD / ADVISORY`       | Proposal         |
| 章节标题       | `chapter-planner / FAST` | 不更新状态       |
| 剧情合理性讨论 | `novel-reviewer`         | 只读             |

## 11. 模糊用户意图处理

| 用户表达           | 可能意图                     | 默认处理                                          |
| ------------------ | ---------------------------- | ------------------------------------------------- |
| “这章感觉平”       | 节奏、冲突或兑现不足         | 先调用 `novel-reviewer` 诊断                      |
| “帮我改改”         | 范围不明确                   | 默认先评审；最多授权 L2                           |
| “主角太弱了”       | 能力设定、表现或剧情压力问题 | 先区分问题类型，不直接改设定                      |
| “后面都推翻吧”     | 大范围 Retcon                | 先 `IMPACT_ANALYSIS`，不直接修改                  |
| “接着写”           | 续写当前场景或写下一章       | 根据当前草稿完成度判断；不清楚时只补必要信息      |
| “把设定补全”       | 可能无限扩展世界观           | 只补当前剧情所需规则                              |
| “不要动原文”       | 禁止修改源文件               | `READ_ONLY`；独立报告默认不落盘，除非用户明确要求 |
| “只分析这一章”     | 只读诊断                     | 源文件和状态不变；默认允许保存独立评审报告        |
| “不要修改任何东西” | 项目完全只读                 | 三个细粒度写权限全部为 `false`，目标路径为空      |

确认策略：

- 低风险：直接执行并报告。
- 中风险：明确范围和保留项后执行。
- 高风险：输出影响和选项，等待显式确认。
- 范围不明：采用最低安全权限；不得用猜测扩大权限。

## 12. V1 子 Skill 契约

### 12.1 `novel-brief`

**职责**：将模糊创意转化为明确、可确认的作品定义。

**触发**：创建新项目、修改定位、目标读者或创作承诺不明确。

**必需输入**：

```yaml
user_request: string
```

**可选输入**：

```yaml
platform: string
genre: string
target_length: string
target_reader: string
reference_preferences: []
exclusions: []
existing_project_brief: file
```

**输出**：

```yaml
project_brief:
  genre: string
  subgenre: string
  target_reader: string
  target_platform: string | null
  core_hook: string
  protagonist_promise: string
  primary_conflict: string
  intended_reader_experience: []
  length_and_pacing: string
  creative_constraints: []
  exclusions: []
  assumptions: []
  unresolved_decisions: []
```

**可写**：`project_brief.md`。

**禁止**：写完整大纲、设计详细世界百科、写正文、擅自确定结局、承诺市场结果。

**完成标准**：

- 一句话可以说明作品是什么。
- 目标读者和阅读承诺明确。
- 已确认项、假设和待确认项分离。
- 没有把低置信度推断写成事实。

**默认后继**：`story-architect / STORY`。

### 12.2 `story-architect`

**职责**：按单一模式完成高层故事、人物、世界或大纲设计。

#### 模式激活规则

当前调用只激活一个专业角色。未激活模式的规则、写入权限和完成标准视为不可用。

调用方必须在 `TaskEnvelope.task.skill_mode` 中声明且只能声明一个模式。`target_skill_mode` 仅作为兼容别名。未声明、声明多个模式或目标路径跨越多个所有权区域时，返回 `BLOCKED / INVALID_SKILL_MODE`。

#### `STORY` 模式

必需输入：`project_brief.md`。

输出：

```yaml
story_architecture:
  premise: string
  thematic_question: string
  protagonist_core_desire: string
  central_opposition: string
  story_promise: string
  causal_chain: []
  major_phases: []
  major_turning_points: []
  climax_direction: string
  ending_direction: string
  structural_risks: []
```

可写：`architecture/`。

完成标准：目标、阻力、代价和结果形成因果链；结构可继续拆解。

#### `CHARACTER` 模式

必需输入：`project_brief.md`、`architecture/story_architecture.md`。

输出：

```yaml
character_profile:
  identity: object
  narrative_function: string
  external_goal: string
  internal_need: string
  fear: string
  flaw: string
  strengths: []
  behavioral_logic: string
  moral_boundary: string
  secrets: []
  knowledge_state: []
  voice_characteristics: []
  relationships: []
  arc: object
  canon_candidates: []
```

可写：`characters/`。

完成标准：人物行动逻辑可解释，目标与主线相关，Canon 候选单列。

#### `WORLD` 模式

必需输入：`project_brief.md`、`architecture/story_architecture.md`。

输出：

```yaml
world_design:
  core_world_rules: []
  social_structure: []
  factions: []
  locations: []
  resources_and_economy: []
  technology_or_power_system:
    source: string
    capabilities: []
    costs: []
    limits: []
    counters: []
    progression: []
  terminology: []
  unresolved_rules: []
  contradiction_risks: []
```

可写：`world/`。

完成标准：每项规则服务剧情；能力有来源、代价、限制和反制。

#### `PLOT` 模式

必需输入：故事架构、相关人物和相关世界规则。

输出：

```yaml
plot_plan:
  scope: project | volume | arc
  start_state: string
  end_state: string
  phase_goal: string
  main_conflict: string
  event_chain: []
  subplot_movements: []
  character_progression: []
  reveals: []
  foreshadowing_actions: []
  escalation_curve: []
  climax: string
  transition_to_next_phase: string
  risks: []
```

可写：`outline/`。

完成标准：事件有因果，每个阶段改变状态，可继续拆成章节卡。

#### 共同禁止事项

- 一次调用混合多个模式并跨所有权区域写入。
- 编写正式正文。
- 静默改变已确认的结局、人物命运或世界规则。
- 创造与剧情无关的大量人物或百科内容。
- 把设计可能性当成已经发生的事实。

### 12.3 `chapter-planner`

**职责**：把大纲节点和当前状态转化为可执行章节卡。

**必需输入**：

```yaml
plot_segment: file
context_pack: object
```

**可选输入**：

```yaml
previous_chapter_summary: string
previous_chapter_ending: string
target_word_count: string
chapter_function: string
```

**输出**：

```yaml
chapter_plan:
  chapter_id: string
  chapter_function: string
  viewpoint_character: string
  time_and_location: string
  opening_state: object
  scenes:
    - scene_id: string
      goal: string
      conflict: string
      action: string
      information_revealed: []
      state_change: string
      transition: string
  required_elements: []
  prohibited_reveals: []
  active_foreshadowing: []
  chapter_climax: string
  ending_state: object
  continuity_risks: []
```

**可写**：`chapters/plans/chapter_*.md`。

**禁止**：修改总纲、增加未授权规则、改变人物长期目标、写大量正文、机械制造断章。

**完成标准**：

- 章节功能明确。
- 开始和结束状态不同。
- 每个场景都有目标、阻力和结果。
- 信息揭示符合人物知情范围。
- `chapter-writer` 无需猜测核心剧情方向。

**默认后继**：`chapter-writer / WRITE`。

### 12.3 （v1.1.0 增设）

已在 v1.1.0 冻结。职责、输入、输出和完成标准见相应 SKILL.md 和 references/style-guide-template.md。v1.2.0 输出扩展：新增 scene_modulations、override_policy 和 contract_meta（详见 §20）。

### 12.4 `chapter-writer`

#### `WRITE` / `CONTINUE` 模式

**职责**：执行章节卡并创作或续写正式正文。

**必需输入**：

```yaml
chapter_plan: file
context_pack: object
```

`CONTINUE` 还必须提供当前未完成草稿和续写起点。

**输出**：

```yaml
chapter_draft:
  chapter_id: string
  title: string | null
  body: string
  chapter_lifecycle:
    status: DRAFT
    accepted_by: null
    acceptance_ref: null
    published_ref: null

chapter_report:
  executed_plan_items: []
  deviations_from_plan: []
  new_facts_introduced: []
  character_state_changes: []
  timeline_changes: []
  knowledge_changes: []
  foreshadowing_changes: []
  possible_continuity_risks: []
```

#### `EDIT` 模式

**职责**：按授权等级修改已有正文。

| 等级 | 可修改内容                               |
| ---- | ---------------------------------------- |
| `L1` | 错字、标点、格式、明显病句               |
| `L2` | 句式、描写、对话、文风；不改变事实和剧情 |
| `L3` | 场景节奏、冲突和信息顺序                 |
| `L4` | 章节结构、剧情结果和人物关系             |

必需输入：

```yaml
source_text: file | text
edit_level: L1 | L2 | L3 | L4
edit_objectives: []
must_preserve: []
semantic_impact:
  fact_change: boolean
  state_change: boolean
  plot_outcome_change: boolean
  downstream_scope: NONE | SCENE | CHAPTER | MULTI_CHAPTER
```

输出：

```yaml
edited_text:
  body: string

edit_report:
  edit_level: string
  changes_made: []
  preserved_elements: []
  meaning_changes: []
  plot_changes: []
  new_facts_introduced: []
  state_changes: []
  continuity_risks: []
  resulting_lifecycle_status: DRAFT | REVIEWED
```

**可写**：`chapters/drafts/chapter_*.md`；修订时必须保留旧版或可恢复差异。

**共同禁止事项**：

- 修改总纲或 `state/`。
- 擅自增加核心能力、改变主要人物命运。
- 把临时细节直接提交为 Canon。
- 计划有问题时静默改写故事方向。
- 超出 `max_edit_level` 修改。
- 在 L1/L2 中改变剧情或事实。
- 模仿特定在世作者的可识别文风。

**完成标准**：

- 正文执行章节卡或编辑目标。
- 视角、时间、人物动机和知情范围符合上下文。
- 所有新增事实、状态变化和计划偏离均已报告。
- 修改没有超出授权等级。
- 新 revision 的生命周期已按实际评审状态标记。

**默认后继**：严格模式下先 `novel-reviewer`；最终 revision 必须通过接受闸门，只有 `ACCEPTED` 或 `PUBLISHED` 的正式事实变化才能进入 `continuity-keeper / COMMIT_CHAPTER_STATE`。

### 12.5 `novel-reviewer`

**职责**：基于文本证据进行只读诊断。

**必需输入**：

```yaml
review_target: file | text
review_scope: string
```

**可选输入**：项目简报、故事架构、章节卡、上下文包和指定评审维度。

**输出**：

```yaml
review_report:
  overall_assessment: string
  confirmed_issues:
    - category: string
      severity: string
      evidence: string
      impact: string
      recommended_action: string
  potential_risks: []
  preference_based_suggestions: []
  strengths_to_preserve: []
  continuity_flags: []
  recommended_edit_level: L1 | L2 | L3 | L4
  recommended_next_skill: string
```

**可写**：只有 `artifact_persistence_allowed: true` 时可以写 `reviews/*.md`；不得修改评审对象或 `state/`。保存的报告必须标明被评审内容的 `deliverable_id`、`revision` 和 `content_hash`。

**禁止**：直接重写、笼统评价、把偏好当错误、承诺作品成败、为爽点破坏定位。

**完成标准**：

- 重要问题都有文本或项目证据。
- 明确区分已证实问题、潜在风险和偏好建议。
- 建议可执行并说明应保留的优点。
- 给出合理编辑等级。

### 12.6 `continuity-keeper`

**职责**：管理项目事实、时间线和连续性，是 `state/` 唯一正式写入者。

#### 模式

| 模式                                 | 行为                                                   | 写状态           |
| ------------------------------------ | ------------------------------------------------------ | ---------------- |
| `EXTRACT_CONTEXT`                    | 提取最小上下文包                                       | 否               |
| `CHECK_CONTRADICTIONS`               | 检查证据冲突                                           | 仅登记冲突       |
| `COMMIT_CHAPTER_STATE`               | 提交正式章节产生的增量状态                             | 是               |
| `COMMIT_CANON`                       | 提交已授权 Canon 变化                                  | 是               |
| `IMPACT_ANALYSIS`                    | 分析拟议变化影响                                       | 否               |
| `GENERATE_SUMMARY`                   | 生成章节、卷、项目恢复摘要或当前状态说明               | 仅写摘要目标文件 |
| `RESTORE_PROJECT / EXTRACT_EVIDENCE` | 从现有文件提取证据并生成 RecoveryReport                | 否               |
| `RESTORE_PROJECT / REBUILD_STATE`    | 基于已确认 RecoveryReport 重建最小状态                 | 是，需单独授权   |
| `REBUILD_DERIVED_STATE`              | 从已确认来源重建时间线、人物、知识、伏笔和开放循环索引 | 是，仅派生文件   |

**必需输入**：

```yaml
operation_mode: string
source_material: []
current_state_files: []
base_revision: object
```

**可选输入**：

```yaml
state_change_proposals: []
user_confirmed_decisions: []
target_chapter: string
affected_scope: string
approval_ref: object | null
change_set: object | null
```

**输出**：

```yaml
continuity_result:
  context_pack: object | null
  contradictions: []
  committed_updates:
    canon: []
    timeline: []
    character_state: []
    knowledge_state: []
    foreshadowing: []
    open_loops: []
    chapter_summaries: []
  pending_updates: []
  deprecated_items: []
  impact_analysis: []
  recovery_report: object | null
  change_set_result: object | null
```

**可写**：`state/` 中与模式对应的文件。

`COMMIT_CHAPTER_STATE` 还必须满足：

- 来源章节状态为 `ACCEPTED` 或 `PUBLISHED`。
- 来源 `deliverable_id`、revision 和 hash 与接受记录一致。
- `base_revision` 与当前状态文件一致。
- ChangeSet 通过完整事务。

`COMMIT_CANON` 和 `RESTORE_PROJECT / REBUILD_STATE` 还必须提供覆盖目标范围和当前 revision 的有效 ApprovalRef。

#### `RecoveryReport`

```yaml
recovery_report:
  report_id: string
  based_on_revision: object
  confirmed_evidence:
    - source_file: string
      source_revision: string
      evidence_type: canon | timeline | character_state | foreshadowing
      content: string
      confidence: high | medium | low
  inferred_candidates:
    - description: string
      evidence: string
      recommended_action: string
  contradictions: []
  unknowns: []
  recommended_reconstruction_routes: []
```

恢复协议：

```text
1. RESTORE_PROJECT / EXTRACT_EVIDENCE
2. 输出 RecoveryReport，不写 state/
3. novel-master 按文件所有权路由 novel-brief、STORY、CHARACTER、WORLD、PLOT
4. 用户审阅重建结果并生成 ApprovalRef
5. COMMIT_CANON 或 RESTORE_PROJECT / REBUILD_STATE
```

`inferred_candidates` 只能作为 Proposal。若 RecoveryReport 的来源 revision 变化，报告和基于它生成的授权全部失效。

#### `GENERATE_SUMMARY` 与 `REBUILD_DERIVED_STATE`

`GENERATE_SUMMARY` 只用于：

- 章节摘要。
- 卷摘要。
- 项目恢复摘要。
- 当前状态说明。

`REBUILD_DERIVED_STATE` 只用于从 `ACCEPTED`/`PUBLISHED` 章节和当前 Canon 重建：

- 时间线索引。
- 人物当前状态索引。
- 知识状态索引。
- 伏笔索引。
- 开放循环索引。

派生状态重建不是创建新 Canon。发现来源矛盾时停止相关条目写入并登记冲突。

**禁止**：

- 创造剧情或承担审美评审。
- 为解决矛盾擅自改正文。
- 把 Proposal 自动提交为 Canon。
- 删除冲突记录来掩盖问题。
- 无证据推断人物知情或事件已发生。
- 在恢复模式中把推断写成已确认事实。
- 用 `GENERATE_SUMMARY` 隐式重建或覆盖派生状态。
- 在 revision 不一致时继续提交。

**完成标准**：

- 每项更新有来源。
- Canon、Proposal、Deprecated 和 Unknown 分离。
- 冲突未被静默覆盖。
- 上下文包最小、相关、可回查。
- 状态提交是增量且可审计。
- 恢复报告将证据、推断、冲突和未知项分离。
- ChangeSet 已提交或完整回滚，不存在部分状态。

<a id="nm-contract-skill-style"></a>

### 12.7 `novel-style`

**职责**：把作品定位和故事基调转化为可执行的叙事风格约束，填写项目 `style_guide.md`，供 `chapter-writer` 作为硬约束、`novel-reviewer` 作为风格维度证据。

**触发**：新书初始化阶段 `story_architecture` 已生成、作品定位或故事基调发生重大变化、`style_guide.md` 仍存在未填写占位符。

**必需输入**：

```yaml
project_brief: file
architecture/story_architecture.md: file
```

**可选输入**：

```yaml
characters/: [] # 参考人物声音差异
world/: [] # 参考世界质感与题材规则
outline/: [] # 参考节奏与信息揭示曲线
existing_style_guide: file # 修订时读取
```

**输出**：

```yaml
style_guide:
  narrative_pov: object # 主视角、视角人物、切换规则、限制
  narrative_distance: object # 默认距离、变化规则、禁止
  sentence_rhythm: object # 默认句长、节奏模式、段落长度、禁止
  description_density: object # 动作/过渡/情感/环境密度、禁止
  dialogue_rules: object # 占比、标签、潜台词、节奏、禁止
  character_voice: object # 主角特征、配角区分、叙述者声音、禁止
  exposition_strategy: object # 背景说明、体系说明、前情回顾、禁止
  chapter_word_count: object # 标准字数、浮动、高潮/过渡章节
  hook_principles: object # 章首/章尾 Hook、断章规则、禁止
  recall_strategy: object # 已知信息、伏笔提醒、前章衔接
  ai_voice_avoidance: [] # 可执行的 AI 腔规避清单
  genre_specific_rules: [] # 题材特殊规则
  assumptions: []
  unresolved_decisions: []
```

**可写**：`style_guide.md`。

**禁止**：

- 写正文、章节卡、大纲或人物档案。
- 修改 Canon 或写 `state/`。
- 固化某一题材的默认风格（占位符必须基于本作品定位具象化，不得用通用默认值填充）。
- 把低置信度推断写成已确认风格。
- 模仿特定在世作者的可识别文风。

**完成标准**：

- 模板全部占位符已具象化，无遗留 `{{}}` 或 `<!-- TODO -->`。
- 每条约束可被 `chapter-writer` 当作硬约束执行、可被 `novel-reviewer` 当作证据判定。
- 风格与 `project_brief` 的目标读者体验、`story_architecture` 的基调一致。
- 已确认项、假设和待确认项分离。
- 没有把低置信度推断写成事实。

**默认后继**：`INITIALIZATION_REVIEW`（初始化阶段）或回到调用方。

## 13. 异常与降级策略

| 场景                         | 检测                                 | 降级动作                                                    | 状态                                   |
| ---------------------------- | ------------------------------------ | ----------------------------------------------------------- | -------------------------------------- |
| Canon 资料冲突               | 同一事实出现不兼容证据               | 保留双方证据，登记 `contradictions.md`，继续无关部分        | `NEEDS_DECISION`                       |
| `continuity-keeper` 疑似误报 | 用户覆核或与更高优先级证据冲突       | 标记 `false_positive`，保留原记录和覆核依据                 | `COMPLETED_WITH_WARNINGS`              |
| 上下文包超限                 | 字符/token 预算检查                  | 保留高优先级项，输出 `omitted_context_refs`，必要时按需读取 | `COMPLETED_WITH_WARNINGS`              |
| 项目文件缺失                 | 启动校验                             | 从正文、摘要和 Canon 抽取最小状态；其余标记 `UNKNOWN`       | `NEEDS_DECISION`                       |
| 项目文件损坏                 | 解析或完整性校验失败                 | 停止写入，保留原文件，从可验证来源生成候选恢复报告          | `BLOCKED`                              |
| 用户推翻大量 Canon           | 影响范围超过单章或涉及高风险项       | 先输出影响报告，分批确认、修改和提交                        | `NEEDS_DECISION`                       |
| 子 Skill 越权                | 输出路径、操作或内容超出权限         | 拒绝写入；可用内容降级为 Proposal；登记路由警告             | `COMPLETED_WITH_WARNINGS` 或 `BLOCKED` |
| 写作计划不可执行             | 缺少关键目标或与 Canon 冲突          | 完成安全部分，报告偏离；不得静默重定故事                    | `NEEDS_DECISION`                       |
| 状态提交中断                 | 写入后校验不一致                     | 停止后续路由，按变更日志恢复到一致状态                      | `FAILED`                               |
| 输入 revision 过期           | `base_revision` 与当前状态不一致     | 拒绝提交，重新提取上下文并重新授权                          | `BLOCKED / STALE_CONTEXT`              |
| 授权过期或范围不足           | ApprovalRef 校验失败                 | 拒绝高风险操作，生成新的待确认摘要                          | `BLOCKED / INVALID_APPROVAL`           |
| 未接受章节提交状态           | 生命周期不是 `ACCEPTED/PUBLISHED`    | 仅保留 state_change_proposals                               | `BLOCKED / CHAPTER_NOT_ACCEPTED`       |
| ChangeSet 部分失败           | APPLY、VERIFY 或 COMMIT 任一步骤失败 | 回滚全部临时变更并清理临时文件                              | `FAILED`                               |
| 跨项目路径                   | 路径不在当前 `root_path`             | 拒绝读取和写入                                              | `BLOCKED`                              |

### 13.1 冲突输出

```yaml
issues:
  - severity: blocker
    category: canon_conflict
    description: string
    affected_files: []
    evidence_refs: []
    suggested_resolution: string
```

### 13.2 越权降级

子 Skill 提出的越权创作内容可以保留为：

```yaml
proposals:
  - description: string
    source_skill: string
    rationale: string
    requires_user_confirmation: true
    proposal_type: creative_option | structural_change | canon_change | workflow_change
    source_ref: string
```

不得进入交付物或正式状态。

### 13.3 部分成功

能够安全完成部分任务时：

- 在 `completion.criteria_met` 列出已完成项。
- 在 `completion.criteria_unmet` 列出未完成项。
- 使用 `NEEDS_DECISION` 或 `COMPLETED_WITH_WARNINGS`。
- 禁止把部分成功返回为无警告的 `COMPLETED`。

## 14. 编排器输出：`MasterResult`

```yaml
master_result:
  schema_version: "1.0"
  request_id: string
  project_id: string
  request_summary: string

  route_executed:
    - skill: string
      mode: string
      purpose: string
      status: string

  deliverables:
    - name: string
      path: string
      summary: string

  confirmed_changes: []
  pending_decisions: []
  warnings: []
  recommended_next_action: string | null
```

面向用户的结果必须回答：

1. 完成了什么。
2. 哪些文件或内容发生变化。
3. 哪些内容已经正式生效。
4. 哪些仍是 Proposal 或待决策项。
5. 是否存在冲突、降级或未验证项。
6. 下一步最自然的工作是什么。

内部路由日志写入 `workflow/route_log.md`，不得无差别倾倒给用户。

## 15. 契约一致性检查清单

实现或修改任何 V1 Skill 前后必须检查：

- [ ] `schema_version` 一致。
- [ ] `request_id` 和 `project_id` 全链路一致。
- [ ] 输入路径全部位于当前项目根目录。
- [ ] 操作符合目标 Skill 和模式权限。
- [ ] 写入路径属于目标 Skill 所有权区域。
- [ ] `READ_ONLY` 不修改源文件和状态；独立产物写入符合 `artifact_persistence_allowed`。
- [ ] “不要修改任何东西”时三个细粒度权限均为 `false`。
- [ ] 高风险操作有影响分析和确认引用。
- [ ] ApprovalRef 覆盖操作、scope 和当前 revision。
- [ ] 输入 FileRef 和 `base_revision` 未过期。
- [ ] Canon 更新有来源。
- [ ] Proposal 没有进入 `committed_updates`。
- [ ] Deprecated 内容没有被当作当前事实。
- [ ] Unknown 没有被静默补造。
- [ ] 正式章节附带 `chapter_report`。
- [ ] `COMMIT_CHAPTER_STATE` 的来源为 `ACCEPTED` 或 `PUBLISHED`。
- [ ] 生命周期转换属于允许集合。
- [ ] 评审没有修改原文。
- [ ] 上下文包满足预算或明确记录降级。
- [ ] `status` 与完成标准实际结果一致。
- [ ] ChangeSet 已完整提交或完整回滚。
- [ ] RecoveryReport 将证据、推断、冲突和未知项分离。
- [ ] `GENERATE_SUMMARY` 没有写入派生索引。

## 17. 章节质量契约：reader_experience（v1.2 新增）

完整定义见 v1.2.0-rc1 §17。核心结构：chapter_role（primary + secondary）、promise、payoff（FULL|PARTIAL|DEFERRED|NONE_JUSTIFIED + 条件必填）、emotional_arc、information_gain（数组 target_id 引用）、tension_curve（RISING|WAVE|SPIKE|RELEASE|FLAT_JUSTIFIED）、continuation_drive（QUESTION|DANGER|DECISION|REVELATION|EMOTIONAL|GOAL|NONE_JUSTIFIED + justification）。条件必需：FAST 可选、STANDARD/STRICT 必需、ADVISORY 按任务。跨对象校验由 validate_quality_contract.py 负责。

## 18. Writer 执行追踪：reader_experience_execution（v1.2 新增）

Writer 在 chapter_report 中增加 target_execution 数组。每项：target_ref（JSON Pointer）、execution（PRESENT|PARTIAL|DEVIATED）、evidence_ref（source_type + deliverable_id + revision + paragraph_start/end + excerpt）。Writer 禁止输出全局质量评分。evidence_ref.source_type 枚举：CHAPTER_DRAFT|CHAPTER_PLAN|CANON|CONTEXT_PACK|STYLE_GUIDE|CHAPTER_REPORT。

## 19. Reviewer 分层诊断（v1.2 新增）

review_scope 从 string 改为 list[review_dimension]。四个维度：CONTRACT_COMPLIANCE、NARRATIVE_SOUNDNESS、READER_EXPERIENCE、CRAFT_EXECUTION。mandatory_guardrail_scan：CANON_CONFLICT、KNOWLEDGE_STATE_VIOLATION、PROHIBITED_REVEAL、MAJOR_FACT_CONTRADICTION。输出分为 guardrail_results（独立）和 dimension_results（恰好四个维度）。未激活维度：NOT_EVALUATED + reason_code。编排调用时 review_scope 必填。

## 20. 场景风格调制（v1.2 新增）

style_guide 新增 scene_modulations：project-level modulation_id + category enum（COMBAT|EMOTIONAL|MYSTERY|TRANSITION|CLIMAX|EXPOSITION|DEFAULT）+ typed relative overrides（SHORTER|LONGER|HIGHER|LOWER|CLOSER|FARTHER|SAME）。override_policy.protected_fields 使用 JSON Pointer 路径。style_modulation_ref 跨文件引用由 validate_quality_contract.py 校验。

## 21. 契约版本化：contract_meta（v1.2 新增）

所有 v1.2 业务交付物必须包含 contract_meta { schema_id, schema_version }。适用类型：ChapterPlan、ChapterReport、ReviewRequest、ReviewReport、StyleGuide。缺少 contract_meta 按 v1.1 legacy 解析，只读兼容。

## 22. 兼容与迁移策略（v1.2 新增）

v1.1 遗留章节卡：只读兼容。FAST 写作：可带警告继续。STANDARD/STRICT 写作：先由 Planner 升级。Reviewer 审查旧正文：READER_EXPERIENCE 维度 NOT_EVALUATED + reason_code: MISSING_PLAN_CONTRACT。

## 23. 确定性校验（v1.2 新增）

新增 validate_quality_contract.py：跨对象/跨文件语义校验。JSON Schema 仅负责单对象结构校验。跨对象条件（reader_experience 按模式必填、style_modulation_ref 引用存在、protected_field 违规检测、relative 操作符合法性）由本脚本负责。可选辅助：resolve_style_profile.py 确定性风格解析。

## 16. V1 到目标架构的兼容要求

后续拆出 `character-designer`、`world-builder`、`plot-planner` 或 `novel-editor` 时：

1. 保持现有 `TaskEnvelope` 和 `SkillResult` 顶层结构。
2. 将对应模式的文件所有权迁移给新 Skill。
3. 保留现有模式作为兼容路由，直至迁移测试完成。
4. 不得借拆分改变 Canon 权限。
5. 为新旧路由运行相同回归用例并比较结果。
6. 更新架构和契约版本，记录破坏性变更。

## 17. 变更记录

### 1.1.0（2026-07-25）

| 变更                                                     | 原因                                                                                                                                                       | 影响                                                          |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| 新增子 Skill `novel-style` 及其契约 §12.7                | `style_guide.md` 在 §3.1 列为标准文件，但 §3.3 无所有权、§2.2 无产出方、§10 无路由，是冻结契约留白；`chapter-writer`/`novel-reviewer` 已把它当必需只读输入 | §2.2 子 Skill 表、§3.3 文件所有权表、§10.4 路由表新增对应条目 |
| §3.3 新增 `style_guide.md` 所有权行，归属 `novel-style`  | 消除孤儿文件                                                                                                                                               | 其他组件对 `style_guide.md` 为只读或 Proposal                 |
| §7.2 初始化 `approval_scope` 新增 `style_guide`          | 初始化范围纳入风格约束                                                                                                                                     | INITIALIZATION_REVIEW 输出六类摘要（原五类）                  |
| §10.4 「完整新书初始化」路由在 PLOT 后插入 `novel-style` | 初始化阶段补齐风格指南                                                                                                                                     | 新增「确立或修订风格指南」路由行                              |

本次为次版本修订：新增独立子 Skill 属于架构调整，按架构总纲 §1.3 规则增加次版本号。现有 6 个子 Skill 的模式、可写区域、输入输出和顶层契约字段保持不变；`style_guide.md` 的所有权和 `approval_scope` 的 `style_guide` 项为新增字段，不与现有字段冲突。

### 1.0.1（2026-07-24）

| 变更                                        | 原因                            | 影响                                              |
| ------------------------------------------- | ------------------------------- | ------------------------------------------------- |
| 增加章节生命周期和接受闸门                  | 阻止 DRAFT/REVIEWED 内容误提交  | 单章状态提交增加生命周期校验                      |
| 增加初始化 `approval_gate`                  | 确保重大初始化决策显式确认      | `COMMIT_CANON` 需要 `INIT_PROJECT` 授权           |
| 增加 `semantic_impact` 风险推导             | 解决 L3 风险等级冲突            | L3 根据是否改变事实、状态和结果分级               |
| 增加三个细粒度写权限                        | 区分“不改原文”和“完全只读”      | 评审报告落盘与源文件/状态写入解耦                 |
| 增加 `ApprovalRef`                          | 绑定授权范围、revision 和有效期 | 旧自由文本确认仅作为兼容 ID                       |
| 增加 FileRef、`base_revision` 和 stale 检测 | 防止基于旧上下文提交            | revision 不一致时必须重跑                         |
| 增加 `ChangeSet` 事务                       | 防止多状态文件部分写入          | 状态提交采用 prepare/validate/apply/verify/commit |
| 恢复拆成证据提取和授权重建                  | 防止推断进入 Canon              | 新增 RecoveryReport 和两阶段路由                  |
| 分离摘要与派生状态重建                      | 明确写状态边界                  | `REBUILD_DERIVED_STATE` 只重建索引                |
| 增加来源优先级                              | 统一冲突证据判断                | 未接受正文不能覆盖 Canon                          |
| 统一风险枚举、Proposal 和交付物标识         | 提升 schema 可执行性            | 新写出方必须产生 1.0.1 字段                       |

向后兼容策略：

- 保留 `TaskEnvelope`、`SkillResult`、`ContextPack` 和 `MasterResult` 顶层结构。
- 保留全部 1.0.0 字段；`user_confirmation_ref` 和 `deliverables.status` 继续可读。
- 1.0.0 的纯路径 `required_files` 可以在兼容期读取，1.0.1 写出方必须输出 `FileRef`。
- 1.0.0 小写风险枚举可以在兼容期读取并规范化为大写；1.0.1 写出方只输出大写。
- 1.0.0 的 `RESTORE_PROJECT` 输入在兼容期按只读 `RESTORE_PROJECT / EXTRACT_EVIDENCE` 处理；任何状态重建都必须显式使用新子阶段并重新授权。
- V1 的 1+6 架构和专业 Skill/模式不变；新增的是治理操作和恢复子阶段。（注：1.1.0 起 V1 架构调整为 1+7，新增 `novel-style`，详见 §17 变更记录。）
