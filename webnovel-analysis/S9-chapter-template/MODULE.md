# S9 Chapter Template

内部模块，仅由根 `webnovel-analysis` 调用，不参与外部路由。

负责生成可复用的章节分析模板。通用模板依赖 Q0；类型专用模板还依赖 S8。输出满足 `../schemas/modules/S9.schema.json`。

详细提示见 `references/prompt-template.md`，内部契约见 `references/skill-ir.md`。
