# scripts/ — 设计决策与脚本索引

## 设计决策：不复制仓库调试脚本

本 skill 刻意不放任何可执行脚本副本。原因：

1. **单一事实源**：调试脚本（catch_ila.tcl、capture_frames.py、stream_and_catch.py
   等）live 在 pw-gige 仓库 `tools/`，与 RTL/约束同仓库演化（探针名、参数、
   板级地址都会随集成变化）。复制一份进 skill 必然漂移。
2. **skill 引用、仓库执行**：本 skill 的价值是**路由与判读**（哪条链路、什么
   判据、哪些坑），执行动作永远落到仓库脚本——脚本改进自动生效。

## tools/ 脚本 → 功能映射

| 脚本 | 功能 | 典型调用 |
|---|---|---|
| `tools/catch_ila.tcl` | ILA 抓波（默认循环 3-5 次，core_arvalid 触发） | cmd //c vivado.bat ... -source tools/catch_ila.tcl |
| `tools/catch_now.tcl` | ILA 立即抓波（无触发条件——链路活性/时钟域判活） | 同上 |
| `tools/catch_ar.tcl` | ILA 抓波（core_arvalid 触发版） | 同上 |
| `tools/capture_frames.py N` | GVCP 配流 + UDP 收 N 帧落盘 frames.bin（对拍输入） | python tools/capture_frames.py 4 |
| `tools/stream_and_catch.py` | 仅配流开流（保持 30s 自动关；供 ILA 并行抓波） | python tools/stream_and_catch.py |
| `tools/gvcp_cli.py` | 交互式 GVCP host（Discovery/ReadReg/WriteReg/CCP/Heartbeat/配流，--auto 自动化） | python tools/gvcp_cli.py 192.168.1.128 |
| `tools/gvcp_discover.py` | 单发 Discovery 活性探针（3 轮） | python tools/gvcp_discover.py |
| `tools/cc_board_check.py` | 切档 + 收流核对（几何/帧率容差），自动开关流 | python tools/cc_board_check.py capture 0 8 |

注意：`catch_ila.tcl` 现按 `dbg_loss_event` 触发、循环 3 次导出；`catch_now` 为立即
捕获变体；`catch_ar.tcl` 仍按 `core_arvalid` 过滤，但该信号已并入 probe4 位段，
触发会静默退化成立即捕获（细节见 references/ila-workflow.md §4）。

## 交付件打包/验证脚本（仓库 `scripts/`，非 tools/）

| 脚本 | 功能 | 典型调用 |
|---|---|---|
| `scripts/package_ip.tcl` | 打包交付 IP（`gige_vision_ip_wrap`）→ `build/ip_pack/pkg` | cmd //c "make package-ip" |
| `scripts/verify_packaged_ip.tcl` | 独立工程 `pw_gige_ipverify` 从 IP repo 取交付件全流程构建 → `build/ipverify/top.bit` | cmd //c "make verify-ip" |
| `scripts/customer_bd_add_ip.tcl` | 客户 BD 加 IP + validate + 综合（交付件能否被客户工程吃下） | cmd //c "...vivado.bat -source scripts/customer_bd_add_ip.tcl" |
| `tools/package_delivery.py` | 交付物清单核对 | python tools/package_delivery.py |

判据与坑见 references/ip-delivery-verify.md（bit 溯源、等价性、OOC 限制）。

## 上位机侧（不在本仓库）

`gigev-host-demo\build\vs2022-x64\src\cli\Release\gige_cli.exe`（子命令全表见
references/host-capture.md）；抓包分析用系统 Python + scapy（管线见
references/tshark-workflow.md §4）。

## 若要新增调试脚本

放仓库 `tools/`（命名 `catch_<对象>.tcl` / `gvcp_<功能>.py` / `<动作>_<对象>.py`），
文件头注释写三段式：用途 / 用法 / 前提；然后把一行映射加进上表。
