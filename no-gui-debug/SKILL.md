---
name: no-gui-debug
description: >-
  pw-gige 无 GUI 板级调试完整链路：不打开 Vivado Hardware Manager / Wireshark GUI，
  全程命令行完成「构建含 ILA 的比特流 → 烧板 → 抓波形 → 导出 CSV 分析」、
  「上位机 gige_cli 录帧/单帧 snap/原始 wire dump」、「dumpcap/tshark 网络抓包与
  逐包分析」三条证据链路，外加「打包 IP 交付件验证（package-ip/verify-ip、
  与平铺构建等价性、bit 溯源）」的采集、分析与对拍。用户提到：定位板上 bug、板级调试、
  ILA 抓波/看波形/看信号、上位机录帧/抓帧/拍快照/snap、tshark/抓包/pcap 分析、
  打包 IP/verify-ip 上板验证、烧错 bit/同名 bit、控制面全 PASS 但 GVSP 0 包、
  无 GUI 调试/命令行调试，或报告成像撕裂/花屏/丢帧/错位/帧率异常等设备侧异常
  需要定位时使用。核心价值：按症状路由到正确的证据链路，给出每条链路的采集
  命令、分析判据与实测坑清单，并把「sim 全绿、板上出错」的差异系统化为可
  复现的实验矩阵。深度绑定 pw-gige 仓库 tools/ 下的调试脚本（catch_ila.tcl、
  capture_frames.py 等）——脚本单一事实源在仓库，本 skill 只引用不复制。
---

# no-gui-debug — 无 GUI 板级调试三链路（+ 打包 IP 交付验证）

目的：板级 bug 定位的全部证据采集与分析都可在命令行完成。本 skill 回答
三个问题：**用哪条链路采证据**（决策树）、**命令怎么敲**（references 细节）、
**结果怎么判读**（对拍判据与方法论）。

## Non-goals

- 不复制仓库调试脚本进本 skill——单一事实源在仓库 `tools/`（防双份漂移）。
- 不写 GUI 操作流程（Wireshark GUI / Vivado Hardware Manager 只在对照时一句带过）。
- 不做寄存器/协议值的记忆性断言——查 `docs/register_map.md`、`docs/interfaces.md`。

## 前提与环境（本机实测）

| 项 | 值 |
|---|---|
| 仓库脚本 | pw-gige 仓库 tools/（catch_ila.tcl、catch_ar.tcl、catch_now.tcl、capture_frames.py、stream_and_catch.py、gvcp_cli.py、cc_board_check.py 等）。ILA 链脚本自 4d8fda3 起已在主线，直接在当前分支执行，不再需要 .worktrees/mig |
| Vivado | C:\Software\Xilinx\Vivado\2021.1\bin\vivado.bat（必须 .bat，无扩展名会解析到缺 DLL 的 unwrapped） |
| Python | C:/Software/Python/Python311/python.exe（pyserial + scapy 已装） |
| tshark/dumpcap | C:\Program Files\Wireshark\（4.6.9，不在 PATH，需全路径；dumpcap 抓包需管理员） |
| 上位机 CLI | gigev-host-demo build\vs2022-x64\src\cli\Release\gige_cli.exe（子命令全表见 references/host-capture.md） |
| 设备缺省 | IP 192.168.1.128:3956，GVSP host_port 由配流决定（仓库脚本缺省 49152）。**ICMP 已实现**（`rtl/net/icmp_echo.sv`）：`ping 192.168.1.128` 应通，**ping 不通 = 烧的是旧镜像**。代价：回包目的 MAC 不在 ARP 缓存时 `ip_arb_mux` 被占约 22 s（2s×4 次重试 + 16s 超时），期间 GVCP/GVSP/后续 ping 全停 |
| 板 | Kintex-7 Base（xc7k325tffg676-2），JTAG=FT232HL，调试串口 CH340E |
| 固件 | `BOOT_MODE_SELECT=0` ⇒ bit 里只有 bootrom，**每次 JTAG 重配/掉电后必须重传**（`cmd //c "make neorv32_upload PORT=COM6"`；bootrom 固定 19200、应用 115200，脚本自动切速；发 `h` 有菜单即台活着）。固件没跑 = MDIO 从不初始化 = GVCP 必然无应答；口径见 `docs/neorv32_firmware_build_uart.md` |

