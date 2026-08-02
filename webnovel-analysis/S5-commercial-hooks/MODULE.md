# S5 Commercial Hooks

内部模块，仅由根 `webnovel-analysis` 调用，不参与外部路由。

负责识别留存、追读、付费与传播钩子。依赖 S1、S2、S4，输出满足 `../schemas/modules/S5.schema.json`。

详细提示见 `references/prompt-template.md`，内部契约见 `references/skill-ir.md`。
