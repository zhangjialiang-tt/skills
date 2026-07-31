# 包契约冻结文档 v1

> 基线 commit: e0d6736 (feature/novel-master)
> 冻结日期: 2026-07-30
> 状态: FROZEN — Phase 2-4 实施期间，契约变更需要新 revision

---

## 1. StorySynopsisPackage

### 文件组成

```
source/
├── synopsis.md              # 完整故事梗概（3000-5000 字）
└── synopsis-contract.yaml   # 机器交接契约
```

### synopsis-contract.yaml 必填字段

```yaml
schema_version: 1                    # 必填，整数
artifact_type: story_synopsis_contract

identity:
  design_id: <string>                # 必填
  title: <string>                    # 必填
  language: zh | en                  # 必填

source:
  synopsis_ref: source/synopsis.md   # 必填
  synopsis_revision: <int>           # 必填，≥1

status:
  synopsis_status: complete_draft | user_confirmed   # 必填
  handoff_ready: bool                # 必填，仅 user_confirmed 时可为 true
  review_status: pending | passed    # 必填
  accepted_risks: []                 # 可选

story_core:
  premise: <string>                  # 必填
  genre: <string>                    # 必填
  tone: [<string>]                   # 必填，≥1
  central_question: <string>         # 必填
  story_promise: <string>            # 必填

protagonist:
  name: <string>                     # 必填
  identity: <string>                 # 必填
  external_desire: <string>          # 必填
  internal_need: <string>            # 必填
  starting_belief: <string>          # 必填
  flaw: <string>                     # 必填
  agency: <string>                   # 必填
  arc:
    start: <string>                  # 必填
    turning_point: <string>          # 必填
    final_choice: <string>           # 必填
    end: <string>                    # 必填

opposition:
  type: <string>                     # 必填
  primary_opponent:
    identity: <string>               # 必填
    goal: <string>                   # 必填
    motivation: <string>             # 必填
    logic: <string>                  # 必填

core_conflict:
  external: <string>                 # 必填
  internal: <string>                 # 必填
  stakes:
    personal: <string>               # 必填
    thematic: <string>               # 必填

world_rules:                         # 必填，≥1
  - id: <string>
    statement: <string>
    boundary: <string>
    cost: <string>
    frozen: bool

story_truth:
  hidden_truth: <string>             # 必填
  truth_origin: <string>             # 必填
  protagonist_connection: <string>   # 必填

ending:
  external_outcome: <string>         # 必填
  final_choice: <string>             # 必填
  personal_cost: <string>            # 必填
  thematic_answer: <string>          # 必填
  ending_type: <string>              # 必填
  frozen: true                       # 必填

major_turning_points:                # 必填，≥3
  - id: <string>
    stage: <string>
    event: <string>
    state_change: <string>
    frozen: bool

adaptation_boundaries:
  frozen_facts: [<string>]           # 必填，≥1
  expandable_zones: [<string>]       # 必填，≥1
  prohibited_directions: [<string>]  # 必填，≥1
  unresolved_non_blocking: [<string>] # 可选

quality:
  blocking_issues: []                # 必填（空 = 无阻塞）
  non_blocking_risks: [<string>]     # 可选
```

### 交接前置条件

```
handoff_ready == true
synopsis_status == user_confirmed
blocking_issues == []
protagonist 完整
core_conflict 完整
story_truth 完整
ending 完整且 frozen == true
major_turning_points ≥ 3
```

### 版本规则

- 每次用户确认定稿后 revision +1
- 下游记录消费的 revision
- 两者实质矛盾时包无效，退回 story-synopsis

---

## 2. SerialDesignPackage

### 文件组成

```
serial/
├── serial-contract.yaml
├── design/
│   ├── 00-serialization-brief.md
│   ├── 01-serial-promise.md
│   ├── 02-story-engine.md
│   ├── 03-character-serialization.md
│   ├── 04-world-pressure-system.md
│   ├── 05-volume-architecture.md
│   ├── 06-payoff-and-rhythm.md
│   ├── 07-mystery-and-information.md
│   ├── 08-launch-plan.md
│   ├── 09-endgame-convergence.md
│   └── 10-readiness-review.md
└── reviews/
    ├── gate-a-architecture.yaml
    ├── readiness-review.yaml
    └── gate-b-freeze.yaml
```

### serial-contract.yaml 必填字段

