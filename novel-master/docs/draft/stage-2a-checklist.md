# novel-master v1.2.0 — 阶段 2A：修改落点清单

> 基于：阶段 -1 Reality Check + 阶段 1 RC1 契约
> 时间：2026-07-25
> 状态：2A 完成，准备进入 2B

---

## 决策：Schema 存放方式

**采用平铺 + defs/ 子目录混合**：
- 5 个业务 Schema 平铺在 `schemas/` 下（与现有 schema 一致）
- 4 个共享定义放 `schemas/defs/`（用于 `$ref` 复用）

原因：现有 7 个 schema 都是平铺的，保持一致性。但 4 个共享定义（reader_experience、review_dimensions、evidence_ref、contract_meta）会被 5 个业务 schema 引用，集中管理避免重复。

---

## 修改清单（10 个操作）

### 1. 新建目录

```text
schemas/defs/
```

### 2. 新建：`schemas/defs/contract-meta.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "defs/contract-meta.schema.json",
  "title": "Contract Meta",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_id", "schema_version"],
  "properties": {
    "schema_id": { "type": "string", "minLength": 1 },
    "schema_version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" }
  }
}
```

引用方式：`{ "$ref": "defs/contract-meta.schema.json" }`

### 3. 新建：`schemas/defs/evidence-ref.schema.json`

- 字段：`source_type`（enum 6 种）、`deliverable_id`、`revision`、`scene_id`、`paragraph_start`、`paragraph_end`、`json_pointer`、`excerpt`
- `source_type` 必填
- `deliverable_id` + `revision` 必填

### 4. 新建：`schemas/defs/reader-experience.schema.json`

- 完整 reader_experience 结构（chapter_role、promise、payoff、emotional_arc、information_gain、tension_curve、continuation_drive）
- 条件必填：`payoff.mode=DEFERRED → deferred_reason`，`NONE_JUSTIFIED → justification`，`continuation_drive.type=NONE_JUSTIFIED → justification`
- `chapter_role.primary` 枚举：8 值
- `payoff.expected_payoff_window.type` 枚举：4 值 + null

### 5. 新建：`schemas/defs/review-dimensions.schema.json`

- `mandatory_guardrail_scan`：4 值枚举
- `review_dimension` 枚举：4 值
- `dimension_results[].status`：4 值枚举
- `reason_code` 枚举：5 值
- `severity` 枚举：3 值
- `guardrail_results.status`：3 值枚举

### 6. 新建：`schemas/chapter-plan.schema.json`

- 初始大小目标：~180 lines
- 引用：`contract-meta`、`reader-experience`
- 条件校验：`contract_meta.schema_version` 必须为 `"1.2.0"`
- `style_modulation_ref` 可为 string 或 null

### 7. 新建：`schemas/chapter-report.schema.json`

- 初始大小目标：~150 lines
- 引用：`contract-meta`、`evidence-ref`
- `target_execution[]` 数组：`target_ref`、`execution`(枚举 `PRESENT|PARTIAL|DEVIATED`)、`evidence_ref`

### 8. 新建：`schemas/review-request.schema.json`

- 初始大小目标：~100 lines
- 引用：`contract-meta`
- `review_scope`：`list[review_dimension]` (enum)
- `review_target`、`chapter_plan_ref`、`chapter_report_ref`、`context_pack_ref`

### 9. 新建：`schemas/review-report.schema.json`

- 初始大小目标：~180 lines
- 引用：`contract-meta`、`evidence-ref`、`review-dimensions`
- `guardrail_results` + `dimension_results`（恰好 4 个维度）

### 10. 新建：`schemas/style-guide.schema.json`

- 初始大小目标：~130 lines
- 引用：`contract-meta`
- `scene_modulations`：`modulation_id` → `category`(enum 7 值) + `overrides`（typed relative operators 每个字段预定义）
- `override_policy.protected_fields`：`array[string]`（JSON Pointer 路径）

### 11. 修改：`schemas/context-pack.schema.json`

- 在 `properties` 中新增 `style_profile` 对象（与现有 `style_constraints` 并列）
- `style_constraints` 保留原 `array[string]` 不修改
- `style_profile` 对象包含 `global_defaults_ref`（path + revision）和 `relevant_scene_modulations`（数组）

### 12. 新建：`scripts/validate_quality_contract.py`

- 初始大小目标：~300 lines
- 纯过程式，argparse CLI，与现有脚本风格一致
- 功能：
  - 读取 TaskEnvelope + ChapterPlan → 校验 reader_experience 条件必需
  - 读取 ChapterPlan + StyleGuide → 校验 style_modulation_ref 引用存在
  - 读取 StyleGuide → 校验 override_policy.protected_fields 未被 modulation 覆盖
  - 校验 relative_to_global 操作符合法性
- 退出码：0=通过，1=失败，2=输入错误

### 13. 更新：`reports/skill-ir.json`

- 在 `schemas` 中添加 5 个新 schema 路径（去掉已存在的 schemas/ 映射格式）
- 在 `scripts` 中添加 `scripts/validate_quality_contract.py`

---

## 不修改项确认

| 项目 | 原因 |
| --- | --- |
| `schemas/skill-result.schema.json` | 仅管理通用信封，不承载 Skill 专属 payload |
| `schemas/task-envelope.schema.json` | review_scope 通过 review-request.schema.json 管理 |
| `schemas/approval-ref.schema.json` | 未涉及变更 |
| `schemas/changeset.schema.json` | 未涉及变更 |
| `schemas/master-result.schema.json` | 未涉及变更 |
| `schemas/recovery-report.schema.json` | 未涉及变更 |
| `scripts/commit_changeset.py` | 事务协议不变 |
| `scripts/validate_approval.py` | 未涉及变更 |
| `scripts/validate_contract.py` | validate_quality_contract 是补充而非替代 |
| `registry/packages/novel-master.json` | 包元数据升级在阶段 5 freezing 时更新 |

---

## 阶段 2B 执行顺序（待进入）

```text
1. mkdir schemas/defs/
2. 新建 schemas/defs/contract-meta.schema.json
3. 新建 schemas/defs/evidence-ref.schema.json
4. 新建 schemas/defs/reader-experience.schema.json
5. 新建 schemas/defs/review-dimensions.schema.json
6. 修改 schemas/context-pack.schema.json（新增 style_profile）
7. 新建 schemas/chapter-plan.schema.json
8. 新建 schemas/chapter-report.schema.json
9. 新建 schemas/review-request.schema.json
10. 新建 schemas/review-report.schema.json
11. 新建 schemas/style-guide.schema.json
12. 新建 scripts/validate_quality_contract.py
13. 更新 reports/skill-ir.json
14. 运行 pytest tests/test_schemas.py 确认原测试通过
```
