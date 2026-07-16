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

- [ ] 宽组合路径 — 单时钟内超过 10 级 LUT 的路径
- [ ] 大 mux（>32:1）— 考虑 case 分级或二叉树
- [ ] 超宽数据总线直接进入复杂逻辑 — 如 512-bit 总线直接进加法/比较
- [ ] RAM/FIFO 推断不稳定
- [ ] block RAM / distributed RAM 推断是否符合预期
- [ ] reset 过重导致资源浪费或时序压力（复位所有数据路径寄存器）
- [ ] 大量高扇出控制信号 — 如复位信号扇出 >1000
- [ ] 大量跨层级 internal net 被 debug core 探测后可能影响实现
- [ ] 是否需要将 memory、FIFO、line buffer、history buffer 拆成独立子模块

## §3 时序优化

- [ ] 目标时钟域下是否存在长组合路径
- [ ] ready/valid 反压链是否过长 — ready 条件是否跨多级组合逻辑
- [ ] input valid 到 output ready 是否存在组合环
- [ ] 宽数据路径是否缺少寄存器切分
- [ ] 计数器/比较器/地址计算是否在同一拍堆叠过多
- [ ] min/max/sum/checksum/encode 等计算是否需要 rolling 或 pipeline
- [ ] 状态机 next-state 是否过重
- [ ] FIFO full/empty 到 upstream ready 是否组合路径过深
- [ ] 是否需要使用 registered ready
- [ ] 是否需要把"计算"和"状态推进"拆拍

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
