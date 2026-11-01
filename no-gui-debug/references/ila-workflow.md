# ILA 链 — 构建含 ILA 的比特流、烧板、无 GUI 抓波与 CSV 分析

> 通用化版本（底本：pw-gige `docs/k7_base/ila_debug_workflow.md`，2026-09-27/28
> 实战验证）。适用条件：Vivado 工程 + `ifdef DBG_ILA` 风格的板级 ILA 例化 +
> `scripts/catch_*.tcl` 无 GUI 抓波脚本。所有命令在 Git Bash 里执行，
> vivado 一律走 `cmd //c` 直调 .bat。

## 1. 探针定义（pw-gige 板顶 `ifdef DBG_ILA`，8 探针 / 深度 4096 / mig_ui_clk 同域）

位宽单一事实源是 `scripts/create_ila.tcl`（改了要先对这里和 CSV 表头）。2026-10-25
帧源链收进交付壳后，帧源类探针经壳的 `dbg_*` 口引出；**当前版本不含地址/数据探针**。

| probe | 宽 | 内容 | 用途 |
|---|---|---|---|
| 0 | 32 | `dbg_tx_submit_count` | core 提交发包数 |
| 1 | 32 | `dbg_tx_good_count` | MAC TX FIFO 收下的包数 |
| 2 | 32 | `{dbg_tx_overflow_count, dbg_tx_bad_count}` | FIFO 溢出 / 坏包 |
| 3 | 32 | `{dbg_tx_user_count, dbg_tx_underflow_count}` | user 侧错误 / 下溢 |
| 4 | 10 | `{dbg_wr_ctrl[4:0], core_arvalid, core_arready, core_rvalid, mig_calib_done, mig_ui_rst}` | 握手活性 + 校准/复位前提 |
| 5 | 66 | `{cfg_vend_act_seq[31:0], vend_act_w[15:0], vend_act_h[15:0], dbg_desc_valid, dbg_desc_ready}` | 几何生效序号与 desc 握手对账 |
| 6 | 22 | `dbg_loss_state` | 帧源丢帧 sticky 状态 |
| 7 | 1 | `dbg_loss_event_seen` | loss 事件粘滞位（`catch_ila.tcl` 触发源） |

**地址/数据示踪器不再在片内**：counter 图案对拍走上位机链（host-capture §5）。
**打包 IP 版（`gige_vision_ip_wrap`）不引出 `dbg_*`，IP bit 挂不了 ILA**——
要在 IP bit 上定位，需先在 wrapper 加观测口再重打包（见 ip-delivery-verify.md）。

## 2. 构建含 ILA 的比特流

```bash
# DEBUG_ILA=1 → create_project.tcl source create_ila.tcl（生成 dbg_ila IP）
#              并对 sources_1 设 verilog_define DBG_ILA=1 → 板顶 ifdef 生效
cmd //c "make build DEBUG_ILA=1"
# 等价直调（Git Bash 裸跑 make 会崩，必须 cmd）：
#   cmd //c "C:\Software\Xilinx\Vivado\2021.1\bin\vivado.bat -mode batch \
#     -nojournal -nolog -notrace -source scripts/build.tcl"
```

- `TOP` 缺省 `top`、`NEED_MIG` 缺省 1（不要再用已删除的 `TOP=gige_vision_ip_k7`）。
- 产物：`build/<top>.bit` + `<top>.ltx`（probes 文件，抓波必需；若 build.tcl
  未自动拷贝，从 `proj/...runs/impl_1/*.ltx` 手动 cp 到 build/）。
- **mtime 核对**：bit 时间必须晚于全部改动 RTL 的时间。

## 3. 烧板

```bash
cmd //c "make jtag"
# 直调等价：cmd //c "...vivado.bat ... -source scripts/program_jtag.tcl"
# 成功输出恰 1 行 "OK  : JTAG programmed <top>.bit -> xc7k325t_0"
```

烧后短暂失联（Discovery 无应答、ARP 无条目）多为 PHY/ARP 收敛瞬态：等 8-10s
重试；持续失联时重烧一次并做 30s+ 存活探针再下结论。

## 4. 抓波（tools/catch_ila.tcl / catch_ar.tcl / catch_now.tcl）

```bash
cmd //c "C:\Software\Xilinx\Vivado\2021.1\bin\vivado.bat -mode batch -nojournal -nolog -notrace -source tools/catch_ar.tcl"
```

脚本骨架（v3，全部 API 坑已修）：

1. `set_property PROBES.FILE <build/*.ltx> $dev` → `refresh_hw_device $dev`
   （不关联 ltx 直接报 `Use refresh_hw_device with a valid debug_nets.ltx`）。
2. `set_property CONTROL.TRIGGER_POSITION 2048 $ila`（前置 2048 样本；
   触发点=窗口头则设 0）。
3. 触发条件（可选）：
   `set_property TRIGGER_COMPARE_VALUE eq1'b1 [get_hw_probes -of_objects $ila -filter {NAME == <probe>}]`
   —— **eq1'b1 连写是唯一合法格式**；不带条件 = 全 don't-care 立即捕获。
4. `run_hw_ila` → `wait_on_hw_ila`。
5. **`set dat [lindex [upload_hw_ila_data $ila] 0]`** —— 缺失这一步导出必为
   空文件（只有表头 2 行）。这是全流程最大的坑：CORE_STATUS=FULL 但
   current_hw_ila_data 无数据，必须显式 upload。
6. `write_hw_ila_data -csv_file tools/log/ila_cap_<ts>.csv $dat`。

深度 4096 拍：ui_clk 100 MHz = 41 µs 窗口。持续现象（撕裂每帧都有）任意窗口
即可；事件稀疏（如 desc 交付是 ctrl 域 8ns 窄脉冲）用 ui 域 ILA 采样会漏——
改用事件同域或高频信号触发（现成触发源见下）。

