---
name: build-testbench
description: 为 Verilog/VHDL RTL 模块搭建 ModelSim/QuestaSim 仿真框架（L1 smoke + L2 功能验证）。用户提到搭建仿真、创建 testbench、生成 Makefile、建立 sim 目录、验证 RTL 模块时使用。支持 ANSI 和 Verilog-2001 端口声明风格。从 workspace 根目录（含 .git）扫描 RTL 依赖闭包，生成 sim/subx-modulename/ 结构。L1 自动生成时钟/复位/smoke TB；L2 需 sub-agent 分析 RTL 功能、生成 simulation_plan.md 和 checker TB，逐 testcase 报告 PASS/FAIL。
---

# Build Testbench — ModelSim 仿真框架编排器

为指定 RTL top 创建可重复运行的 ModelSim/QuestaSim 仿真工程，提供 L1 可运行性验证和 L2 功能验证。不修改 DUT 算法。

## Non-goals

修改 DUT 算法；根据编译成功宣称功能正确；静默选择同名依赖；从 RTL 自证产品需求正确；覆盖用户已有仿真框架（冲突时备份/改名）。

## Inputs and defaults

| 输入 | 说明 | 默认 |
|------|------|------|
| `top` | workspace-relative RTL 文件路径（推荐）或模块名 | 从用户明确提到的 RTL 解析 |
| `level` | `l1` / `l2` | `l1` |
| `simulator` | 目标仿真器 | `modelsim` |
| `parameters` | 符号参数覆盖，如 `DW=16` | 从 RTL parameter 默认值 |
| `existing_sim_policy` | `reuse` / `update` / `create_new` | `reuse` |
| `specification_sources` | spec/golden/reference 路径列表 | `[]`（影响 L2 分类） |

未指定 top 时从用户明确提到的 RTL 文件解析；存在多个同名 top 时**停止自动选择**，输出候选。

## Execution invariants

1. `top` 必须使用 workspace-relative 文件路径，避免历史版本同名模块歧义
2. **模块名必须来自 `build_fileset.py --json` 的 `top.name`，禁止从文件名推导**
3. 不允许静默解决依赖歧义——暴露候选、caller、语言、路径
4. L2 前必须通过 L1 编译和 elaboration 门禁
5. L1 PASS 不代表功能正确；仅从 RTL 推导期望的 L2 属于行为刻画（L2-C）
6. 不覆盖已有用户文件；冲突时备份/改名并报告
7. 每阶段必须保存命令、日志和结果
8. 完成声明必须与证据等级一致（见 Stage gates）

## Level routing

| 用户意图 | 执行级别 |
|---|---|
| 搭建框架 / 确认编译运行 / smoke test | L1 |
| 验证功能 / 设计 testcase / 检查输出正确性 | L2 |
| 用户明确指定 | 按指定 |
| 未说明且无框架 | 先 L1 |
| 要求完整验证但 L1 未通过 | 先完成 L1 再 L2 |

L2 是 L1 之上的增量，不允许跳过 L1 编译和 elaboration 门禁。

## Workflow

### Step 1：Resolve request（冻结运行上下文）

定位 workspace 根，冻结本次任务的输入契约（见上表）：

```powershell
$WorkspaceRoot = python .pi\skills\build-testbench\scripts\workspace_root.py --start <rtl_file_or_dir>
```

找不到 `.git` 时停止，不要把 RTL 子目录默认为 workspace 根。安装方式见 `docs/installation.md`。

### Step 2：Bootstrap framework（解析依赖、提取模块名、建目录、注入 license）

**关键：模块名来自脚本输出，不从文件名推导。** 先跑依赖解析：

```powershell
$FilesetJson = python .pi\skills\build-testbench\scripts\build_fileset.py `
  --root $WorkspaceRoot `
  --top <workspace-relative-rtl-path> `
  --output "$WorkspaceRoot\sim\$SimSubDir\fileset.f" `
  --json
```

