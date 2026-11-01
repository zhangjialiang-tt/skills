# 上位机链 — gige_cli 录帧/snap/wire dump 与 capture_frames.py 对拍

> 适用：gigev-host-demo（C++ 无 Qt 依赖 CLI）+ pw-gige tools/capture_frames.py。
> 证据类型：完整帧文件（RAW）+ 原始 wire 字节流 + manifest 连续性——内容级
> 对拍的首选链路。

## 1. gige_cli 子命令全表（9 个，实测）

二进制：`gigev-host-demo\build\vs2022-x64\src\cli\{Debug,Release}\gige_cli.exe`
（Release 优先；Debug 与 Release 行为一致）。

| 子命令 | 参数 | 说明 |
|---|---|---|
| nic | 无 | 枚举网卡（过滤 loopback/未启用/无 IPv4）。**先跑它**——Tailscale/蓝牙/Meta 虚拟口会干扰自动选择 |
| discover | [--nic i] [--timeout ms] [--camera ip] | 广播或定向发现；ICMP 现镜像可实现 `ping` 探活，discover 是协议级活性判据 |
| readreg / writereg | --camera ip --addr hex [--value n] | 单寄存器读写 |
| heartbeat | --camera ip [--seconds n] | 取控制权 + 心跳保活 |
| stream | --camera ip [--seconds n] [--resend-to-trailer] | 只计数不落盘（帧率/重传统计） |
| capture | --camera ip --dir path [--blocks n] [--max-seconds n] [--wire] [--snapshot] [--nic i] | 完整帧落盘 + manifest，详见 §2 |
| snap | --camera ip --dir path [--wait ms] [--wire] | 单帧快照：开流→等首帧完整→落一张→停流 |
| forceip | --camera ip --ip new --mask nm [--gateway] [--mac] [--no-confirm] | RTL 子集布局 MAC+IP+Mask+GW；MAC 不匹配设备静默丢包 |

退出码：0 成功 / 1 业务失败 / 2 用法错误 / 3 环境错误。正常结束自动 CCP=0
释放控制权；进程强杀靠设备心跳超时兜底。

## 2. capture 语义（容易误读的点）

- `--blocks N` = 观察 **N 个连续 Block ID**（OK/RECOVERED/DROPPED 全计入），
  不是"存够 N 张成功帧"。默认 1000。
- `--blocks 0` = 无 timeline 预算 = **录像模式**，Ctrl+C 手动停（有序收尾：
  停流→排空 writer→flush manifest→释放 CCP）；须配 `--max-seconds 0`。
- 环形缓冲 64 槽（~10MB）吸收 400fps 突发；溢出计 `ring_overflows` 并判
  FAIL；**被丢帧不写 manifest 行**（行数+溢出数=观测数）。
- 结束打印 capture/frames/receiver/assembly 四组统计 + `VERDICT: PASS|FAIL`。
- `--wire`：额外落盘原始 payload 字节流（`.wire` 后缀）——**内容错位类 bug
  的首选证据**（可逐字节反解设备实际发出的数据）。

输出产物（会话目录内）：

```text
frame_<blockid>_320x256_mono16_le.raw      # 完整帧（Mono16 小端原字节，不转换）
frame_<blockid>_..._.wire                  # --wire 时**只出 .wire**（manifest 的 RawFile 列也指向它），内容对拍读这个
capture_manifest.csv                       # 列：BlockID,Status,Timestamp,MissingPackets,ResendAttempts,RecoveredPackets,RawFile
snapshot_frame_<blockid>_....raw           # --snapshot / snap 子命令
# Status ∈ {OK, RECOVERED, DROPPED}；DROPPED 有行无文件
```

## 2.5 stream 逐秒输出的判读（帧率 bug 首选工具）

`gige_cli stream` 每秒打一行，字段比 capture 摘要更连续（无落盘开销）：

```text
t=  30s  rx=1006483 (1387.29 MB)  fps=293.4  ok=8828  recov=0  drop=0  resend=0 ...
--- stream result ---
frames: complete=8828 (ok=8828 recovered=0) dropped=0
assembly: missing=0 duplicate=0 resend_req=0 recovered_pkt=0 ...
receiver: packets=1006501 malformed=0 ... receive_errors=0 ...
VERDICT: PASS
```

- `fps` = host 组装完成的帧率；`ok/recov/drop` = 完整/重传补齐/放弃的帧数。
- **关键推理**（2026-09-28 帧频案）：dropped=0 且 assembly/receiver 全 0 且
  resend=0 ⇒ host 一个包都没缺、重传机制都没动过 ⇒ **fps 就是设备发送侧真值**，
  帧率缺口在设备侧，不用再查 host。
