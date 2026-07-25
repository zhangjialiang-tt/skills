# lifecycle-and-approval.md

> 用途：统一章节生命周期、接受闸门、状态提交资格和 ApprovalRef 校验规则。
> 读取时机：涉及章节接受、生命周期转换、COMMIT_CHAPTER_STATE、COMMIT_CANON、RETCON、EDIT_L3/L4 或初始化确认时，通过 SKILL.md 中的相对链接读取。
> 来源：[冻结契约](../docs/novel-master-contracts-v1.1.0-frozen.md) §4.3、§7、§8。

## 目录

- [章节生命周期](#章节生命周期)
- [允许的转换](#允许的转换)
- [接受闸门](#接受闸门)
- [状态提交资格](#状态提交资格)
- [ApprovalRef](#approvalref)
- [授权有效性检查](#授权有效性检查)
- [失败处理](#失败处理)

## 章节生命周期

| 状态 | 含义 |
| --- | --- |
| `PLANNED` | 章节卡已形成，尚未生成正文 |
| `DRAFT` | 正文草稿或修改后的新 revision |
| `REVIEWED` | 当前 revision 已完成自动或人工评审 |
| `ACCEPTED` | 用户或有效自动工作流接受当前 revision |
| `SUPERSEDED` | 当前已接受版本被新版本替代 |
| `DEPRECATED` | 用户明确废弃当前已接受版本 |
| `PUBLISHED` | 用户标记为已发布并提供发布引用 |

`SUPERSEDED`、`DEPRECATED` 和 `PUBLISHED` 是 V1 终态。终态内容如需修改，必须创建新 `deliverable_id` 或新 revision。

章节生命周期元数据必须绑定同一份内容的 `deliverable_id`、`revision` 和 `content_hash`。`accepted_by` 仅在 `ACCEPTED` 或 `PUBLISHED` 时非空；`acceptance_ref` 必须指向有效的 `ApprovalRef.approval_id`；`published_ref` 仅在 `PUBLISHED` 时必填。

## 允许的转换

| 转换 | 触发条件 |
| --- | --- |
| `PLANNED → DRAFT` | chapter-writer 基于章节卡产出正文 |
| `DRAFT → REVIEWED` | 当前 revision 完成评审 |
| `DRAFT → ACCEPTED` | 用户直接接受，或命中允许跳过评审的自动接受授权 |
| `REVIEWED → DRAFT` | 按评审修改并产生新 revision |
| `REVIEWED → ACCEPTED` | 用户明确接受，或命中自动接受工作流 |
| `ACCEPTED → SUPERSEDED` | 新版本被接受并替换当前版本 |
| `ACCEPTED → DEPRECATED` | 用户明确废弃当前版本 |
| `ACCEPTED → PUBLISHED` | 用户标记已发布并提供发布引用 |

未列出的转换全部禁止。

## 接受闸门

1. chapter-writer 输出新正文或修改后的新 revision 时，状态必须为 `DRAFT`。
2. novel-master 在写作链末尾插入 `ACCEPT_CHAPTER` 闸门，不得把正文生成视为自动接受。
3. 用户直接接受或命中仍有效的自动接受授权后，生成或引用覆盖当前 `deliverable_id`、`revision` 和 `content_hash` 的接受记录。
4. 接受记录中的 `deliverable_id`、`revision`、`content_hash` 和 `chapter_lifecycle_status` 必须与状态提交来源完全一致。
5. 内容、hash 或 revision 发生变化后，旧接受记录和旧授权不得用于新版本。
6. 自动日更授权必须限定项目、章节范围、允许偏离程度和失效条件。

## 状态提交资格

- 只有 `ACCEPTED` 或 `PUBLISHED` 章节可以作为 `COMMIT_CHAPTER_STATE` 来源。
- `DRAFT` 或 `REVIEWED` 内容产生的变化只能进入 `state_change_proposals`。
- `SUPERSEDED` 或 `DEPRECATED` 内容不得成为新的状态提交来源。
- COMMIT_CHAPTER_STATE 前必须同时校验来源交付物、接受记录、当前内容 hash 和 base revision。

## ApprovalRef

ApprovalRef 必须包含：

```yaml
approval_id: string
request_id: string
approved_by: user
approved_at: ISO-8601 string
operation: COMMIT_CANON | RETCON | EDIT_L3 | EDIT_L4 | ACCEPT_CHAPTER | INIT_PROJECT
approved_scope:
  files: []
  items: []
based_on_revision: string
expires_after_use: boolean
status: ACTIVE | USED | EXPIRED | REVOKED
```

- `L4` 和 `RETCON` 必须使用 `expires_after_use: true` 的一次性授权。
- `EDIT_L3` 仅在风险为 `HIGH` 时强制授权。
- `INIT_PROJECT` 可在同一初始化范围内授权一次初始 `COMMIT_CANON`。
- 一次性授权成功使用后必须转为 `USED`。
- `user_confirmation_ref` 只能保存兼容用 `approval_id`，不能用自由文本代替 ApprovalRef。

## 授权有效性检查

执行前必须同时满足：

1. `status` 为 `ACTIVE`。
2. `request_id` 与当前请求一致，或批准范围明确覆盖当前请求。
3. `operation` 与实际操作一致。
4. `approved_scope.files` 和 `approved_scope.items` 覆盖全部目标。
5. `based_on_revision` 与用户审阅并批准的当前 revision 一致。
6. 授权未被使用、撤销或判定过期。

## 失败处理

- 生命周期转换非法：`BLOCKED / LIFECYCLE_VIOLATION`。
- 未接受章节请求状态提交：`BLOCKED / CHAPTER_NOT_ACCEPTED`。
- ApprovalRef 任一校验失败：`BLOCKED / INVALID_APPROVAL`。
- revision 或内容 hash 已变化：旧授权失效；重新提取上下文、生成待确认摘要并请求新授权。
