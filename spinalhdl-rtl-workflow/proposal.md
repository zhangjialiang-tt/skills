# SpinalHDL RTL 工作流技能提案（复核修订版）

## 目标与边界

在本目录创建 `spinalhdl-rtl-workflow`：支持 SpinalHDL RTL 设计、展开错误定位和 SpinalSim 功能验证。复用项目构建与时钟复位契约；不自动升级依赖，不代替综合、时序分析、CDC 签核或板上验证。SoC 架构与形式化验证留给后续独立技能。

## 结构

- `SKILL.md`：探查 → 契约 → 最小修改 → 分层验证 → 证据报告。
- `references/01-language-semantics.md`：Scala/硬件/仿真边界、算术与复位。
- `references/02-errors-cheatsheet.md`：错误证据与最小修复路径。
- `references/03-rtl-recipes.md`：Stream、FSM、Mem、CDC 与集成检查。
- `references/04-sim-validation.md`：入口选择、watchdog、scoreboard 与覆盖清单。
- `scripts/run_checked.py`：跨平台命令执行、完整日志、可配置墙钟超时与子进程树终止。
- `assets/SimTemplate.scala`：独立模型与明确结束条件的示例；依赖项目现有构建。
- `evals/evals.json`：可重复的技能应用测试。

## 复核后确定的技术契约

1. 区分 elaboration 的硬件 AST 构造与仿真运行时。仿真驱动 DUT 使用 `#=`，读取使用 `.toBigInt` / `.toBoolean` 等；判断语义边界，不按 doSim 内出现的关键字一刀切。
2. `SCOPE VIOLATION` 是声明作用域/赋值作用域问题，与 CDC 分开诊断。`crossClockDomain` 标签豁免检查，不实现同步；多 bit 数据按一致性契约选择握手、异步 FIFO 或适用的 Gray 编码方案。
3. 位宽修复先确定完整精度、模运算或饱和语义及 signedness。不能将 `+^` 随意替换为 `+` 来消除报错。
4. 核对生效的 Scala binary version、Spinal 核心/库/idsl compiler plugin 版本；内部 `when_*_lN` 名字不是插件失效判据。只检查本次生成物及外部端口契约。
5. 普通 main/App 用对应作用域 `runMain`；测试框架 suite 用 `testOnly`。退出码零不足以证明测试执行，必须核查用例数、事务数、断言和收尾证据。
6. `SimTimeout` 参数为仿真时间单位，不是周期数。分别预算仿真时间、按时钟域计数的进展 watchdog 和构建/运行墙钟时间。冷启动不能强套 60/120 秒。
7. Stream 测试分离 source valid 与 sink ready；定向验证满吞吐、持续停顿与恢复、气泡，再做可复现随机。停顿时保持 valid/payload，按 fire 计数；结束时非零事务、scoreboard 排空且计数一致。
8. Verilator `--no-timing` 仅在实际版本与模型语义允许时使用，不作为通用补丁。
9. SpinalEnum + switch 与库 FSM 都合法；按项目惯例选取。存储器推断、CDC 安全和实际时序不能由 elaboration 成功推出。

## 验证与交付

- 静态：frontmatter、引用和资源存在；检查上述语义边界。
- 脚本：成功、非零退出、完整日志、超时与子进程终止；不依赖下载硬件工具链。
- 技能：至少三个情景，覆盖 scope/CDC/位宽、仿真入口与假通过、Stream/环境兼容；对比有技能和无技能结果。
- Scala 示例：只有在匹配的项目版本和后端实际执行后，才能标记编译或功能验证通过。环境阻塞时保留待执行命令，明确实际验证深度。

创建不含全局部署、Git commit/push 或依赖安装。已有项目的 build.sbt 不被模板覆盖；空项目应先从官方对应版本模板确认兼容组合，再固定版本，避免发布未经执行验证的通用构建模板。
