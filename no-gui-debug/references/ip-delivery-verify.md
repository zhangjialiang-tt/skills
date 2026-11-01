# 打包 IP 交付件验证 — 第四条链路（先定 bit 来源，再谈现象）

> 适用：把交付壳打包成 Vivado IP（pw-gige：`gige_vision_ip_wrap`）后，验证
> 「从 ip_repo 取出的交付件」能编译、能落地、且与平铺构建**功能等价**。
> 入口：`make package-ip` → `make verify-ip`；产物 `build/ip_pack/pkg/`、
> `build/ipverify/top.bit`。这条链路本身不是证据来源，它回答的是
> 「我现在烧的/测的到底是哪份逻辑」——结论前置。

## 1. 两条构建入口与 bit 归属（最容易出错的一步）

| 入口 | Vivado 工程 | 产物 | 逻辑来源 |
|---|---|---|---|
| `make build` | `pw_gige` | `build/top.bit` | 平铺：直接用 `rtl/` 源，交付壳是本地 RTL |
| `make verify-ip` | `pw_gige_ipverify` | `build/ipverify/top.bit` | 从 ip_repo 取打包 IP，经 `verify/` shim 替换 |

- **`rtl/top.sv` 始终例化的是 `gige_vision_ip`**；IP 替换只发生在 verify 工程的
  shim 里（shim 同名定义 `gige_vision_ip`，内部例化 `gige_vision_ip_wrap_0`）。
  所以「默认 `make build` 不走 IP」是正常行为，不是漏配。
- 同名文件多处存在：`build/top.bit`（平铺/临时工程）与 `build/ipverify/top.bit`（IP）
  **同名不同物**，烧错一次整轮结论作废。
- 日志标记（用来认源，比文件路径可靠）：
  - verify-ip：`packaged IP pwgige:gige:gige_vision_ip_wrap:1.0 已入工程`
  - 临时改 `create_project.tcl` 的 IP 构建：`board sources=N（IP 内部源已排除…）`
    ——见到这条说明当前树上的脚本与当次构建不一致，**该 bit 不可复现**，
    要么把改动提交，要么改回 verify-ip 入口重跑。

## 2. bit 溯源（替代「只看 mtime」）

每次上板前登记四件事：**构建入口 + 工程名 + 日志标记 + sha256**（另存
`reports/*timing_summary_routed.rpt` 的 WNS/WHS 与 LUT 数）。
mtime 只能挡住「改了 RTL 没重编」，挡不住「同名 bit 来自另一条入口」——后者在
本项目真实发生过（平铺 bit 与 IP bit 同目录同前缀）。

## 3. 打包正确性核对（纯静态，不用上板）

1. **端口**：`component.xml` 模型端口数 == wrapper 端口数，名称/方向逐项一致
   （pw-gige 当前 131）。
2. **总线**：三个 aximm 的 portMap 全部指向真实端口；时钟
   `ASSOCIATED_BUSIF/ASSOCIATED_RESET`、复位极性、存储器映射与主地址空间齐全。
3. **源**：`pkg/src/*` 与工作树逐字节一致（批量 `diff -q`）。未打包的文件必须能
   说清「IP 不引用它」（pw-gige 是 `rtl/common/DC_FIFO.v`，板级在用）。
4. **参数**：MODELPARAM 缺省 == 板级有效值（pw-gige：`TARGET=XILINX`、
   `DDR_ADDR_WIDTH=32`、`AXI_DATA_WIDTH=256`、`AXI_ID_WIDTH=4`、
   `CLOCK_INPUT_STYLE=BUFR`、`BUF_BASE=0`、`SLOT_COUNT=4`、`SLOT_BYTES=655360`）。
5. **stub 位宽**：`wdata[255:0]`、`araddr[31:0]`、`awid[3:0]`、`cfg_w/h[16:0]` 与 RTL 一致。
6. `ipx::check_integrity` 无 ERROR；父级综合**无 `8-439`**（黑盒 = 源缺失或文件名不一致）。

## 4. 等价性判据（回答「是不是打包引入的」）

