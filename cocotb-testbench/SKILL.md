---
name: cocotb-testbench
description: 为 Verilog/SystemVerilog/VHDL RTL 生成基于 cocotb 2.x（runner + pytest）的跨平台 Python 仿真测试框架。cocotb、Python testbench、pytest 验证 RTL、golden model 位精确对拍、免 make/Tcl 流程等请求时使用。扫描依赖闭包生成 sim/<top>/ 的 smoke/functional 测试组，pytest 运行产出 JUnit 报告；有用户参考模型优先对拍，无模型时 agent 分析 RTL 生成 characterization 测试并如实降级结论。ModelSim 原生 Verilog TB、subx 目录契约、sim.do 波形走 build-testbench，不用本 skill。
---

# Cocotb Testbench — cocotb 仿真框架生成器

为指定 RTL top 生成 cocotb runner + pytest 测试框架并跑通。不修改 DUT。

**Non-goals**：修改 DUT；smoke/RTL 自推宣称功能正确；静默选同名依赖；覆盖用户文件；ModelSim 原生 TB（走 build-testbench）。
## Hard invariants

1. 先 `probe_env.py`；缺依赖报告安装建议并**等确认**
2. 模块名只取 `build_fileset --json` 的 `top.name`；歧义暴露候选
3. functional 前必过 smoke 门禁；smoke PASS ≠ 功能正确
4. golden 对拍是唯一「功能验证」依据；无 golden 一律 `characterization` 降级结论
5. 修错只改 `design.json`/`ports.json`；生成器拒绝覆盖，冲突备份/改名

## Workflow（完整命令与失败策略见 `references/workflow.md`）

`workspace_root.py` → `probe_env.py` → `build_fileset.py --json` →
`tb_extract_ports.py --json` → `gen_cocotb_skeleton.py` →
`cd sim/<top> && pytest -m smoke` → `pytest -m functional`。

生成后必做：对照 RTL 复核时钟/复位极性/symbolic width，记入报告 `classification_assumptions`。VHDL top 手写 ports.json（schema 见 workflow.md）。

## Stage gates

| 达到状态 | 允许宣称 |
|---|---|
| `pytest -m smoke` PASS | 可编译、可 elaborate、基本驱动无 X/Z——**仅此** |
| golden 对拍 PASS | 功能与参考模型一致（指明模型路径） |
| characterization PASS | 行为刻画与 RTL 阅读一致——**不得称功能正确** |

## Deeper reading

- 步骤命令、报告字段与失败策略：`references/workflow.md`
- 路由回归用例：`evals/evals.json`
- runner/pytest API 事实基线与版本矩阵：`references/cocotb-runner-api.md`
- 证据分级与 golden 契约：`references/verification-policy.md`
- 实测踩坑与跨平台排障：`references/troubleshooting.md`
- 已知输出风险与 v1 边界：`reports/output-risk-profile.md`
