# routing-table.md

> 用途：novel-master 路由决策的可测试规则表。
> 引用方式：novel-master SKILL.md 中 `include: references/routing-table.md`。
> 来源：冻结契约 §10。

## 路由优先级（从高到低）

1. 用户显式禁止项和只读要求
2. 安全、项目隔离和权限边界
3. Canon 冲突与高风险影响分析
4. 上游必要依赖
5. 用户显式指定的操作
6. 最小路由原则
7. 默认工作流

## 路由规则

```yaml
routes:
  # ─── 显式只读 ───
  - route_id: READ_ONLY_ANALYSIS
    when:
      user_says_readonly: true
      # "不要动原文" / "只分析" / "不要修改任何东西"
    steps:
      - skill: novel-reviewer
        mode: DEFAULT
    approval_gate: null
    state_commit: null
    constraints:
      source_mutation_allowed: false
      state_mutation_allowed: false
      # artifact_persistence_allowed 取决于用户是否要求保存报告

  # ─── 新书初始化 ───
  - route_id: INIT_NEW_PROJECT
    when:
      task_type: INIT_PROJECT
      project_exists: false
    steps:
      - skill: novel-brief
        mode: DEFAULT
      - skill: story-architect
        mode: STORY
      - skill: story-architect
        mode: CHARACTER
      - skill: story-architect
        mode: WORLD
      - skill: story-architect
        mode: PLOT
      - skill: novel-master
        mode: INITIALIZATION_REVIEW
    approval_gate: INIT_PROJECT
    state_commit:
      skill: continuity-keeper
      mode: COMMIT_CANON
      after: USER_CONFIRMED
    constraints:
      approval_must_cover: [project_brief, story_architecture, principal_characters, core_world_rules, active_plot_plan]

  # ─── 章节规划 ───
  - route_id: PLAN_CHAPTER
    when:
      task_type: PLAN_CHAPTER
    steps:
      - skill: continuity-keeper
        mode: EXTRACT_CONTEXT
      - skill: chapter-planner
        mode: DEFAULT
    approval_gate: null
    state_commit: null
    constraints:
      no_state_commit: true  # 规划不提交已发生状态

  # ─── 默认章节写作（有章节卡） ───
  - route_id: WRITE_CHAPTER_WITH_PLAN
    when:
      task_type: WRITE_CHAPTER
      chapter_plan_exists: true
      task_mode: STANDARD
    steps:
      - skill: continuity-keeper
        mode: EXTRACT_CONTEXT
      - skill: chapter-writer
        mode: WRITE
    approval_gate: ACCEPT_CHAPTER
    state_commit:
      skill: continuity-keeper
      mode: COMMIT_CHAPTER_STATE
      after: ACCEPTED

  # ─── 默认章节写作（无章节卡，需先规划） ───
  - route_id: WRITE_CHAPTER_NO_PLAN
    when:
      task_type: WRITE_CHAPTER
      chapter_plan_exists: false
      task_mode: STANDARD
    steps:
      - skill: continuity-keeper
        mode: EXTRACT_CONTEXT
      - skill: chapter-planner
        mode: DEFAULT
      - skill: chapter-writer
        mode: WRITE
    approval_gate: ACCEPT_CHAPTER
    state_commit:
      skill: continuity-keeper
      mode: COMMIT_CHAPTER_STATE
      after: ACCEPTED

  # ─── 严格章节写作 ───
  - route_id: WRITE_CHAPTER_STRICT
    when:
      task_type: WRITE_CHAPTER
      task_mode: STRICT
    steps:
      - skill: continuity-keeper
        mode: EXTRACT_CONTEXT
      - skill: chapter-planner
        mode: DEFAULT
      - skill: chapter-writer
        mode: WRITE
      - skill: novel-reviewer
        mode: DEFAULT
    approval_gate: ACCEPT_CHAPTER
    state_commit:
      skill: continuity-keeper
      mode: COMMIT_CHAPTER_STATE
      after: ACCEPTED
    constraints:
      review_required: true

  # ─── 章节修订 ───
  - route_id: EDIT_CHAPTER
    when:
      task_type: EDIT_TEXT
    steps:
      - skill: novel-reviewer
        mode: DEFAULT
      - skill: chapter-writer
        mode: EDIT
    approval_gate:
      when_risk: HIGH
      requires: ApprovalRef
    state_commit:
      skill: continuity-keeper
      mode: COMMIT_CHAPTER_STATE
      after: ACCEPTED
      condition: semantic_impact has fact/state/plot change
    constraints:
      edit_level_from_envelope: true
      # L1/L2 通常不更新状态
      # L3 改变事实/状态/结果时为 HIGH，需 ApprovalRef
      # L4 必须 ApprovalRef + expires_after_use: true

  # ─── Canon 修改 ───
  - route_id: UPDATE_CANON
    when:
      task_type: UPDATE_CANON | RETCON
    steps:
      - skill: continuity-keeper
        mode: IMPACT_ANALYSIS
      - skill: novel-master
        mode: USER_CONFIRM
      - skill: story-architect
        mode: "{affected_mode}"  # STORY/CHARACTER/WORLD/PLOT
      - skill: continuity-keeper
        mode: COMMIT_CANON
    approval_gate: COMMIT_CANON | RETCON
    state_commit:
      skill: continuity-keeper
      mode: COMMIT_CANON
      after: USER_CONFIRMED
    constraints:
      impact_analysis_required: true
      approval_must_cover_revision: true
      retcon_requires_one_time_approval: true

  # ─── 冲突检查 ───
  - route_id: CHECK_CONTINUITY
    when:
      task_type: CHECK_CONTINUITY
    steps:
      - skill: continuity-keeper
        mode: CHECK_CONTRADICTIONS
    approval_gate: null
    state_commit:
      skill: continuity-keeper
      mode: CHECK_CONTRADICTIONS
      writes: [state/contradictions.md]  # 仅登记冲突
    constraints:
      no_canon_creation: true
      no_prose_modification: true

  # ─── 断更恢复 ───
  - route_id: RESUME_PROJECT
    when:
      task_type: RESUME_PROJECT
    steps:
      - skill: continuity-keeper
        mode: RESTORE_PROJECT / EXTRACT_EVIDENCE
      - skill: novel-master
        mode: RECOVERY_REVIEW  # 输出 RecoveryReport
      - skill: continuity-keeper
        mode: RESTORE_PROJECT / REBUILD_STATE
        condition: user_confirmed
      - skill: chapter-planner
        mode: DEFAULT
    approval_gate: COMMIT_CANON
    state_commit:
      skill: continuity-keeper
      mode: RESTORE_PROJECT / REBUILD_STATE
      after: USER_CONFIRMED
    constraints:
      inferred_candidates_are_proposals_only: true
      recovery_report_revision_bound: true

  # ─── 低风险 Advisory ───
  - route_id: LOW_RISK_ADVISORY
    when:
      task_mode: ADVISORY | FAST
      risk_level: LOW
      # 情节方向讨论、人物名字、设定灵感、章节标题、合理性讨论
    steps:
      - skill: "{target_skill}"
        mode: "{target_mode}"
    approval_gate: null
    state_commit: null
    constraints:
      no_formal_artifact: true
      no_state_mutation: true
      output_as_proposal: true
```

## 项目阶段默认路由

```yaml
stage_routing:
  - stage: no_project
    next: novel-brief
  - stage: has_brief_no_architecture
    next: story-architect / STORY
  - stage: has_architecture_missing_characters_or_world
    next: story-architect / CHARACTER | WORLD
  - stage: has_architecture_no_outline
    next: story-architect / PLOT
  - stage: has_outline_no_chapter_plan
    next: chapter-planner
  - stage: has_chapter_plan_no_draft
    next: chapter-writer / WRITE
  - stage: has_draft
    next: review | edit | state_commit  # 根据请求
```

## 接受闸门规则

- 章节写作后必须经过接受闸门，不可省略。
- 只有 ACCEPTED 或 PUBLISHED 的正式事实变化才能进入 COMMIT_CHAPTER_STATE。
- DRAFT/REVIEWED 状态的变化只能进入 state_change_proposals。
- 自动日更需预授权（覆盖项目、章节范围、偏离程度、失效条件）。