| 证据 | 判据 | pw-gige 实测 |
|---|---|---|
| LUT / 寄存器 | 两入口相差 < 0.1% | 25767 vs 25778（11 LUT） |
| 实现时序 | WNS/WHS 一致或同差一档 | +0.028 / +0.051，两侧完全相同 |
| 黑盒 / 缺源 | 两侧均为 0 | 0 次 `8-439` |
| 上板行为 | 同脚本同窗口症状应一致 | 两侧同为 0 包 ⇒ 不是打包的锅 |

**反例警示**：如果 IP 与平铺症状一致，继续加造「打包假设」只会浪费两轮；此时
应回到数据面前置分流（§6）与 methodology 的启动窗口差异项。

## 5. IP 化带来的真实差异（全部实测踩过）

1. **OOC 无时钟上下文**：不要给 OOC 综合开 `-retiming`（CDC 链会被当普通流水线重
   定时）；也**不要**给 OOC 挂 `create_clock`——时钟对象随 DCP 带进父级，与板级
   MMCM 形成双时钟，跨边界全按无关时钟计时（pw-gige 实测 11727 端点假违例）。
2. **参数不转发**：shim/wrapper 声明了参数但例化时不写 `#(...)`，父级参数被静默
   忽略。k7base 的 `BUFR` 恰好等于打包缺省掩盖了它；`lzy1280` 要 `BUFG` 时会静默降级。
3. **常量接输出口**：`8-2900 ignoring illegal expression in output port connection`
   表示该连接被**忽略**（不是错误）；`8-689` 与 `8-2900` 成对出现多见于 `'0` 接端口
   （2021.1 按 1 bit 处理）。
4. **观测面丢失**：wrapper 只暴露契约端口，`dbg_*` 不进 IP ⇒ **IP bit 无 ILA**。
   要在 IP bit 上定位数据面，先在 wrapper 加调试口再重新打包；否则先用平铺 bit 定位。
5. **位宽偷偷截断**：标量/常量接多位端口只驱动低位（pw-gige shim 的
   `m_axi_arregion` 1 bit 接 4 bit 网）。引用任何探针/网表前先确认 `8-689` 已清零。

## 6. 控制面绿、数据面死（0 包）的分流顺序

判据：GVCP 全 PASS + `stream_on` 成功 + 收流窗口 0 包。按序排除，每步都要有读数：

1. **出流前提**：MIG 校准完成；TPG 未被复位（pw-gige：
   `tpg_rst34 = rst34 | ~mig_calib_done | ~tpg_pattern_valid`，任一为 0 就整链不出帧）。
2. **设备残留开流态**：先写 `SCP0=0` 干净关流再开流（残留 `0x77770000` 一类写值会
   造成「开流成功但线上无包」）。
3. **主机防火墙按 exe 拦入向 UDP**（2026-11-01 baseline 板测实测根因）：Windows
   防火墙有状态——GVCP 是 host 先发的出向流，ACK 属已建流回包放行；GVSP 是设备
   主动向 host_port 发的**新入向流**，未放行的 exe 默认拦。签名：同一端口 python
   （已放行）能收包、CLI 收 0 包。二分：python 裸 UDP bind `0.0.0.0:<host_port>`
   统计包数/block_id（`tools/capture_frames.py` 即可，只看 block_id 计数、忽略其
   组装结果，见 host-capture.md §4）。修：管理员
   `netsh advfirewall firewall add rule name=gige_cli_udp_in dir=in action=allow
   program="<gige_cli.exe 全路径>" protocol=udp`。
4. **复位前置**：JTAG 重配后 `rst -system` 在本机不可用（Vivado Tcl 无
   `reset_hw_target`、xsdb 报 `Invalid reset type`）；替代 = 重烧 bit + 固件重传 +
   干净关流，并在报告登记「未做系统软复位」。
5. 以上都排除后才回到 RTL/IP，此时 ILA 才有意义。

## 7. 交付前门（打包方自查）

- 静态：端口 / 源 / 参数 / stub 四项核对 + `check_integrity`。
- 构建：`make verify-ip` 全流程通过，WNS/WHS 与平铺一致。
- 客户侧：BD 加 IP 后 `validate_bd_design` + 综合通过（`scripts/customer_bd_add_ip.tcl`）；
  BD 里未连的输入会被 tie 0，其中 **`user_ack/user_rdata/user_error` 未连会让 IF-U 挂死**，
  必须在交付说明里点名。
