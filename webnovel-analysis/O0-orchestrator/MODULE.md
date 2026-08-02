# O0 Orchestrator

内部模块，仅由根 `webnovel-analysis` 调用，不参与外部路由。

负责把用户范围转成任务清单、输入来源、批次策略和执行计划。输出必须满足 `../schemas/modules/O0.schema.json`；不得伪造运行状态、哈希或检查点。

详细提示见 `references/prompt-template.md`，内部契约见 `references/skill-ir.md`。