## 链路决策树（症状 → 链路 → 证据 → 判据）

| 症状/疑点 | 首选链路 | 证据类型 | 判据示例 |
|---|---|---|---|
| 内部握手卡死（valid/ready 无应答）、寄存器读写异常、时钟域活性 | **ILA 链** | 片内拍级波形（TX 计数/握手位/几何序号/loss 状态） | `mig_calib_done=1` 且 `mig_ui_rst=0`；good≥submit 无差；desc 握手数与 seq 自洽 |
| 成像撕裂/花屏/错位、需要完整帧或单帧字节级证据 | **上位机链** | 帧文件（RAW）+ 原始 wire dump + manifest | counter 图案值=帧内索引，逐字节对拍；manifest 连续无缺号 |
| 丢包/包序/重传/帧率/吞吐统计、网络层异常 | **tshark 链** | pcapng + 逐包字段导出 | Leader 间隔分布、每帧包数、block_id 连续性 |
| **控制面全 PASS 但 GVSP 0 包**；或上板的是**打包 IP 交付件** | **交付/前置分流**（先定 bit 来源，再谈现象） | bit 溯源（入口+日志标记+sha256）、打包核对与等价性、出流前提读数 | 见 references/ip-delivery-verify.md |
| 复杂 bug（一层证据说不清） | **多链路并行** | 交叉印证 | 见 references/methodology.md 的 MIG 撕裂案例 |

MIG 撕裂完整案例的链路组合（2026-09-27/28 实战）：tshark 抓包定性（发送侧
387fps 健康、撕裂在 payload 内容）→ 上位机对拍（counter=地址示踪器读出错位
偏移）→ ILA 定位（写侧自洽/读侧事务边界滞后）→ shim 源码 sim 洗清 →
补偿修复 + 三级复验。

## 执行不变量（每轮实验必须遵守）

1. **bit 溯源（mtime 不够用）**：先确认烧的 bit 出自哪条入口——`make build`
   （平铺，`build/top.bit`）与 `make verify-ip`（打包 IP，`build/ipverify/top.bit`）
   同名不同物；登记「入口 + 工程名 + 日志标记 + sha256」，再看 mtime 是否晚于 RTL。
   改了 RTL 忘重编、以及烧了另一条入口的 bit，是最高频的两类假结论来源。
2. **板/JTAG 状态先行**：每轮记录 program_jtag.tcl 输出（成功恰 1 行
   "OK  : JTAG programmed ..."）；板不可达 → 降级 sim 模式并在报告登记待验证
   清单，不无限等待硬件。
3. **实验串行**：Vivado 与 ModelSim 并行会撞 MIG IP 文件锁（error renaming
   ... permission denied）；撞了先 taskkill //F vivado.exe 与 hw_server.exe。
4. **区分证据层级**：事实（实测输出）/ 观察（数据现象）/ 推导（未直接验证）/
   未验证——报告与结论必须标注。
5. **构建三入口**（Git Bash 裸跑 make 必崩，msys64 缺 sh.exe；一律
   `cmd //c "make ..."` 或 cmd 直调 vivado.bat）：
   - 构建：`cmd //c "make build"`——`TOP` 缺省 `top`、`NEED_MIG` 缺省 1、
     `BOARD` 缺省 k7base；带 ILA 加 `DEBUG_ILA=1`（同时产出 top.bit + top.ltx）
   - 烧板：`cmd //c "make jtag"`（scripts/program_jtag.tcl）
   - 固件：`cmd //c "make neorv32_upload PORT=COM6"`
   - 含 IP 顶层不做 elaborate_check（synth_design 直调无法解析 IP OOC 产物），
     以 build 为准。

