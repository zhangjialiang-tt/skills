---
name: continuity-keeper
description: "管理网文事实、时间线和连续性，是 state/ 唯一正式写入者。仅由 $novel-master 路由或用户显式调用 $continuity-keeper，用于上下文、矛盾、状态提交、影响分析或恢复；普通网文请求统一交给 $novel-master。"
---

# continuity-keeper

## 职责

管理项目事实、时间线和连续性。是 `state/` 唯一正式写入者。

## 何时触发

- 需要提取上下文包（写作/规划前）。
- 需要检查前后矛盾。
- 章节被接受后需要提交增量状态。
- 需要提交已授权的 Canon 变化。
- 高风险改动前需要影响分析。
- 需要生成摘要。
- 断更后需要恢复项目。
- 需要重建派生状态索引。

## 何时不触发

- 任务仅涉及创作设计（故事、人物、世界、大纲）。
- 任务仅涉及正文写作或编辑。
- 任务仅涉及只读评审（除非评审需要上下文包）。

## 激活模式

| 模式 | 行为 | 写状态 |
|------|------|--------|
| `EXTRACT_CONTEXT` | 提取最小上下文包 | 否 |
| `CHECK_CONTRADICTIONS` | 检查证据冲突 | 仅登记冲突 |
| `COMMIT_CHAPTER_STATE` | 提交正式章节产生的增量状态 | 是 |
| `COMMIT_CANON` | 提交已授权 Canon 变化 | 是 |
| `IMPACT_ANALYSIS` | 分析拟议变化影响 | 否 |
| `GENERATE_SUMMARY` | 生成章节/卷/项目摘要 | 仅写摘要目标文件 |
| `RESTORE_PROJECT / EXTRACT_EVIDENCE` | 从现有文件提取证据，生成 RecoveryReport | 否 |
| `RESTORE_PROJECT / REBUILD_STATE` | 基于已确认 RecoveryReport 重建最小状态 | 是，需单独授权 |
| `REBUILD_DERIVED_STATE` | 从已确认来源重建派生索引 | 是，仅派生文件 |

## 必需输入

- `operation_mode`: 当前模式。
- `source_material`: 来源材料列表。
- `current_state_files`: 当前状态文件。
- `base_revision`: 基础版本对象。

## 允许读取

- `state/` 全部文件。
- `chapters/drafts/`（只读，用于状态提取）。
- `architecture/`、`characters/`、`world/`、`outline/`（只读参考）。
- `project_brief.md`、`style_guide.md`（只读）。

## 允许写入

- `state/` 中与当前模式对应的文件。
- `state/archives/`（归档）。
- 不写 `chapters/`、`architecture/`、`characters/`、`world/`、`outline/`。

## 操作步骤

### EXTRACT_CONTEXT
1. 确定任务所需的最小相关信息。
2. 从状态文件提取相关 Canon、人物状态、伏笔、开放循环。
3. 按预算裁剪（硬约束 > Canon > 当前状态 > 知识 > 伏笔 > 风格）。
4. 输出 ContextPack，标记 unknowns 和 omitted_context_refs。

### COMMIT_CHAPTER_STATE
1. 校验来源章节状态为 ACCEPTED 或 PUBLISHED。
2. 校验 deliverable_id、revision 和 hash 与接受记录一致。
3. 校验 base_revision 与当前状态文件一致。
4. 准备 ChangeSet（PREPARE → VALIDATE → APPLY → VERIFY → COMMIT）。
5. 增量更新状态文件，写入 change_log。

### COMMIT_CANON
1. 校验 ApprovalRef 覆盖目标范围和当前 revision。
2. 执行 ChangeSet 事务。
3. 更新 Canon 文件。

### RESTORE_PROJECT / EXTRACT_EVIDENCE
1. 只读扫描现有文件。
2. 提取证据，标记置信度。
3. 分离证据、推断候选、冲突和未知项。
4. 输出 RecoveryReport，不写 state/。

## 禁止事项

- 创造剧情或承担审美评审。
- 为解决矛盾擅自改正文。
- 把 Proposal 自动提交为 Canon。
- 删除冲突记录来掩盖问题。
- 无证据推断人物知情或事件已发生。
- 在恢复模式中把推断写成已确认事实。
- 用 GENERATE_SUMMARY 隐式重建或覆盖派生状态。
- 在 revision 不一致时继续提交。
- COMMIT_CHAPTER_STATE 接受非 ACCEPTED/PUBLISHED 来源。

## 输出

```yaml
continuity_result:
  context_pack / contradictions / committed_updates
  pending_updates / deprecated_items / impact_analysis
  recovery_report / change_set_result
```

## 完成标准

- 每项更新有来源。
- Canon、Proposal、Deprecated 和 Unknown 分离。
- 冲突未被静默覆盖。
- 上下文包最小、相关、可回查。
- 状态提交是增量且可审计。
- 恢复报告将证据、推断、冲突和未知项分离。
- ChangeSet 已提交或完整回滚，不存在部分状态。

## 阻塞条件

- base_revision 与当前状态不一致（`BLOCKED / STALE_CONTEXT`）。
- COMMIT_CHAPTER_STATE 来源非 ACCEPTED/PUBLISHED（`BLOCKED / CHAPTER_NOT_ACCEPTED`）。
- COMMIT_CANON 缺少有效 ApprovalRef（`BLOCKED / INVALID_APPROVAL`）。
- ChangeSet 任一步骤失败（`FAILED / ROLLBACK_FAILED`）。

## 按需读取

- 执行前读取[公共规则](../references/common-rules.md)和[文件所有权](../references/file-ownership.md)。
- EXTRACT_CONTEXT 或依赖上下文包的模式读取[上下文提取规则](../references/context-retrieval-rules.md)。
- 从正文或报告生成状态候选时，读取[事实提取规则](../references/fact-extraction-rules.md)。
- COMMIT_CHAPTER_STATE、COMMIT_CANON、恢复写入或影响分析时，读取[生命周期与授权](../references/lifecycle-and-approval.md)。
- 返回冲突、陈旧上下文、无效授权或事务失败时，读取[错误码](../references/error-codes.md)。
- 需要核对状态、ChangeSet 或 ContextPack 字段时，读取[冻结契约](../docs/novel-master-contracts-v1.0.1-frozen.md) §12.6、§8、§9 和[冻结架构](../docs/novel-master-architecture-v1.0.1-frozen.md) §5、§6.1、§6.4、§9。
