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

要求 cocotb>=2.0（模板用 2.x API）。probe 退出码 2 = cocotb 缺失：向用户报告安装
命令，**等确认后**执行。Verilator 即使可用也不作为 smoke 默认（2-state，X/Z 检查失效）。

## Step 2 — 依赖闭包与端口

```text
python scripts/build_fileset.py --root <rtl_root>... --top <top> --output sim/<top>/fileset.json --json
python scripts/tb_extract_ports.py --rtl-root <rtl_root>... --top <top.name> --json > sim/<top>/ports.json
```

- 模块名只取 JSON `top.name`，禁止从文件名推导。
- VHDL top：extractor 仅支持 Verilog 系，agent 按 entity 手写同 schema ports.json
  （`{name, direction, width, signed, type}`；symbolic 宽度原样放字符串）。
- fileset 含 `+incdir+`/`+define+` 行 → 转入 design.json `includes`/`defines`。

## Step 3 — 生成与复核

```text
python scripts/gen_cocotb_skeleton.py --fileset-json ... --ports-json ... --out sim/<top> [--sim <name>] [--golden mod.fn]
```

生成后 agent 必须对照 RTL 复核并记入报告 `classification_assumptions`：
时钟判定、复位极性与同步/异步、symbolic width 端口、inout/unknown 未驱动端口。

## Step 4 — smoke

```text
cd sim/<top> && pytest -m smoke --junitxml=report.xml
```

必须在生成目录内运行（runner 把 pytest sys.path 传给仿真进程作 PYTHONPATH）。
失败先对照 `references/troubleshooting.md` 分类（timescale/路径/incdir/license），
只改 design.json/ports.json。

## Step 5 — functional

- **有 golden**：把真实测试向量流入 `test_<top>_functional.py` golden 槽位
  （驱动→等 latency→位精确比较）。禁止为 PASS 放宽断言或改 golden，
  除非有独立证据证明 golden 自身错误。
- **无 golden**：sub-agent 读 RTL/spec 填 characterization 测试，每个期望注明来源；
  结论上限「行为刻画」。

```text
cd sim/<top> && pytest -m functional --junitxml=report_func.xml
```

## Step 6 — 报告（Output contract）

固定字段，过程日志不得淹没结论：

DUT（top+path）/ Simulator+cocotb 版本 / Simulation directory / Highest gate reached /
Port classification assumptions / Verification basis（golden 路径或 RTL-only characterization）/
Execution：逐用例 PASS/FAIL，**以 `sim_build/*.result.xml` 为准**（pytest 单行摘要会
把整模块折叠成一行）/ Artifacts / Remaining issues。

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
