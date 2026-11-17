---
name: spinalhdl-rtl-workflow
description: >
  SpinalHDL RTL 设计、展开诊断和 SpinalSim 功能验证工作流。编写或修改 Scala
  Component、Bundle、Stream、FSM、Mem、CDC、BlackBox，定位 WIDTH MISMATCH、
  SCOPE VIOLATION、锁存、组合环，或搭建/调试 SimConfig、Verilator 仿真及 Python/Scala
  bit-exact 参考模型比对时使用。适用于从 Verilog 封装到 SpinalHDL 的任务；生成 RTL 后的
  ModelSim/Questa 验证可配合 build-testbench；纯 Scala 软件、纯 HDL 与厂商实现流程使用相应工具。
---

# SpinalHDL RTL 工作流

## 1. 探查当前工程

读取适用项目规则和目标上下文；定位 build.sbt/build.sc、project/、现有生成入口与测试入口。
记录 Scala/Spinal 版本、有效 compiler plugin、后端版本、时钟复位配置和输出位置。
保留已有构建布局、依赖版本、顶层端口与生成策略。插件可能来自公共构建设置，不能只 grep 一个 build.sbt 就认定缺失。
存量工程只读遵从生效版本，不擅改 build.sbt/build.sc/project/build.properties；空工程复制随包构建、sbt 版本与忽略规则模板，采用 Test JVM 隔离和独立生成目录，详见[工程与编译链](references/05-project-toolchain.md)。
首次执行确认 java/sbt/verilator/g++/make 的实际路径与版本构成同一 OS/ABI 闭环；Windows 与 WSL 不混用本地库或构建缓存。

## 2. 确定最小硬件契约

从用户需求、接口文档和测试确定宽度/signedness、算术溢出/舍入语义、握手、延迟、吞吐、帧/行边界、消隐间隔与排空周期（flush cycles）、reset、时钟域、存储读写冲突与延迟及参数边界。
明确外部集成边界；Testbench 的理想存储模型不能自动代表真实存储/DMA 的请求、响应、背压与顺序协议。
仅对会改变外部行为的关键缺失信息提问；可按项目惯例确定的局部选择直接执行。
修改前读取以下相关参考，检查直接上下游。

| 当前任务 | 读取 |
| --- | --- |
| 初始化工程、依赖/后端兼容、JVM 隔离、目录与跨平台工具链 | [工程与编译链](references/05-project-toolchain.md) |
| RTL 编写、迁移、位宽或软件/硬件混淆 | [语言语义](references/01-language-semantics.md) |
| 编译、展开或后端失败 | [错误速查](references/02-errors-cheatsheet.md) |
| Stream、FSM、Mem、CDC、BlackBox、命名 | [设计检查](references/03-rtl-recipes.md) |
| 仿真、超时、随机激励、测试入口 | [仿真验证](references/04-sim-validation.md) |

## 3. 修改与验证

采用符合契约的最小修改；优先现有库算子和项目范式，不重写无关逻辑。
编码遵循硬件友好型 Scala 规范：硬件引用用 `val`，复杂逻辑按 `Area`/具名节点组织，控制与数据路径分别设计复位，`Mem` 端口保持清晰可推断结构，不新增自定义隐式转换；细则见[语言语义](references/01-language-semantics.md)与[编码护栏](references/03-rtl-recipes.md)。
按变更选择验证层级：

- Static Check：文档或静态检查；不能声称编译/功能通过。
- Build / Elaboration：RTL 变化运行项目生成入口，核对本次生成物和外部端口。展开检查不是完整 CDC 或综合证明。
- Targeted Test：算术、FSM/计数边界、握手/流水线、Mem 或 CDC 行为改变时运行聚焦仿真。使用独立参考模型（Scala 或 Python 向量）、确定采样相位、断言与覆盖条件；按需覆盖极值、帧间隙、反压和 flush。
  期望值不得从 DUT 输出反推；序列比对先检查长度相等，预期有输出的用例还需 `expected.nonEmpty`，再使用 zip/逐项比对，防止空集合静默通过。合法零输出用例单列，检查零输出与实际触发的拒绝/过滤条件。
- Regression：公共模块、总线、顶层连接变化运行受影响回归。生成 RTL 的 ModelSim/Questa 验证可配合 `build-testbench`；保留项目已有 Makefile 与 ROM 暂存约定。
- Runtime / Hardware：仅实际执行后报告。仿真不证明 BRAM 推断、时序收敛或物理 CDC 安全。

执行命令优先项目原生入口。需墙钟保护时使用：

```text
python <skill-dir>/scripts/run_checked.py --cwd <project> --timeout 1800 --log <run-log> -- sbt -batch "Test / runMain pkg.MySim"
```

1800 只是示例预算；根据依赖冷启动、C++ 构建和仿真规模调整。脚本只负责进程/日志，不注入 Scala watchdog，也不判定功能通过。
每次使用独立日志路径；保留完整错误与退出码。有效断言、非零测试/事务数及收尾证据决定仿真是否通过。

失败后按证据定位实现、测试、模型或环境归属。数据/像素失配默认依次隔离：激励与参考模型参数 → 输出采样相位 → 存储读写延迟与流水线对齐 → 地址与帧/行边界 → DUT 算术；已有直接证据可优先定位对应环节，不盲改算术。
C++ 包装层编译失败先核对实际 Verilator 路径、headers/VERILATOR_ROOT、JDK 与 Spinal 版本及完整诊断；仿真未启动不能判算法失败。不要为获得 PASS 弱化 checker、标记 CDC 豁免或改变算术契约。
工具链、license、依赖阻塞时完成可用的静态检查并报告阻塞；不拼凑替代工具链。

## 4. 报告与停止

报告改动与关键契约、实际命令/结果/验证深度、当前生成物、未覆盖风险。
功能仿真报告 seed、执行用例/事务数、scoreboard 剩余量与完成条件；不能用进程退出码替代这些证据。
目标及匹配验证完成后停止。不自动安装、部署、提交或推送技能。

## 随包资源

`assets/build.sbt.template`、`assets/build.properties.template` 与 `assets/gitignore.template` 是空工程固定基线；使用范围和历史验证边界见工程与编译链参考，不覆盖存量工程。
`assets/SimTemplate.scala` 展示 8 bit 模加组合 DUT 的独立模型和检查收尾；复制前按项目 package、版本与入口调整，示例不是已在目标环境验证的 IP。
`evals/evals.json` 提供技能行为评估情景。`proposal.md` 是创建背景，执行任务时无需加载。
