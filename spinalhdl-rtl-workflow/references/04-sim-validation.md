# 仿真验证

## 选择真实入口

读取源码继承/定义和 build scope，而不是看文件名是否以 Sim 结尾。

| 入口类型 | sbt 示例 |
| --- | --- |
| src/main 中 object extends App / main | `sbt -batch "Compile / runMain pkg.MySim"` |
| src/test 中普通 main / App | `sbt -batch "Test / runMain pkg.MySim"` |
| 测试框架已发现的 suite | `sbt -batch "testOnly pkg.MySuite"` |

多模块项目加项目 scope；mill 复用已有任务。框架测试检查发现/执行用例数，普通 main 检查实际进入仿真和断言/事务收尾；零测试和仅 println 都不证明正确。

## 三层超时

1. `SimTimeout(duration)` 限制仿真时间，duration 不是周期数。按仿真时间精度和 clock period 换算。
2. 按对应时钟域采样计数的 watchdog 检查有限周期内进展，区分持续背压与真正死锁；测试允许的停顿应计入预算。
3. `scripts/run_checked.py` 控制整个命令的墙钟预算，含依赖下载、Scala/C++ 构建与运行。根据冷/热启动调整，不静默重试；超时杀子进程树并保留日志。

启动时初始化输入与 ready、启动时钟和项目规定的复位；明确采样点，避免与驱动发生竞态。波形按问题开启并记录本次路径。

以下片段放在已有 doSim 中，`duration`、`cycleBudget` 与时钟域由测试契约确定；不是通用固定预算：

```scala
SimTimeout(duration) // 仿真时间单位；即使时钟停止也能限制仿真时间
var completed = false
fork {
  dut.clockDomain.waitSampling(cycleBudget) // 目标域采样周期，不是时间单位
  assert(completed, s"not complete within $cycleBudget cycles")
}
// 主线程在激励、比较、协议断言和有界排空全部通过后执行：
// completed = true
// simSuccess()
```

若另设无进展 watchdog，仅在实际 fire/规定进展事件发生时清零；允许背压时间计入阈值。不要在 watchdog 中调用 simSuccess。

## Stream 最小覆盖

先定向，再固定 seed 随机。source 的 valid 和 sink 的 ready 独立控制；factor 名称/取值不是覆盖证明。
- 满吞吐：连续 valid/ready，验证无预期外气泡。
- 持续背压：ready 拉低多个周期，验证 valid/payload 稳定，然后恢复并排空。
- 输入气泡：valid 间歇，确认不生成幽灵输出。
- 随机：记录 seed，覆盖不同 source/sink 速率，边界数据与复位行为。

用 Scala Queue 存独立模型结果：input fire 时 enqueue；output fire 时要求队列非空，dequeue 比较。输入/输出分别计数；结束先停止新输入，再保持消费直到有界排空。
完成条件：输入事务 > 0，输出数等于预期，队列为空，所有比较/协议断言通过。缺少任何一项都不能声明功能通过。允许丢弃或乱序的协议按其契约使用 ID 和独立计数，不能硬套顺序模型。

### 停顿稳定性检查器

在已初始化的仿真内启动；按项目驱动/采样约定在同一时钟域检查。下面以 UInt/Bits payload 的 `dut.io.output` 为例。`inReset` 是测试按实际极性/复位契约维护的 Scala Boolean，不是直接读取为硬件 Bool。

```scala
var stalledPayload: Option[BigInt] = None
fork {
  while (true) {
    dut.clockDomain.waitSampling()
    val valid = dut.io.output.valid.toBoolean
    val ready = dut.io.output.ready.toBoolean
    val payload = dut.io.output.payload.toBigInt
    if (inReset) {
      stalledPayload = None // 仅当协议允许复位中取消在途事务
    } else {
      stalledPayload.foreach { previous =>
        assert(valid, "valid withdrawn while stalled")
        assert(payload == previous, "payload changed while stalled")
      }
      stalledPayload = if (valid && !ready) Some(payload) else None
    }
  }
}
```

Bundle payload 应在 Scala 中采样全部 data/last/keep/ID 等字段形成不可变快照，并按同样模式比较；也可在 elaboration 阶段预先暴露完整扁平观测信号。不要在 doSim 运行线程调用 asBits 创建硬件转换。输入激励端也应检查相同性质。

## 独立模型与测试归属

全精度和、模运算、饱和、signedness 先用 Scala 整数公式定义，不能复制 DUT 结构或把 DUT 输出填成 expected。Mem 按规范建模读写冲突与延迟；FSM 检查状态转移和输出周期。
测试失败先定位 DUT/测试/checker/模型/环境；修改 golden 需独立协议或数学证据。

集合比对先执行长度/非空断言，再 zip；Python zip 与 Scala zip 都会截短至较短序列：

```scala
assert(expected.nonEmpty, "positive-output case produced no reference vectors")
assert(actual.length == expected.length, "missing or extra outputs")
actual.zip(expected).zipWithIndex.foreach { case ((got, ref), index) =>
  assert(got == ref, s"mismatch at $index: got=$got expected=$ref")
}
```

预期合法零输出的拒绝/过滤用例独立检查实际输入事件、拒绝原因和 `actual.isEmpty`；不能用它替代正常路径非零覆盖。外部 Python 向量还需核对生成参数、数量、路径和文件存在性，不能缺文件就跳过。
图像/帧流显式验证首末像素、行场边界、消隐、连续帧与 flush；对真实存储/DMA 按请求/响应、读延迟、背压、顺序和完成协议建模，不能仅凭理想数组模型宣称集成通过。
失配默认沿激励/模型参数 → 采样相位 → 存储延迟/流水对齐 → 地址/帧行边界 → 算术逐项取证；已有直接证据时优先对应环节。

`assets/SimTemplate.scala` 是组合模加的最小示例，不代表 Stream 测试。复制后使用项目已有构建与兼容后端；不要默认添加 --no-timing。
