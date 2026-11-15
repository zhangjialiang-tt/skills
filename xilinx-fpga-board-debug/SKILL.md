---
name: xilinx-fpga-board-debug
description: >-
  Use when 需要对 Xilinx/AMD FPGA 做无 GUI 板级调试或板测执行：上板验证/烧 bit/JTAG
  下载/hw_server 连接、软核固件 UART 上传、串口控制台无输出、板测执行链（构建→烧板→
  固件→连通性→功能用例→证据登记）、bit 溯源/同名 bit/烧错镜像、Vivado batch 退出码
  假成功、监督服务或后台 shell 跑 make、rst -system 不可用、ILA 抓波导出、时序报告
  判读（WNS/WHS）、控制面 PASS 但数据面 0 包的分流、遗留缺陷 vs 改动回归的 A/B 归因。
  通用 Xilinx 层（7 系列 + Vivado 2021.x 基准）；深度项目实例与三链路细节见同库
  no-gui-debug 技能。
---

# xilinx-fpga-board-debug — Xilinx FPGA 无 GUI 调试与板测（通用层）

目的：Xilinx FPGA 板测/调试的全部命令行操作按一条**可登记、可复核**的链路执行。
本技能回答三个问题：**板测按什么顺序跑**（执行链）、**命令怎么敲才可信**
（退出码/产物复核纪律）、**结果怎么判读登记**（时序/覆盖面/A-B 归因）。

**与 no-gui-debug 的分工**：本技能是通用层（任何 Xilinx 项目适用）；深度项目
实例——ILA/上位机/tshark 三条证据链路、脚本绑定、地址示踪方法论——在同库
`no-gui-debug`（pw-gige GigE Vision 实测）。两处共有的坑以实例技能为单点深化，
本表只保留通用行，防双份漂移。

## 前提与环境（模板；基准列 = K7 xc7k325t + Vivado 2021.1 + Windows 实测）

| 项 | 基准（本机实测） | 项目适配 |
|---|---|---|
| Vivado | 必须用 `vivado.bat`（无扩展名 vivado 会解析到缺 DLL 的 unwrapped）；batch 参数 `-mode batch -nojournal -nolog -notrace` | 版本/安装路径 |
| hw_server | 自动拉起，但 3121 端口易被本机代理进程抢占（Socket bind error）→ 先 `hw_server.bat -stcp::3122` 再 `connect_hw_server -url localhost:3122` | 端口 |
| shell | msys64 Git Bash 缺 sh.exe → `cmd //c "make ..."`；omp 内置 bash 5.3 自带 sh/coreutils，可直跑 `cd <msys 路径> && make`（cd 用 `/c/...` 形式，`C:/` 盘符形式会被吃掉） | — |
| 串口 | 软核 bootrom 引导常见双速：bootrom 低波特率（如 19200）、应用高波特率（如 115200），上传工具自动切速；`发 h 有菜单` = 固件活着 | PORT/波特率 |
| 设备 | IP/端口/发现协议【项目自定】；ping 不通 ≠ 板坏——先查烧的 bit（旧镜像可能没有 ICMP 等能力），再查 ARP/防火墙 | — |

## 板测执行链（顺序即不变量；跳步必须在报告登记）

1. **构建**：退出码显式回显——`make build > logs/build.log 2>&1; echo BUILD_EXIT=$?; tail -N logs/build.log`。**禁止 `make ... | tail`**（管道退出码被 tail 吃成 0，假成功实锤：exit 0 但 bit 未产出）。产物复核：`.bit` mtime 必须晚于会话开始。
2. **bit 溯源**：登记「入口 + 工程名 + 日志标记 + sha256」。同名不同物：`make build`（平铺 `build/top.bit`）vs `make verify-ip`（打包 IP `build/ipverify/top.bit`）。改了 RTL 忘重编、烧了另一入口的 bit = 最高频的两类假结论来源。
3. **烧板**：`program_hw_devices` 成功恰一行 `OK : JTAG programmed ...`，原文登记；bit 有多入口时先核对 `PROGRAM.FILE` 指向。
4. **（软核）固件重传**：bootrom 引导类设计每次 JTAG 重配/掉电后**必须重传**（bit 里只有 bootrom，固件不固化）。固件没跑 = 外设从不初始化 = 控制面必然无应答。纯 RTL 项目跳过此步。
5. **软复位（通常做不了，按替代流程）**：batch hw Tcl **没有 `rst`/`xreset`**（`info commands *rst*` 枚举实证）；xsdb `rst -system` 报 `Invalid reset type`；且 PROGRAM_B 类复位从 **flash 重载**——JTAG 易失流程下 flash 里是旧 bit，强复位 = 回退旧设计。替代 = 重烧 bit + 固件重传（+ 项目门控写，如先清流使能），报告登记「未做系统软复位」。
6. **连通性/发现**：ping / 发现包。不通先分流：烧错 bit → ARP/MAC 占用窗口（部分设计 ARP 失败后有数十秒占用期）→ 防火墙（设备主动入向流被按 exe 拦是高频坑；控制面回包属已建出向流不受影响——表现为控制面全 PASS 而数据面 0 包）。
7. **功能用例（声明覆盖面）**：控制面自动化（冻结表/保护语义/心跳）≠ 全链板测。三类用例分开登记：①控制面（寄存器/发现/心跳）②配置面（shadow→生效/快照闭环）③数据面（帧计数/帧率口径/字节对拍）。自动化脚本没覆盖的（常见：APPLY 快照、流帧）用交互菜单或专用脚本补跑。
8. **证据登记**：日志落盘（`logs/<日期>_<主题>_*.log`）、bit sha256 + 入口、对照基线（checks 数/帧率口径）、未覆盖面与遗留项。

