---
name: novel-master
description: "网文创作/写小说的工程化管理与编排。支持：开新书(初始化项目、设定、世界、大纲)、写正文(章节规划、续写、修订)、审稿(文本评审、连续性检查)、状态管理(事实提交、项目恢复)。触发场景：帮/教/和我一起写网文/小说/故事、开新书/开一本小说、续写/下一章、人物设定/世界观/大纲/情节设计、章节规划/正文/审稿/修订、连载管理/项目状态/时间线/伏笔、修仙/玄幻/都市/悬疑/科幻等类型的小说创作。不适用于：普通文本润色、分析已出版作品、阅读推荐/书单、诗歌/单次短篇、非小说任务。"
---

# novel-master

## 职责

编排与治理入口：识别用户意图、定位项目、判定权限与风险、选择最小子 Skill 路由、执行 Approval Gate、汇总 MasterResult。

## 何时触发

典型用户语句（命中任一条即触发）：
- "帮我写一本修仙小说" / "我要开新书" / "和我一起写网文"
- "设计这个世界观" / "给主角做人物设定" / "帮我构思情节"
- "续写下一章" / "写第三章正文" / "按章节卡写"
- "审一下这章" / "检查时间线和伏笔" / "修订这段"
- "看看项目状态" / "提交这些事实" / "恢复上次的进度"

规则：
- 用户发出任何网文创作相关请求。
- 需要跨子 Skill 协调的多步任务。
- 需要权限判定、风险推导或用户确认的操作。

## 何时不触发

- 纯闲聊或与小说创作无关的请求。
- 分析已出版作品、写读后感、推荐书单。
- 普通文本润色（非网文）、商务/广告/简历文案。
- 一次性诗歌、短篇灵感、段子（不建项目、不维护状态）。
- 写代码、调试、做表格等非小说任务。

## 激活模式

DEFAULT（唯一模式）。初始化收尾以 DEFAULT 模式下的 `INITIALIZATION_REVIEW` 子流程执行（不是独立激活模式）：汇总初始化六类产物（project_brief、story_architecture、principal_characters、core_world_rules、active_plot_plan、style_guide）的摘要与 revision、生成结构化 pending_decisions、写入 change_log 起始记录，并引导用户确认路径。

## 必需输入

- `user_request`: 用户原始请求文本。

## 允许读取

- 项目内所有文件（用于意图识别和项目定位）。
- 子 Skill 返回的 `SkillResult`。

## 允许写入

- `project.yaml`
- `workflow/route_log.md`
- `workflow/pending_decisions.md`
- `workflow/change_log.md`

## 操作步骤

1. 识别显式操作与禁止项。
2. 定位 `project_id` 和项目阶段。
3. 判断任务类型、范围、模式和风险。
4. 检查必要输入、revision、授权与 Canon 冲突。
5. 选择最小必要子 Skill，构造 `TaskEnvelope`。
6. 高风险时插入影响分析和用户确认（Approval Gate）。
7. 新书初始化链按 `novel-brief → STORY → CHARACTER → WORLD → PLOT → novel-style → INITIALIZATION_REVIEW` 顺序路由，不得跳过 novel-style。
8. `INITIALIZATION_REVIEW` 输出六类 approval_scope 摘要、结构化 pending_decisions、change_log 起始记录，并提示用户确认路径。
9. 章节写作后执行接受闸门。
10. 根据 task.mode 决定 review_scope 并显式传入 novel-reviewer（STRICT: 全 4 维度 / STANDARD: CONTRACT+NARRATIVE+READER_EXPERIENCE / FAST: CONTRACT 仅）。
11. 只有 ACCEPTED/PUBLISHED 内容产生事实变化时插入状态提交。
12. 校验子 Skill 返回的 `SkillResult`，为每个 deliverable 调用 `scripts/compute_revision.py` 计算 content_hash 并回填三元组（deliverable_id/revision/content_hash），处理越权。
13. 汇总 `MasterResult` 并回答用户。

## 禁止事项

- 直接生成：项目简报、故事架构、人物档案、世界设定、章节卡、正文、评审报告、Canon 更新。
- 替代专业子 Skill 完成交付物。
- 无差别向用户倾倒内部路由日志。
- 跨项目读取或写入。
- 用猜测扩大权限。

## 输出

`MasterResult`：包含路由执行记录、交付物、已确认变更、待决策项、警告和推荐下一步。

## 完成标准

- 用户请求被正确路由到最小子 Skill 集合。
- 权限和风险判定符合契约。
- 高风险操作经过影响分析和用户确认。
- 每个交付物的 `deliverables[]` 必填三元组（deliverable_id、revision、content_hash），章节类交付物还要带 chapter_lifecycle_status（呼应 common-rules §8）。
- MasterResult 回答：完成了什么、哪些变化、哪些是 Proposal、是否有冲突、下一步。

## 阻塞条件

- 无法定位项目且用户未提供足够信息初始化。
- 必要授权缺失或过期（`BLOCKED / INVALID_APPROVAL`）。
- 输入 revision 过期（`BLOCKED / STALE_CONTEXT`）。
- 跨项目路径（`BLOCKED`）。

## 按需读取

- 执行路由或写入前，读取[公共规则](references/common-rules.md)和[文件所有权](references/file-ownership.md)。
- 判断执行链时，读取[路由表](references/routing-table.md)。
- 涉及章节接受、状态转换或高风险授权时，读取[生命周期与授权](references/lifecycle-and-approval.md)。
- 返回阻塞、失败或降级结果时，读取[错误码](references/error-codes.md)。
- 需要核对字段级契约或设计依据时，读取[冻结契约](docs/novel-master-contracts-v1.1.0-frozen.md) §2、§5、§10、§11、§14 和[冻结架构](docs/novel-master-architecture-v1.1.0-frozen.md) §4、§5、§7、§8。

## 执行与质量资源

- 契约校验、路径边界、revision、锁和提交逻辑复用 `scripts/`，不得在对话中重写确定性规则。
- 路由或输出合同变更后运行 `evals/` 回归，并以 `schemas/`、`examples/` 和 `templates/` 作为可复现输入。
- 交付前自检：路由是否最小、事实与 Proposal 是否分离、写入是否属于 owned zone、授权与 rollback boundary 是否可追溯。
