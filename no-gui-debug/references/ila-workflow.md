# ILA 链 — 构建含 ILA 的比特流、烧板、无 GUI 抓波与 CSV 分析

> 通用化版本（底本：pw-gige `docs/k7_base/ila_debug_workflow.md`，2026-09-27/28
> 实战验证）。适用条件：Vivado 工程 + `ifdef DBG_ILA` 风格的板级 ILA 例化 +
> `scripts/catch_*.tcl` 无 GUI 抓波脚本。所有命令在 Git Bash 里执行，
> vivado 一律走 `cmd //c` 直调 .bat。

## 1. 探针定义（pw-gige 板顶 ifdef DBG_ILA，时钟 mig_ui_clk）

| probe | 信号 | 位宽 | 观测内容 |
|---|---|---|---|
| 0 | fs_aw_addr | 32 | frame_source 写地址流（应 +32 严格线性） |
| 1 | core_araddr | 32 | packer 读地址流（AR 碎片化/跳变判据） |
| 2 | fs_w_data[63:0] | 64 | 写数据（counter 图案：小端 16-bit 帧内索引） |
| 3 | core_rdata[63:0] | 64 | 读数据（撕裂 = 值跳变） |
| 4 | 控制位组 | 10 | aw/w/ar/r 握手 + mig_calib_done + mig_ui_rst |
| 5 | fs_desc_data_c 切片 | 64 | desc 交付内容（注意 desc_t 位图，见 §6-4） |

**counter 图案 = 地址示踪器**：像素值 n = 帧内索引（v·320+h 截 16 位），
因此 DDR/payload 内容的值 = 它所在的帧内偏移——读出的值直接暴露实际读写的
位置。撕裂帧表现 = 每包起始索引随机（非 pid×每包像素数）。

## 2. 构建含 ILA 的比特流

```bash
# DEBUG_ILA=1 → create_project.tcl source create_ila.tcl（生成 dbg_ila IP）
#              并对 sources_1 设 verilog_define DBG_ILA=1 → 板顶 ifdef 生效
TOP=gige_vision_ip_k7 NEED_MIG=1 DEBUG_ILA=1 cmd //c \
  "C:\Software\Xilinx\Vivado\2021.1\bin\vivado.bat -mode batch -nojournal -nolog -notrace -source scripts/build.tcl"
```

- 产物：`build/<top>.bit` + `<top>.ltx`（probes 文件，抓波必需；若 build.tcl
  未自动拷贝，从 `proj/...runs/impl_1/*.ltx` 手动 cp 到 build/）。
- **mtime 核对**：bit 时间必须晚于全部改动 RTL 的时间。

## 3. 烧板

```bash
TOP=gige_vision_ip_k7 cmd //c \
  "C:\Software\Xilinx\Vivado\2021.1\bin\vivado.bat -mode batch -nojournal -nolog -notrace -source scripts/program_jtag.tcl"
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
改用事件同域或高频信号触发（如 core_arvalid）。

触发 probe 选择经验：
- `core_arvalid`：读活动触发（配流后必触发）——通用首选。
- `fs_desc_valid_c`：desc 交付触发（窄脉冲可能漏采，等不到属正常）。
- 无条件立即：链路活性/时钟域判活（calib_done、写通路静默检查）。

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

判据（counter = 地址示踪器）：

1. **写地址流**：aw_valid=1 拍的 addr 应 +32 严格线性（bank 翻转处跳
  BANK_BYTES）。乱序 = 写侧问题。
2. **读地址流**：arvalid=1 拍的 addr 按 chunk/页钳位碎片化是正常的；异常 =
   地址与 desc.base + 帧内偏移不符。
3. **读数据**：rvalid=1 拍的 rdata 低 16 位（小端）应 = 读取位置的帧内像素
   索引；beat 间 +16（32B/2）为正常推进；跳变 = 撕裂点。
   ⚠ **期望值公式必须含 bank 基址**：counter 值 = 帧内偏移/2 = (DDR 地址 −
   bank_base)/2，**不是 DDR 绝对地址/2**——漏算 bank 基址会得到恒偏 +
   BANK_BYTES/2（本项目 +49152px）的「全部 BAD」假象（2026-09-28 实测 4/4 假
   BAD，修正公式后 4/4 dx=0）。
   ⚠ ILA 时钟若不是被测数据域时钟（如用 clk125 采 ui_clk 数据），跨域采样
   混叠，内容分析不可靠——只可看握手存在性，不可对拍内容。
   ⚠ 探针组没有 rready 时，AR↔R 配对只能用「rvalid + rdata 变化边沿」近似
   （rvalid 可在 rready=0 时长期驻留——正好是滞后缺陷的形态），结论要标注
   该近似。
4. **desc 交付**：valid && ready 拍的 data 按 desc_t 位图解码（pw-gige：
   base_addr=desc[296:265]、frame_bytes=desc[264:233]，**packed struct 首字段
   在 MSB**——切片前先对位图，实测切 [264:201] 会切到 frame_bytes+tag）。
5. **原始逐拍 dump**：定位精确时序时不要用"变化点压缩"，直接打印窗口内
   每拍的 (rv, px0, arv, addr)——变化点合并会掩盖"重复拍驻留 N 拍"这类
   关键细节（MIG 滞后一拍的实锤就是这么拿到的）。

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
