# 编译链与工程骨架

## 存量工程：遵从生效配置

只读探查 build.sbt/build.sc、project/build.properties、project/Dependencies.scala、公共 settings、子项目与插件设置。记录生效 Scala binary version、Spinal 四件套版本和 idsl plugin 注入位置，不能因子模块未写而重复添加。
不为修复 RTL/仿真错误擅改依赖、Scala、sbt 或全局工具安装。配置不匹配时报告实际证据；只有用户明确授权构建迁移才修改版本。保留既有目录、生成配置及仿真入口；既有 src/main 仿真程序也不能仅为本规范搬迁。

## 空工程：复制精确模板

仅在确认目标目录为空或用户明确要求初始化时复制；不覆盖存量文件：

| 随包资源 | 新工程目标 |
| --- | --- |
| assets/build.sbt.template | build.sbt |
| assets/build.properties.template | project/build.properties |
| assets/gitignore.template | .gitignore |
| assets/SimTemplate.scala | src/test/scala/SimTemplate.scala |

模板锚定 JDK 17、sbt 1.13.1、Scala 2.13.12、Spinal core/lib/sim/idsl-plugin 1.15.1；英文历史资料另记录 Verilator 5.052 在 Linux 跑过 SpinalSim/生成 RTL。本包本轮没有重现该组合，不能声明已在当前 Windows 或其他主机验证。版本可获得性、仓库解析与后端兼容须在使用现场确认；离线缺依赖时报告阻塞，不换成随机相近版本。
版本不使用范围；四件套由一个 spinalVersion 变量绑定。若用户指定其他基准栈，按其契约确认整组兼容并记录差异，不将 Scala 2.12 等既有项目一概判废弃。历史资料曾记录 1.10.2a 的后端包装编译失败，因此不将其与任意 Verilator 5.x 组合视为等价兜底。

## 源码与生成物

新工程按以下布局建立：

```text
build.sbt
project/build.properties
src/main/scala/<pkg>/    # RTL、Bundle、Config、生成入口
src/test/scala/<pkg>/    # SimConfig、scoreboard、参考模型
rtl/gen/                # 生成 RTL 及相关初始化文件
simWorkspace/<run-id>/   # 本次仿真、波形与后端编译缓存
```

新工程中 sim import 与仿真辅助观测代码置于 Test scope；保持主 RTL 源码不依赖 spinal.core.sim。随包 SimTemplate 将演示 DUT 与驱动放在同一 Test 文件以独立展示，实际模块提取到 main 时将仿真驱动留在 test。
生成入口显式传入 `SpinalConfig(targetDirectory = "rtl/gen", defaultConfigForClockDomains = ...)`；省略号需用已确定的 resetKind/resetActiveLevel 等契约填写，不能直接复制为可编译代码。初始化文件与下游 ROM 暂存路径一并检查，不能只移动 .v。
仿真按当前版本 API 配置 workspacePath/workspaceName，参数配置及并发进程使用唯一 run-id，波形和日志记录对应路径。生成目录加入 .gitignore；若项目要求版本化 RTL，则按项目交付规则处理。

## JVM 与并发边界

模板固定 `Test / fork := true` 与 `Test / parallelExecution := false`。前者让 Test scope 的仿真主程序/测试使用独立 JVM，降低本地库生命周期对 sbt 进程的影响；后者限制本 sbt 实例中的框架测试并行。两者不保证消除所有 JNI 错误，也不串行化独立 sbt 进程、手工 fork 或不同项目任务。每个并发运行仍需独立 workspace；Compile / runMain 不受 Test / fork 设置保护。
运行使用 `sbt -batch "Test / runMain ..."` 等真实入口，并保留进程树墙钟保护；不要用 `sbt test` 代替普通 App 的执行证明。

## 工具链同域探查

首次执行记录 JAVA_HOME、java/sbt/verilator/g++/make 实际路径及版本（不输出其他无关环境变量或凭据）。PowerShell 用 Get-Command，Linux/WSL 用 command -v；Windows 可由随包 runner 解析 PATHEXT 启动器。
JVM、本地库、C++ 编译器与 make 必须形成同一目标 OS/ABI 的兼容闭环。可全部在 Linux/WSL，或使用已验证的 Windows 原生 JDK/sbt + MSYS2/MinGW 工具组合；不要求所有可执行文件来自同一个发行包。不要让 Windows JVM 直接加载 WSL 的 .so，或混用 Windows/Linux target 与 simWorkspace 缓存。跨环境使用独立 checkout 或独立输出/缓存目录，并明确路径转换边界。
探查失败或工具缺失时保留命令和诊断，不自行安装、升级或拼凑替代链。
