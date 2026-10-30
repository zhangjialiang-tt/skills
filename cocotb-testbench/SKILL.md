---
name: cocotb-testbench
description: 为 Verilog/SystemVerilog/VHDL RTL 生成基于 cocotb 2.x（runner + pytest）的跨平台 Python 仿真测试框架。cocotb、Python testbench、pytest 验证 RTL、golden model 位精确对拍、免 make/Tcl 流程、Windows + ModelSim/Questa 排障等请求时使用。扫描依赖闭包生成 sim/<top>/ 的 smoke/functional 测试组，pytest 运行产出 JUnit 报告；有用户参考模型优先对拍，无模型时 agent 分析 RTL 生成 characterization 测试并如实降级结论。ModelSim 原生 Verilog TB、subx 目录契约、sim.do 波形走 build-testbench，不用本 skill。
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
6. 结果必须绑定实际 simulator + version；Icarus PASS 不得替代 ModelSim/Questa 证据
7. 对时序输出在 `RisingEdge` 后先 `ReadOnly` 再采样；golden 必须对齐 signedness、截断规则、位宽和 RAM/协议 latency
8. 提速改动必须有同命令墙钟 A/B（`results.xml` 的 `time` + `sim_time_ratio`）；未做过 A/B 的优化不得写成默认

## 性能原则（2026-10-28 实测：pw-gige `cocotb-gige_video_ip` 30+ min → 2.2 min）

1. **时钟在 SV 生成，Python 只等待**：套件有 TB 包装层时，`always #<半周期> clk = ~clk;`
   放 SV，Python 只 `await RisingEdge`。Python `Clock` 每个半周期唤醒一次（本机标定
   ≈20 µs/次），100 MHz 时钟跑 32.5 ms 仿真就是 650 万次唤醒。实测：vbw 用例
   980.5→78.0 s（12.6×）、scps 181.9→28.0 s（6.5×）、整套 30+ min→129.9 s。
   单元级套件（DUT 直接作顶层、无 SV 包装）没有这个选项，改走第 3 条。
2. **跨用例共享的 TB 状态在 setup 里归零**：捕获数组/计数器、使能开关、配置快照、
   parser 游标。`test_filter` 命中的所有用例在**同一仿真会话**内顺序跑，DUT/TB 初值
   只给第一个用例。实测：6 条一起跑时 scps/vbw 因 `word_cnt` 未清零、`tpg_en` 残留而
   假失败（单独跑全绿）。
3. **判据不要等「真实时间」**：按目标帧率/周期反算消隐，会在仿真里真的等那么久。
   实测：120 Hz 一档每帧插 8.33 ms 空场，占该用例 26.3 ms 仿真时间的 63%。
   判据优先用事件计数（帧数、包数、握手次数）。
4. **提速前后用同一命令各跑一次并登记**（含 simulator 版本、`time`、`sim_time_ratio`）。
   「感觉快了」不算证据。

## Workflow（完整命令与失败策略见 `references/workflow.md`）

`workspace_root.py` → `probe_env.py` → `build_fileset.py --json` →
`tb_extract_ports.py --json` → `gen_cocotb_skeleton.py` →
`cd sim/<top> && pytest -m smoke` → `pytest -m functional`。

生成后必做：对照 RTL 复核时钟/复位极性/symbolic width、注册输出采样点、signed 运算与接口 latency，记入报告 `classification_assumptions`。VHDL top 手写 ports.json（schema 见 workflow.md）。Windows + ModelSim/Questa 还要先做 license/PATH 预检，并用同一 simulator 重跑 smoke；不能用 Icarus 结果代替。

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
- 实测踩坑与跨平台排障：`references/troubleshooting.md`（含 Windows + ModelSim、cocotb 2.x、采样时序与缓存失效）
- 已知输出风险与 v1 边界：`reports/output-risk-profile.md`
