# 故障排查

主 SKILL.md 只保留通用失败原则（缺失 / 歧义 / 编译失败 / 仿真失败 / 验证依据不足）。本文件收录厂商与环境特定问题。

## License

| 现象 | 处理 |
|------|------|
| `vsim license checkout failed` / `Invalid license environment` | Makefile 中设置 `export LM_LICENSE_FILE=<路径>` |
| MSYS2/Git-Bash make 不继承 Windows 系统环境变量 | **根因**：Windows 系统级环境变量（System Properties 设置）不会自动转发给 MSYS2/Git-Bash 子进程。
  **修复（Step 2 已自动化）**：在生成 Makefile 前，通过 PowerShell 读取系统级变量并明文写入 Makefile：
  ```powershell
  $LicensePath = powershell -Command "[Environment]::GetEnvironmentVariable('LM_LICENSE_FILE', 'Machine')"
  if (-not $LicensePath) { $LicensePath = powershell -Command "[Environment]::GetEnvironmentVariable('LM_LICENSE_FILE', 'User')" }
  ```
  将获取到的值替换 Makefile 中的占位符 `export LM_LICENSE_FILE = <YOUR_LICENSE_FILE_OR_LICENSE_SERVER>`。
  路径分隔符保持原样即可。 |

## 厂商 IP

| 现象 | 处理 |
|------|------|
| Efinix FIFO 等可选端口悬空产生 `TFMPC` / `vopt-2718` warning | 不影响功能仿真，**不要修改 IP 文件**，可忽略 |
| 厂商 IP 端口不匹配 | 检查 IP 版本与 RTL 实例化是否一致，不改 IP |

## VHDL / 混合语言

| 现象 | 处理 |
|------|------|
| VHDL component 未绑定 | 从工程脚本 / 既有仿真流程补齐真实模型到 `fileset.f`，不能只按文件名排序 |
| Verilog 调用 VHDL 模块 | 确保双方都在扫描路径内（`--root` 参数） |
| `include` 文件未找到 | 补 `+incdir+<workspace_root>`，**不要改 DUT include** |

## 编译 / 仿真

| 现象 | 处理 |
|------|------|
| `file not found` 但路径看起来对 | fileset 条目相对于 workspace 根；Makefile/sim.do 必须以 `../..` 为前缀 |
| L1 编译失败 | 先修复路径 / 依赖 / 模板，**不能转称 L2** |
| 仿真超时 / X 扩散 | 检查复位极性、时钟名检测、未驱动输入是否拉 0 |
| workspace 根扫描很慢 | 扫描范围扩大后的预期行为，不是 bug |

## 找不到 `.git`

停止，要求用户确认 workspace 根。不要把 RTL 所在子目录默认为 workspace 根。
