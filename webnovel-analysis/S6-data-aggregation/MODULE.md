# S6 Data Aggregation

内部模块，仅由根 `webnovel-analysis` 调用，不参与外部路由。

只负责合并 S1-S5 结构化结果、统计覆盖率、记录冲突并形成导出计划。不得生成最终分析报告；最终报告由 R0 负责。输出满足 `../schemas/modules/S6.schema.json`。

详细提示见 `references/prompt-template.md`，内部契约见 `references/skill-ir.md`。
