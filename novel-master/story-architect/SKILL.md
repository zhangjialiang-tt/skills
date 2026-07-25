---
name: story-architect
description: "按单一互斥模式完成长篇网文的故事、人物、世界或大纲设计。仅由 $novel-master 路由或用户显式调用 $story-architect；一次调用只激活 STORY、CHARACTER、WORLD、PLOT 之一，普通网文请求统一交给 $novel-master。"
---

# story-architect

## 职责

按单一模式完成高层设计：故事结构（STORY）、人物（CHARACTER）、世界（WORLD）或大纲（PLOT）。

## 何时触发

- 需要设计或修改故事主线、主题、结构。
- 需要设计或修改人物档案、关系。
- 需要设计或修改世界规则、力量体系。
- 需要生成或修改整书/分卷大纲。

## 何时不触发

- 任务仅涉及章节卡或正文写作。
- 任务仅涉及只读评审。
- 任务仅涉及状态管理。

## 激活模式

四种互斥模式，一次只能激活一个：

| 模式 | 可写区域 | 必需输入 |
|------|----------|----------|
| `STORY` | `architecture/` | `project_brief.md` |
| `CHARACTER` | `characters/` | `project_brief.md` + `architecture/story_architecture.md` |
| `WORLD` | `world/` | `project_brief.md` + `architecture/story_architecture.md` |
| `PLOT` | `outline/` | 故事架构 + 相关人物 + 相关世界规则 |

未声明模式、声明多个模式或目标路径跨越多个所有权区域时，返回 `BLOCKED / INVALID_SKILL_MODE`。

## 必需输入

- `TaskEnvelope.task.skill_mode`: 必须声明且只能声明一个模式。
- 对应模式的必需输入文件（见上表）。

## 允许读取

- 项目内所有设计文件（只读参考）。
- `state/` 中的 Canon（只读）。

## 允许写入

- 仅当前激活模式对应的所有权区域（见上表）。

## 操作步骤

1. 校验 `skill_mode` 唯一且有效。
2. 读取对应模式的必需输入。
3. 按模式执行设计任务。
4. 输出对应结构（story_architecture / character_profile / world_design / plot_plan）。
5. 将跨模式内容作为 Proposal 输出，不写入非负责区域。

## 禁止事项

- 一次调用混合多个模式并跨所有权区域写入。
- 编写正式正文。
- 静默改变已确认的结局、人物命运或世界规则。
- 创造与剧情无关的大量人物或百科内容。
- 把设计可能性当成已经发生的事实。

## 输出

按模式输出对应 YAML 结构（详见契约手册 §12.2）。跨模式内容进入 `proposals`。

## 完成标准

- STORY：目标、阻力、代价和结果形成因果链；结构可继续拆解。
- CHARACTER：人物行动逻辑可解释，目标与主线相关，Canon 候选单列。
- WORLD：每项规则服务剧情；能力有来源、代价、限制和反制。
- PLOT：事件有因果，每个阶段改变状态，可继续拆成章节卡。

## 阻塞条件

- 模式未声明或声明多个（`BLOCKED / INVALID_SKILL_MODE`）。
- 必需输入文件缺失（`BLOCKED`）。
- 目标路径跨越多个所有权区域（`BLOCKED / INVALID_SKILL_MODE`）。

## 按需读取

- 执行前读取[公共规则](../references/common-rules.md)和[文件所有权](../references/file-ownership.md)。
- 设计变更影响已确认 Canon 或需要用户授权时，读取[生命周期与授权](../references/lifecycle-and-approval.md)。
- 模式无效、越权或发生冲突时，读取[错误码](../references/error-codes.md)。
- 需要核对模式输出结构时，读取[冻结契约](../docs/novel-master-contracts-v1.0.1-frozen.md) §12.2 和[冻结架构](../docs/novel-master-architecture-v1.0.1-frozen.md) §4.2、§6.5。
