# common-rules.md

> 用途：所有子 Skill 必须遵守的最小规则集。
> 引用方式：每个子 Skill 的 SKILL.md 中 `include: references/common-rules.md`。

## 1. 信息状态定义与转换

四种状态：

| 状态 | 含义 |
|------|------|
| CANON | 已确认事实，有来源和授权 |
| PROPOSAL | AI 或用户提出的候选，未正式确认 |
| DEPRECATED | 曾为 Canon，已被明确废弃 |
| UNKNOWN | 无法定位来源，不可当作事实使用 |

允许的转换：

```
UNKNOWN → PROPOSAL
PROPOSAL → CANON          （需授权 + continuity-keeper 提交）
CANON → DEPRECATED        （需影响分析 + 用户确认）
DEPRECATED → PROPOSAL     （仅作为恢复旧方案的候选）
```

禁止的转换：

```
UNKNOWN → CANON           （无证据直接确认）
PROPOSAL → CANON          （子 Skill 自行确认）
DEPRECATED → CANON        （静默恢复旧设定）
CANON → 删除              （抹除历史）
```

## 2. 不得静默扩大范围

- 只补齐当前任务的必要上游，不自动执行整个初始化链。
- 范围不明时采用最低安全权限，不得用猜测扩大权限。
- 执行中实际语义影响高于预估时，停止扩大修改，返回 NEEDS_DECISION。

## 3. 不得伪造缺失上下文

- 无法定位来源的信息只能标记为 UNKNOWN 或 PROPOSAL。
- 不得无证据推断人物知情或事件已发生。
- 不得把低置信度推断写成事实。
- 恢复模式中推断只能作为 inferred_candidates，不得写成已确认事实。

## 4. 重大决策归用户

- 高风险操作必须先输出影响报告，等待显式确认。
- Canon 修改、Retcon、大范围结构变化必须用户确认。
- 子 Skill 不得用 COMPLETED 掩盖 criteria_unmet。
- 确认策略：LOW→直接执行；MEDIUM→明确范围后执行；HIGH→等待确认。

## 5. 输出新增事实候选

- 所有新增事实、状态变化和计划偏离必须在 chapter_report 或 state_change_proposals 中报告。
- 新增事实进入 state_change_proposals，类型为 canon_candidate。
- 未接受章节的变化只能进入 proposals，不得进入 committed_updates。

## 6. 只写所属区域

- 每个 Skill 只能写入自己的所有权区域（见 file-ownership.md）。
- 同一调用不得同时写入两个不同主要负责人区域。
- 跨区域任务必须由 novel-master 拆分调用。
- 越权内容降级为 Proposal，不得进入交付物或正式状态。

## 7. 显式只读优先

- 用户表达只读意图时，source_mutation_allowed 和 state_mutation_allowed 必须为 false。
- READ_ONLY 操作不得修改源文件和状态。
- 独立报告落盘需 artifact_persistence_allowed: true。
- "不要修改任何东西"时三个细粒度写权限全部为 false，目标路径为空。

## 8. 所有正式产物带来源和 revision

- 每个 Canon 或状态更新必须包含：id、statement、source（type + ref）、effective_from、status。
- 交付物必须携带 deliverable_id、revision、content_hash。
- 文件引用使用 FileRef（path + revision + hash）。
- 文件内容变化时必须更新 revision 和 hash。
- 评审报告必须标明被评审内容的 deliverable_id、revision 和 content_hash。
