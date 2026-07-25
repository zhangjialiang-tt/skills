---
name: novel-style
description: "基于作品定位和故事基调，把项目 style_guide.md 的占位符转化为可执行的叙事风格约束。仅由 $novel-master 路由或用户显式调用 $novel-style，用于初始化或修订风格指南；普通网文请求统一交给 $novel-master。"
---

# novel-style

## 职责

把作品定位（project_brief）和故事基调（story_architecture）转化为可执行的叙事风格约束，填写项目 `style_guide.md`。产出供 chapter-writer 作为硬约束、novel-reviewer 作为风格维度证据。

## 何时触发

- 新书初始化阶段，story_architecture 已生成，需要确立风格约束。
- 作品定位或故事基调发生重大变化，风格指南需要同步修订。
- style_guide.md 仍存在未填写占位符，影响后续写作或评审。

## 何时不触发

- project_brief 或 story_architecture 尚未生成（应先路由上游 skill）。
- 任务仅涉及章节卡或正文写作。
- 任务仅涉及只读评审。
- 任务仅涉及状态管理。

## 激活模式

DEFAULT（唯一模式）。

## 必需输入

- `project_brief.md`
- `architecture/story_architecture.md`

## 允许读取

- `project_brief.md`、`architecture/story_architecture.md`（必需输入）。
- `characters/`、`world/`、`outline/`（只读参考，用于让风格约束贴合具体人物声音与世界质感）。
- `state/` 中的 Canon（只读）。

## 允许写入

- `style_guide.md`

## 操作步骤

1. 读取 project_brief 和 story_architecture，提炼作品定位、目标读者体验和故事基调。
2. 基于风格指南模板，逐章节把占位符替换为与定位一致的具体约束。
3. 参考已有人物档案与世界设定，使「角色声音」「题材特殊规则」等章节贴合具体内容。
4. 对 AI 腔规避项给出可执行清单（每条可被写作和评审直接判定）。
5. 分离已确认项、假设和待确认项。
6. 输出结构化 `style_guide`。

## 禁止事项

- 写正文、章节卡、大纲或人物档案。
- 修改 Canon 或写 `state/`。
- 固化某一题材的默认风格（占位符不得用通用默认值填充，必须基于本作品定位）。
- 把低置信度推断写成已确认风格。
- 模仿特定在世作者的可识别文风。

## 输出

```yaml
style_guide:
  narrative_pov / narrative_distance / sentence_rhythm
  description_density / dialogue_rules / character_voice
  exposition_strategy / chapter_word_count
  hook_principles / recall_strategy
  ai_voice_avoidance[] / genre_specific_rules[]
  assumptions / unresolved_decisions
```

## 完成标准

- 模板全部占位符已具象化，无遗留 `{{}}` 或 `<!-- TODO -->`。
- 每条约束可被 chapter-writer 当作硬约束执行、可被 novel-reviewer 当作证据判定。
- 风格与 project_brief 的目标读者体验、story_architecture 的基调一致。
- 已确认项、假设和待确认项分离。
- 没有把低置信度推断写成事实。

## 阻塞条件

- project_brief 或 story_architecture 缺失（`BLOCKED`）。
- 输入过于模糊，无法提炼任何有效风格约束（返回 `NEEDS_DECISION`）。

## 按需读取

- 执行前读取[公共规则](../references/common-rules.md)和[文件所有权](../references/file-ownership.md)。
- 填写风格指南时，读取[风格指南模板](../references/style-guide-template.md)作为结构依据。
- 涉及初始化确认、Canon 候选或授权时，读取[生命周期与授权](../references/lifecycle-and-approval.md)。
- 返回阻塞或待决策结果时，读取[错误码](../references/error-codes.md)。
- 需要核对输出结构时，读取[冻结契约](../docs/novel-master-contracts-v1.1.0-frozen.md) §12.7 和[冻结架构](../docs/novel-master-architecture-v1.1.0-frozen.md) §4.2、§8.1。
