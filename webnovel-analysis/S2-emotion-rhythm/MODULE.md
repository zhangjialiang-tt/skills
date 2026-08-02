# S2 Emotion Rhythm

内部模块，仅由根 `webnovel-analysis` 调用，不参与外部路由。

负责章节情绪强度、节奏和趋势记录。输入来自 S0，输出满足 `../schemas/modules/S2.schema.json`。

详细提示见 `references/prompt-template.md`，内部契约见 `references/skill-ir.md`。
