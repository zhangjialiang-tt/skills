# Q0 Quality Audit

内部模块，仅由根 `webnovel-analysis` 调用，不参与外部路由。

负责审计 S6 的契约完整性、跨模块冲突、证据覆盖与风险等级。依赖 S6，P0 阻断，P1 按风险判定。输出满足 `../schemas/modules/Q0.schema.json`。

详细提示见 `references/prompt-template.md`，内部契约见 `references/skill-ir.md`。
