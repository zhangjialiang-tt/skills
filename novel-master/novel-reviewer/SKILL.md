---
name: novel-reviewer
description: "基于文本证据只读诊断长篇网文，不直接修改正文。仅由 $novel-master 路由或用户显式调用 $novel-reviewer；只有 artifact_persistence_allowed=true 时保存 reviews/，普通网文请求统一交给 $novel-master。"
---

# novel-reviewer

## 职责

基于文本证据进行只读诊断：识别问题、评估风险、给出可执行建议和推荐编辑等级。

## 何时触发

- 用户要求分析、评审或诊断章节/正文。
- 修改前需要先诊断问题（评审与修改分离）。
- 卷末复盘。
- 剧情合理性讨论。

## 何时不触发

- 用户要求直接修改正文（应路由 chapter-writer / EDIT）。
- 任务涉及状态提交或 Canon 更新。
- 任务涉及设计（故事、人物、世界、大纲）。

## 激活模式

DEFAULT（唯一模式）。

## 必需输入

- `review_target`: 被评审的文件或文本。
- `review_scope`: `list[review_dimension]`。由 novel-master 编排调用时必填；用户直接调用时可推导。
  - CONTRACT_COMPLIANCE：是否违反章节卡、Canon、知情范围或风格指南。
  - NARRATIVE_SOUNDNESS：因果、动机、冲突、信息揭示是否成立。
  - READER_EXPERIENCE：是否兑现 reader_experience、情绪曲线、阅读动力。
  - CRAFT_EXECUTION：对话、句式、AI 腔、角色声音。
- `chapter_plan_ref`：章节卡引用（optional，READER_EXPERIENCE 维度激活时需）。
- `chapter_report_ref`：Writer 执行报告引用（optional，READER_EXPERIENCE 维度激活时需）。

## 允许读取

- 被评审的正文文件。
- `project_brief.md`、`architecture/`、`chapters/plans/`、`state/`（只读参考）。
- 上下文包（如提供）。

## 允许写入

- 仅当 `artifact_persistence_allowed: true` 时可写 `reviews/*.md`。
- 保存的报告必须标明被评审内容的 `deliverable_id`、`revision` 和 `content_hash`。
- `artifact_persistence_allowed: false` 时不得写入任何文件。

## 操作步骤

1. 读取评审目标和相关上下文。
2. 执行 mandatory_guardrail_scan：无论 review_scope 是什么，始终扫描 CANON_CONFLICT、KNOWLEDGE_STATE_VIOLATION、PROHIBITED_REVEAL 和 MAJOR_FACT_CONTRADICTION。结果输出到独立的 guardrail_results。
3. 按 review_scope 激活对应维度，每个维度输出独立的 dimension_results（恰好四个维度，每个出现一次）。未激活维度的 status 为 NOT_EVALUATED，填写 reason_code。
4. 每个 finding 附带结构化 evidence_ref（source_type/deliverable_id/revision/excerpt），区分已证实问题、潜在风险和偏好建议。
5. 识别应保留的优点。
6. 给出推荐编辑等级和推荐后继 Skill。
7. 如允许持久化（artifact_persistence_allowed: true），写入 `reviews/`。

## 禁止事项

- 直接重写或修改评审对象。
- 修改 `state/`。
- 笼统评价（无证据）。
- 把偏好当错误。
- 承诺作品成败。
- 为爽点破坏定位。
- 省略未激活维度（dimension_results 必须恰好包含四个维度）。
- 对未激活维度做系统性评审（guardrail 偶然发现除外）。

## 输出

```yaml
review_report:
  # v1.1 原有
  overall_assessment
  confirmed_issues[] / potential_risks[]
  preference_based_suggestions[] / strengths_to_preserve[]
  recommended_edit_level / recommended_next_skill

  # v1.2 新增：Guardrail 安全扫描（无论 scope 均执行）
  guardrail_results:
    status: PASS | WARNING | BLOCKED
    findings:
      - guardrail: CANON_CONFLICT | KNOWLEDGE_STATE_VIOLATION |
                   PROHIBITED_REVEAL | MAJOR_FACT_CONTRADICTION
        severity: BLOCKER | WARNING | INFO
        evidence_ref: { source_type, deliverable_id, revision, excerpt, ... }
        assessment: string
        recommended_action: string

  # v1.2 新增：维度化诊断（恰好四个维度）
  dimension_results:
    - dimension: CONTRACT_COMPLIANCE
      status: PASS | WARNING | FAIL | NOT_EVALUATED
      reason_code: string | null
      findings:
        - criterion: string
          evidence_ref: { ... }
          assessment: string
          recommended_action: string
          severity: INFO | WARNING | BLOCKER
    - dimension: NARRATIVE_SOUNDNESS  # 同上结构
    - dimension: READER_EXPERIENCE    # 同上结构
    - dimension: CRAFT_EXECUTION      # 同上结构

  # v1.2 新增
  contract_meta:
    schema_id: "novel-master/review-report"
    schema_version: "1.2.0"
```

## 完成标准

- 重要问题都有文本或项目证据（evidence_ref 含 source_type/deliverable_id/revision/excerpt）。
- 明确区分已证实问题、潜在风险和偏好建议（severity 字段）。
- guardrail_results 已执行 mandatory_guardrail_scan，独立于 dimension_results。
- dimension_results 恰好包含四个维度（CONTRACT_COMPLIANCE/NARRATIVE_SOUNDNESS/READER_EXPERIENCE/CRAFT_EXECUTION）；未激活维度的 status 为 NOT_EVALUATED 且填写 reason_code。
- 旧正文无 reader_experience 时 READER_EXPERIENCE 维度标记 NOT_EVALUATED + reason_code: MISSING_PLAN_CONTRACT。
- 建议可执行并说明应保留的优点。
- 给出合理编辑等级。
- contract_meta 已填写。

## 阻塞条件

- 评审目标缺失或不可读（`BLOCKED`）。
- 评审范围不明确且无法从上下文推断（`NEEDS_DECISION`）。

## 按需读取

- 执行前读取[公共规则](../references/common-rules.md)和[文件所有权](../references/file-ownership.md)，严格保持只读边界。
- 评估文风时，读取[风格指南模板](../references/style-guide-template.md)并以项目实际 `style_guide.md` 为证据。
- 判断报告能否落盘、revision 是否匹配或后继编辑是否需授权时，读取[生命周期与授权](../references/lifecycle-and-approval.md)。
- 返回阻塞或降级结果时，读取[错误码](../references/error-codes.md)。
- 需要核对评审报告结构时，读取[冻结契约](../docs/novel-master-contracts-v1.1.0-frozen.md) §12.5、§5.6 和[冻结架构](../docs/novel-master-architecture-v1.1.0-frozen.md) §6.3。
