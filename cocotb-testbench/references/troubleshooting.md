# 跨平台排障（含本 skill 实测踩坑）

## 构建期

**`Bad 'period': Unable to accurately represent 10(ns) with the simulator precision of 1e0`**
RTL 无 `` `timescale `` 时仿真器默认精度 1s。修复：`design.json["timescale"] = ["1ns","1ps"]`
（生成器已默认注入；若 RTL 自带更细精度 directive，按需调整该字段）。*实测：Windows+Icarus13 复现并验证修复。*

**`Unable to find the root module "x"` / 源文件 No such file**
`build_fileset` 输出相对**扫描根**的路径，runner 按 pytest cwd 解析。生成器已绝对化
（多 root 逐个探测存在性）。仍出现时检查 `design.json["sources"]` 是否指向真实文件，
常见于 fileset 含 `+incdir+`/`+define+` 行——手工转入 `includes`/`defines` 并从
`sources` 删除。

**`iverilog -g2012` 报 syntax error**
RTL 用了 SystemVerilog 2017+ 特性（如 `always_ff`）；在 `build_args` 加
`["-g2017"]` 或换 Questa/Xcelium。

**license 类失败（Questa/ModelSim/Xcelium/VCS）**
probe_env 只看可执行文件，license 错误在 build 阶段暴露：报告原日志，不猜测参数。

## 运行期

**pytest PASS 但怀疑测试没跑**
核对 `sim_build/<test_module>.result.xml` 的逐用例记录。runner 在 pytest 下自动改写
`COCOTB_RESULTS_FILE`，不要设 `results_xml` 参数。

**仿真进程 `ModuleNotFoundError: tb_runner`**
没有从 `sim/<top>/` 目录内运行 pytest（sys.path 未含该目录）。cd 进目录再跑。

**复位后输出仍 X**
两种合法解释：DUT 真缺陷（记录 FAIL 归因 DUT）或 smoke 的 `SETTLE_CYCLES` 小于流水深度。
先看波形/日志确认，再调 `SETTLE_CYCLES`，不许反过来删断言。

**端口极性/方向错误**
名称启发式（`CLK_RE`/`RST_RE`/`_n` 后缀）必然有例外：同步复位、高有效 `_n` 命名、
双向总线。修 `ports.json` 或用例内代码，并在报告 `classification_assumptions` 记录。

## 环境

**Windows**
- cocotb wheel 自带 GPI dll，无需编译；Icarus 用 bleyer 安装包并加 PATH。
- 混合 MSYS2/Git-Bash/PowerShell 时以 `where`/`shutil.which` 实测 PATH 为准；
  不再依赖 make——本 skill 的 runner 路线即为此痛点（cocotb+make 需 MSYS2 bash）而选。

**Linux CI**
- `apt install cocotb` 缺失时 pip 装；Icarus/GHDL 走发行版包。
- JUnit 汇聚：pytest `--junitxml` + `sim_build/*.result.xml` 两层都收。

**Verilator**
- 2-state：X 检查恒「干净」，smoke 语义失效；`value` 读回无 LogicX。
- 仅作 functional 快速回归用，不作 smoke 证据；需 `--timing` 支持延迟类测试。

## 版本兼容

| cocotb | 影响 |
|---|---|
| <1.8 | 无 `cocotb_tools.runner`，本 skill 不可用 |
| 1.8–1.9 | runner 在 `cocotb_tools`，但 `Clock.start()` 为协程需 `cocotb.start(...)` 包装——升级 2.x 或手工改测试 |
| 2.x | 目标版本；`verilog_sources`/`vhdl_sources` 弃用 |
| 伴生包 | `cocotb-bus<2` 与 cocotb 2.x 冲突（pip 会警告）；用 cocotb 2.x 自带的 `cocotb_tools.*`/`cocotb.*` 总线扩展 |
