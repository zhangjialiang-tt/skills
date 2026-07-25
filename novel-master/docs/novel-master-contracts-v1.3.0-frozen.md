---
title: novel-master V1.3 契约手册
document_id: NM-CONTRACT
version: 1.3.0
status: FROZEN
frozen_at: 2026-07-25
supersedes: novel-master-contracts-v1.2.0-frozen.md
applies_to: novel-master V1.3 长篇故事规划与漂移控制
companion: novel-master-architecture-v1.3.0-frozen.md
---

# novel-master V1.3 契约手册（候选版本）

本文仅记录 v1.3 新增和修改的契约条目。v1.2 已冻结的契约继续有效，本文不重复。

---

## A. 分层规划体系

### 目录结构（v1.3 新增）

```text
architecture/
├─ story_architecture.md    # v1.1 原有，STORY
├─ story_engine.md          # v1.3 新增，STORY
└─ project_spine.md         # v1.3 新增，STORY

outline/
├─ volume_index.md          # v1.3 新增，PLOT
├─ volumes/
│  └─ volume_01.md          # v1.3 新增，PLOT（独立 revision/hash）
├─ arc_index.md             # v1.3 新增，PLOT
└─ arcs/
   └─ arc_01_01.md          # v1.3 新增，PLOT（独立 revision/hash）

chapters/
└─ batches/
   └─ batch_001.md          # v1.3 新增，chapter-planner
```

### 文件所有权（v1.3 补丁）

| 文件区域 | 写入者 |
| --- | --- |
| `architecture/story_engine.md` | STORY |
| `architecture/project_spine.md` | STORY |
| `outline/volume_index.md` | PLOT |
| `outline/volumes/volume_*.md` | PLOT |
| `outline/arc_index.md` | PLOT |
| `outline/arcs/arc_*.md` | PLOT |
| `chapters/batches/batch_*.md` | chapter-planner |
| `workflow/plan_progress.md` | novel-master |

STORY 不跨域写 outline/，PLOT 不跨域写 architecture/。单次调用不跨越主要负责人所有权区域。

---

## B. 规划元数据与引用模型

### B1. PlanningArtifactMeta

每个规划产物文件必须包含的元数据：

```yaml
planning_artifact_meta:
  schema_id: string            # novel-master/story-engine / project-spine / volume-arc / arc-plan / chapter-batch
  schema_version: "1.3.0"
  artifact_type: STORY_ENGINE | PROJECT_SPINE | VOLUME_ARC | ARC_PLAN | CHAPTER_BATCH
  artifact_id: string
  revision: string
  lifecycle_status: DRAFT | APPROVED | ACTIVE | SUPERSEDED | COMPLETED | DEPRECATED
```

不包含 content_hash（content_hash 由外部观察者计算，放入 PlanRef）。

### B2. PlanRef

```yaml
plan_ref:
  artifact_type: STORY_ENGINE | PROJECT_SPINE | VOLUME_ARC | ARC_PLAN | CHAPTER_BATCH
  artifact_id: string
  path: string
  revision: string
  content_hash: string
```

### B3. ItemRef

```yaml
item_ref:
  item_type: PHASE | MILESTONE | ARC_BEAT | BATCH_SLOT | PAYOFF
  item_id: string              # 规范身份，不可变
  json_pointer: string         # 定位缓存
```

### 引用矩阵

| 引用字段 | artifact_type | item_type |
| --- | --- | --- |
| `phase_ref` | PROJECT_SPINE | PHASE |
| `milestone_ref` | PROJECT_SPINE | MILESTONE |
| `beat_ref` | ARC_PLAN | ARC_BEAT |
| `payoff_ref` | ARC_PLAN | PAYOFF |
| `batch_slot_ref` | CHAPTER_BATCH | BATCH_SLOT |

`batch_slot_ref` 约束：PlanRef 部分必须与 `batch_ref` 指向同一 artifact_id/revision/content_hash。

### ItemRef 解析规则

1. 按 item_id 查找 → ID 存在：json_pointer 变化不使引用失效（更新缓存）。
2. ID 不存在 → 返回 ITEM_NOT_FOUND。
3. PlanRef 的 revision/hash 不匹配 → 返回 STALE_PLAN_REF。

### 哈希策略

```yaml
hash_policy:
  algorithm: SHA-256
  encoding: UTF-8
  line_endings: LF
  source: canonical_payload
  excluded_fields: [generated_at, display_metadata]
```

对 YAML payload 规范化（解析 → 去除非语义字段 → 键排序 → 规范 JSON → SHA-256）。

---

## C. 规划产物生命周期