从 JSON 的 `top.name` 读取**权威模块名**用于目录命名和后续步骤。检查 JSON 的 `diagnostics`（path proximity / path priority / language 选择），不要静默接受错误候选。

**⚠️ License 注入（Windows/MSYS2 必做）**：
在写入 Makefile 之前，通过 PowerShell 读取 Windows 系统级 `LM_LICENSE_FILE`，
将其明文写入 Makefile 的 `export LM_LICENSE_FILE = ...` 行。

```powershell
$LicensePath = powershell -Command "[Environment]::GetEnvironmentVariable('LM_LICENSE_FILE', 'Machine')"
if (-not $LicensePath) {
    $LicensePath = powershell -Command "[Environment]::GetEnvironmentVariable('LM_LICENSE_FILE', 'User')"
}
if (-not $LicensePath) {
    Write-Warning "LM_LICENSE_FILE not found in Windows env. Makefile will use placeholder. Update manually."
}
```

路径分隔符保持原样（`;` 分隔的多路径即可），无需转义。
此举解决 MSYS2/Git-Bash 子进程不继承 Windows 环境变量导致的
`Invalid license environment` 错误。

序号计算（无歧义，可用 PowerShell）：

```powershell
$MaxIndex = 0
Get-ChildItem -Path "$WorkspaceRoot\sim" -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^sub(\d+)-' } |
    ForEach-Object { $Idx = [int]$Matches[1]; if ($Idx -gt $MaxIndex) { $MaxIndex = $Idx } }
$NextIndex = $MaxIndex + 1
$SimSubDir = "sub${NextIndex}-$ModuleName"   # $ModuleName 来自 build_fileset 的 top.name
```

创建 `sim/sub{x}-{modulename}/` 下 `tb/ data/ scripts/ log/` 子目录。`fileset.f` 条目相对 workspace 根；Makefile/sim.do 以 `../..` 为 workspace root 前缀。

依赖选择顺序：版本/项目路径前缀 → 已知共享 IP 路径 → HDL 语言匹配 → root priority → 失败。详见 `scripts/README.md`。

### Step 3：Inspect diagnostics

检查 `build_fileset` 的 `diagnostics`、`summary.unresolved_dependencies`。有未解析项时暴露完整候选列表，不猜测。VHDL component / 厂商 IP / `include` 可能不在正则闭包内，需从工程脚本补进 `fileset.f`（见 `references/troubleshooting.md`）。

### Step 4：Run L1

提取端口、生成 L1 TB、生成 Makefile/sim.do/wave.do，然后编译仿真。端口提取与 L1 TB 生成详见 `references/l1-generation.md`，模板见 `assets/Makefile.template`、`assets/sim.do.template`、`assets/wave.do.template`。

```powershell
Set-Location "$WorkspaceRoot\sim\$SimSubDir"
make compile
make l1
make wave
```

L1 日志必须出现 `[SIM_RESULT] L1 PASS`。L1 是 smoke test，不证明算法/时序/边界正确。

### Step 5：Optionally plan and run L2

L2 流程：分析 → （风险驱动）确认 → 生成 → 验证。**完整规则见 `references/l2-planning.md`**，计划模板见 `references/l2-plan-template.md`，TB 结构见 `references/l2-tb-template.v`。

要点：
1. 启动 Explore sub-agent 读 DUT RTL，判定 **L2-C（行为刻画）vs L2-V（功能验证）**，按模板生成 `data/simulation_plan.md`
2. **风险驱动确认**：仅在期望只能从 RTL 猜测 / 接口多种解释 / 缺关键参数 / 固化产品判断 / 用户要求时暂停；spec/golden/reference 明确或复现已确认计划时自动继续
3. 用户确认（或满足自动继续条件）后生成 `tb/tb_<top>_l2.v`，每个 testcase 对应一组 driver + checker
4. 编译仿真，逐 testcase 报告 PASS/FAIL

```powershell
make compile
make l2
```

