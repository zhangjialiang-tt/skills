# S4 Payoff Engineering

内部模块，仅由根 `webnovel-analysis` 调用，不参与外部路由。

负责识别爽点铺垫、触发、兑现与落空；S2 是硬依赖，S1 仅为可选结构上下文。每个 `payoff_event` 必须包含 `payoff_nature`，输出满足 `../schemas/modules/S4.schema.json`。

详细提示见 `references/prompt-template.md`，内部契约见 `references/skill-ir.md`。