```text
DRAFT ──(用户或approved_workflow)──→ APPROVED
APPROVED ──(novel-master, 同Scope无另一ACTIVE)──→ ACTIVE
ACTIVE ──(新revision激活)──→ SUPERSEDED
ACTIVE ──(exit criteria满足)──→ COMPLETED
ACTIVE/APPROVED/DRAFT ──(用户确认)──→ DEPRECATED
```

### 引用规则

- STANDARD/STRICT：只引用 ACTIVE
- FAST：可引用 APPROVED（有警告）
- DRAFT：不可被正式引用

### 唯一性约束

- 同一项目一个 ACTIVE PROJECT_SPINE
- 同一卷一个 ACTIVE VOLUME_ARC
- 同一 Arc 一个 ACTIVE CHAPTER_BATCH

### 原子激活协议

```yaml
planning_activation_change:
  activation_id: string
  artifact_id: string
  previous_active_ref: PlanRef | null
  new_active_ref: PlanRef
  base_revisions: object
  status: PREPARED | VALIDATED | COMMITTED | ROLLED_BACK | FAILED
```

由 novel-master 原子执行：
1. 校验 ApprovalRef（操作：REPLAN_ARC 或 REPLAN_VOLUME）
2. 验证同 Scope 无另一 ACTIVE
3. 旧版标记 SUPERSEDED
4. 新版标记 ACTIVE
5. 更新索引文件
6. 记录 workflow 日志

---

## D. 过期规则

| 产物状态 | 上游 PlanningArtifact 更新后 |
| --- | --- |
| PLANNED 章节卡 | 标记 STALE，要求重规划 |
| DRAFT 正文对应的章节卡 | 标记 STALE，禁止直接接受 |
| REVIEWED 正文 | 标记 STALE，重新评审或确认 |
| ACCEPTED/PUBLISHED 章节 | **保留历史 PlanRef，不标记 STALE** |
| 已完成 Batch Slot | 保留历史映射 |
| 未执行 Batch Slot | 新 Batch revision 可替换 |

---

## E. 规划构件

### E1. StoryEngine（STORY / L1）

```yaml
planning_artifact_meta:
  artifact_type: STORY_ENGINE
  artifact_id: string
  revision: string
  lifecycle_status: ACTIVE

story_engine:
  primary_cycle: string          # 核心循环：每次XX→产生YY→推动ZZ
  escalation_axes:
    - axis: string
      escalation: string
  refresh_mechanisms:
    - mechanism: string
      purpose: string
  engine_constraints:
    - constraint: string
```

示例：
```yaml
story_engine:
  primary_cycle: "每次获取新资源→吸引新威胁→迫使扩大势力→暴露新的资源需求"
  escalation_axes:
    - axis: "威胁规模"
      escalation: "个体掠夺者→小团体→大型势力→环境级灾难"
    - axis: "道德困境"
      escalation: "保护自己→保护他人→牺牲少数→选择谁牺牲"
  refresh_mechanisms:
    - mechanism: "势力扩张解锁新地理区域（不同资源/威胁）"
      purpose: "打破资源-威胁单调循环"
    - mechanism: "外来幸存者引入新知识和冲突"
      purpose: "注入不可预测的社会变量"
```

### E2. ProjectSpine（STORY / L2）

```yaml
planning_artifact_meta:
  artifact_type: PROJECT_SPINE
  artifact_id: string
  revision: string
  lifecycle_status: ACTIVE

project_spine:
  phases:
    - phase_id: PHASE-01
      name: string
      core_question: string
      non_negotiable_milestones:
        - milestone_id: MILESTONE-01-01
          description: string
          irreversible_change: string
          exit_condition: string
      flexible_elements:
        - description: string
```

全书 3~5 phase，每 phase 3~5 个 non_negotiable_milestones。future_phases 粗略即可。

### E3. VolumeArc（PLOT / L3）

```yaml
planning_artifact_meta:
  artifact_type: VOLUME_ARC
  artifact_id: string
  revision: string
  lifecycle_status: ACTIVE

volume_arc:
  volume_id: string
  phase_ref: PlanRef + PHASE ItemRef
  core_question: string
  irreversible_change: string
  reader_payoff: string
  target_chapter_count: integer
  arcs:
    - arc_id: ARC-01-01
      name: string
      chapter_range: [CH-001, CH-010]
      function: string
```

独立文件（outline/volumes/volume_01.md），含独立 revision。

### E4. ArcPlan（PLOT / L4）

