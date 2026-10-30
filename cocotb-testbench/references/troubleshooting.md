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
Windows 下尤其要区分“`vsim` 可执行文件在 PATH”与“license 可 checkout”：在启动
pytest 的同一 shell 检查 `LM_LICENSE_FILE`、`MGLS_LICENSE_FILE` 或 license-server 配置，
并确认 `where vsim` 指向预期版本。runner 继承 pytest 环境，不要把凭据写入 `design.json`。
若升级 cocotb 后只重跑了 Icarus，不能把结果写成 ModelSim/Questa 已验证；用目标版本先跑
一个最小 smoke，再扩大 functional。

**cocotb 2.x 标量输出报 `Logic` 没有 `.integer`**
标量端口的 `.value` 是 `Logic`，不能像 `LogicArray` 一样读取 `.integer`。先用
`.value.is_resolvable` 检查 X/Z；确认已解析后，多 bit 信号再读 `.integer`，有符号值用
`.to_signed()`。新模板已按此区分。

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
不要只看端口名：同时核对 reset 时序、valid/ready、frame/line 边界和 inout 驱动方向。

**RisingEdge 后读到旧的寄存器值 / 结果整体偏一拍**
这是 cocotb scheduler 采样区间问题的常见表现，不要先改 DUT。`RisingEdge` 后先
`await ReadOnly()`，再读取 registered output；同时核对 DUT 的 pipeline/RAM read latency。
若 Icarus 与 ModelSim 只在采样点不同，先统一 TB 调度和采样阶段再归因。

**signed 结果与参考模型相差 1 或多个 LSB**
确认 DUT 与 golden 的 signed/unsigned 扩展、负数除法语义（向零截断 vs floor）、右移语义、
overflow 和最终 truncation。不要用 `>>` 代替需要向零截断的 signed 除法，也不要为了 PASS
改 golden 或放宽断言；先用一个负数 directed case 固定语义。

**长工况墙钟远大于仿真时间（例：32.5 ms 仿真跑 980 s）**
先看 ratio：`results.xml` / 末尾 TEST 表的 `sim_time_ratio` 只有几十 µs/s 时，瓶颈通常
不是 RTL。首要嫌疑是 Python `Clock`——每半周期一次唤醒（本机 ≈20 µs/次），100 MHz 时钟
跑 32.5 ms 即 650 万次。修法：有 TB 包装层就把时钟挪进 SV `always`，Python 只
`RisingEdge` 等待；实测 vbw 980.5→78.0 s（12.6×）、套件 30+ min→129.9 s。无包装层的
单元级套件没有这个选项，改为事件/边界等待，减少逐沿轮询次数。

**单独跑绿、同一 `test_filter` 全跑红**
cocotb 把命中的用例放在同一仿真会话里顺序执行，仿真实例初值只给第一个用例。检查 TB
内跨用例共享状态：捕获数组与 `word_cnt`、图源使能（如 `tpg_en`）、配置快照、parser 游标。
在每个用例入口统一清零/复位（放 bring_up / setup），不要依赖初值。判据特征：失败用例的
SIM TIME 明显膨胀。实测：gige_video_ip 6 条一起跑时 scps/vbw 因 `word_cnt` 未清零与
`tpg_en` 残留假失败。

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

**参数已改但仿真仍像旧配置**
runner 的 `always_build=True` 默认避免生成器复用陈旧构建；若用户把它改为 false，或
使用外部 Makefile/缓存，必须按参数/宏/源文件 hash 隔离 `build_dir` 或显式清缓存。
不要仅凭“编译成功”判断参数已生效；在 smoke 日志或 result artifact 中记录实际参数。

**单测拆得过细导致 ModelSim 很慢或 license 被反复 checkout**
把同一 DUT、同一仿真会话可覆盖的 directed/boundary vectors 合并到一个 cocotb test，
保留逐向量断言和失败上下文。不要为了省几行 Python 让每个边界值启动一次 simulator。

## 版本兼容

| cocotb | 影响 |
|---|---|
| <1.8 | 无 `cocotb_tools.runner`，本 skill 不可用 |
| 1.8–1.9 | runner 在 `cocotb_tools`，但 `Clock.start()` 为协程需 `cocotb.start(...)` 包装——升级 2.x 或手工改测试 |
| 2.x | 目标版本；`verilog_sources`/`vhdl_sources` 弃用；新 TB 使用 `unit=`, `ReadOnly`, `LogicArray`, `task.cancel()` |
| 伴生包 | `cocotb-bus<2` 与 cocotb 2.x 冲突（pip 会警告）；用 cocotb 2.x 自带的 `cocotb_tools.*`/`cocotb.*` 总线扩展 |
