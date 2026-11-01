# tshark 链 — dumpcap 无 GUI 抓包与逐包分析

> 适用：网络层证据（包序/丢包/重传/帧率/吞吐/包间隔分布），以及与上位机链
> 交叉定性（"发送侧健康，异常在内容"这类关键分流就是 tshark 给出的）。
> 本机：tshark/dumpcap 4.6.9，`C:\Program Files\Wireshark\`（不在 PATH，
> 全路径调用）；dumpcap 需管理员。

## 1. 采集（dumpcap，无 GUI）

```bash
# 列接口（找业务网卡序号/名；pw-gige 实验网 = "以太网" 系列，1Gbps）
"C:/Program Files/Wireshark/dumpcap.exe" -D

# 抓 60s 到 pcapng（-a duration 自动停；避免无限抓撑爆盘）
"C:/Program Files/Wireshark/dumpcap.exe" -i "以太网 29O3EW3" \
  -a duration:60 -w tools/log/cap_$(date +%Y%m%d_%H%M%S).pcapng
```

- 文件名带空格/中文的接口名直接引号包裹即可（实测可用）。
- 权限：**权限不足会直接报错，报错再提权**——本机实测非管理员 shell 可直接抓
  （1M 包 99.9% 无丢），"必须管理员"是过强假设。
- ⚠ **`dumpcap -D` 报 `Operation aborted`**（Git Bash 实测复现）：换 cmd 调用；
  仍不行就用 python 裸 UDP 探针二分（host-capture.md §4）——定性「设备在不在发」
  不依赖 pcap。
- ⚠ **后台复合命令的变量作用域坑**（实测）：`a && TS=$(date) && dumpcap … & PID=$!`
  会把**整条链**送进后台 subshell——前台 `$TS` 为空、`ls cap_e1_$TS.pcapng` 必失败。
  规避：固定文件名，或分两次调用（先启动抓包、再起业务流量）。
- 设备流是 UDP 单向洪流（387fps × 114 包 ≈ 44k 包/s），60s ≈ 85MB——
  先短抓定性，确需长抓再放大 duration。
- Wireshark GUI 手抓的 pcapng 同样可用（本链路分析脚本都吃标准 pcapng）。

## 2. 快速统计（tshark）

```bash
TS="C:/Program Files/Wireshark/tshark.exe"

# 端口/协议概览（确认 GVSP 动态端口——host_port 是配流决定的，别假设 55246）
"$TS" -r capture.pcapng -T fields -e udp.srcport -e udp.dstport | sort | uniq -c | sort -rn | head

# 只留 GVSP 流（设备→host）
"$TS" -r capture.pcapng -Y "udp.srcport==3956" -T fields \
  -e frame.time_relative -e udp.dstport -e data.data
```

大 pcap（85MB/60s）用 tshark 全量解析较慢；逐包深度分析（重组 beat 流、
像素对拍）建议转 scapy（§4）——tshark 适合过滤/概览/字段导出三件事。

## 3. 帧级判据（GVSP 结构，pw-gige 口径）

GVSP 头（UDP payload 前 8B）：`[0:2]=status [2:4]=block_id [4]=packet_format
[6:8]=packet_id`；fmt 0x01 Leader / 0x02 Trailer / 0x03 Payload。

| 判据 | 健康值 | 异常含义 |
|---|---|---|
| Leader 间隔分布 | 恒定 ≈ 帧周期（板级 2.5ms@400fps） | 拉长/抖动 = 发送或读通路停顿 |
| 每帧包数 | 114（1 Leader + 112 Payload + 1 Trailer，SCPS=1500 几何） | 少包 = 丢包/组装缺陷 |
| block_id 连续性 | +1 递增 | 跳号 = desc 丢弃/帧被中止 |
| payload 首像素 | = pid × 每包像素数（counter 图案） | 错位 = 读通路/内容错配 |
| **Leader→Trailer 时长** | ≈ 114 × 线速包时（1500B@1GbE ≈ 1.40ms）——"突发+空等"型 | ≈ 帧周期 = **连续细流**：TX 被上游数据供给限速，每包间隔 = 帧周期/113（2026-09-28 帧频案：30µs/包 ⇒ 读供给 48.7MB/s） |
| **Trailer→下一 Leader gap** | 大 gap（帧间读/写翻转期） | ≈0 = 背靠背，瓶颈在帧内供给速率而非帧间调度 |

后两行是**帧率类 bug 的第一分流判据**：先判"细流还是空等"，细流 ⇒ 查数据供给
（MIG 读速率/带宽预算），空等 ⇒ 查帧间调度（desc 交付/bank 翻转/带宽门）。

⚠ **发送侧健康 ≠ 无 bug**：MIG 撕裂案里发送侧 387.7fps、114 包/帧、block_id
连续全部正常，异常藏在 payload 内容里——帧级判据全过之后必须进内容对拍
（见 references/host-capture.md §5 的地址示踪器）。

## 4. scapy 逐包重建（深度分析）

tshark 概览 → scapy 全量解析 → 判据统计的标准管线（脚本模式，`2>&1 | grep -v
"WARNING|Cryptography"` 静音）：

```python
from scapy.all import PcapReader, UDP
frames = {}
for p in PcapReader(PCAP):
    if not p.haslayer(UDP): continue
    u = p[UDP]
    if u.sport != 3956: continue            # 设备→host 方向
    raw = bytes(u.payload)
    b = int.from_bytes(raw[2:4], "big"); fmt = raw[4]
    pid = int.from_bytes(raw[6:8], "big")   # pid 在 6:8（不是 5:7！）
    frames.setdefault(b, []).append((fmt, pid, raw[8:]))
