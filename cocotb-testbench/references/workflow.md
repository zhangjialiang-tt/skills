# 工作流细则（SKILL.md 的展开）

## Inputs 契约

| 输入 | 说明 | 默认 |
|------|------|------|
| `top` | workspace-relative RTL 文件路径（推荐）或模块名 | 从用户明确提到的 RTL 解析 |
| `level` | `smoke` / `functional` | `smoke` |
| `simulator` | runner 仿真器名（icarus/questa/modelsim/ghdl/xcelium/vcs/nvc…） | 探测后取可用项 |
| `golden_model` | `"python_module.function"` | 探测工作区候选，无则空 |
| `parameters` | 参数覆盖 | RTL 默认值 |
| `existing_sim_policy` | `reuse` / `update` / `create_new` | `reuse` |

未指定 top 且多个同名候选 → 停止自动选择，输出候选清单（caller、语言、路径）。

## Step 1 — 环境探测

```text
python scripts/workspace_root.py --start <rtl_file_or_dir>   # 无 .git 即停，不以 RTL 子目录为根
python scripts/probe_env.py                                   # JSON：python/cocotb/pytest/仿真器 PATH 可用性
```

要求 cocotb>=2.0（模板用 2.x API）。probe 退出码 2 = cocotb 缺失或版本不兼容：向用户报告安装/升级
命令，**等确认后**执行。Verilator 即使可用也不作为 smoke 默认（2-state，X/Z 检查失效）。

Windows + ModelSim/Questa 额外做一次环境预检：确认 `vsim` 来自预期安装、当前 shell
能看到 `LM_LICENSE_FILE`/`MGLS_LICENSE_FILE` 或等价 license-server 配置，并让 runner
继承该环境。`vsim` 在 PATH ≠ license 可用；license checkout 失败应停在 E0，不修改 DUT。
升级 cocotb 或切换 simulator 后，必须用目标 simulator 重新跑最小 smoke；Icarus PASS
不能转移为 ModelSim/Questa 证据。

## Step 2 — 依赖闭包与端口

```text
python scripts/build_fileset.py --root <rtl_root>... --top <top> --output sim/<top>/fileset.json --json
python scripts/tb_extract_ports.py --rtl-root <rtl_root>... --top <top.name> --json > sim/<top>/ports.json
```

- 模块名只取 JSON `top.name`，禁止从文件名推导。
- VHDL top：extractor 仅支持 Verilog 系，agent 按 entity 手写同 schema ports.json
  （`{name, direction, width, signed, type}`；symbolic 宽度原样放字符串）。
- fileset 含 `+incdir+`/`+define+` 行 → 转入 design.json `includes`/`defines`。
- 复核 interface contract：同步/异步 reset、valid/ready、frame/line 边界、注册输出采样点、RAM 读延迟、signed/unsigned 与位宽；这些不能靠端口名称启发式决定。

## Step 3 — 生成与复核

```text
python scripts/gen_cocotb_skeleton.py --fileset-json ... --ports-json ... --out sim/<top> [--sim <name>] [--golden mod.fn]
```

生成后 agent 必须对照 RTL 复核并记入报告 `classification_assumptions`：
时钟判定、复位极性与同步/异步、symbolic width 端口、inout/unknown 未驱动端口、
registered output 的 `ReadOnly` 采样点、运算截断/舍入、RAM/ready-valid latency。
模板只使用 cocotb 2.x API：`Clock(..., unit="ns")`、`LogicArray`/`to_signed()`、
`task.cancel()`；不要重新引入 1.x 的 `units=`、`BinaryValue` 或 `task.kill()`。
若套件要加 TB 包装层（分层拓扑、自带激励源），**时钟由 SV `always` 生成**、Python 只
`RisingEdge` 等待（SKILL.md 性能原则 1）；生成的单元级用例保持在 setup 里复位共享状态
（性能原则 2）。

## Step 4 — smoke

```text
cd sim/<top> && pytest -m smoke --junitxml=report.xml
```

必须在生成目录内运行（runner 把 pytest sys.path 传给仿真进程作 PYTHONPATH）。
失败先对照 `references/troubleshooting.md` 分类（timescale/路径/incdir/license/采样/缓存），
只改 design.json/ports.json；若错误来自 DUT、测试、golden 或 simulator，先归因再改，
不得通过删除断言、放宽比较或修改 golden 获得 PASS。

## Step 5 — functional

- **有 golden**：把真实测试向量流入 `test_<top>_functional.py` golden 槽位
  （驱动→按协议/流水线/RAM latency 等待→`ReadOnly` 采样→位精确比较）。
  负数除法必须明确是向零截断还是 floor，不能用右移悄悄替代 signed 除法；比较前确认
  输出宽度、符号扩展、overflow/truncation 与 golden 相同。禁止为 PASS 放宽断言或改 golden，
  除非有独立证据证明 golden 自身错误。
- **无 golden**：sub-agent 读 RTL/spec 填 characterization 测试，每个期望注明来源；
  结论上限「行为刻画」。

```text
cd sim/<top> && pytest -m functional --junitxml=report_func.xml
```

## Step 6 — 报告（Output contract）

固定字段，过程日志不得淹没结论：

DUT（top+path）/ Simulator+simulator version+cocotb 版本 / Simulation directory /
Highest gate reached / Port classification assumptions / Verification basis（golden 路径或
RTL-only characterization）/ Execution：逐用例 PASS/FAIL，**以 `sim_build/*.result.xml` 为准**
（pytest 单行摘要会把整模块折叠成一行）/ Artifacts / Remaining issues。
商业 simulator 启动和 license checkout 有固定开销：同一会话合并 directed/boundary vectors，
不要把每个值拆成独立仿真进程；这只是效率优化，不改变逐用例记录。

## Failure policy

| 失败类型 | 处理 |
|---|---|
| cocotb/仿真器缺失 | 报告缺失项+安装命令，等确认 |
| build 失败 | 修 design.json；见 troubleshooting 分类表 |
| 端口分类错 | 修 ports.json 重新生成，报告记录修正 |
| functional 失败 | 区分 DUT/测试/环境归因；不默认改期望 |
| 生成目录已存在 | 按 existing_sim_policy；冲突备份/改名并报告 |

## Directory contract

`sim/<top>/`：`fileset.json` / `ports.json` / `design.json`（单一事实来源，可手改）/
`tb_runner.py` / `conftest.py` / `test_<top>_smoke.py` / `test_<top>_functional.py` /
`sim_build/`（自动 gitignore）/ `report*.xml`。
