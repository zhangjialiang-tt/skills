---
title: novel-master V1.2 契约手册（候选版本）
document_id: NM-CONTRACT
version: 1.2.0-rc1
status: RC
based_on: novel-master-contracts-v1.1.0-frozen.md
drafted_at: 2026-07-25
applies_to: novel-master V1.2 章节生产与质量契约
companion: novel-master-architecture-v1.2.0-rc1.md
change_log: |
  - 新增 §12.7：novel-style 子 Skill 契约（已在 v1.1.0 冻结，此处为追溯记录）
  - 扩展 §4.3：章节生命周期（新增 contract_meta 要求）
  - 扩展 §6：SkillResult.deliverables（新增 evidence_ref 共享定义）
  - 新增 §17：章节质量契约（reader_experience）
  - 新增 §18：Writer 执行追踪（reader_experience_execution）
  - 新增 §19：Reviewer 分层诊断（review_dimensions、guardrail_results、dimension_results）
  - 新增 §20：场景风格调制（scene_modulations、override_policy）
  - 新增 §21：契约版本化（contract_meta）
  - 扩展 §9：ContextPack（新增 style_profile）
  - 扩展 §12.3–12.6：子 Skill 契约（补充 v1.2 字段）
  - 新增 §22：兼容与迁移策略
  - 新增 §23：确定性校验（validate_quality_contract.py）
---

# `novel-master` V1.2 契约手册（候选版本）

> 本文基于 `novel-master-contracts-v1.1.0-frozen.md`。仅记录 v1.2.0 的新增、修改和扩展。未列举的章节（§1–§16）与 v1.1.0 冻结版本一致。

---

## 4. 信息状态、章节生命周期与来源（扩展）

### 4.3 章节生命周期（扩展）

v1.2.0 在章节卡中增加 `contract_meta` 强要求：

```yaml
contract_meta:
  schema_id: novel-master/chapter-plan
  schema_version: "1.2.0"
```

兼容规则：
- 缺少 `contract_meta` → v1.1 遗留章节卡。只读兼容，STANDARD/STRICT 使用前必须用 Planner 升级。
- `schema_version: "1.2.0"` → v1.2 章节卡。reader_experience 按模式条件必需。

---

## 9. ContextPack（扩展）

v1.2.0 在 ContextPack 中新增 `style_profile` 对象。保留 v1.1 的 `style_constraints: array[string]` 向后兼容。

### 9.x style_profile（新增）

```yaml
style_profile:
  global_defaults_ref:
    path: string       # style_guide.md 路径
    revision: string   # style_guide.md 的当前 revision
  relevant_scene_modulations:
    - modulation_id: string     # 当前章节 scens 引用的调制类型 ID
      overrides: object         # 该调制类型的完整覆盖规则
      source_ref: string        # 来源（style_guide.md 路径 + revision）
```

加载器兼容规则：`schema_version: "1.0"` 或 `"1.1"` 的 ContextPack 无 `style_profile` → 视为无风格调制信息。

---

## 12.1–12.7 子 Skill 契约（扩展）

### 12.3 chapter-planner（扩展）

**新增输出字段**（在原有 `chapter_plan` 结构基础上）：

```yaml
chapter_plan:
  # v1.1 原有字段保持不变：chapter_id、chapter_function、
  # viewpoint_character、time_and_location、opening_state、
  # scenes[]、required_elements、prohibited_reveals、
  # active_foreshadowing、chapter_climax、ending_state、
  # continuity_risks

  reader_experience:  # v1.2 新增，FAST 可选
    chapter_role:
      primary: enum
      secondary: list[enum] | null
      description: string
    promise: string
    payoff: object
    emotional_arc: object
    information_gain: list[object] | null
    tension_curve: object
    continuation_drive: object

  contract_meta:      # v1.2 新增，必须
    schema_id: "novel-master/chapter-plan"
    schema_version: "1.2.0"

scenes:
  - scene_id: string
    # v1.1 原有字段
    style_modulation_ref: string | null  # v1.2 新增
```

### 12.4 chapter-writer（扩展）

**新增输出字段**（在原有 chapter_report 基础上）：

