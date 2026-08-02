# S3 Character Network

内部模块，仅由根 `webnovel-analysis` 调用，不参与外部路由。

负责角色登记、关系事件与势力变化。输入来自 S0，输出满足 `../schemas/modules/S3.schema.json`。

详细提示见 `references/prompt-template.md`，内部契约见 `references/skill-ir.md`。
