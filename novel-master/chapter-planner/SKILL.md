---
name: chapter-planner
description: 把大纲节点和当前状态转化为可执行章节卡，输出到 chapters/plans/。
version: 1.0.0
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
3. 定义开始状态和结束状态（必须不同）。
4. 拆分场景：每个场景有目标、冲突、行动、信息揭示、状态变化和转场。
5. 标注必需元素、禁止揭示、活跃伏笔。
6. 识别连续性风险。
7. 输出章节卡。

## 禁止事项

- 修改总纲（`outline/`）。
- 增加未授权规则。
- 改变人物长期目标。
- 写大量正文。
- 机械制造断章。

## 输出

```yaml
chapter_plan:
  chapter_id / chapter_function / viewpoint_character
  time_and_location / opening_state / ending_state
  scenes[] / required_elements / prohibited_reveals
  active_foreshadowing / chapter_climax / continuity_risks
```

## 完成标准

- 章节功能明确。
- 开始和结束状态不同。
- 每个场景都有目标、阻力和结果。
- 信息揭示符合人物知情范围。
- chapter-writer 无需猜测核心剧情方向。

## 阻塞条件

- 大纲片段缺失或不可执行（`BLOCKED`）。
- 上下文包缺失（`BLOCKED`）。
- 章节卡与 Canon 存在未解决冲突（`NEEDS_DECISION`）。

## 相关 references

- `docs/novel-master-contracts-v1.0.1-frozen.md` §12.3
- `docs/novel-master-architecture-v1.0.1-frozen.md` §4.2, §8.2