```yaml
chapter_report:
  # v1.1 原有字段保持不变
  reader_experience_execution:  # v1.2 新增
    target_execution:
      - target_ref: string          # JSON Pointer，如 /reader_experience/promise
        execution: PRESENT | PARTIAL | DEVIATED
        evidence_ref:
          source_type: CHAPTER_DRAFT | CHAPTER_PLAN | CANON |
                       CONTEXT_PACK | STYLE_GUIDE | CHAPTER_REPORT
          deliverable_id: string
          revision: string
          scene_id: string | null
          paragraph_start: integer | null   # 1-based, closed interval
          paragraph_end: integer | null
          json_pointer: string | null       # YAML evidence
          excerpt: string
    deviations:
      - planned: string
        actual: string
        reason: string
    unplanned_effects:
      - effect: string
        evidence_ref: object      # 同上结构

  contract_meta:     # v1.2 新增，必须
    schema_id: "novel-master/chapter-report"
    schema_version: "1.2.0"
```

**禁止**：Writer 不得输出全局 quality_score 或 ACHIEVED/FAILED 等自我评分字段。是否达标由 Reviewer 决定。

### 12.5 novel-reviewer（扩展）

**输入契约变更**：

```yaml
review_request:
  review_target: FileRef | inline_text
  review_scope:       # v1.2 改为 list[review_dimension]
    - CONTRACT_COMPLIANCE
    - NARRATIVE_SOUNDNESS
    - READER_EXPERIENCE
    - CRAFT_EXECUTION
  chapter_plan_ref: FileRef | null
  chapter_report_ref: FileRef | null
  context_pack_ref: FileRef | null

  contract_meta:      # v1.2 新增，必须
    schema_id: "novel-master/review-request"
    schema_version: "1.2.0"
```

由 novel-master 编排调用时 `review_scope` **必填**。

**输出契约变更**：

```yaml
review_report:
  # v1.1 overall_assessment、confirmed_issues 等保留

  # v1.2 新增：Guardrail 扫描（独立于维度评审）
  guardrail_results:
    status: PASS | WARNING | BLOCKED
    findings:
      - guardrail: CANON_CONFLICT | KNOWLEDGE_STATE_VIOLATION |
                   PROHIBITED_REVEAL | MAJOR_FACT_CONTRADICTION
        severity: BLOCKER | WARNING | INFO
        evidence_ref: object
        assessment: string
        recommended_action: string

  # v1.2 新增：维度化诊断（必须恰好包含四个维度）
  dimension_results:
    - dimension: CONTRACT_COMPLIANCE
      status: PASS | WARNING | FAIL | NOT_EVALUATED
      reason_code: string | null          # NOT_EVALUATED 时必须
      findings:
        - criterion: string
          evidence_ref: object
          assessment: string
          recommended_action: string
          severity: INFO | WARNING | BLOCKER
    - dimension: NARRATIVE_SOUNDNESS
      # 同上结构
    - dimension: READER_EXPERIENCE
      # 同上结构
    - dimension: CRAFT_EXECUTION
      # 同上结构

  contract_meta:     # v1.2 新增，必须
    schema_id: "novel-master/review-report"
    schema_version: "1.2.0"
```

**reason_code 枚举**：`NOT_REQUESTED`（未在 review_scope 中激活）、`MISSING_PLAN_CONTRACT`（旧版章节卡无 reader_experience）、`MISSING_SOURCE`、`STALE_REVISION`、`INSUFFICIENT_CONTEXT`。

### 12.6 continuity-keeper（扩展）

EXTRACT_CONTEXT 的 ContextPack 输出扩展：在原有结构基础上增加 `style_profile` 对象（详见 §9.x）。

### 12.7 novel-style（新增 — 在 v1.1.0 已落地）

**输出扩展**（v1.2 新增）：

```yaml
style_guide:
  # v1.1 原有 12 节保持不变
  scene_modulations:          # v1.2 新增
    COMBAT_FAST:              # 项目级 modulation_id
      category: COMBAT
      overrides:
        sentence_rhythm:
          relative_to_global: SHORTER
        action_density:
          relative_to_global: HIGHER
    # 更多调制类型...

  override_policy:            # v1.2 新增
    protected_fields:
      - /narrative/viewpoint
      - /narrative/person
      - /characters/*/voice/core
      - /constraints/prohibited_author_styles
      - /constraints/must_avoid
      - /constraints/content_safety

  contract_meta:              # v1.2 新增
    schema_id: "novel-master/style-guide"
    schema_version: "1.2.0"
```