## 坑速查（全部实测踩过，细节见 references）

| 坑 | 一句话规避 |
|---|---|
| ILA 导出 CSV 空（只有表头） | wait_on_hw_ila 后必须 upload_hw_ila_data |
| TRIGGER_COMPARE_VALUE 报错 | 写成 eq1'b1 连写（eq 1'b1 会报 No apostrophe） |
| set_property 参数顺序 | PROP VALUE OBJ，value 在 obj 前 |
| CONTROL.CAPTURE_MODE | 只读属性，不设置 |
| .ltx 未关联 | set_property PROBES.FILE 后 refresh_hw_device |
| ILA-FREQ 读 0 | 静态属性不可靠，以 STATUS.CORE_STATUS/SAMPLE_COUNT 为准 |
| elaborate_check 含 IP 顶层 | module not found——用 build |
| Git Bash 裸跑 make | msys64 缺 sh.exe——cmd //c 直调 vivado.bat |
| gige_cli discovery 超时 | 先 `gige_cli nic` 枚举 + `Get-NetAdapter` 看 Status：期望业务口缺席/Disconnected 属物理链路，先查线再换网卡；--nic 序号显式指定，且插拔后序号会漂移 |
| capture_frames 组装 0 完整帧 | GVSP pid 在头 bytes[6:8]（不是 5:7）；先裸收后组装；SO_RCVBUF 32MB |
| dumpcap 权限 | 权限不足才提权；本机实测非管理员可直接抓；不在 PATH 用全路径 |
| 后台复合命令变量为空 | `a && V=x && cmd &` 整链进 subshell，前台 $V 为空——固定文件名或分两次调用 |
| `rst -system` 两条路都不通 | Vivado hw-manager Tcl 无 `reset_hw_target`、xsdb `rst -system` 报 `Invalid reset type`（K7+FT2 实测）；替代 = 重烧 bit + 固件重传 + 开流前写 `SCP0=0`，并在报告登记「未做系统软复位」 |
| `0xA014` 读回报错 | APPLY 是**只写**邮箱，读回必拒属设计；生效判据看 `CONFIG_STATUS.busy` 清零 |
| 批量 READREG 串位 | 多地址一次读会串位/回陈旧值，别据此判「写序列错位」；一律单字逐读再对设计缺省值 |
| 控制台/工具输出乱码 | Git Bash 按 GBK 解码设备输出，乱码行不是读数现场；判据用数字/正则抽取后再下结论 |

## 工作流（按链路展开）

1. **ILA 链**（构建→烧板→抓波→CSV 分析、触发条件选择、探针表）：
   读 references/ila-workflow.md。
2. **上位机链**（gige_cli 全子命令、capture 语义、snap、wire dump、
   capture_frames.py 对拍）：读 references/host-capture.md。
3. **tshark 链**（dumpcap 采集、tshark 字段导出、scapy 逐包重建、**帧率 bug
   双端同窗分流**——§6 先做这个再谈根因）：读 references/tshark-workflow.md。
4. **打包 IP 交付验证**（bit 溯源、打包核对四件套、与平铺构建的等价性判据、
   OOC/参数/观测面坑、0 包分流顺序）：读 references/ip-delivery-verify.md。
5. **方法论**（多链路组合、地址示踪器、sim 全绿板上错的差异清单、修复闭环）：
   读 references/methodology.md。
6. **脚本索引**（tools/ 脚本→功能映射，单一事实源说明）：
   读 scripts/README.md。

## 交付纪律

- 排查报告落 .planning/<日期>-<主题>-debug.md：结论速览 → 症状 → 排除项 →
  根因（机制+证据）→ 修复 → 验证（sim/板上/主机三级）→ 遗留与下一步。
- 修复留工作区不 commit，等用户验收（用户明示后按 Conventional Commits 提交）。
- 关键流程沉淀为仓库文档（如 docs/k7_base/ila_debug_workflow.md），skill 只引用。
