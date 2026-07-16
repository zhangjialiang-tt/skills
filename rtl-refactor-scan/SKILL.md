---
name: rtl-refactor-scan
description: RTL 工程成熟化扫描与小步重构。对 Verilog/SystemVerilog 模块执行五大维度（可综合性/可实现性/时序/仿真上板一致性/EDA调试友好性）成熟度评估，输出结构化审计报告并制定最小安全重构计划。快速语法检查/注释增强类请求请走 rtl-annotator。触发：RTL代码评审、工程成熟度检查、综合/时序问题诊断、小步重构。
output_contract:
  artifacts:
    - "审计报告_<模块名>.md — 结构化扫描结果（A/B/C 三级风险）"
    - "修改计划_<模块名>.md — 分阶段重构计划（含回归测试命令）"
    - "最终报告_<模块名>.md — 重构完成摘要"
  format: "markdown"
  constraints:
    - "不改变模块外部接口"
    - "不改变协议语义"
    - "不修改已有 testbench"
triggers:
  include:
    - "RTL 检查/扫描/评审/审计"
    - "代码成熟度/工程化检查"
    - "综合/时序/上板问题诊断"
    - "RTL 小步重构/优化"
  exclude:
    - "新功能开发（非扫描/重构）"
    - "纯 testbench 编写（无 RTL 修改）"
    - "综合/布局布线执行（仅扫描分析）"
---

# RTL 工程成熟化扫描与重构

## 概述

本 Skill 提供了一套端到端流程，将 RTL 模块从"功能仿真可用"提升到"可综合 + 可实现 + 时序友好 + 上板稳定 + 易调试"。以**先分析、后计划、再修改、最后回归验证**为核心原则，不做一步到位的大重构。

## 流程概览

```
用户指定模块/目录
    ↓
[Phase 1] 定义扫描范围 → 确认时钟/复位/接口/协议
    ↓
[Phase 2] 结构化扫描 → 按 5 大维度 + A/B/C 三级风险检查
    ↓
[Phase 3] 输出审计报告 → 含风险列表/严重度/位置/说明
    ↓
[Phase 4] 最小安全重构计划 → 分阶段、可验证、可回退
    ↓
[Phase 5] 小步实施 + 回归验证 → 每阶段跑 testbench
    ↓
[Phase 6] 最终报告 → 修改摘要/风险消除/剩余风险/下一步建议
```

**每个阶段必须先完成再进下一阶段，不能跳步。**

---

## Phase 1：定义扫描范围

在与用户确认或从需求中明确：

1. **待分析模块及源文件路径** — 不要假设路径，先搜索确认
2. **相关 testbench 目录和回归命令**
3. **相关上级/下级模块**
4. **当前时钟/复位方案** — 单时钟/多时钟/CDC
5. **当前接口协议** — AXI-Stream/自定义 ready-valid / frame-based
6. **功能行为描述** — 如果源文件注释不足，向用户询问

---

## Phase 2：结构化扫描

按以下五个维度分别检查，每个维度的详细检查项见参考文档。
每个发现点记录：位置(行号)、分类(A/B/C)、详细描述、影响评估。

### 检查维度

| # | 维度 | 参考文档 | 说明 |
|---|------|----------|------|
| 1 | 可综合性 | `references/scan-checklist.md` §1 | 综合器能否正确推断，EDA 是否稳定 |
| 2 | 可实现性 | `references/scan-checklist.md` §2 | 资源/扇出/宽路径是否可实现 |
| 3 | 时序优化 | `references/scan-checklist.md` §3 | 组合路径/反压链/流水划分 |
| 4 | 仿真与上板一致性 | `references/scan-checklist.md` §4 | CDC/reset/valid-就绪/跨帧残留 |
| 5 | EDA LA 友好性 | `references/scan-checklist.md` §5 | debug bus / 数组探测 / 宽总线 |
| 6 | 风险分类 | `references/risk-classification.md` | A/B/C 三级标记，C 类只报告不修改 |

### 检查方法

- **读取源文件**：完整阅读待分析的 RTL 文件
- **逐行扫描风险写法**：对照参考文档中的风险清单
- **关注混合 blocking/non-blocking 赋值**：在 `always @(posedge clk)` 中混用 = 和 <= 是核心风险
- **关注 variable part-select**：`data[idx*W +: W]` 模式在 EDA debug 中不稳定
- **关注 unpacked array**：`reg [W-1:0] arr [0:N-1]` 需评估是否拆分子模块
- **关注 reset 策略**：是否完整，是否合理
- **关注组合环风险**：ready/valid 反压链
- **关注 pipeline drain**：frame_done 是否等待全部排空

---

## Phase 3：输出审计报告

按以下结构化模板输出报告，写入 `审计报告_<模块名>.md`：

```markdown
# RTL 成熟度审计报告 — <模块名>

## 一、模块功能概述

## 二、时钟/复位域
| 项目 | 现状 | 评价 |

## 三、数据流路径
pipeline 阶段图或状态机描述

## 四、ready/valid 反压路径
反压路径分析，组合环检查

## 五、pipeline drain 条件

## 六、RAM/FIFO 使用情况

## 七、风险列表
### ⚠️ A 类：必须优先处理
### 🔶 B 类：建议优化
### 🟢 C 类：只报告，暂不改

## 八、上板不一致风险
## 九、EDA LA/debug 不稳定写法
## 十、建议修改项列表
## 十一、推荐的最小修改集合
## 十二、是否建议进入修改阶段
（基于风险严重度和修改收益评估）
```

详细模板见 `references/output-format.md` §1。

---

