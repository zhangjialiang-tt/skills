---
title: novel-master V1.2 架构总纲（候选版本）
document_id: NM-ARCH
version: 1.2.0-rc1
status: RC
based_on: novel-master-architecture-v1.1.0-frozen.md
drafted_at: 2026-07-25
applies_to: novel-master V1.2 章节生产与质量契约
companion: novel-master-contracts-v1.2.0-rc1.md
change_log: |
  - 新增 novel-style 子系统（已在 v1.1.0 冻结，此处仅为追溯记录）
  - 新增 §15：V1.2 章节生产与质量契约（本章本版新增）
  - 新增 ADR 6.6：章节质量契约闭环
  - 新增 ADR 6.7：场景风格调制
  - 扩展 §5 不变量：新增不变量 16–20
  - 扩展 §7：用户权限与风险控制，增加质量闸门
  - 扩展 §8 标准工作流，增加 v1.2 质量链
---

# `novel-master` 架构总纲 V1.2（候选版本）

> 本文基于 `novel-master-architecture-v1.1.0-frozen.md`。仅记录 v1.2.0 的新增和变更。未列举的章节与 v1.1.0 冻结版本一致。

---

## 5. 系统级不变量（扩展）

以下为 v1.2.0 新增不变量。原来的 1–15（可能会因 v1.1.0 的 novel-style 新增而有微小偏移）保持不变。

**16. 必须：章节生产与质量契约。** chapter-planner 输出必须包含 reader_experience 结构（FAST 模式除外）。Writer 必须在 chapter_report 中逐项报告 reader_experience 的执行位置和证据。Reviewer 必须按 review_dimension 独立验证，未激活维度的诊断不得混入已激活维度。

**17. 必须：Guardrail 扫描。** 无论 review_scope 是什么，Reviewer 必须始终对 CANON_CONFLICT、KNOWLEDGE_STATE_VIOLATION、PROHIBITED_REVEAL 和 MAJOR_FACT_CONTRADICTION 进行最小扫描。结果输出到独立的 guardrail_results，不混入 dimension_results。

**18. 禁止：Writer 自我评分。** Writer 只报告逐项目标执行情况（PRESENT | PARTIAL | DEVIATED），不得输出全局质量评分或声称已达标。质量判定由 Reviewer 负责。

**19. 必须：风格调制闭环。** novel-style 为每种场景类型输出 scene_modulations 覆盖项。chapter-planner 为每个 scene 引用 modulation_id。continuity-keeper 通过 ContextPack 传递相关的风格调制定义给 Writer 和 Reviewer。任何 modulation 不得覆盖 protected_fields 中定义的硬约束。

**20. 必须：契约版本标记。** 所有业务交付物（ChapterPlan、ChapterReport、ReviewRequest、ReviewReport、StyleGuide）必须包含 contract_meta 结构（schema_id + schema_version）。缺少 contract_meta 的输入按 v1.1 legacy 解析，只读兼容。

---

## 6. 关键设计决策（扩展）

### ADR 6.6：章节质量契约闭环（新增）

**背景**：v1.1 将系统正确性（权限、事务、Canon）治理得很好，但产出的章节在读者体验上没有结构化的质量目标。Planner 仅通过 chapter_function 单一字符串描述章节目的；Writer 仅报告事实变化而无质量追踪；Reviewer 仅使用通用 overall_assessment，无维化诊断。

**决策**：引入 reader_experience 结构作为章节质量目标，打通 Planner → Writer → Reviewer 的闭环。

**替代方案**：
- A. 在 Skill 内隐式定义质量（依赖提示词约束）。否决：不可测试、不可验证。
- B. 引入独立质量评分器 Skill。否决：增加 Skill 数量，且质量判定与 Reviewer 职责重叠。
- C. **（采用）在现有 Planner/Writer/Reviewer 链中增加质量字段**。不新增 Skill，复用已有生产链。

**结果**：
- Planner 必须产生 reader_experience（含 chapter_role、promise、payoff 等结构化目标）。
- Writer 必须在 chapter_report 中逐项报告执行情况（target_execution + evidence_ref）。
- Reviewer 的 dimension_results 必须对 READER_EXPERIENCE 维度进行独立验证。
- 质量判定形成了"定义→执行→验证"的闭环。

