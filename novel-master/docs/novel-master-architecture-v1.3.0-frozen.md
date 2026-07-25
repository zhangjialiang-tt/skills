---
title: novel-master V1.3 架构总纲
document_id: NM-ARCH
version: 1.3.0
status: FROZEN
frozen_at: 2026-07-25
supersedes: novel-master-architecture-v1.2.0-frozen.md
applies_to: novel-master V1.3 长篇故事规划与漂移控制
companion: novel-master-contracts-v1.3.0-frozen.md
change_log: |
  - 新增 §5 不变量 21–27：规划分层、ChapterBatch、偏差分级、计划版本化、PlanningPack、历史章节保护、规划进度
  - 新增 ADR 6.8：分层滚动规划
  - 新增 ADR 6.9：偏差分级与漂移控制
  - 新增 ADR 6.10：规划元数据与引用模型
  - 扩展 §7 质量闸门：新增规划进度检查点
  - 扩展 §8 标准工作流：新增 v1.3 规划生产链
  - 新增 §17：V1.3 长篇规划与漂移控制
---

# novel-master 架构总纲 V1.3（候选版本）

## 1. 文档定位

本文是 v1.3.0-rc1 的候选架构。基于 v1.2.0-frozen，新增分层滚动规划与漂移控制。

字段、路由、文件所有权和子 Skill 输入输出以配套文档
[《novel-master V1.3 契约手册》](novel-master-contracts-v1.3.0-rc1.md)
为规范来源。

---

## 版本变更（仅 v1.3 新增/修改项）

### 新增不变量

**21. 必须：分层规划体系。** 规划分为 L0（读者契约）→ L1（故事发动机）→ L2（全书主干）→ L3（分卷大纲）→ L4（剧情弧）→ L5（章节批次）→ L6（单章卡）。每层有自身 revision/hash。上层更新不使下层已接受产物失效。

**22. 必须：ChapterBatch。** chapter-planner 必须在章节写作前生成 ChapterBatch（含 slot_id + beat_refs + payload_plan），单章卡引用 batch_slot_ref。batch_slot_ref 的 PlanRef 部分必须与 batch_ref 指向同一 artifact_id/revision/content_hash。

**23. 必须：偏差分级。** 章节偏离分为 LOCAL（记录）→ TACTICAL（重规划 Arc）→ STRATEGIC（影响分析+用户确认）。Planner 通过 deviation_policy 预先声明最大自动接受级别。Writer 报告 actual_deviations。Reviewer 通过 deviation_assessment 确认最终级别。任何模式不得跳过 STRATEGIC 的 ApprovalRef 校验。

**24. 必须：规划产物版本化。** 所有规划产物（StoryEngine、ProjectSpine、VolumeArc、ArcPlan、ChapterBatch）必须包含 planning_artifact_meta（schema_id + schema_version + artifact_type + artifact_id + revision + lifecycle_status）。外部引用必须使用 PlanRef（含 content_hash）。嵌套项必须使用 ItemRef（item_id 为规范身份，json_pointer 为定位缓存）。

**25. 必须：PlanningPack。** 由 scripts/build_planning_pack.py 确定性构建，novel-master 调用。包含当前 active_phase/volume/arc/batch 的 PlanRef + planning_execution 历史。不塞入 ContextPack。

**26. 保护：历史章节不受规划更新影响。** ACCEPTED/PUBLISHED 章节不因上游规划更新而标记 STALE。它们是当时有效规划下的历史证据。仅高风险 Retcon 时通过 IMPACT_ANALYSIS 处理。

**27. 必须：规划进度追踪。** novel-master 在每次章节 ACCEPT 后更新 workflow/plan_progress.md（独立、幂等、可重建）。不绑定 COMMIT_CHAPTER_STATE，因为无状态变化的章节也推进规划。plan_progress 更新失败时标记 SYNC_PENDING，可从 ACCEPTED 章节重建。

### 新增架构决策

### 6.8 决策：分层滚动规划（v1.3 新增）

**背景**：v1.2 仅有一层 plot_plan（事件时间线），不能支撑"当前章节在全书中承担什么角色、偏离后如何调整后续"的需求。

