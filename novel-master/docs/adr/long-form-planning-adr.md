# ADR：长篇故事规划与漂移控制

> document_id: NM-ADR-PLANNING
> status: RC
> version: 1.3.0-rc1
> drafted_at: 2026-07-25

## 背景

v1.2 已经将单章生产过程工程化（reader_experience → target_execution → dimension_results），但长期连载的"规划层"仍然薄弱。

### 当前 v1.2 规划现状

| 问题 | 证据 |
| --- | --- |
| 无分层规划 | plot_plan 是平铺的事件时间线，不区分全书/分卷/弧线/批次 |
| 无故事发动机 | 无"核心循环+升级轴+刷新机制"定义，故事可持续性依赖模型每次临时判断 |
| 无章节批次 | 章节卡每次临时规划下一章，章节间无预先协调 |
| 无偏差机制 | 偏离要么全接受（ACCEDPT_CHAPTER）要么全拒绝（IMPACT_ANALYSIS），无中间状态 |
| 无规划版本 | plan 文件修改后，已生成章节卡引用旧版本，无法检测 stale |
| 无规划进度 | 不知道"弧线完成多少、还剩多少、超前还是落后" |

### v1.2 规划基线数据

对三题材（cultivation-progression / mystery-case / wasteland-lights）的 v1.2 规划基线评分：

| 维度 | 均分 |
| --- | --- |
| DP1 长期方向可追踪性 | 2.0/5 |
| DP2 故事发动机可持续性 | 1.7/5 |
| DP3 章节间协调性 | 2.0/5 |
| DP4 人物规划深度 | 2.0/5 |
| DP5 规划弹性 | 1.0/5 |
| DP6 计划传递一致性 | 2.0/5 |
| **总分** | **10.7/30** |

最低分 DP5（1.0/5）— v1.2 无偏差分级机制。

## 决策

### 1. 分层滚动规划（L0–L6）

不要求开书前一次性规划 150 万字。分层粒度：

```text
L0 读者契约（brief）         — 全书稳定
L1 故事发动机（STORY）        — 全书稳定
L2 全书主干（STORY）          — 不可变锚点 + 可调路径
L3 分卷大纲（PLOT）           — 当前卷详细，后续卷粗略
L4 剧情弧（PLOT）             — 当前弧详细
L5 章节批次（chapter-planner）— 未来 3~10 章详细
L6 单章卡（chapter-planner）  — 下一章完整可执行
```

### 2. 偏差分级

```text
LOCAL → 记录，不阻塞
TACTICAL → 弧级重规划（更新剩余 Batch）
STRATEGIC → 影响分析 + 用户确认（可能修改 Volume/Spine）
```

### 3. 规划版本化

PlanningArtifactMeta（自身标识）+ PlanRef（外部含 content_hash）+ ItemRef（嵌套项，item_id 规范身份）。

### 4. 不使用新 Skill

保持 1+7 架构。新增构件由已有 Skill 负责：
- STORY → StoryEngine + ProjectSpine
- PLOT → VolumeArc + ArcPlan
- chapter-planner → ChapterBatch
- novel-master → plan_progress

## 替代方案评估

### A. 新建 PlanningEngineer Skill

否决：增加 1+7 架构复杂度。当前 STORY/PLOT 已覆盖规划维度。

### B. 仅增加字段不增加层级

否决：无法区分"全书不变的锚点"和"当前 Arc 的具体事件"。

### C. 全量一次性规划

否决：不适用于网文动态创作。

### D. （采用）分层滚动规划 + 偏差分级

不新增 Skill，分层 SORY/PLOT/chapter-planner。

## 影响分析

| 子系统 | 变更 |
| --- | --- |
| STORY | 新增 story_engine + project_spine 产出 |
| PLOT | volume_arcs + arc_catalog 替代当前 plot_plan |
| chapter-planner | 新增 ChapterBatch 产出 + planning_alignment 字段 |
| chapter-writer | 新增 planning_execution + deviation_report |
| novel-reviewer | 新增 PLAN_ALIGNMENT 维度 + deviation_assessment |
| novel-master | 新增 plan_progress + 偏差路由 + PlanningPack 调用 |
| continuity-keeper | 无新增状态责任；EXTRACT_CONTEXT 可提供 PlanningPack（由 novel-master 协调） |
| novel-brief | 新增 reader contract 结构 |
| CHARACTER | 新增 concrete_competences + conflict_edges |
| Schema | 11 新增 + 12 修改 |
| 路由表 | 新增 CHECK_PLAN_PROGRESS |
| 测试 | 168 → 204（+36） |

## 验收条件

1. 原 168 条测试全部通过
2. 新增 36 条确定性测试全部通过
3. 三题材 A/B：v1.3 ≥ v1.2 在 DP1–DP6 全维度上（WIN+TIE ≥ 80%）
4. DP5（规划弹性）从 1.0 → ≥ 3.5
5. STANDARD/STRICT batch_slot 引用率 ≥ 95%
6. STRATEGIC recall 100%、precision ≥ 90%、LOCAL false-block ≤ 10%