### ADR 6.7：场景风格调制（新增）

**背景**：v1.1 的 novel-style 将 style_guide.md 定义为统一整书固定规则。但实际网文创作中，战斗章、情感章和解谜章对句式、描写密度和节奏的要求完全不同。固定规则会让所有章节写作风格趋同。

**决策**：在 style_guide 中增加 scene_modulations，为每类场景提供相对于全局默认值的覆盖项（如 COMBAT 使用 SHORTER 句子、HIGHER 动作密度）。

**替代方案**：
- A. 固定调制规则（硬编码 COMBAT/EMOTIONAL 等类型）。否决：无法覆盖项目特殊类型。
- B. 不使用覆盖项，每个场景单独定义完整 Style。否决：增加冗余且维护困难。
- C. **（采用）项目级 modulation_id + stable category + typed relative overrides**。允许项目自定义调制类型，使用稳定 category 枚举进行跨项目分类。

**结果**：
- novel-style 输出 scene_modulations 和 override_policy（含 protected_fields）。
- Planner 为每个 scene 引用 style_modulation_ref。
- 风格合并优先级为：章节 overrides > scene modulation > global defaults。
- protected_fields（如 POV、narrative_person）不可被任何 modulation 覆盖。

---

## 7. 用户权限与风险控制（扩展）

v1.2.0 新增**质量闸门**（不同于 Approval Gate）：

| 风险级别 | 场景类型 | 质量闸门行为 |
| --- | --- | --- |
| HIGH | Continuation_drive=NONE_JUSTIFIED 且无有效 justification | Reviewer 必须标记 WARNING 或 FAIL |
| HIGH | Payoff 被连续 DEFERRED 超过预期时间窗 | Planner 下一章必须调整，Reviewer 必须记录 |
| MEDIUM | Tension_curve=FLAT_JUSTIFIED 但 justification 弱 | Reviewer 标记 INFO 并建议增强 |
| MEDIUM | Reader_experience 目标与正文实际内容脱节 | Writer 的 target_execution=DEVIATED，Reviewer 验证 |

---

## 8. 标准工作流（扩展）

V1.2.0 的质量生产链取代了 V1.1 的线性链条：

```text
novel-style
 → continuity-keeper / EXTRACT_CONTEXT（ContextPack 内含 style_profile）
 → chapter-planner（输出 reader_experience + scene style_modulation_ref）
 → chapter-writer（消费 reader_experience + 输出 target_execution）
 → novel-reviewer（按 review_scope 独立验证 + guardrail_results）
 → novel-master（显式传入 review_scope，路由）
```

V1.1 的链仍可用，但：
- STANDARD/STRICT 模式下必须走 V1.2 质量链。
- FAST 模式下可以省略 reader_experience 和 dimension_results 中的 READER_EXPERIENCE 维度。
- ADVISORY 模式下按实际任务决定。

---

## 15. V1.2 章节生产与质量契约

V1.2.0 的发布范围严格限定为：

> 引入章节生产与质量契约，使 Planner 能定义读者体验目标、Writer 能按目标逐项报告执行情况、Reviewer 能按维度独立验证并提供证据化诊断、Style 能按场景提供项目级弹性约束。

以下能力**不属于** V1.2.0 范围，明确排除：
- 正式质量状态机（UNASSESSED / NEEDS_REVISION / PASS_INTERNAL / READY_TO_PUBLISH）
- 创作模式简化（FAST 模式的自动接受或预授权）
- 质量评分与状态自动流转
- 自动日更授权

---

## 16. 变更记录

| 版本 | 日期 | 主要变更 |
| --- | --- | --- |
| 1.2.0-rc1 | 2026-07-25 | 新增 §15 V1.2 章节生产与质量契约；新增 ADR 6.6–6.7；扩展不变量 16–20；扩展质量闸门；引入 v1.2 质量链 |
| 1.1.0 | 2026-07-25 | 冻结基线，增设 novel-style |
