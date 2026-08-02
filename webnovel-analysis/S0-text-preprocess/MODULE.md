# S0 Text Preprocess

内部模块，仅由根 `webnovel-analysis` 调用，不参与外部路由。

负责文本标准化、章节索引、批次清单与预处理问题记录。输入来自 O0，输出满足 `../schemas/modules/S0.schema.json`。

详细提示见 `references/prompt-template.md`，内部契约见 `references/skill-ir.md`。
