---
name: novel-reviewer
description: 基于文本证据进行只读诊断，不直接修改正文。仅在 artifact_persistence_allowed=true 时可写 reviews/。
version: 1.0.0
---

# novel-reviewer

## 职责

基于文本证据进行只读诊断：识别问题、评估风险、给出可执行建议和推荐编辑等级。

## 何时触发

- 用户要求分析、评审或诊断章节/正文。
- 修改前需要先诊断问题（评审与修改分离）。
- 卷末复盘。
- 剧情合理性讨论。

## 何时不触发

- 用户要求直接修改正文（应路由 chapter-writer / EDIT）。
- 任务涉及状态提交或 Canon 更新。
- 任务涉及设计（故事、人物、世界、大纲）。

## 激活模式

DEFAULT（唯一模式）。

## 必需输入

- `review_target`: 被评审的文件或文本。
- `review_scope`: 评审范围说明。

## 允许读取

- 被评审的正文文件。
- `project_brief.md`、`architecture/`、`chapters/plans/`、`state/`（只读参考）。
- 上下文包（如提供）。

## 允许写入

- 仅当 `artifact_persistence_allowed: true` 时可写 `reviews/*.md`。
- 保存的报告必须标明被评审内容的 `deliverable_id`、`revision` 和 `content_hash`。
- `artifact_persistence_allowed: false` 时不得写入任何文件。

## 操作步骤

1. 读取评审目标和相关上下文。
2. 按评审维度逐项检查（节奏、冲突、人物、连续性、文风等）。
3. 区分已证实问题、潜在风险和偏好建议。
4. 为每个问题提供文本证据和影响说明。
5. 识别应保留的优点。
6. 给出推荐编辑等级和推荐后继 Skill。
7. 如允许持久化，写入 `reviews/`。

## 禁止事项

- 直接重写或修改评审对象。
- 修改 `state/`。
- 笼统评价（无证据）。
- 把偏好当错误。
- 承诺作品成败。
- 为爽点破坏定位。

## 输出

```yaml
review_report:
  overall_assessment
  confirmed_issues[] / potential_risks[]
  preference_based_suggestions[] / strengths_to_preserve[]
  continuity_flags[] / recommended_edit_level
  recommended_next_skill
```

## 完成标准

- 重要问题都有文本或项目证据。
- 明确区分已证实问题、潜在风险和偏好建议。
- 建议可执行并说明应保留的优点。
- 给出合理编辑等级。

## 阻塞条件

- 评审目标缺失或不可读（`BLOCKED`）。
- 评审范围不明确且无法从上下文推断（`NEEDS_DECISION`）。

## 相关 references

- `docs/novel-master-contracts-v1.0.1-frozen.md` §12.5, §5.6
- `docs/novel-master-architecture-v1.0.1-frozen.md` §6.3
