# S1 Narrative Structure

内部模块，仅由根 `webnovel-analysis` 调用，不参与外部路由。

负责按章节识别叙事阶段、故事单元和结构变化。输入来自 S0，输出满足 `../schemas/modules/S1.schema.json`。

详细提示见 `references/prompt-template.md`，内部契约见 `references/skill-ir.md`。
