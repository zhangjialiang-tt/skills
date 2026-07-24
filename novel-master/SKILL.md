---
name: novel-master
description: 长篇网文创作编排器，负责意图识别、路由、权限判定和结果汇总，不直接生成创作内容。
version: 1.0.0
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

## 相关 references

- `docs/novel-master-contracts-v1.0.1-frozen.md` §2, §5, §10, §11, §14
- `docs/novel-master-architecture-v1.0.1-frozen.md` §4, §5, §7, §8
