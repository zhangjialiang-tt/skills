# Model Output Contract

所有内部模块只输出以下模型信封；领域数据放入 `payload`，具体字段由 `schemas/modules/<module>.schema.json` 约束。

```json
{
  "task_id": "TASK-001",
  "batch_id": "BOOK",
  "skill_id": "S1",
  "skill_version": "1.0.0",
  "schema_version": "1.0.0",
  "operation": "analyze",
  "payload": {},
  "uncertain_items": [],
  "conflicts": [],
  "manual_review_items": []
}
```

- `batch_id` 使用 `TASK`、`BOOK` 或 `BATCH-<id>`。
- `uncertain_items`、`conflicts`、`manual_review_items` 的元素必须是结构化对象，不得用裸字符串。
- `mode`、`merge_mode`、`audit_scope`、`template_mode` 的动作语义统一写入 `operation`。
- `output_hash`、`validated_at`、`invalidated_by`、`status` 由未来 artifact registry 管理，模型不得生成。
- 各模块 Prompt 中标记为“领域 payload 参考”的旧示例只用于理解字段语义，不是可直接提交的完整输出。
