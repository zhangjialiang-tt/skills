# 14 项问答测卷设计（probes）

> 重建说明：按 v2.1 设计记录重建。测卷区分 answered / implicit / undocumented 三态。

14 项问答（probes）按六个维度组织；寄存器文件类模块追加 ADDRESS_MAP 维度（v2.1 新增）：

| # | 维度 | 问题 | 可答性判据 |
|---|---|---|---|
| 1 | HANDSHAKE | valid/ready 的来源与目的地 | 端口连接与驱动逻辑 |
| 2 | HANDSHAKE | data_hold：输出在无新数据时是否保持 | 保持寄存器/组合直通 |
| 3 | HANDSHAKE | 握手协议类型（valid-ready / credit / 无握手） | 协议逻辑 |
| 4 | PROTOCOL | 帧边界如何标定（sof/eof/计数） | 帧头尾标记逻辑 |
| 5 | PROTOCOL | 反压传播路径 | ready 链路 |
| 6 | PROTOCOL | 协议常量（超时/计数上限） | 常量定义与来源 |
| 7 | TIMING | 跨时钟域信号清单与同步方式 | CDC 结构 |
| 8 | TIMING | 输出采样点（RisingEdge 后 ReadOnly？） | 采样逻辑 |
| 9 | FSM | 状态机状态清单与转移条件 | case/if 转移 |
| 10 | FSM | 异常态处理（非法态恢复） | default 分支 |
| 11 | NAME | 关键信号命名与含义 | 命名一致性 |
| 12 | NAME | 缩写是否在模块内声明映射 | 声明处注释 |
| 13 | PARAM | 参数默认值与约束范围 | parameter 声明 |
| 14 | ADDRESS_MAP | （寄存器文件类）RO/RW/触发/位图门控/读覆盖/地址别名 | 寄存器译码逻辑 |

## 三态判据

- **answered**：注释或文档中可直接找到答案（引用行号）。
- **implicit**：源码逻辑可推导，但注释未写明。建议 L0 补契约注释，不计为"缺失"。
- **undocumented**：源码不可推导或行为不确定（如依赖外部时序假设）。
