# RTL 扫描检查清单

## §1 可综合性

逐项检查并记录发现：

- [ ] 不适合综合的写法（`initial`、`fork/join`、延时控制等）
- [ ] 综合器支持但 FPGA EDA 不稳定的写法（`force/release`、`assign/deassign`）
- [ ] SystemVerilog-only 语法是否误用于 `.v` 文件（`logic`、`always_ff`、`always_comb`、`interface`、`package` 等）
- [ ] function/task 在综合路径中的使用是否安全（是否在 `always @(*)` 或组合赋值中使用）
- [ ] `automatic function` 是否必要 — 递归或可重入场景才需要
- [ ] for-loop 是否会综合成过深组合逻辑 — 检查循环体是否含大量嵌套操作
- [ ] variable part-select — `data[idx*W +: W]` 是否导致综合/调试不稳定
- [ ] 动态数组索引 — `reg_array[index]` 是否导致复杂 mux
- [ ] unpacked reg array 是否被误当 memory 或导致调试器异常
- [ ] 多维数组、深层数组、RAM-like array 是否需要封装成独立 RAM 子模块
- [ ] 是否存在 latch 推断 — `always @(*)` 中分支不完整
- [ ] 是否存在多驱动 — 同一 reg 被多个 `always` 块赋值
- [ ] 是否存在未初始化状态机
- [ ] 是否存在不可达状态或默认分支不完整
- [ ] 混合 blocking/non-blocking 赋值 — `always @(posedge clk)` 中同时使用 `=` 和 `<=`

## §2 可实现性

> **证据等级提示**：本节多数指标无法仅靠源码确认，需综合/实现报告（E3）。仅基于源码的判断只能标 hypothesis，不得标 confirmed。

- [ ] `E1` 宽组合路径 — 源码可见结构；实际 LUT 级数需综合报告 `E3`（对应规则 TIM-LONG-COMBINATIONAL-001）
- [ ] `E3` 大 mux（>32:1）— 需综合报告 mux fanin 统计（对应规则 TIM-WIDE-MUX-001，阈值已统一为 >32:1）
- [ ] `E1` 超宽数据总线直接进入复杂逻辑 — 源码可见位宽，"复杂度"需综合确认
- [ ] `E3` RAM/FIFO 推断不稳定 — 需综合日志
- [ ] `E3` block RAM / distributed RAM 推断是否符合预期 — 需综合资源报告
- [ ] `E3` reset 过重导致资源浪费或时序压力 — 需时序/资源报告
- [ ] `E3` 大量高扇出控制信号（复位扇出 >1000）— 需实现报告 fanout 统计
- [ ] `E3` 大量跨层级 internal net 被 debug core 探测后可能影响实现 — 需实现报告
- [ ] `E1` 是否需要将 memory/FIFO/line buffer 拆成独立子模块 — 源码可初判

## §3 时序优化

> **证据等级提示**：本节核心指标依赖时序报告（E3）。源码只能给出启发式怀疑（E0/E1）。

- [ ] `E3` 目标时钟域下是否存在长组合路径 — 需时序报告
- [ ] `E1` ready/valid 反压链是否过长 — 源码可初判组合深度（对应规则 HS-VALID-DEPENDS-READY-001）
- [ ] `E1` input valid 到 output ready 是否存在组合环 — 源码可初判
- [ ] `E3` 宽数据路径是否缺少寄存器切分 — 需时序报告
- [ ] `E3` 计数器/比较器/地址计算是否在同一拍堆叠过多 — 需时序报告
- [ ] `E1` min/max/sum/checksum/encode 等计算是否需要 rolling 或 pipeline — 源码可见结构
- [ ] `E1` 状态机 next-state 是否过重 — 源码可初判
- [ ] `E3` FIFO full/empty 到 upstream ready 是否组合路径过深 — 需时序报告
- [ ] `E1` 是否需要使用 registered ready — 源码可初判（注意：此变换会改变 latency，必须遵守 Transformation Contract）
- [ ] `E1` 是否需要把"计算"和"状态推进"拆拍 — 源码可初判

## §4 仿真与上板一致性

- [ ] 仿真中默认初始化但 FPGA 上未 reset 的寄存器
- [ ] frame_start 与第一个 valid 同拍时行为是否明确
- [ ] ready/valid 握手是否严格遵守 — valid 不能依赖 ready
- [ ] valid 为 0 时 data 是否被错误消费
- [ ] last 标志是否只在 valid/fire 时有语义
- [ ] 错误状态是否可恢复
- [ ] frame_done 是否等待全部 pipeline drain
- [ ] FIFO 中残留数据是否会污染下一帧
- [ ] 跨帧状态是否清零完整
- [ ] 错误码是否锁存第一现场
- [ ] 仿真 testbench 是否掩盖了上板真实 backpressure
- [ ] 是否存在 CDC 风险或复位跨域风险

### §4.1 跨时钟域（CDC）专项检查

当模块涉及多时钟域或异步接口时，必须逐项确认：

- [ ] **单 bit 信号跨时钟**：是否使用双触发器同步（2-stage synchronizer），是否遗漏了 meta-stability 防护
- [ ] **多 bit 总线跨时钟**：是否使用 async FIFO 或 handshake 同步，禁止直接打拍同步多 bit 控制总线
- [ ] **脉冲跨时钟**：单周期脉冲是否通过 pulse synchronizer（toggle + 双触发器）传递，禁止直接同步窄脉冲
- [ ] **复位跨时钟**：各时钟域的复位释放是否独立同步，避免复位释放顺序导致亚稳态
- [ ] **CDC 路径是否有虚假收敛（re-convergence）**：经不同同步链到达目的时钟域的相关信号是否重新汇聚导致时序窗口不一致
- [ ] **Gray 码 FIFO**：async FIFO 的读写指针是否使用 Gray 码编码，深度是否为 2 的幂次
- [ ] **CDC 约束文件**：是否在综合/实现阶段提供了 `set_false_path` 或 `set_clock_groups` 约束，避免工具对 CDC 路径做无效时序优化

## §5 EDA LA 友好性

- [ ] 不要依赖 EDA 直接探测深层内部数组
- [ ] 不要让调试器直接探测 128/512-bit 超宽内部总线
- [ ] 不要直接探测 RAM-like array、multi-dimensional array、动态索引 net
- [ ] 建议增加可选 DEBUG 宏下的 32-bit/64-bit debug bus
- [ ] debug bus 必须是寄存器输出，不要是复杂组合 wire
- [ ] debug bus 应从 top 或上级模块导出，避免从深层级点选内部 net
- [ ] 错误现场应使用 latch（锁存第一拍，不被后续覆盖），而不是依赖 LA 正好采到瞬间
- [ ] debug 逻辑必须不影响默认功能路径
- [ ] debug 逻辑必须可通过宏 `ifdef` 关闭

## §6 验证条件

根据模块类型选择合适的 PASS 判据：

### 压缩链路模块
```text
block mismatches = 0
o_overflow = 0
o_error = 0
[SIM_RESULT] PASS
```

### AXI/AXIS 模块
```text
desc/status/data handshake 正常
tlast/tkeep 正常
mismatch = 0
error = 0
[SIM_RESULT] PASS
```

### Frame 类模块
```text
frame_count 正确
frame_done 正确
frame_size 正确
无提前结束
无跨帧残留
[SIM_RESULT] PASS
```