- `rx` 的包数/字节数可反推线速利用率（除以窗口秒数），与 pcap 互核。
- `--resend-to-trailer` 才启用重传路径；默认路径 resend 恒 0 属正常。

## 3. 已知坑

- **discovery 超时**：先 `gige_cli nic` 枚举，`--nic <序号>` 显式指定业务网卡
  （Tailscale/Meta/蓝牙虚拟口排前面时自动选择会选错）。pw-gige 侧
  `tools/gvcp_discover.py` 可交叉验证设备活性。
- **ICMP**：现镜像实现 Echo Reply（`rtl/net/icmp_echo.sv`），`ping 192.168.1.128` 应通；
  不通说明烧的是旧镜像（旧镜像才以 discover 判活）。注意 ARP 未命中时回包会造成约 22 s
  UDP 全停（`ip_arb_mux` 被占），别把这 22 s 判成链路故障。
- **只写寄存器不可读**：`0xA014`（APPLY 邮箱）读回必报 WRITE_PROT/INVALID_ADDRESS 属设计行为；
  写生效判据看 `CONFIG_STATUS.busy`。多地址批量 READREG 会串位，判读一律单字逐读并对设计缺省值
  （`SCPS0=1500<<16`、`SCDA0=192.168.1.3`）。
- 烧板后短暂失联：PHY/ARP 收敛瞬态，等 8-10s 重试。
- **GVCP 通但 stream/snap rx=0**：按 ip-delivery-verify.md §6 分流，先用 python
  裸 UDP 探针二分「设备没发 vs 主机拦截」——能收到即防火墙按 exe 拦入向 UDP
  （`gige_cli.exe` 需管理员 netsh 放行，规则名 `gige_cli_udp_in`）。
- **紧接裸收探针后 CLI 首跑 STALL**：探针收尾写 `SCP0=0` 关流与 CLI 开流存在竞态
  （实测 250 帧＝5s @50fps 后停），复跑干净即瞬态，不追。

## 4. capture_frames.py（pw-gige tools/，UDP 直收对拍）

```bash
"C:/Software/Python/Python311/python.exe" tools/capture_frames.py [帧数，默认4]
# 产物：tools/log/cap_fix/frames.bin（每帧 163840B payload 顺序拼接）
```

与 gige_cli capture 的分工：gige_cli 带组装/重传/manifest 完整管线（证据规范）；
capture_frames.py 裸 UDP 直收（轻量、可改、组装逻辑透明），适合快速迭代对拍。

实现要点（改它之前必读）：

- `SO_RCVBUF = 32MB`（内核缓冲不足会整批丢包，表现为完整帧 0）；**先裸收后
  组装**（边收边组装 Python 跟不上 387fps×114 包）。
- **GVSP 头格式**：`[0:2]=status [2:4]=block_id [4]=packet_format
  [6:8]=packet_id`（**pid 在 6:8**，写成 5:7 会把保留位当 pid 高位——所有包
  pid 恒 0、一帧都组不出来的假象就是这么来的）。fmt：0x01 Leader / 0x02
  Trailer / 0x03 Payload；完整帧 = 1+112+1（SCPS=1500、320×256 Mono16 几何）。
- host_port 等寄存器值：IP 必须转 int（socket.inet_aton 大端）。
- **0 完整帧 ≠ 链路异常**：每帧 114 包 / `FRAME_BYTES=163840` 是老 320×256 几何
  写死校验，新几何（如 638×512 mono16，649 包/帧）下永远凑不满。判「设备是否
  在发流」只看裸收包数与 block_id 计数，组装结果作废。

## 5. 对拍判据（counter 图案 = 地址示踪器）

测试图案像素值 = 帧内索引（v·320+h 截 16 位，Mono16 **小端**落盘）：

```python
FRAME_BYTES = 163840
for off in range(0, FRAME_BYTES, 2):
    got = fr[off] | (fr[off+1] << 8)     # 小端
    want = (off // 2) & 0xFFFF
    # got != want 即错位；首个错位 offset 直接给出内容漂移量
```

判读：

- 错位字节 0 → PASS。
- 恒定偏移（所有帧相同首错）→ 确定性地址/内容错位（如丢 N 组、恒定滞后）。
- 每帧随机偏移 → 竞态（反压/延迟窗口碰撞），回 ILA 链定位。
- 段边界 16px（32B）粒度锯齿 → 以 beat 为单位的丢/错位。
- 值跳到 0..15 一类的小值 → 帧尾混入下一帧首组（写指针/翻转时序问题）。
