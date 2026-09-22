# 任务：通用化改进 build-testbench 技能

## 背景
build-testbench 是一个 ModelSim/QuestaSim 仿真框架搭建技能（路径：C:\Users\zhangjl\.workbuddy\skills\build-testbench\），
定位是【通用技能】，服务任意 Verilog/VHDL RTL 模块的仿真框架搭建（L1 smoke + L2 功能验证）。
近期一次"同 DUT 不同参数集"的使用暴露了几处通用缺陷。本任务只做【通用化】改进，
严禁加入任何图像/分辨率/数据放大等场景专属内容（那属于项目经验，不入技能）。

## 修改前必读
1. 先通读 SKILL.md、scripts/ 下脚本（bootstrap_testbench.py / build_fileset.py / scan_rtl_modules.py）、references/ 全部文档、assets/ 模板、tests/ 用例，理解现有结构与设计原则。
2. 检查 SKILL.md frontmatter 是否含 agent_created: true；若无，在修改前向用户报告（skill-creator 只允许改 agent 创建的技能）。
3. 遵循技能自身文档中"零外部依赖 / 确定性输出 / 渐进式降级 / 不改变 RTL 源码"的设计原则。

## 修改项（按优先级，全部通用化表述）

### A1（核心，脚本级）：build_fileset.py 支持 VHDL component/entity 实例化闭包解析
现状缺陷：依赖闭包扫描对 VHDL 只能解析 entity 声明，无法解析实例化语句
（如 `x : entity work.y` 与 `x : y port map`），导致任何 VHDL 工程 bootstrap 后
fileset.f 都缺依赖、需手工补。
要求：
- 在 scan_rtl_modules.py / build_fileset.py 增加 VHDL 实例化语句解析：
  从 VHDL 源码提取 component 实例名与端口映射中引用的 entity，并匹配已扫描到的 entity 声明。
- 未命中的实例化引用必须进入 diagnostics / summary.unresolved_dependencies，输出候选 entity 列表，便于审计与手工补全。
- 不得破坏现有 Verilog 解析行为与拓扑排序；输出格式向后兼容（schema 字段只增不改）。
- 在 tests/ 增加 VHDL component 实例化解析的正向用例 + 未命中诊断用例。
- 渐进式降级：解析器对无法识别的 VHDL 结构保持 warning，不 FAIL。

### A2（文档）：references/troubleshooting.md 补"厂商 IP / sim-only 仿真模型不在闭包"条目
现状缺陷：仅仿真存在的支撑模型（如 IP 行为模型、厂商 DDR/PHY 仿真模型）不属于 RTL 依赖闭包，
fileset 需手工追加，但文档无通用恢复规则。
要求：新增一条通用规则：仿真专属模型统一放 tb/ 目录，在 fileset.f 末尾追加；
示例用占位描述（如 <vendor_sim_model>.v），禁止出现项目专有文件名。

### B1（文档，新增）：references/framework-cloning.md —— 已有框架的参数化克隆工作流
现状缺陷：技能只定义了 from-scratch 路径（sub-agent 分析 RTL → simulation_plan.md → 新写 TB），
缺少"同 DUT、参数集不同（位宽/深度/尺寸/帧数等）时，克隆已验证框架"的通用工作流，
也未明确何时可跳过行为刻画（L2-C）直接复用已验证 L2 计划（L2-V reuse）。
要求新增文档，内容：
- 适用条件：DUT 文件未变、仅参数化点变化（列出 DUT generic/parameter 清单）
- 复用顺序：复制已验证框架（Makefile/fileset/TB 支撑模型）→ 只改参数化点 → 重生成输入数据 → 过 L1 门禁 → L2
- 参数随动审计：列出与 DUT 参数相关的 TB 硬编码常量类别（超时、突发计数、输入文件长度、边界标记计数等）需同步修改
- 何时可跳过 sub-agent L2 行为刻画：spec/golden/reference 已知且 DUT 未变 → 克隆 + 参数化即 L2-V reuse，并引用 config.mk 默认级别切换
- 禁止出现任何项目/图像/分辨率具体数值与文件名，全部用通用参数名表述。

### B2（模板注释）：references/l2-tb-template.v 头部加"参数随动检查清单"注释
要求：在模板头部注释段增加通用 checklist，提醒 TB 中与 DUT 参数相关的硬编码常量
（仿真超时、burst 计数、输入数据长度、边界标记计数等）在 DUT 参数变化时必须同步审计，
避免静默错误。通用表述，不写具体数值。

## 明确不做（范围外）
- 图像数据放大/插值/golden 重算类经验 → 不入技能
- 任何具体项目（如 guogai）相关数值、文件名、分辨率 → 不入技能
- 不修改 Makefile 模板、sim.do/wave.do 模板（除非有直接关联的缺陷）
- 不做与上述 4 项无关的重构或格式化

## 验证门禁（必须全部通过）
```powershell
cd C:\Users\zhangjl\.workbuddy\skills\build-testbench
python -m py_compile scripts/*.py
python -m pytest tests/ -q
python scripts/validate_skill_package.py    # 检查 SKILL.md 引用路径都存在
```
新增/修改的脚本与用例需随 pytest 全绿。

## 输出要求
1. 修改文件清单（路径 + 每处改动的摘要）
2. 验证结果（上述三条命令实际输出摘要）
3. 若 frontmatter 缺 agent_created 或发现其他阻塞，先报告再动工
4. 未运行验证不得声称完成
