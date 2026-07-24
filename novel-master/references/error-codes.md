# error-codes.md

> 用途：统一错误码定义，所有子 Skill 和 novel-master 使用相同错误码。
> 引用方式：所有 Skill 中 `include: references/error-codes.md`。
> 来源：冻结契约 §13（异常与降级策略）。

## 错误码总表

| 错误码 | 对应状态 | 含义 | 可重试 | 推荐恢复动作 |
|--------|---------|------|--------|-------------|
| INVALID_SKILL_MODE | BLOCKED | 未声明模式、声明多个模式、或目标路径跨越多个所有权区域 | 否 | 修正 TaskEnvelope 中的 skill_mode 为单一合法模式，重新提交 |
| PATH_OUTSIDE_PROJECT | BLOCKED | 目标路径不在当前项目 root_path 内，或跨项目访问 | 否 | 检查路径拼写和 project_id，确保所有路径位于 root_path 下 |
| OWNERSHIP_VIOLATION | BLOCKED / COMPLETED_WITH_WARNINGS | 子 Skill 试图写入非所属区域 | 否 | 拒绝写入；可用内容降级为 Proposal；由 novel-master 拆分调用重新路由 |
| SCHEMA_INVALID | BLOCKED | 输入/输出不符合契约 schema（缺字段、类型错误、枚举非法） | 否 | 校验 TaskEnvelope/SkillResult 字段，修正后重新提交 |
| STALE_CONTEXT | BLOCKED | base_revision 与当前状态文件 revision 不一致 | 是 | 重新提取上下文（EXTRACT_CONTEXT），刷新 base_revision，必要时重新授权 |
| INVALID_APPROVAL | BLOCKED | ApprovalRef 校验失败：过期、范围不足、revision 不匹配、已使用或已撤销 | 是 | 生成新的待确认摘要，请求用户重新授权，生成新 ApprovalRef |
| LIFECYCLE_VIOLATION | BLOCKED | 章节生命周期转换不在允许集合内，或未接受章节试图提交状态 | 否 | 检查章节当前状态；DRAFT/REVIEWED 只能进入 proposals；需先通过接受闸门 |
| CANON_CONFLICT | NEEDS_DECISION | 同一事实出现不兼容证据，新内容与现有 Canon 矛盾 | 是 | 保留双方证据，登记 contradictions.md，继续无关部分，等待用户裁决 |
| WRITE_LOCKED | BLOCKED | 目标文件正被其他事务占用，或 ChangeSet 正在执行中 | 是 | 等待当前事务完成或回滚后重试；检查是否有未清理的 .tmp 文件 |
| CHANGESET_INVALID | FAILED | ChangeSet 校验失败：来源无效、权限不足、ApprovalRef 缺失、base_revision 过期 | 否 | 检查 commit_input 全部字段；确认来源章节为 ACCEPTED/PUBLISHED；重新构造 ChangeSet |
| ROLLBACK_FAILED | FAILED | ChangeSet 回滚失败，临时文件清理异常，正式文件状态不确定 | 否 | 停止所有后继写操作；保留诊断信息；人工检查 .tmp 文件和 change_log 确定一致状态 |
| UNKNOWN_REQUIRED_CONTEXT | NEEDS_DECISION | 必要上下文缺失且无法从现有文件推断（如关键人物档案丢失） | 是 | 从正文/摘要/Canon 抽取最小状态；缺失项标记 UNKNOWN；请求用户补充或确认 |

## 错误输出格式

错误通过 SkillResult.issues 输出：

```yaml
issues:
  - severity: blocker
    category: "{error_code}"
    description: "具体错误描述"
    affected_files: ["path/to/file"]
    suggested_resolution: "推荐恢复动作"
```

## 重试规则

- 可重试错误：修正前置条件后可重新提交同一请求。
- 不可重试错误：必须修改请求内容或由用户介入后才能继续。
- ROLLBACK_FAILED 后禁止任何自动写操作，必须人工介入。
- STALE_CONTEXT 重试时必须完整重跑上下文提取，不得只刷新 revision 字段。

## 降级规则

- 越权内容不丢弃，降级为 Proposal（requires_user_confirmation: true）。
- 部分成功时使用 NEEDS_DECISION 或 COMPLETED_WITH_WARNINGS，禁止伪装为 COMPLETED。
- Canon 冲突时继续无关部分，不阻塞整个任务。
- 上下文超限时按优先级截断，输出 omitted_context_refs。
