# S8 Genre Formula

内部模块，仅由根 `webnovel-analysis` 调用，不参与外部路由。

负责从审计后的分析结果归纳类型公式、适用条件和反例。依赖 Q0，输出满足 `../schemas/modules/S8.schema.json`。

详细提示见 `references/prompt-template.md`，内部契约见 `references/skill-ir.md`。
