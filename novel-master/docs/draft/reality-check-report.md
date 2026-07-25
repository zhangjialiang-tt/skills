# novel-master v1.2.0 — Reality Check 报告

> 阶段：-1（仓库现实检查，只读）
> 时间：2026-07-25
> 基线：v1.1.0 冻结文档

## 1. Git 状态

```
分支：main
HEAD：ee0a37a feat(novel-master): ✨ initial project scaffolding
标签：无 v1.1 标签
```

建议在进入阶段 0 前打一个轻量标签：`git tag v1.1.0-baseline`，固定基线 commit。

## 2. Schema 组织方式（7 个文件，flat 目录，无 defs/ 子目录）

| Schema | 状态 | additionalProperties |
| --- | --- | --- |
| `task-envelope.schema.json` | 存在 | ✅ false |
| `skill-result.schema.json` | 存在 | ✅ false（含嵌套） |
| `approval-ref.schema.json` | 存在 | ✅ false |
| `changeset.schema.json` | 存在 | ✅ false |
| `context-pack.schema.json` | 存在 | ✅ false |
| `master-result.schema.json` | 存在 | ✅ false |
| `recovery-report.schema.json` | 存在 | ✅ false |
| `chapter-plan.schema.json` | **不存在** | — |
| `chapter-report.schema.json` | **不存在** | — |
| `review-request.schema.json` | **不存在** | — |
| `review-report.schema.json` | **不存在** | — |
| `style-guide.schema.json` | **不存在** | — |
| `schemas/defs/` | **不存在** | — |

**确认**：
- `skill-result.schema.json` 仅管理通用交付物元数据信封（type/path/content_summary/deliverable_id/revision/content_hash/chapter_lifecycle_status）。不承载 Skill 专属 payload（如 chapter_plan 的内容字段）。
- 所有现有 schema 已严格执行 `additionalProperties: false`。
- v1.2.0 新增的 Schema 需平铺在 `schemas/` 下或新建 `schemas/defs/` 子目录。
- `context-pack.schema.json` 中 `style_constraints` 为 `array[string]`，新增 `style_profile` 对象可避免中断 v1.1 兼容。

## 3. 子 Skill 输出契约组织方式

所有 7 个子 Skill 的输出结构在各自 `SKILL.md` 中通过 YAML 示例定义，无独立的输出 Schema 文件。

**chapter_plan（v1.1.0 冻结契约定义）**：
```
chapter_id, chapter_function, viewpoint_character, time_and_location,
opening_state, scenes[], required_elements, prohibited_reveals,
active_foreshadowing, chapter_climax, ending_state, continuity_risks
```

**chapter_report（Writer 输出）**：
```
executed_plan_items, deviations_from_plan, new_facts_introduced,
character_state_changes, timeline_changes, knowledge_changes,
foreshadowing_changes, possible_continuity_risks
```

无 `reader_experience`、无 `reader_experience_execution`、无 `contract_meta`、无 `evidence_ref`。

## 4. Registry 功能

```
registry/
├── index.json                                    — 索引
├── packages/novel-master.json                    — 包元数据（schema_version 2.0）
└── examples/novel-master-1.0.0-reconstructed.json
```

**确认**：registry 当前仅承担包元数据管理，不承担业务输出契约注册。v1.2.0 的新增 Schema 需在 `skill-ir.json` 中注册。

## 5. Evals 现状（12 个用例）

```
evals/evals.json                                  — 12 个 eval 用例
evals/fixtures/results-valid.json                 — 校验器测试夹具
evals/{adversarial,blind_holdout,confusion,dev,holdout}/ — 分级测试集
```

## 6. 测试现状

| 文件 | 行数 | 测试函数 |
| --- | --- | --- |
| `test_changeset.py` | 1042 | 29 |
| `test_schemas.py` | 335 | 25 |
| `test_approval.py` | 147 | 10 |
| `test_lifecycle.py` | 105 | 13 |
| `test_paths.py` | 132 | 18 |
| `test_prompt_regressions.py` | 122 | 7 |
| `test_skill_family_governance.py` | 94 | 6 |
| **合计** | **1977** | **108** |

实际测试数 108（非计划中的 133，需核实差异来源）。

## 7. 冻结契约关键条款

- **state/ 所有权**：v1.1.0 冻结架构 §6.1 明确 `continuity-keeper` 是 `state/` 唯一写入者。质量状态不写入 `state/`。
- **Canon 单一写入者**：§3 "只有 continuity-keeper 可以正式写入 state/"。
- **chapter_plan**：定义了 13 个字段，无 reader_experience。
- **review_scope**：当前为 `string`，v1.2.0 需改为 `list[review_dimension]`。

## 8. 实施差异确认

| 计划假设 | 实际状况 | 影响 |
| --- | --- | --- |
| 133 条测试 | 108 条 | 发布门槛中"133 条治理测试全部通过"需改为"108 条" |
| `schemas/defs/` 可建 | 目录不存在 | 需新建或平铺 |
| 10 个 eval 用例 | 12 个 | 新增 eval 编号从 QE-013 开始 |
| git 有 tag | 无 | 需在阶段 0 前打标签 |

## 9. 阶段 -1 结论

**仓库结构清晰，现状与计划假设差异可控。可以进入阶段 0。**

需在执行前调整：
- 测试基线从"133"改为"108"。
- 决定 Schema 存放方式（平铺 vs `defs/` 子目录）。
- 打 `v1.1.0-baseline` 标签固定基线。