# RTL 风险分类标准

用于在审计报告中标记每个发现点的风险等级。

## A 类：必须优先处理

这些写法可能导致综合、时序、上板或 EDA 调试问题，**必须修复**才能通过工程成熟度要求。

### 检查清单

| # | 风险项 | 典型代码模式 |
|---|--------|-------------|
| 1 | 综合路径中的复杂 function | `out <= heavy_func(input_bus);` |
| 2 | automatic function 用于关键数据路径 | `function automatic ...;` |
| 3 | for-loop 串行依赖导致长组合链 | 循环体内结果依赖上一轮迭代 |
| 4 | variable part-select | `data[idx*WIDTH +: WIDTH]` |
| 5 | 动态数组索引 | `reg_array[index]` |
| 6 | unpacked reg array 被大量层级引用 | 数组在多个模块中被直接引用 |
| 7 | 大量 internal RAM-like array 暴露在主模块中 | 主模块内部大容量 `reg mem [0:D-1]` |
| 8 | 超宽内部总线直接被组合处理 | 直接对 512-bit 总线做组合运算 |
| 9 | valid/ready 组合环 | ready 条件通过组合路径依赖自身 |
| 10 | frame_done 未等待 pipeline/FIFO drain | 帧结束信号不含 pipeline 排空握手 |
| 11 | 错误状态下 ready 行为不清晰 | error 触发后 ready 未明确置高/低 |
| 12 | reset/clear 不完整导致跨帧残留 | 部分跨帧寄存器未在帧结束、帧开始时正确初始化 |
| 13 | 同一 `always @(posedge clk)` 内混合 blocking/non-blocking | 用 `=` 算中间值，用 `<=` 写寄存器 |

## B 类：建议优化

这些写法不会导致功能错误，但可能影响综合质量、时序余量、调试效率或代码可维护性。

### 检查清单

| # | 风险项 | 说明 |
|---|--------|------|
| 1 | 状态机编码不清晰 | 建议用 parameter 定义 state names |
| 2 | next-state 组合逻辑过大 | 考虑拆成多个小状态机或流水线 |
| 3 | 宽 mux 可以改成 case 或分级寄存 | >8:1 mux 考虑分级 |
| 4 | RAM 可以拆成独立子模块 | 提高调试可见性和可维护性 |
| 5 | debug 信号应打包成 bus | 标准化为 32/64-bit debug bus |
| 6 | 计数器位宽过大或过小 | 使用 $clog2 确定最小位宽 |
| 7 | 常量参数不一致 | 参数化同类常量 |
| 8 | block_x/block_y/line/row/col 位宽不明确 | 用 parameter 定义 |
| 9 | signed/unsigned 比较混用 | 显式声明 signed/unsigned |
| 10 | `last` 信号没有与 fire 绑定 | `last` 应只在 `valid && ready` 时有语义 |

## C 类：只报告，不修改

以下情况只记录观察，不要贸然修改。

### 清单

| # | 风险项 | 原因 |
|---|--------|------|
| 1 | 参数化结构复杂但目前功能稳定 | 修改收益不足以覆盖回归风险 |
| 2 | 已有 testbench 依赖的时序行为 | 修改 latency 会导致 TB 失败 |
| 3 | 与外部 IP 接口相关的时序 | 外部时序不可控 |
| 4 | CDC 模块 | CDC 修改涉及跨时钟域验证 |
| 5 | vendor FIFO/RAM wrapper | 供应商 IP，不能修改 |
| 6 | AXI/AXIS 标准接口逻辑 | 标准协议，不能改 |