## Phase 4：最小安全重构计划

在修改前输出计划，等待用户确认。计划必须包含：

1. **修改文件列表**
2. **每项修改内容** — 具体到行号
3. **不修改的内容** — 接口、协议、latency、已有 testbench
4. **是否改变时序 latency** — 明确说明
5. **是否改变 ready/valid/帧行为**
6. **是否改变 reset 行为**
7. **是否需要新增 debug 宏**
8. **回归测试命令和 PASS 判据**
9. **回退方案**

**严格执行：无计划不修改。**

---

## Phase 5：小步实施 + 回归验证

### 修改原则

- 一次只做一个明确的优化主题
- 保持 diff 可读，不做无关格式化/无关重命名
- 不删除有用注释
- 新增注释说明为什么这样写对综合/时序/上板更稳
- 遵守 `Verilog-2001` 风格（非必要不用 SystemVerilog 语法）
- **保持模块外部接口不变**
- **不改变协议语义**
- **不降低 testbench 覆盖率**
- **不绕过错误检查**
- **不为了仿真 PASS 而屏蔽真实问题**

### 修改后验证

```bash
cd <tb-dir>/sim
make sim
```

根据模块类型检查对应 PASS 条件（详见 `references/scan-checklist.md` §验证条件）。

---

## Phase 6：最终报告

完成后输出最终报告，包含：

1. 修改文件列表
2. 修改摘要（每项改了什么、为什么改）
3. 解决了哪些综合/时序/上板调试风险
4. 是否改变接口 / latency / ready-valid 语义 / reset / 帧行为
5. 回归测试命令和结果
6. 剩余风险
7. 下一步建议

---

## 重构模式参考

本 Skill 收录了以下经过验证的重构模式，详见参考文档：

| 模式 | 适用场景 | 参考 |
|------|----------|------|
| 数组标量化 | 小规模 unpacked array（≤16） | `references/refactor-patterns.md` §1 |
| RAM 子模块化 | history/line/frame/cache buffer | `references/refactor-patterns.md` §2 |
| function 去综合路径化 | 关键路径上复杂 function | `references/refactor-patterns.md` §3 |
| variable part-select 显式化 | 固定宽度/数量的总线拆分 | `references/refactor-patterns.md` §4 |
| debug bus 标准化 | 上板调试信号封装 | `references/refactor-patterns.md` §5 |
| 混合赋值分离 | blocking/non-blocking 分离 | `references/refactor-patterns.md` §6 |
| 寄存器化 ready | 切断长组合反压链 | `references/refactor-patterns.md` §7 |

---

## 渐进式参考文档

详情在以下文件中，按需加载：

- `references/scan-checklist.md` — 五大维度详细检查清单 + 验证条件
- `references/risk-classification.md` — A/B/C 三级风险分类标准
- `references/refactor-patterns.md` — 7 种具体重构模式及代码示例
- `references/output-format.md` — 审计报告/修改计划/最终报告模板
- `references/trigger-eval.md` — 触发条件评估（什么情况应该/不应该触发）
- `references/quality-gates.md` — 质量门控检查清单（确保输出质量）

---

## Skill OS 2.0 资产（可移植接口与实证）

| 资产 | 路径 | 作用 |
|------|------|------|
| 可移植接口 | `agents/interface.yaml` | 外部化 Skill IR（job/triggers/excludes/near-neighbor/workflow/decision/failure/evals/trust） |
| 元数据 | `manifest.json` | 打包/安装/registry 识别 |
| 确定性检查 | `scripts/scan_check.py` | 校验生成的审计报告是否满足 5 维度 + A/B/C + 必需章节契约 |
| 实证 | `evals/evals.json` + `evals/smoke_runner.py` | 3 用例（1 smoke + 2 近邻边界）+ 确定性 smoke runner |
| 风险档案 | `reports/output-risk-profile.md` | 输出失败模式与防御策略 |
| 成熟度评分卡 | `reports/output_quality_scorecard.md` | yao-meta-skill 评估门结果 |

---

## 约束

- **不以修改 SystemVerilog 为手段** — 优先保持 Verilog-2001
- **不以精简代码为目标** — FPGA EDA 友好优先于代码短小
- **不以消灭 lint warning 为目标** — 有意义的结构变更优先于静默警告
- **不上板时序分析不在当前范围** — 如有需要单独提出
- **不修改已有 testbench 路径和 golden 数据**

---

## Output Contract

本 Skill 保证输出以下结构化产物：

| 产物 | 文件名格式 | 内容 |
|------|------------|------|
| 审计报告 | `审计报告_<模块名>.md` | 五大维度扫描结果、A/B/C 三级风险列表、修改建议 |
| 修改计划 | `修改计划_<模块名>.md` | 分阶段重构计划、回归测试命令、回退方案 |
| 最终报告 | `最终报告_<模块名>.md` | 修改摘要、风险消除情况、剩余风险、下一步建议 |

**质量门控** — 每个阶段完成后必须检查：

| 门控 | 检查项 |
|------|--------|
| Phase 2 完成 | 所有 5 个维度已扫描，风险已分类（A/B/C） |
| Phase 3 完成 | 审计报告已写入文件，包含具体行号位置 |
| Phase 4 完成 | 修改计划已输出并等待用户确认 |
| Phase 5 完成 | 回归测试已通过（提供 testbench 命令和输出） |
| Phase 6 完成 | 最终报告已输出，剩余风险已说明 |

**不输出的情况**：
- 用户只要求快速检查（非系统性扫描）→ 建议直接使用 Phase 2 简化版
- 模块过大（>5000 行）→ 建议分模块扫描
