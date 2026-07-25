---
name: novel-brief
description: "将模糊创意转化为明确、可确认的作品定义并输出 project_brief.md。仅由 $novel-master 路由或用户显式调用 $novel-brief，用于创建项目、补齐简报或修改作品定位；普通网文请求统一交给 $novel-master。"
---

# novel-brief

## 职责

将模糊创意转化为明确作品定义：类型、读者承诺、核心钩子、主要冲突、篇幅节奏和创作约束。

## 何时触发

- 创建新项目。
- 修改作品定位、目标读者或创作承诺。
- 项目简报不明确或缺失。

## 何时不触发

- 项目简报已明确且用户未要求修改。
- 任务仅涉及故事结构、人物、世界或大纲设计。

## 激活模式

DEFAULT（唯一模式）。

## 必需输入

- `user_request`: 用户的创意描述或修改需求。

## 允许读取

- `project_brief.md`（如已存在）。
- 用户提供的参考偏好和排除项。

## 允许写入

- `project_brief.md`

## 操作步骤

1. 解析用户创意中的显式信息和隐含假设。
2. 确定类型、子类型、目标读者和平台。
3. 提炼核心钩子、主角承诺和主要冲突。
4. 明确篇幅节奏和创作约束。
5. 分离已确认项、假设和待确认项。
6. 输出结构化 `project_brief`。

## 禁止事项

- 写完整大纲或详细世界百科。
- 写正文。
- 擅自确定结局。
- 承诺市场结果。
- 把低置信度推断写成事实。

## 输出

```yaml
project_brief:
  genre / subgenre / target_reader / target_platform
  core_hook / protagonist_promise / primary_conflict
  intended_reader_experience / length_and_pacing
  creative_constraints / exclusions
  assumptions / unresolved_decisions
```

## 完成标准

- 一句话可以说明作品是什么。
- 目标读者和阅读承诺明确。
- 已确认项、假设和待确认项分离。
- 没有把低置信度推断写成事实。

## 阻塞条件

- 用户输入过于模糊，无法提取任何有效信息（返回 `NEEDS_DECISION`）。

## 按需读取

- 执行前读取[公共规则](../references/common-rules.md)和[文件所有权](../references/file-ownership.md)。
- 风格指南由 `novel-style` 基于 project_brief 产出，novel-brief 不负责填写 style_guide.md；需要理解风格定位时，读取[风格指南模板](../references/style-guide-template.md)作为下游参考。
- 涉及初始化确认、Canon 候选或授权时，读取[生命周期与授权](../references/lifecycle-and-approval.md)。
- 返回阻塞或待决策结果时，读取[错误码](../references/error-codes.md)。
- 需要核对输出结构时，读取[冻结契约](../docs/novel-master-contracts-v1.1.0-frozen.md) §12.1 和[冻结架构](../docs/novel-master-architecture-v1.1.0-frozen.md) §4.2。