## 执行不变量

1. **bit 溯源**（执行链第 2 步）——mtime 只作旁证，「入口 + sha256」才是身份。
2. **板/JTAG 状态先行**：烧板输出逐轮登记；板不可达 → 降级 sim 模式并登记待验证清单，不无限等待硬件。
3. **实验串行**：Vivado 与 ModelSim 并行会撞 IP 文件锁（`error renaming ... permission denied`）→ `taskkill //F vivado.exe hw_server.exe` 后重跑。
4. **证据层级**：事实（实测输出）/观察（数据现象）/推导（未直接验证）/未验证——报告必须标注。
5. **shell 环境**：监督服务/后台 shell 的 `cwd` 参数不生效（落 $HOME）、盘符路径 cd 被吃、POSIX sh 无 `pipefail`（`set -o pipefail` 秒退 exit 2）——一律普通会话 + **命令体内显式 cd**。
6. **遗留 vs 回归 A/B 归因**：怀疑本次改动引入失败时，暂存改动（stash）在基线重跑同一用例比对失败签名；同签名 FAIL = 遗留缺陷（引用既有登记），异签名 = 本次回归。禁止只凭「改动可能相关」就归因。

## 坑速查（通用，全部实测）

| 坑 | 一句话规避 |
|---|---|
| ILA 导出 CSV 空（只有表头） | wait_on_hw_ila 后必须 upload_hw_ila_data |
| TRIGGER_COMPARE_VALUE 报错 | 写成 eq1'b1 连写（eq 1'b1 会报 No apostrophe） |
| set_property 参数顺序 | PROP VALUE OBJ，value 在 obj 前 |
| CONTROL.CAPTURE_MODE | 只读属性，不设置 |
| .ltx 未关联 | set_property PROBES.FILE 后 refresh_hw_device |
| ILA-FREQ 读 0 | 静态属性不可靠，以 STATUS.CORE_STATUS/SAMPLE_COUNT 为准 |
| 含 IP 顶层跑 elaborate_check | module not found（synth_design 直调解析不了 IP OOC 产物）——用 build |
| `rst -system` | batch Tcl 无此命令 + xsdb 报 Invalid reset type + PROGRAM_B 重载 flash 旧 bit——见执行链第 5 步替代流程 |
| `make …` 管道接 tail | 退出码被吃成 0 假成功——重定向落盘 + `echo X_EXIT=$?`，产物 mtime 复核 |
| 监督服务/后台 shell 跑 make/vivado | cwd 参数不生效、盘符路径 cd 被吃、POSIX sh 无 pipefail——普通会话 + 命令体内显式 cd |
| 后台复合命令变量为空 | `a && V=x && cmd &` 整链进 subshell，前台 $V 为空——固定文件名或分两次调用 |
| dumpcap -D 报 Operation aborted | 换 cmd 调用；抓包权限不足才提权，不在 PATH 用全路径 |
| 防火墙拦设备入向流 | 按可执行文件放行（netsh 规则），控制面回包不受影响、数据面新入向流被拦 |
| 控制台/工具输出乱码 | 终端按 GBK 解码设备输出，乱码行不是读数现场；判据用数字/正则抽取后再下结论 |

## 时序报告判读（build 后必读）

- 读 `reports/*_timing_summary_routed.rpt`：**Setup/Hold `Failing Endpoints = 0` 且 Worst Slack > 0** 才算时序过；Hold 行 `NA` 常见于无 hold 分析域，不算缺失。
- WNS < 0 先分流：跨域约束缺失（假路径被当真路径）vs 真违例；再看违例端点是数据面还是配置面。
- 「build 通过」≠「时序通过」——build.tcl 是否以时序为 gate 由项目定，登记 WNS/WHS 数字本身。

## 交付纪律

- 板测报告：结论速览 → 步骤与证据（退出码/日志路径/计数数字）→ 覆盖面声明（三类用例各跑到哪）→ 未覆盖与遗留。
- 排查报告（出 bug 时）：结论速览 → 症状 → 排除项 → 根因（机制+证据）→ 修复 → 验证（sim/板上/主机三级）→ 遗留。
- 深化原则：项目专属链路沉淀回项目实例技能（如 no-gui-debug）或仓库文档；本技能只收通用 Xilinx 条目。