```yaml
schema_version: 1
artifact_type: serial_design_contract

identity:
  design_id: <string>                # 必填
  title: <string>                    # 必填
  revision: <int>                    # 必填

source:
  synopsis_contract_ref: <path>      # 必填
  synopsis_revision: <int>           # 必填

status:
  serial_design_status: draft | reviewing | frozen   # 必填
  handoff_ready: bool                # 必填
  readiness_verdict: pending | pass | revise | block # 必填
  accepted_risks: []                 # 可选

serialization_target:
  form: long_webnovel                # 必填
  platform: <string>                 # 必填
  genre: <string>                    # 必填
  target_chapters: <int>             # 必填
  chapter_words: <int>               # 必填
  pacing_profile: <string>           # 必填

upstream_integrity:
  preserved_synopsis_facts: [<string>]  # 必填
  approved_revision_proposals: []       # 可选
  forbidden_story_changes: [<string>]   # 必填

serial_promise:
  click_hook: <string>               # 必填
  first_three_chapters:
    promise: <string>                # 必填
    required_payoffs: [<string>]     # 必填，≥1
  long_term_promise: <string>        # 必填

story_engine:
  engine_id: <string>                # 必填
  loop: [<string>]                   # 必填，≥4 步
  variable_inputs: [<string>]        # 必填，≥3
  cumulative_state: [<string>]       # 必填，≥2
  escalation_axes: [<string>]        # 必填，≥2
  anti_repetition_rules: [<string>]  # 必填，≥2

volumes:                             # 必填，≥2
  - id: <string>
    title: <string>
    chapter_range: [<int>, <int>]
    external_goal: <string>
    primary_opposition: <string>
    major_reveal: <string>
    climax: <string>
    irreversible_state_changes: [<string>]  # ≥1
    ending_hook: <string>

serial_characters:                   # 必填，≥1（主角）
  - id: <string>
    synopsis_character_ref: <string>
    serial_function:
      primary: <string>
    arc_checkpoints:                 # ≥2
      - volume: <string>
        belief: <string>
        forced_choice: <string>
        cost: <string>
    prohibited_drift: [<string>]     # 可选

payoff_system:
  primary_payoffs:                   # 必填，≥2
    - id: <string>
      type: <string>
      pattern: <string>
      minimum_cadence:
        chapters: <int>
  density_rules: {}                  # 必填
  prohibited_shortcuts: [<string>]   # 必填，≥1

information_design:
  truths:                            # 必填，≥1
    - id: <string>
      statement: <string>
      authority: canonical
      reveal_volume: <string>
      clue_schedule: []              # ≥1
      omission_policy: forbidden | warning | allowed

launch_plan:
  first_three_chapters:              # 必填，3 项
    - chapter: <int>
      required_event: <string>
      chapter_end_hook: <string>
  first_thirty_chapters:
    required_progress: [<string>]    # 必填，≥3

endgame_convergence:
  required_upstream_ending_ref: <string>  # 必填
  convergence_conditions: [<string>]      # 必填，≥2
  forbidden_endgame_changes: [<string>]   # 必填，≥1

assertions:                          # 必填，≥10（300 章长篇约 30-60）
  - id: <string>
    type: <string>                   # 见类型枚举
    statement: <string>
    status: confirmed | provisional | proposal | optional | rejected
    importance: critical | major | supporting
    source_ref: <string>
    invariants: [<string>]           # 可选
    supersedes: [<string>]           # 可选

compilation_policy:
  must_preserve: [<string>]          # 必填
  may_summarize: [<string>]          # 必填
  may_omit: [<string>]               # 必填
  must_not_emit: [<string>]          # 必填
  block_if_missing: [<string>]       # 必填

external_reviews:
  status: not_requested | requested | received_unstructured | incorporated | rejected
  references: []
```

### assertion type 枚举

```
story_engine | volume_architecture | character_arc | payoff_cadence |
foreshadowing | world_pressure | serial_promise | launch_plan |
endgame_convergence | information_reveal | anti_repetition |
illustrative_example | design_rationale | rejected_direction
```

### assertion status 枚举

```
confirmed | provisional | proposal | optional | rejected
```

### 冻结前置条件

```
serial_design_status == frozen
handoff_ready == true
readiness_verdict == pass
gate-a-architecture.yaml status == approved
gate-b-freeze.yaml status == approved
所有 critical assertion status == confirmed
上游 synopsis_revision 一致
blocking_issues 为空
volumes ≥ 2 且每卷有 irreversible_state_changes
story_engine.loop ≥ 4 步
endgame_convergence 引用上游结局
```

---

## 3. InkOSBuildPackage

### 文件组成

```
compile/inkos/
├── book-brief.md                # inkos book create --brief 输入
├── author_intent.md             # 对齐基线
├── story_frame.md               # 对齐基线
├── volume_map.md                # 对齐基线
├── book_rules.md                # 对齐基线
├── pending_hooks.md             # 对齐基线（InkOS 13 列表格）
├── roles/                       # 对齐基线
│   ├── 主要角色/*.md
│   └── 次要角色/*.md
├── mapping-plan.yaml            # 编译映射记录
└── compilation-report.yaml      # 遗漏/压缩/未映射报告
```

### mapping-plan.yaml 结构

```yaml
schema_version: 1
compiled_at: <ISO 8601>
source_serial_revision: <int>
inkos_version_target: ">=1.7.2 <1.8.0"

mappings:
  - assertion_id: <string>
    profile: <string>              # 使用的策略类型
    targets:
      - file: <string>
        section: <string>
    result: mapped | split | summarized | retained_as_baseline | omitted_allowed | unmapped_warning | blocked
    information_loss: none | low | medium | high
    override: null | <string>
```

