# cocotb runner + pytest API（grounded @ cocotb 2.1.0，2026-09）

来源：cocotb 官方文档 `runner.rst`（howto-python-runner）、`pytest_plugin.rst`、
`examples/simple_dff/test_dff.py`、`src/cocotb_tools/runner.py` 签名。

## 主流程：runner-with-pytest（稳定，官方示例采用）

```python
import os
from cocotb_tools.runner import get_runner

runner = get_runner(os.getenv("SIM", "icarus"))
runner.build(sources=[...], hdl_toplevel="top", always=True, verbose=True)
runner.test(hdl_toplevel="top", test_module="test_x")   # 返回 results XML 路径
```

pytest 控制函数（非 async）调用 runner；cocotb 协程测试放同目录模块内由仿真器执行。
`SIM=<name> pytest` 选择仿真器；文件名/函数名遵循 pytest discovery。

## Runner.build 关键参数（2.x 签名摘录）

| 参数 | 说明 |
|---|---|
| `sources` | 语言无关源列表（`verilog_sources`/`vhdl_sources` **2.0 起弃用**） |
| `includes` / `defines` | Verilog incdir / define；defines 值不再自动加引号（2.0 变更） |
| `parameters` | Verilog parameter / VHDL generic |
| `hdl_toplevel` / `hdl_library` | top 模块名 / 编译库名 |
| `build_dir` / `cwd` / `clean` / `always` | 构建目录 / 执行目录 / 先删 / 总是重编 |
| `timescale` | `(unit, precision)` 元组，如 `("1ns", "1ps")` |
| `waves` / `verbose` / `log_file` / `build_args` | 波形 / 输出 / 日志 / 追加编译参数 |

## Runner.test 关键参数

`test_module`（str 或列表，逗号拼接）、`hdl_toplevel`、`hdl_toplevel_lang`（verilog/vhdl，混合语言时决定入口 GPI）、`testcase`（生成 `COCOTB_TEST_FILTER` 正则）、`seed`、`waves`、`gui`、`build_dir`、`test_dir`、`results_xml`（**pytest 下不要设置**）、`extra_env`、`elab_args`、`test_args`、`plusargs`、`pre_cmd`、`timescale`、`log_file`、`test_filter`。

## 路径与环境机制（跨平台要点）

- runner 以 `PYTHONPATH = os.pathsep.join(sys.path)` 启动仿真进程（runner.py:278）：
  **在生成目录内跑 pytest**，`tb_runner`/`test_*` 模块即可被仿真进程 import。
- `WAVES=1` / `GUI=1` 环境变量覆盖代码里的 waves/gui 参数；无 GUI 仿真器用
  Surfer/GTKWave 打开波形（`COCOTB_WAVEFORM_VIEWER` 指定）。
- build 失败时 runner 抛 `RuntimeError`，test 失败抛 `SystemExit`；逐用例结果看
  `sim_build/<test_module>.result.xml`，不是 pytest 单行摘要。

## cocotb 2.x 测试端惯用法（生成模板所用）

- `from cocotb.clock import Clock; Clock(dut.clk, 10, unit="ns").start(start_high=False)`
  （1.x 需 `await start(clock)`，2.x 直接 `.start()`；本 skill 要求 cocotb>=2.0）
- 信号读写一律 `dut.<sig>.value`；X/Z 检测用 `.value.integer` 捕获 `ValueError`
- `@cocotb.test()`；仿真内日志用标准 `logging.getLogger("cocotb.test")`
- 1-bit 随机 `random.randint(0,1)`，多 bit `random.getrandbits(w)`

## 不采用：`cocotb_tools._pytest` 插件

官方警告 "API **will** change in breaking ways over the next release or two"。
其 fixture/marker（`hdl`、`cocotb_runner`、`cocotb_test`、`cocotb_timeout`）在插件
稳定前不进入生成模板；references/verification-policy.md 的分级已覆盖其报告价值。

## 仿真器适配备注

| 仿真器 | 备注 |
|---|---|
| Icarus | Windows 首选开源；VPI dll 随 cocotb wheel 分发 |
| ModelSim/Questa | `vsim` 在 PATH 且有 license；`questa` 支持 qrun 流程 |
| GHDL | VHDL 专用 top |
| Verilator | **2-state：X/Z 检测失效**，smoke 的 resolve 检查无意义；时序模型受限，v1 标 experimental，probe 到也不默认选 |
| Xcelium/VCS/Riviera/nvc | 商用/小众，runner 支持，参数透传 `build_args`/`elab_args` |