```

实战技巧（全部实测）：

- **先诊断分组结构再跑判据**：`每 block_id 包数分布` 若全是 1，先怀疑自己的
  dict/pid 解析，而不是设备。
- payload 拼接前按 `(block_id, pid)` 去重；完整帧判定 = 恰 114 包且 payload
  112 个。
- counter 图案下，**包内 +1 连续段的长度分布与断点位置**直接给出错位机制：
  段长都是 16px 整数倍 = 以 beat 为单位的丢/错位；断点值跳到 0..15 = 帧尾
  混入下一帧首组。
- **同 pid 跨帧起始值统计**：唯一值多 = 随机竞态；恒定 = 确定性地址错位。
  这一个统计就能把排查分成两条完全不同的路。

## 5. 与其他链路的分工

| 需求 | 用谁 |
|---|---|
| 包级定性（发送侧健康？丢包？帧率？） | tshark/scapy（本文件） |
| 完整帧内容对拍（撕裂/错位定位到字节） | 上位机链 capture/capture_frames.py |
| 片内拍级（握手/地址/状态机） | ILA 链 |
| 长期流量画像（每小时帧率/丢包率曲线） | dumpcap 分段 + scapy 批处理 |

典型组合：dumpcap 抓 60s → scapy 判帧级四判据 → 异常在内容则转上位机对拍 →
内容错位模式确定后转 ILA 拍级定位。

## 6. 帧率类 bug 的双端同窗分流（先做这个再谈根因）

症状只有"帧率低"时，第一件事是同窗口双端测速，把损失定位到三段之一
（设备发送 / 链路 / host 接收）：

```bash
# 后台起抓包（固定文件名，见 §1 作用域坑），3s 后前台跑 gige_cli stream
'/c/Program Files/Wireshark/dumpcap.exe' -i '<接口>' -a duration:42 -f 'udp' \
  -w tools/log/cap_split.pcapng &
sleep 3
gige_cli stream --camera <ip> --nic <n> --seconds 30   # 自带配流，只计数
```

| 结果组合 | 结论 |
|---|---|
| pcap Leader 速率 ≈ gige_cli fps，且 stream dropped/missing 全 0 | **host 零丢帧，pcap 值就是发送侧真值**——别去查 host，直接进 §3 后两行判细流/空等（2026-09-28 帧频案：293fps 一测即钉死在发送侧） |
| pcap ≈ 目标、gige_cli fps 低、dropped>0 | host 侧丢（socket/组装/环形缓冲）→ 上位机链 manifest 判读 |
| pcap 本身就低 | 发送侧回退 → §3 后两行分流细流/空等 → ILA 链 |

要点：gige_cli stream 的统计（ok/recov/drop、missing、receive_errors）全 0 +
VERDICT PASS 是"host 无辜"的**完整**证据——重传机制都没动过说明 host 一个
包都没缺，无需再用 capture 复核。