```yaml
planning_artifact_meta:
  artifact_type: ARC_PLAN
  artifact_id: string
  revision: string
  lifecycle_status: ACTIVE

arc_plan:
  arc_id: string
  volume_ref: PlanRef
  arc_goal: string
  dramatic_question: string
  required_beats:
    - beat_id: BEAT-001
      description: string
      constraints: string
  payoffs:
    - payoff_id: PAYOFF-001
      description: string
      delivery_criteria: string
  exit_state: object
```

独立文件（outline/arcs/arc_01_01.md），含独立 revision。

### E5. ChapterBatch（chapter-planner / L5）

```yaml
planning_artifact_meta:
  artifact_type: CHAPTER_BATCH
  artifact_id: string
  revision: string
  lifecycle_status: ACTIVE

chapter_batch:
  batch_id: BATCH-001
  arc_ref: PlanRef
  target_range:
    start_chapter: string
    end_chapter: string
  batch_goal: string
  required_arc_beats: [PlanRef, ...]
  payoff_plan: [PlanRef, ...]
  chapter_slots:
    - slot_id: SLOT-001
      status: PLANNED | ASSIGNED | COMPLETED | SKIPPED | SUPERSEDED
      intended_function: SETUP | ESCALATION | PAYOFF | CLIMAX | TRANSITION
      assigned_chapter_refs: []
      beat_refs: [PlanRef, ...]
      flexibility: HIGH | MEDIUM | LOW
      superseded_by: string | null
  refresh_trigger:
    after_chapters: 5
    on_tactical_deviation: true
```

Batch 生成的章节卡引用 `batch_ref` + `batch_slot_ref`（PlanRef 一致性校验）。

### E6. 读者回报链（v1.3.0 仅引用+追踪，v1.3.1 调度优化）

```text
project_brief.payoff_cadence → ArcPlan.payoffs → ChapterBatch.payoff_plan → Writer.payoff_consumption
```

---

## F. 章节卡升级

### F1. planning_alignment

```yaml
chapter_plan:
  planning_alignment:
    phase_ref: PlanRef + PHASE ItemRef
    volume_ref: PlanRef | null
    arc_ref: PlanRef
    batch_ref: PlanRef（CHAPTER_BATCH）
    batch_slot_ref: PlanRef + BATCH_SLOT ItemRef（与batch_ref 一致性校验）
    milestone_refs: [PlanRef + MILESTONE ItemRef, ...]
    arc_beat:
      beat_ref: PlanRef + ARC_BEAT ItemRef
      planned: string
      contribution: string
    planning_function:
      type: ARC_BEAT | SUPPORT | RECOVERY | SETUP | PAYOFF
      justification: string
```

### F2. deviation_policy

```yaml
  deviation_policy:
    max_auto_accept_level: LOCAL
    tactical_requires_replan: true
    strategic_requires_approval: true
```

---

## G. Writer planning_execution

```yaml
chapter_report:
  planning_execution:
    beat_execution:
      - beat_ref: PlanRef
        status: COMPLETED | ADVANCED | NOT_REACHED | DEVIATED
    milestone_effects:
      - milestone_ref: PlanRef
        status_change: NONE | ADVANCED | COMPLETED
    payoff_consumption:
      - payoff_ref: PlanRef
        consumption: NONE | PARTIAL | FULL | PREMATURE
    actual_deviations:
      - deviation_id: string
        planned: string
        actual: string
        proposed_level: LOCAL | TACTICAL | STRATEGIC
        evidence_ref: EvidenceRef
```

### 按模式要求

| 模式 | 要求 |
| --- | --- |
| FAST 正式章节 | 最小版（beat_execution + actual_deviations） |
| STANDARD | 完整版 |
| STRICT | 完整版 + 调用 PLAN_ALIGNMENT |
| ADVISORY | 可选 |

FAST 章节报告 TACTICAL/STRATEGIC 偏差时，升级到检查点流程。

---

## H. Reviewer PLAN_ALIGNMENT 维度

review_dimensions 从 4 个扩展为 5 个：

```yaml
review_dimensions:
  - CONTRACT_COMPLIANCE
  - NARRATIVE_SOUNDNESS
  - READER_EXPERIENCE
  - CRAFT_EXECUTION
  - PLAN_ALIGNMENT             # v1.3 新增
```

### PLAN_ALIGNMENT 维度输出

```yaml
dimension_results:
  - dimension: PLAN_ALIGNMENT
    status: PASS | WARNING | FAIL | NOT_EVALUATED
    deviation_assessment:
      deviations:
        - deviation_id: string
          final_level: LOCAL | TACTICAL | STRATEGIC
          reason: string
          required_action: RECORD | REPLAN_ARC | IMPACT_ANALYSIS
    findings:
      - criterion: string
        evidence_ref: EvidenceRef
        assessment: string
        severity: INFO | WARNING | BLOCKER
```

