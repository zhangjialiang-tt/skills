---
name: novel-master
description: "编排长篇网文项目的初始化、设定与人物/情节设计、章节规划与正文创作/续写/修订、文本评审、连续性维护、状态提交和恢复；负责意图识别、最小子 Skill 路由、权限风险与接受闸门，不直接替代子 Skill 生成内容。用户要求创建或持续维护网文项目、跨阶段协调或治理事实状态时使用；普通文本润色、第三方作品分析、阅读推荐、诗歌/一次性短篇灵感及非小说任务不使用。"
---

# novel-master

## 职责

编排与治理入口：识别用户意图、定位项目、判定权限与风险、选择最小子 Skill 路由、执行 Approval Gate、汇总 MasterResult。

## 何时触发

- 用户发出任何创作相关请求。
- 需要跨子 Skill 协调的多步任务。
- 需要权限判定、风险推导或用户确认的操作。

## 何时不触发

- 纯闲聊或与小说创作无关的请求。
- 已由子 Skill 独立完成且无需编排的单一操作（V1 中不存在此情况，所有请求经编排器）。

## 激活模式

DEFAULT（唯一模式）。

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
7. 章节写作后执行接受闸门。
8. 只有 ACCEPTED/PUBLISHED 内容产生事实变化时插入状态提交。
9. 校验子 Skill 返回的 `SkillResult`，处理越权。
10. 汇总 `MasterResult` 并回答用户。

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
- 需要核对字段级契约或设计依据时，读取[冻结契约](docs/novel-master-contracts-v1.0.1-frozen.md) §2、§5、§10、§11、§14 和[冻结架构](docs/novel-master-architecture-v1.0.1-frozen.md) §4、§5、§7、§8。

## 执行与质量资源

- 契约校验、路径边界、revision、锁和提交逻辑复用 `scripts/`，不得在对话中重写确定性规则。
- 路由或输出合同变更后运行 `evals/` 回归，并以 `schemas/`、`examples/` 和 `templates/` 作为可复现输入。
- 交付前自检：路由是否最小、事实与 Proposal 是否分离、写入是否属于 owned zone、授权与 rollback boundary 是否可追溯。
