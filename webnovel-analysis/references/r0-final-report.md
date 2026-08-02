# R0 Final Report

R0 是根 Skill 内部的最终报告阶段，不是独立 Skill。

## 输入

- 已通过 Schema 校验的 S6 聚合结果。
- Q0 审计结论与未决人工复核项。
- 可选的 S7 可视化、S8 类型公式和 S9 模板资产。

## 输出

按 [final-report-template.md](final-report-template.md) 生成 `payload.analysis_report_md`，并使用 [R0.schema.json](../schemas/modules/R0.schema.json) 的公共信封。

## 硬约束

- 不重新计算 S1-S6 的结构化指标。
- 报告结论必须能回指结构化字段或原文证据。
- P0 未关闭时不得生成“通过”式最终结论。
