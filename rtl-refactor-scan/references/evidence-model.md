# 证据等级模型

每条 Finding 必须标注 evidence_level，表示结论的可信度。禁止把低证据等级的结论标为 `confirmed` 置信度。

| 等级 | 名称 | 含义 | rtl-refactor-scan 责任 |
|------|------|------|------------------------|
| E0 | LLM hypothesis | 仅基于语义推测 | 可作为 semantic finding 的初始证据 |
| E1 | Source evidence | 有明确源码位置和数据流关系 | LLM 审查的基础 |
| E2 | Deterministic static | 脚本或 AST 规则确定识别 | **M2 交付的 deterministic rule 产出此等级** |
| E3 | Tool confirmed | lint/elaboration/综合/CDC/timing 工具确认 | 需 adapter（M4） |
| E4 | Simulation confirmed | 可复现仿真证据 | 需 testbench 回归 |
| E5 | Implementation/board | 实现报告或板上数据确认 | 作为输入证据，根因不由本 Skill 主导 |

## 规则示例

- "可能形成长组合路径" → E0/E1，**不能**标为 confirmed
- "Verilator 报 UNOPTFLAT" → E3
- "随机 backpressure 下 tlast 提前" → E4
- "板上 data FIFO full 且 accepted < cmd_len" → E5

## 本 Skill 覆盖范围

rtl-refactor-scan 的主要责任覆盖 E1–E4。E5 可作为输入证据，但根因调查不由本 Skill 主导。
