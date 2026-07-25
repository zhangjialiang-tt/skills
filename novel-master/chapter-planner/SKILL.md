---
name: chapter-planner
description: "把大纲节点和当前状态转化为可写作的章节卡并输出到 chapters/plans/。仅由 $novel-master 路由或用户显式调用 $chapter-planner，用于规划、续写或重写前拆解章节；普通网文请求统一交给 $novel-master。"
---

# chapter-planner

## 职责

把大纲节点和当前状态转化为可执行章节卡，使 chapter-writer 无需猜测核心剧情方向。

## 何时触发

- 有大纲节点需要转化为具体章节计划。
- 续写或重写前需要重新规划章节。
- 连写多章时需要逐章规划。

## 何时不触发

- 大纲尚未存在（应先路由 story-architect / PLOT）。
- 任务仅涉及正文写作或编辑。
- 任务仅涉及只读评审。

## 激活模式

DEFAULT（唯一模式）。

## 必需输入

- `plot_segment`: 对应大纲片段文件。
- `context_pack`: 由 continuity-keeper 提取的上下文包。

## 允许读取

- `outline/`（大纲文件）。
- `state/`（只读，获取当前状态）。
- `characters/`、`world/`、`architecture/`（只读参考）。
- 前一章摘要和结尾。

## 允许写入

- `chapters/plans/chapter_*.md`

## 操作步骤

1. 读取大纲片段和上下文包。
2. 确定章节功能、视角人物、时间地点。
3. 定义本章的读者体验目标（`reader_experience`）：确定 chapter_role（primary + secondary）、本章向读者兑现的 promise、payoff 模式和 emotional_arc。
4. 定义开始状态和结束状态（必须不同）。
5. 拆分场景：每个场景有目标、冲突、行动、信息揭示、状态变化和转场。
6. 为每个 scene 选择 style_modulation_ref（引用 style_guide.scene_modulations 中的 modulation_id，无特殊调制时引用 DEFAULT；STANDARD/STRICT 下必填）。
7. 标注必需元素、禁止揭示、活跃伏笔。
8. 识别连续性风险。
9. 输出章节卡（含 reader_experience、style_modulation_ref 和 contract_meta）。

## 禁止事项

- 修改总纲（`outline/`）。
- 增加未授权规则。
- 改变人物长期目标。
- 写大量正文。
- 机械制造断章。

## 输出

```yaml
chapter_plan:
  # v1.1 原有字段
  chapter_id / chapter_function / viewpoint_character
  time_and_location / opening_state / ending_state
  scenes[]:
    - scene_id / goal / conflict / action
      information_revealed[] / state_change / transition
      style_modulation_ref: string | null   # v1.2 新增
  required_elements[] / prohibited_reveals[]
  active_foreshadowing[] / chapter_climax / continuity_risks[]

  # v1.2 新增：章节质量目标
  reader_experience:
    chapter_role: { primary: enum, secondary: [] | null, description: string }
    promise: string
    payoff: { mode: enum, description: string, deferred_reason: string | null, justification: string | null, expected_payoff_window: object | null }
    emotional_arc: { target: string, turning_point: string }
    information_gain: [{ target_id: string, what: string, significance: string }] | null
    tension_curve: { type: enum, description: string }
    continuation_drive: { type: enum, description: string, justification: string }

  # v1.2 新增
  contract_meta:
    schema_id: "novel-master/chapter-plan"
    schema_version: "1.2.0"
```

条件必填规则：
- FAST：reader_experience 可选，缺失时产生提示不阻塞。
- STANDARD/STRICT：必须包含 reader_experience；chapter_role.primary/promise/payoff.mode/emotional_arc.target/tension_curve.type/continuation_drive.type 至少必填。
- payoff.mode=DEFERRED → deferred_reason 必填；NONE_JUSTIFIED → justification 必填。
- continuation_drive.type=NONE_JUSTIFIED → justification 必填。

## 完成标准

- 章节功能明确。
- 开始和结束状态不同。
- STANDARD/STRICT 下 reader_experience 存在且必填项（promise/payoff/emotional_arc.target/tension_curve/continuation_drive）不空。
- payoff.mode=DEFERRED 时具备 deferred_reason，NONE_JUSTIFIED 时具备 justification。
- continuation_drive.type=NONE_JUSTIFIED 时具备 justification。
- 每个 scene 的 style_modulation_ref 已设置（STANDARD/STRICT 下每个 scene 必填，FAST 下可选）。
- 每个场景都有目标、阻力和结果。
- 信息揭示符合人物知情范围。
- chapter-writer 无需猜测核心剧情方向。
- contract_meta 已填写正确的 schema_id 和 schema_version。

## 阻塞条件

- 大纲片段缺失或不可执行（`BLOCKED`）。
- 上下文包缺失（`BLOCKED`）。
- 章节卡与 Canon 存在未解决冲突（`NEEDS_DECISION`）。

## 按需读取

- 执行前读取[公共规则](../references/common-rules.md)和[文件所有权](../references/file-ownership.md)。
- 获取或校验 `context_pack` 时，读取[上下文提取规则](../references/context-retrieval-rules.md)。
- 章节卡与 Canon 冲突或输入不足时，读取[错误码](../references/error-codes.md)。
- 需要核对章节卡结构时，读取[冻结契约](../docs/novel-master-contracts-v1.1.0-frozen.md) §12.3 和[冻结架构](../docs/novel-master-architecture-v1.1.0-frozen.md) §4.2、§8.2。