**决策**：引入 L0–L6 分层规划，不同层级不同精度、不同稳定性、不同负责人。

**替代方案**：
- A. 全量一次性规划。否决：不适用于网文动态创作。
- B. 仅增加字段不增加层级。否决：无法区分锚点和路径。
- C. **（采用）分层滚动规划**。不新增 Skill。

**结果**：STORY 负责 L1（story_engine）+ L2（project_spine），PLOT 负责 L3（volume_arcs）+ L4（arc_catalog），chapter-planner 负责 L5（ChapterBatch）+ L6（章节卡）。

### 6.9 决策：偏差分级与漂移控制（v1.3 新增）

**背景**：写作过程中必然产生偏离。v1.2 要么全接受、要么全拒绝，没有"偏离但可接受"的中间状态。

**决策**：三级偏差（LOCAL/TACTICAL/STRATEGIC），不同级别不同处理路径。Planner 预先声明 deviation_policy，Writer 如实报告，Reviewer 独立确认。

**结果**：LOCAL 偏差被记录但不阻塞，TACTICAL 偏差触发弧级重规划，STRATEGIC 偏差必须影响分析和用户确认。

### 6.10 决策：规划元数据与引用模型（v1.3 新增）

**背景**：长期运行中 plan 文件不断修订，章节卡引用的 plan 可能已过期。v1.2 没有 plan 版本化机制。

**决策**：PlanningArtifactMeta（自身标识）+ PlanRef（外部引用含 content_hash）+ ItemRef（引用嵌套项，item_id 为规范身份）。

**结果**：每个 plan 产物有独立 revision/hash，章节卡引用带版本的 PlanRef。PlanRef @STALE 时可被检测。

### 新增质量闸门

| 风险级别 | 场景 | 行为 |
| --- | --- | --- |
| CRITICAL | STRATEGIC 偏差无 ApprovalRef | BLOCKED |
| HIGH | TACTICAL 偏差未在剩余 Batch 中重规划 | WARNING → 要求重规划 |
| HIGH | 上游 plan 更新但章节卡引用旧 revision | 标记 STALE |
| MEDIUM | LOACL 偏差累计达阈值 | 触发 ARC_PROGRESS_CHECK |

### 新增工作流

```text
v1.3 规划生产链：
novel-brief（reader_contract）
→ STORY（story_engine + project_spine）
→ PLOT（volume_arcs + arc_catalog）
→ chapter-planner（ChapterBatch → 章节卡）
→ scripts/build_planning_pack.py（PlanningPack）
→ chapter-writer（planning_execution + deviation_report）
→ novel-reviewer（PLAN_ALIGNMENT 维度 + deviation_assessment）
→ novel-master（更新 plan_progress + 偏差路由）
```

检查点流程：
```text
ARC_PROGRESS_CHECK（每 N 章或 TACTICAL 偏差触发）
→ PLOT 评估 arc_health
→ 必要时 PLOT 更新 arc_catalog
→ chapter-planner 生成新 Batch
```

### V1.3 发布范围

引入分层滚动规划与漂移控制。限定为：PlanningArtifactMeta + PlanRef/ItemRef + ChapterBatch + PlanningPack + planning_execution + deviation_assessment + plan_progress + 偏差分级路由。

明确排除：正式质量状态机、创作模式简化、story_engine 自动评估、world rule_stress_tests。

---

### 章节重新编号

v1.2 的第 17 章（变更记录）重新编号为第 18 章。

### 1.1.0 → 1.2.0 → 1.3.0 变更连续记录

延续 v1.2.0 的变更记录。v1.3.0 新增：

| 变更 | 原因 | 影响 |
| --- | --- | --- |
| 新增不变量 21–27 | 分层规划 + 偏差控制 + 版本化 | 5 Skill 更新 + 11 Schema + PlanningPack 脚本 |
| 新增 ADR 6.8–6.10 | 分层滚动规划、偏差分级、引用模型 | 不改变 1+7 架构 |
| 新增规划生产链 + 检查点流程 | ChapterBatch → planning_execution → plan_progress 闭环 | routing-table 新增 CHECK_PLAN_PROGRESS 路由 |
