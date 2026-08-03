# Milestone 1 Migration

## 包结构

- 新增根 `SKILL.md`、`manifest.json`、`agents/interface.yaml`。
- 12 个子目录的 `SKILL.md` 更名为不带 frontmatter 的 `MODULE.md`。
- 删除旧的 S1 独立 `agents/interface.yaml`。

## 契约

- 公共信封迁移到 `schemas/output-envelope.schema.json`。
- 模块领域字段迁入 `payload`，模块 Schema 位于 `schemas/modules/`。
- `mode`、`merge_mode`、`audit_scope`、`template_mode` 统一映射到 `operation`。
- 字符串问题列表迁移为结构化对象列表。

## 报告职责

- S6 的最终报告职责迁移至 R0。
- 原 `S6-data-aggregation/references/report-template.md` 迁移为根 `references/final-report-template.md`。

## 兼容性

`test/analysis/wukongzhuan` 是历史快照，不作为当前 Schema 的 golden。已知差异记录在同目录 `fixture-manifest.yaml`，原数据不改写。