L2-C（期望仅来自 RTL）报告 `[SIM_RESULT] L2 PASS (characterization)`，**禁止**宣称功能正确。
L2-V（有独立 spec/golden/reference）才允许报告 `[SIM_RESULT] L2 PASS (verification)`。

### Step 6：Switch default level & report（L2 通过后）

**不修改主 Makefile**。L2 通过后只写独立配置文件 `config.mk`（模板见 `assets/config.mk.template`），把 `DEFAULT_LEVEL` 切为 `l2`，然后 `make clean && make sim` 验证默认配置已切到 L2。主 Makefile 始终不变，`make l1` / `make l2` / `make sim` 三个稳定 target 永久可用。

最后按 Output contract 和 Stage gates 允许的措辞发报告。

## Stage gates（执行状态机）

按层级报告，**禁止跨级宣称完成**：

| 当前最高状态 | 允许的报告 |
|---|---|
| REQUEST_RESOLVED | 已冻结运行上下文 |
| FRAMEWORK_READY | 已生成仿真框架（目录/文件就位） |
| DEPENDENCIES_RESOLVED | 依赖闭包已解析 |
| COMPILE_PASS | 编译与 elaboration 通过 |
| L1_PASS | L1 smoke PASS |
| L2_PLAN_READY | L2 计划已生成（含 L2-C/L2-V 标注） |
| L2_PASS (characterization) | 行为刻画 PASS |
| L2_PASS (verification) | 功能验证 PASS |

只生成文件、端口解析成功或 compiler error 为 0，不能称为 L1/L2 仿真通过。

## 完成门禁（两组分离）

### Skill 自身健康检查（仅修改脚本/模板后运行）

```text
python -m py_compile scripts/*.py
pytest tests/
python scripts/validate_skill_package.py    # 检查 SKILL.md 引用路径都存在
```

### 本次仿真任务验收（每次运行）

```text
dependency resolution (build_fileset diagnostics)
compile (make compile)
elaboration
L1 run ([SIM_RESULT] L1 PASS)
L2 testcase results (逐 case，[SIM_RESULT] L2 PASS/FAIL)
default-level state (config.mk，L2 通过后)
```

不要因为没有执行 Skill 自带 pytest 就认为用户的仿真框架未完成。

## Failure policy（通用原则）

| 失败类型 | 处理 |
|---|---|
| 缺失（找不到 `.git` / 依赖 / include） | 停止，要求确认或补全，不猜测 |
| 歧义（同名依赖 / 多 top） | 暴露候选、caller、语言、路径，不静默选择 |
| 编译失败 | 先修路径/依赖/模板，L1 未过不得转称 L2 |
| 仿真失败（超时/X 扩散/协议违规） | 报告现象，DUT 问题还是 TB 问题由用户判断 |
| 验证依据不足（L2 仅 RTL 推导） | 标记 L2-C，不得宣称功能正确 |

厂商特定问题（license / Efinix IP warning / VHDL component 绑定 / MSYS2 env）见 `references/troubleshooting.md`。

## Output contract

报告固定字段（避免过程描述淹没结论）：DUT（path + module_name）/ Simulation directory / Requested level / Highest completed（Stage gates 状态）/ Dependency resolution（sources count + unresolved + ambiguous）/ Execution（Compile / L1 / L2 分类）/ Verification basis（L2-C|L2-V + independent evidence 路径或 "RTL-only"）/ Artifacts（fileset.f / ports.json / Makefile / config.mk / tb_*.v / simulation_plan.md / log/*.log）/ Remaining issues。

措辞必须与 Stage gates 允许的等级一致。

## 目录契约

`sim/sub{x}-{modulename}/`：`Makefile`（生成后不改）/ `config.mk`（可选，L2 通过后写入）/ `fileset.f` / `ports.json` / `tb/` / `data/`（输入、golden、simulation_plan.md）/ `scripts/`（sim.do、wave.do、checker）/ `log/`。序号 `x` 全局递增；`modulename` 来自 `build_fileset` 的 `top.name`；已有内容不得无确认覆盖。
