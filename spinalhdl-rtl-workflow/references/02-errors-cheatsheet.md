# 错误证据与修复路径

先记录完整错误、文件行号、入口、版本与当前修改，再读取源码。一次只验证一个有证据的根因假设。

| 症状 | 检查与最小修复 |
| --- | --- |
| WIDTH MISMATCH | 确定 signedness/全精度/模运算/饱和契约；检查运算宽度与目标宽度。全精度 `+^` 保留进位，不能改成 `+` 来掩盖问题。 |
| SCOPE VIOLATION | 检查声明与赋值所在条件/层次作用域；调整共享信号位置或使用范围。不要用 BufferCC 修复作用域。 |
| CLOCK DOMAIN CROSSING | 确认真实源/目标域与数据一致性契约，选择同步器/握手/FIFO；标签不能实现同步。 |
| LATCH DETECTED | 检查组合路径覆盖，添加符合契约的默认值或完整分支；区分寄存器保持。 |
| COMBINATIONAL LOOP | 沿完整组合依赖追踪 ready/valid/反馈；按延迟契约插入合适存储/流水级，重新检查吞吐。 |
| Hierarchy violation | 检查组件所有权、连接层次及是否在仿真线程构造硬件；不要一概归因于赋值操作符。 |
| 内部 when_*_lN 名字 | 可能是合法内部条件名。核对有效 idsl compiler plugin、Scala binary version 与 Spinal 版本；按接口规范检查本次生成的顶层端口，不能 grep 名字就判失败。 |
| %Error-NEEDTIMINGOPT | 查看完整诊断、后端版本与模型 delay/event 使用。按语义选择受支持 timing 模式；只有确认忽略时序语义可接受才用 --no-timing，不默认追加。 |
| sbt 成功但测试未执行 | 确认 main/App 与测试框架 suite 区别、Compile/Test scope、suite 匹配数与事务完成记录。零测试不算通过。 |
| 仿真不退出 | 检查时钟启动、复位、握手、采样点和 scoreboard 排空；添加独立进展 watchdog，不能仅扩大超时。 |

环境失败与设计失败分开报告；保留最早错误，而非只看最后几十行。版本不确定的 API 在项目依赖源码或对应版本官方文档中确认。

官方入口（页面以 master 为例，使用时切换到项目对应版本）：
- https://spinalhdl.github.io/SpinalDoc-RTD/master/SpinalHDL/Design%20errors/scope_violation.html
- https://spinalhdl.github.io/SpinalDoc-RTD/master/SpinalHDL/Simulation/utils.html
- https://spinalhdl.github.io/SpinalDoc-RTD/master/SpinalHDL/Simulation/bootstrapping.html