### compilation-report.yaml 结构

```yaml
schema_version: 1
compiled_at: <ISO 8601>

summary:
  total_assertions: <int>
  mapped: <int>
  summarized: <int>
  omitted_allowed: <int>
  unmapped_warning: <int>
  blocked: <int>

unmapped:
  - assertion_id: <string>
    reason: <string>
    severity: warning | blocking
    fallback: <string>

information_loss:
  - assertion_id: <string>
    loss_level: low | medium | high
    what_was_lost: <string>
    retained_in_baseline: bool

proposals_blocked:
  - assertion_id: <string>
    reason: "status != confirmed"
```

### 编译前置条件

```
输入 SerialDesignPackage status == frozen
输入 handoff_ready == true
输入 readiness_verdict == pass
所有 status != confirmed 的 assertion 不进入正式产物
compilation-report 中 blocked == 0
```

---

## 4. 编译器静态策略表（inkos-compilation-policy.yaml）

归属：`inkos-brief-compiler/references/inkos-compilation-policy.yaml`（Skill 级，非每本书）

```yaml
schema_version: 1
target: inkos
inkos_version: ">=1.7.2 <1.8.0"

profiles:
  story_engine:
    requirement: must_preserve
    compression: semantic_summary
    omission: forbidden
    default_targets: [book-brief, author-intent, story-frame]

  volume_architecture:
    requirement: must_preserve
    compression: structured_split
    omission: forbidden
    default_targets: [volume-map, book-brief]

  character_arc:
    requirement: must_preserve
    compression: structured_split
    omission: forbidden
    default_targets: [roles, author-intent]

  foreshadowing:
    requirement: must_preserve
    compression: structured_split
    omission: forbidden
    default_targets: [pending-hooks, volume-map]

  world_pressure:
    requirement: must_preserve
    compression: semantic_summary
    omission: forbidden
    default_targets: [story-frame, book-rules]

  payoff_cadence:
    requirement: should_preserve
    compression: semantic_summary
    omission: warning
    default_targets: [author-intent]

  serial_promise:
    requirement: must_preserve
    compression: semantic_summary
    omission: forbidden
    default_targets: [book-brief, author-intent]

  launch_plan:
    requirement: should_preserve
    compression: semantic_summary
    omission: warning
    default_targets: [book-brief, author-intent]

  endgame_convergence:
    requirement: must_preserve
    compression: semantic_summary
    omission: forbidden
    default_targets: [author-intent, volume-map]

  information_reveal:
    requirement: must_preserve
    compression: structured_split
    omission: forbidden
    default_targets: [pending-hooks, volume-map]

  anti_repetition:
    requirement: should_preserve
    compression: semantic_summary
    omission: warning
    default_targets: [author-intent]

  illustrative_example:
    requirement: optional
    compression: semantic_summary
    omission: allowed
    default_targets: []

  design_rationale:
    requirement: optional
    compression: prohibited
    omission: allowed
    default_targets: []

  rejected_direction:
    requirement: prohibited
    compression: prohibited
    omission: required
    default_targets: []
```

---

## 5. manifest.yaml（包级）

```yaml
schema_version: 1
package_type: StoryDesignPackage

identity:
  design_id: <string>
  title: <string>
  revision: <int>

source:
  synopsis_package_revision: <int>

lifecycle:
  created_at: <ISO 8601>
  updated_at: <ISO 8601>

artifacts:
  source: source/
  serial: serial/
  compile: compile/inkos/
  manifest: manifest.yaml
```

注意：manifest 不含阶段状态。阶段状态分别由 synopsis-contract.yaml、serial-contract.yaml、compilation-report.yaml 各自管理。

---

## 6. 状态枚举汇总

| 位置 | 字段 | 合法值 |
|------|------|--------|
| synopsis-contract | synopsis_status | complete_draft, user_confirmed |
| synopsis-contract | handoff_ready | true, false |
| serial-contract | serial_design_status | draft, reviewing, frozen |
| serial-contract | readiness_verdict | pending, pass, revise, block |
| assertion | status | confirmed, provisional, proposal, optional, rejected |
| assertion | importance | critical, major, supporting |
| compilation-report | result | mapped, split, summarized, retained_as_baseline, omitted_allowed, unmapped_warning, blocked |
| gate-a | status | pending, approved, reopened |
| gate-b | status | pending, approved, revise, reopen_gate_a, return_to_synopsis |
| external_reviews | status | not_requested, requested, received_unstructured, incorporated, rejected |

---

## 7. 版本兼容规则

- schema_version 不匹配 → 拒绝消费，报错
- 上游 revision 与下游记录不一致 → 警告，需要确认
- 新增可选字段 → 向后兼容
- 删除或重命名必填字段 → 新 schema_version