触发源现状（2026-11 实测，别照抄旧口径）：

- `catch_ila.tcl`：**`dbg_loss_event` 触发**，TRIGGER_POSITION 2048，循环 3 次导出；
  找不到该探针会直接 error（不再是 core_arvalid）。
- `catch_now.tcl`：无触发立即捕获——链路活性/时钟域判活（calib_done、写通路静默）。
- `catch_ar.tcl`：仍按 `core_arvalid` 过滤，**但该信号已并入 probe4 位段，不再是独立探针**，
  `get_hw_probes` 返回空 → 触发设置失败并静默退化为立即捕获。要按 AR 活动触发，
  得改脚本按 probe4 的 `core_arvalid` 位段判，或抓 `catch_now` 后离线筛。

## 5. 状态判活（ILA 属性）

```tcl
puts "FREQ:  [get_property STATIC.ILA_CLOCK_FREQ $ila]"      # 常 0，不可靠
puts "CORE:  [get_property STATUS.CORE_STATUS $ila]"          # FULL = 捕获完成
puts "SAMPLE: [get_property STATUS.SAMPLE_COUNT $ila]"        # 4096 = 满
puts "TSM:    [get_property STATUS.TSM_STATE $ila]"           # 触发状态机
```

## 6. CSV 分析方法

CSV 结构：行 1 = 表头（列名含探针位段，**以实际表头为准**，切片改动会变）、
行 2 = Radix、行 3 起 = 数据（HEX）。注意 `wc -l` 对无换行结尾的文件会少计，
用 csv.reader 数。

判据（按 §1 探针语义；计数类只取关流后稳定值）：

1. **TX 提交 vs 收下**：probe0 与 probe1，`good < submit` ⇒ MAC TX FIFO 丢包；
   差值随流量线性放大才是最硬的证据（单帧差 1 可能是边界效应）。
2. **TX 错误计数**：probe2/probe3 的 overflow / bad / underflow / user 应恒 0 且平直；
   非 0 先修发送侧（反压、带宽令牌、包长），别急着查读通路。
3. **握手活性 + 出流前提**：probe4 的 `core_arvalid/arready` 有翻转 ⇒ 读通路在跑；
   `mig_calib_done=1`、`mig_ui_rst=0` 是出帧前提——两者不满足时「0 包」与 RTL 无关，
   先查 DDR 校准/复位时序（本机 JTAG 重配后未软复位就会命中这一条）。
4. **几何生效对账**：probe5 的 `cfg_vend_act_seq[31:0]` 必须与 `vend_act_w/h`
   同拍自洽（seq 已变而 act_* 未跟随 = 几何错位，壳内 CDC 会整帧丢弃）；
   `dbg_desc_valid && dbg_desc_ready` 的拍数应与提交帧数一致。
5. **丢帧面**：probe6 的 22 bit 是帧源 sticky 状态，probe7 是 loss 事件粘滞位；
   probe7 触发后回看前后 4096 拍里 probe5 的 desc 握手是否中断、probe4 的 AR 是否停摆。
6. **原始逐拍 dump**：定位精确时序时不要用"变化点压缩"，直接打印窗口内每拍的
   (arvalid, arready, ctrl 位, desc 握手)——变化点合并会掩盖"重复拍驻留 N 拍"这类
   关键细节（MIG 滞后一拍的实锤就是这么拿到的）。
7. **通用注意**：内容级（地址/像素）判据已不在片内，走 host-capture §5；ILA 时钟不是
   被测数据域时钟时只可看握手存在性；探针位段一旦改动，先重读 §1 与 CSV 表头。

## 7. 已知坑清单（全部实测踩过）

| 坑 | 症状 | 正确做法 |
|---|---|---|
| 缺 upload_hw_ila_data | CSV 只有表头+radix（2 行） | wait 后显式 upload（§4-5） |
| TRIGGER_COMPARE_VALUE 格式 | No apostrophe specified in string: eq | eq1'b1 连写 |
| set_property 参数顺序 | Invalid option value ... for 'objects' | PROP VALUE OBJ |
| CONTROL.CAPTURE_MODE | read-only | 不设置 |
| PROBES.FILE+FULL_PROBES.FILE 同设 | 'file' can only be specified once | 只设 PROBES.FILE |
| ILA-FREQ 读 0 | 静态属性不可靠 | 用 STATUS.CORE_STATUS/SAMPLE_COUNT |
| -force 未加 | You must use the -force option to overwrite | 循环抓波加 -force 或唯一时间戳 |
| 并行跑 ModelSim | MIG IP rename permission denied（_tmp 目录） | 串行；kill vivado/hw_server 后重跑 |
| elaborate_check 含 IP 顶层 | module not found | build 为准 |
| 删 .gen IP 目录 | OOC 产物丢失（synth module not found） | 先 reset/launch mig_7series_0_synth_1 再 build |

## 8. 与配流/抓帧的时序配合

- 观测撕裂/读流：先 arm ILA（启动 2-4s），再配流开流（`tools/stream_and_catch.py`
  保持 30s），**时序错了抓到的就是关流后的空档**（araddr=0、desc 挂起是关流后
  的正常状态，不是异常）。
- 配流参数（pw-gige）：SCDA=192.168.1.3、SCPS=1500、SCPD=0、host_port=49152；
  IP 值必须转 int（socket.inet_aton 大端），writereg 不接受字符串。
- **开流前先写 `SCP0=0`**（`stream_and_catch.py` 已内置）：设备残留「开流态」时
  表现是「开流成功但线上 0 包」，会被误判成 RTL 缺陷。