---

## 17. 章节质量契约：reader_experience

### 17.1 结构定义

```yaml
reader_experience:
  chapter_role:
    primary: SETUP | ESCALATION | PAYOFF | REVEAL |
             REVERSAL | TRANSITION | RECOVERY | CLIMAX
    secondary: list[enum] | null
    description: string

  promise: string
    # 具体到本章内容，禁止使用空泛表述

  payoff:
    mode: FULL | PARTIAL | DEFERRED | NONE_JUSTIFIED
    description: string
    deferred_reason: string | null       # DEFERRED 必填
    justification: string | null         # NONE_JUSTIFIED 必填
    expected_payoff_window:
      type: NEXT_CHAPTER | WITHIN_CHAPTERS | ARC_END | VOLUME_END | null
      chapter_count: integer | null

  emotional_arc:
    target: string
    turning_point: string

  information_gain:                     # optional
    - target_id: string
      what: string
      significance: string

  tension_curve:
    type: RISING | WAVE | SPIKE | RELEASE | FLAT_JUSTIFIED
    description: string

  continuation_drive:
    type: QUESTION | DANGER | DECISION | REVELATION |
          EMOTIONAL | GOAL | NONE_JUSTIFIED
    description: string
    justification: string              # NONE_JUSTIFIED 必填
```

### 17.2 条件必需规则

| TaskEnvelope.task.mode | reader_experience 要求 |
| --- | --- |
| FAST | 可选；缺失时产生提示，不阻塞 |
| STANDARD | 必须包含；chapter_role.primary/promise/payoff.mode/emotional_arc.target/tension_curve.type/continuation_drive.type 至少必填 |
| STRICT | 必须包含；同上 + payoff.mode=DEFERRED 必填 deferred_reason + NONE_JUSTIFIED 必填 justification |
| ADVISORY | 按任务判断 |

- 空 reader_experience: {} 在 STANDARD/STRICT 下视为非法。
- 条件必需中的 task.mode 在 TaskEnvelope 中，与 chapter_plan 分属不同对象。交叉校验由 `validate_quality_contract.py` 负责。

---

## 18. Writer 执行追踪：reader_experience_execution

位于 `chapter_report` 中。Writer 按 reader_experience 的每个目标项输出逐项执行报告。

### 18.1 target_ref 引用规则

- 固定单项字段：使用 JSON Pointer，如 `/reader_experience/promise`。
- 数组条目 `information_gain`：使用显式 target_id，如 `/reader_experience/information_gain/INFO-001`。

### 18.2 evidence_ref 规范

段落编号：1-based、闭区间。段落按标准化 Markdown 的非空块顺序编号（标题和空行不算段落）。由于 evidence_ref 已绑定 revision，正文修改后旧引用失效可接受。

---

## 19. Reviewer 分层诊断

### 19.1 review_dimensions 定义

```yaml
review_dimensions:
  CONTRACT_COMPLIANCE:
    question: "是否违反章节卡、Canon、知情范围或风格指南"
  NARRATIVE_SOUNDNESS:
    question: "因果、动机、冲突、信息揭示是否成立"
  READER_EXPERIENCE:
    question: "是否兑现 reader_experience、情绪曲线、阅读动力"
  CRAFT_EXECUTION:
    question: "对话、句式、AI 腔、角色声音"
```

### 19.2 mandatory_guardrail_scan

无论 review_scope 是什么，以下项必须始终扫描：

```yaml
mandatory_guardrail_scan:
  - CANON_CONFLICT
  - KNOWLEDGE_STATE_VIOLATION
  - PROHIBITED_REVEAL
  - MAJOR_FACT_CONTRADICTION
```

> 注：OWNERSHIP_OR_AUTHORITY_VIOLATION 不在 Reviewer guardrail 中，由确定性校验器承担。

### 19.3 review_scope 路由映射