Reviewer 确认 deviation 的最终级别。STRATEGIC → 必须 IMPACT_ANALYSIS + ApprovalRef。

---

## I. plan_progress

```yaml
plan_progress:
  last_processed_acceptance_ref: string
  processed_updates: []

  active_phase_ref: PlanRef
  active_volume_ref: PlanRef
  active_arc_ref: PlanRef
  active_batch_ref: PlanRef | null

  completed_milestones:
    - milestone_ref: PlanRef
      completed_by_acceptance_ref: string
      completed_at_chapter_ref: object

  deviations:
    - deviation_id: string
      source_acceptance_ref: string
      assessment: object
      resolution_status: RECORDED | REPLANNED | APPROVED | REJECTED

  arc_health:
    planned_chapter_count: integer
    used_chapter_count: integer
    total_required_beats: integer
    completed_required_beats: integer
    overdue_beats: integer
    tactical_deviation_count: integer
    unresolved_strategic_deviation_count: integer
    derived:
      beat_completion_ratio: number
      chapter_consumption_ratio: number
      drift_score: number
      status: ON_TRACK | AT_RISK | DELAYED | REPLAN_REQUIRED
```

### 写入者与触发

- **写入者**：novel-master
- **触发**：章节 ACCEPT 后（不绑定 COMMIT_CHAPTER_STATE）
- **事务**：独立、幂等（idempotency_key）

### 重建路径

```text
SYNC_PENDING → 重试 → 失败时：
  scripts/rebuild_plan_progress.py（从 ACCEPTED 章节 + PlanningExecution + ReviewReport + 有效 PlanRef 重建）
  或 CHECK_PLAN_PROGRESS + repair_mode: REBUILD
```

---

## J. PlanningPack

由 scripts/build_planning_pack.py 确定性构建，novel-master 调用。

```yaml
planning_pack:
  schema_version: "1.0"
  generated_for_request: string

  active_phase:
    ref: PlanRef
    core_question: string
    non_negotiable_milestones: []

  active_volume:
    ref: PlanRef
    core_question: string
    irreversible_change: string
    reader_payoff: string

  active_arc:
    ref: PlanRef
    arc_goal: string
    dramatic_question: string
    required_beats: []

  active_batch:
    ref: PlanRef | null
    remaining_slots: []

  current_progress:
    completed_beat_refs: [PlanRef, ...]
    delayed_beat_refs: [PlanRef, ...]
    deviation_summary: []

  prohibited_strategic_changes: []
  unknowns: []
```

---

## K. 偏差路由

| 偏离级别 | 路由 | 闸门 |
| --- | --- | --- |
| LOCAL | 记录到 plan_progress | 无 |
| TACTICAL | ARC_PROGRESS_CHECK → PLOT 重规划 Arc | 无（已有 ACCEPT_CHAPTER） |
| STRATEGIC | IMPACT_ANALYSIS → 用户确认 → REPLAN_VOLUME | APPROVAL_REF(REPLAN_VOLUME) |

---

## L. 任务类型

task-envelope.task.type 新增：

```text
CHECK_PLAN_PROGRESS    # 检查规划进度（含修复模式）
```

重规划复用现有类型：
- TACTICAL 偏差 → `PLAN_PLOT` + scope: ARC
- STRATEGIC 偏差 → `PLAN_VOLUME` + scope: VOLUME

ApprovalRef operation 新增：`REPLAN_ARC`、`REPLAN_VOLUME`。

---

## M. 初始化范围

INITIALIZATION_REVIEW 覆盖：
1. ProjectBrief（含 reader contract）
2. StoryEngine
3. ProjectSpine
4. 当前 VolumeArc
5. 当前 ArcPlan
6. StyleGuide

初始化完成后，chapter-planner 生成首个 ChapterBatch。ChapterBatch 不必须进入初始 Canon 确认，但第一章前必须 ACTIVE。

---

## N. 兼容策略

| 场景 | 行为 |
| --- | --- |
| v1.2 遗留 plot_plan | 只读兼容，标注 MISSING_PLANNING_STRUCTURE |
| v1.2 遗留章节卡（无 planning_alignment） | 只读兼容，PLAN_ALIGNMENT 维度 NOT_EVALUATED + reason_code: MISSING_PLAN_CONTRACT |
| 首次 v1.3 初始化 | STORY 生成 story_engine + project_spine，PLOT 生成 volume_arcs + arc_catalog |
