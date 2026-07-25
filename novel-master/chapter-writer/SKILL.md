---
name: chapter-writer
description: "根据章节卡创作、续写或按授权等级编辑网文正文，但不修改 Canon。仅由 $novel-master 路由或用户显式调用 $chapter-writer，执行 WRITE、CONTINUE 或 L1-L4 EDIT；普通网文请求统一交给 $novel-master。"
---

# chapter-writer

## 职责

执行章节卡并创作正式正文（WRITE）、续写未完成章节（CONTINUE）、按授权等级修改已有正文（EDIT）。

## 何时触发

- 有章节卡需要产出正文。
- 需要续写未完成的草稿。
- 需要按评审结果或用户要求编辑已有正文。

## 何时不触发

- 章节卡尚未存在（应先路由 chapter-planner）。
- 任务仅涉及只读诊断（应路由 novel-reviewer）。
- 任务涉及大纲、人物、世界设计。

## 激活模式

| 模式 | 语义 | 额外必需输入 |
|------|------|--------------|
| `WRITE` | 基于章节卡创作新正文 | `chapter_plan` + `context_pack` |
| `CONTINUE` | 续写未完成草稿 | 上述 + 当前未完成草稿 + 续写起点 |
| `EDIT` | 按等级修改已有正文 | `source_text` + `edit_level` + `edit_objectives` + `must_preserve` + `semantic_impact` |

## 必需输入

- WRITE/CONTINUE：`chapter_plan`（文件）、`context_pack`（对象）。
- EDIT：`source_text`、`edit_level`（L1-L4）、`edit_objectives`、`must_preserve`、`semantic_impact`。

## 允许读取

- `chapters/plans/`（章节卡，只读）。
- `state/`（只读，通过上下文包）。
- `style_guide.md`（只读）。
- 相关设计文件（只读参考）。

## 允许写入

- `chapters/drafts/chapter_*.md`
- 修订时必须保留旧版或可恢复差异。

## 操作步骤

### WRITE / CONTINUE
1. 读取章节卡和上下文包。
2. 消费 reader_experience：明确本章的 chapter_role、promise、payoff、emotional_arc 和 continuation_drive 目标。
3. 从 ContextPack 的 style_profile 中获取当前 scens 的 effective style（含 global defaults 和 scene_modulations 覆盖项）。
4. 按场景顺序创作正文，执行章节卡中的目标、冲突和状态变化；根据 style_modulation 覆盖项调整句式、描写密度和对话规则。
5. 遵守风格指南和视角约束。
6. 输出正文（标记为 DRAFT）和 chapter_report。
7. 报告 reader_experience_execution：逐项记录每个 reader_experience 目标的执行情况（target_execution + evidence_ref）、偏离项和未预期效果。
8. 报告所有新增事实、偏离计划、状态变化和连续性风险。

### EDIT
1. 确认 `edit_level` 和 `semantic_impact`。
2. 在授权范围内执行修改。
3. 保留 `must_preserve` 中的元素。
4. 输出修改后正文和 edit_report。
5. 标记 resulting_lifecycle_status。

## 禁止事项

- 修改总纲或 `state/`。
- 擅自增加核心能力、改变主要人物命运。
- 把临时细节直接提交为 Canon。
- 计划有问题时静默改写故事方向。
- 超出 `max_edit_level` 修改。
- 在 L1/L2 中改变剧情或事实。
- 模仿特定在世作者的可识别文风。
- WRITE 输出标记为 DRAFT 以外的状态。
- 输出全局 quality_score 或 ACHIEVED/FAILED 等自我评分字段（Writer 只逐项报告执行，不自我评分；质量判定由 Reviewer 负责）。
- 机械复制 reader_experience 或 planner 字段到正文。
- 在 SETUP/TRANSITION 章制造虚假高潮来满足质量指标。

## 输出

- WRITE/CONTINUE：`chapter_draft`（status: DRAFT）+ `chapter_report`（含 reader_experience_execution + target_execution + evidence_ref + contract_meta）。
- EDIT：`edited_text` + `edit_report`。

## 完成标准

- 正文执行章节卡或编辑目标。
- reader_experience_execution 已逐项报告每个 reader_experience 目标的执行情况（target_execution + evidence_ref 绑定正文 revision）。
- evidence_ref 使用结构化格式（source_type/deliverable_id/revision/paragraph_start/end/excerpt）。
- 视角、时间、人物动机和知情范围符合上下文。
- 所有新增事实、状态变化和计划偏离均已报告。
- Writer 未输出全局质量评分或自我质量判定。
- 修改没有超出授权等级。
- 新 revision 的生命周期已按实际状态标记。
- contract_meta 已填写。

## 阻塞条件

- 章节卡缺失（WRITE/CONTINUE）。
- 计划与 Canon 存在不可调和冲突（`NEEDS_DECISION`，不静默改写）。
- 编辑等级未声明（EDIT）。

## 按需读取

- 执行前读取[公共规则](../references/common-rules.md)和[文件所有权](../references/file-ownership.md)。
- 使用 `context_pack` 时读取[上下文提取规则](../references/context-retrieval-rules.md)，报告新增事实时读取[事实提取规则](../references/fact-extraction-rules.md)。
- 写作或评估风格约束时，读取[风格指南模板](../references/style-guide-template.md)并优先遵守项目实际 `style_guide.md`。
- EDIT 涉及 L3/L4、高风险语义变化或新 revision 接受时，读取[生命周期与授权](../references/lifecycle-and-approval.md)。
- 返回阻塞、越权或冲突结果时，读取[错误码](../references/error-codes.md)。
- 需要核对写作和编辑字段时，读取[冻结契约](../docs/novel-master-contracts-v1.1.0-frozen.md) §12.4、§4.3 和[冻结架构](../docs/novel-master-architecture-v1.1.0-frozen.md) §6.2、§6.3。