| 模式 | review_scope |
| --- | --- |
| STRICT | [CONTRACT_COMPLIANCE, NARRATIVE_SOUNDNESS, READER_EXPERIENCE, CRAFT_EXECUTION] |
| STANDARD | [CONTRACT_COMPLIANCE, NARRATIVE_SOUNDNESS, READER_EXPERIENCE] |
| FAST | [CONTRACT_COMPLIANCE] |
| 编排调用（novel-master） | review_scope 必填，由路由表显式传入 |
| 用户直接调用 | 可推导时按请求推导；无法推导时默认全量 |

---

## 20. 场景风格调制

### 20.1 scene_modulations 结构

```yaml
scene_modulations:
  <project_specific_modulation_id>:
    category: COMBAT | EMOTIONAL | MYSTERY | TRANSITION |
              CLIMAX | EXPOSITION | DEFAULT
    overrides:
      sentence_rhythm:
        relative_to_global: SHORTER | LONGER | SAME
      action_density:
        relative_to_global: HIGHER | LOWER | SAME
      narrative_distance:
        relative_to_global: CLOSER | FARTHER | SAME
      description_density:
        relative_to_global: HIGHER | LOWER | SAME
      dialogue_ratio:
        relative_to_global: HIGHER | LOWER | SAME
```

- `category` 使用稳定枚举，`modulation_id` 允许项目自定义（如 `COMBAT_FAST`、`ROMANCE_TENSION`）
- 禁止使用通用 `relative_to_global: string` — 每个字段仅允许预定义的 typed 操作符
- 两层 override 合并时，更具体的层覆盖更一般的层，**不叠加**
- Planner 引用 `modulation_id` → 校验器确认该 ID 在 style_guide.scene_modulations 中存在

### 20.2 override_policy

`protected_fields` 使用 JSON Pointer 路径。被保护的字段不可被任何 modulation 覆盖（除非用户显式确认）。

### 20.3 style_modulation_ref 必需规则

| 模式 | 要求 |
| --- | --- |
| FAST | 可选，可为 null |
| STANDARD / STRICT | 每个 scene 必填；无特殊调制时引用项目 DEFAULT modulation |
| 遗留计划 | 允许缺失 |

---

## 21. 契约版本化（contract_meta）

所有 v1.2 业务交付物必须包含：

```yaml
contract_meta:
  schema_id: string     # 如 "novel-master/chapter-plan"
  schema_version: string  # 如 "1.2.0"
```

适用类型：ChapterPlan、ChapterReport、ReviewRequest、ReviewReport、StyleGuide。

兼容规则：缺少 contract_meta 的输入 → 按 v1.1 legacy 解析 → 只读兼容 → STANDARD/STRICT 使用前必须升级。

---

## 22. 兼容与迁移策略

| 使用场景 | 处理 |
| --- | --- |
| 只查看旧章节卡 | 直接兼容读取 |
| FAST 写作 | 可以带警告继续 |
| STANDARD/STRICT 写作 | 先由 Planner 生成 v1.2 修订版或补充质量契约 |
| Reviewer 审查旧正文 | reader_experience 维度标记 NOT_EVALUATED + reason_code: MISSING_PLAN_CONTRACT |
| v1.1 遗留文件 | 由加载器根据 contract_meta 缺失识别，不强制修改原文件 |

---

## 23. 确定性校验

### 23.1 validate_quality_contract.py（新增）

承担跨对象/跨文件的语义校验：

- STANDARD/STRICT 下 reader_experience 存在性（需同时读取 TaskEnvelope 和 ChapterPlan）
- style_modulation_ref 引用存在性（需同时读取 ChapterPlan 和 StyleGuide）
- override_policy.protected_fields 是否被 modulation 覆盖
- relative_to_global 操作符是否合法
- chapter_role.primary、payoff.mode、tension_curve.type 等枚举值合法性

JSON Schema 仅负责单对象结构校验。跨对象/跨文件语义由本脚本负责。

### 23.2 resolve_style_profile.py（可选）

确定性风格解析：根据全局默认值、scene modulation overrides 和章节临时覆盖，输出已解析的 effective_scene_styles。Writer 消费已解析结果，避免不同实现对合并优先级产生不同解释。

---

## 24. 变更记录

| 版本 | 日期 | 主要变更 |
| --- | --- | --- |
| 1.2.0-rc1 | 2026-07-25 | 新增 §17–§23；扩展 §4.3、§9、§12.3–§12.7；引入 reader_experience、dimension_results、scene_modulations、contract_meta、guardrail_results |
