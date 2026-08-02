# S7 Visualization

内部模块，仅由根 `webnovel-analysis` 调用，不参与外部路由。

负责把审计后的聚合数据转换为图表规格和工作簿设计，不负责实际渲染证明。依赖 Q0，输出满足 `../schemas/modules/S7.schema.json`。

详细提示见 `references/prompt-template.md`，内部契约见 `references/skill-ir.md`。
