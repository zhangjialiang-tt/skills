# rtl-refactor-scan v2.0 升级提案

## 一、提案结论

建议保留 Skill 名称 `rtl-refactor-scan`，但将其定位从：

> 基于检查清单，由 LLM 扫描 RTL、输出 A/B/C 报告并给出重构建议

升级为：

> **证据驱动的 RTL 工程审计与安全重构控制器。**

v2.0 不应继续以“多写几条检查规则”为主要方向，而应完成五个根本转变：

1. 从 **Markdown 报告优先** 转为 **Finding 事实优先**；
2. 从单一 A/B/C 分级转为 **严重度、置信度、处置策略三轴模型**；
3. 从纯 LLM 阅读转为 **确定性规则、EDA 工具证据、语义审查相结合**；
4. 从自然语言六阶段流程转为 **可恢复、可验证的状态机**；
5. 从“代码改写示例”转为具有前置条件和验证义务的 **安全变换契约**。

---

# 二、当前版本的真实成熟度判断

## 2.1 当前版本已经具备的优势

现有 Skill 已形成较完整的表面架构：

- 五维扫描：可综合性、可实现性、时序、仿真与上板一致性、EDA 调试友好性；
- 快速、报告、完整三种深度；
- 审计、计划、修改、回归、最终报告六阶段；
- A/B/C 风险分类；
- 近邻 Skill 路由；
- `manifest.json`、`agents/interface.yaml`、eval、风险报告和质量评分卡。

`agents/interface.yaml` 已明确输入、输出、约束、流程、决策点和失败模式，说明 Skill 的“产品外壳”已经比较完整。

## 2.2 但当前仍是“内容型 Skill”，不是执行型 Skill

当前唯一主要确定性逻辑是：

```text
scripts/scan_check.py
```

它验证的是：

- 报告中是否出现五个维度；
- 是否有 A/B/C；
- 是否有必需章节；
- 风险表格是否包含行号。

它没有验证某项 RTL 风险是否真实存在，也不检查行号对应的代码是否支持结论。

现有 smoke runner 只是把预先准备好的报告交给 `scan_check.py` 检查，明确不包含模型执行，也不证明模型能从 RTL 中发现缺陷。

质量评分卡虽然把 Skill 标记为 Production、Library 可分发，但同时承认尚未进行 provider-backed 模型实证。

因此更准确的当前判定应是：

> **Skill 工程包装成熟度较高，RTL 审计能力的实证成熟度较低。**

这不是小缺口，而是 v2.0 最需要解决的问题。

---

# 三、当前设计中的关键结构性矛盾

## 3.1 A/B/C 同时混合了风险和修改策略

当前定义中：

- A 类：必须优先处理、必须修复；
- B 类：建议优化；
- C 类：只报告、不修改。

这实际上把三个不同概念混在一起：

1. 问题有多严重；
2. 证据有多可信；
3. 当前是否适合修改。

例如，CDC 结构可能是严重功能风险，但因为验证成本高而不应自动修改。当前文档却把“CDC 模块”整体放入 C 类，而 eval 又要求把单 bit、多 bit 直接跨域识别为 A 类。

这两个判断其实都可能合理：

- CDC 缺陷严重度高；
- CDC 修改处置等级应当保守。

问题在于当前 A/B/C 模型无法同时表达这两个事实。

## 3.2 相同规则在不同文件中分级不一致

`risk-classification.md` 将 variable part-select 列为 A 类，意味着必须修复；但 eval fixture 要求将 variable part-select 标为 B 类。

这意味着当前不存在唯一权威的风险规则源：

```text
SKILL.md
references/scan-checklist.md
references/risk-classification.md
evals/evals.json
```

都在分别定义规则含义。

## 3.3 默认模式自相矛盾

`trigger-eval.md` 的模式表把“完整模式”标注为默认；同一文件后面又规定用户未说明时应按“报告模式”启动。

这会导致不同 Agent 产生不同执行行为：

- 有的默认只读审计；
- 有的默认准备进入代码修改。

对于会修改 RTL 的 Skill，这种歧义不可接受。

## 3.4 一些扫描指标无法仅靠源码确认

检查清单包含：

- 超过 10 级 LUT；
- 大于 32:1 mux；
- reset 扇出大于 1000；
- block RAM 推断是否符合预期；
- 时序路径是否过长。

这些结论无法仅通过 LLM 阅读源码可靠确认，需要综合报告、综合网表或时序报告支持。

当前 Skill 没有明确区分：

- 源码启发式风险；
- 工具确认的实现问题；
- 用户提供的上板证据。

因此容易把“可能”写成“已经确认”。

## 3.5 重构模式可能违反 Skill 自身不变量

当前约束要求：

- 不改变外部接口；
- 不改变协议语义；
- 保持 Verilog-2001；
- 不改变已有 testbench。

但 `refactor-patterns.md` 中：

- Debug Bus 模式会新增模块输出端口；
- registered ready 会增加一个 cycle 延迟；
- RAM 子模块化可能改变 RAM 推断和读延迟；
- 数组标量化可能导致 BRAM 变为寄存器和 mux。

文档虽然对部分影响给出了提醒，但它们仍被展示为通用重构模式。

因此当前模式库的真实性质是：

> 设计思路示例，而不是可以直接应用的安全变换。

## 3.6 无 testbench 时仍允许进入完整模式过于激进

当前接口规定，无 testbench 时仍可扫描，Phase 5 回归验证降级为人工确认。

对于 RTL 重构，人工阅读不能代替行为回归。没有 testbench 时，Skill 最多应：

- 输出审计报告；
- 输出候选修改计划；
- 生成验证缺口；
- 必要时调用 `build-testbench`。

不应宣称完成完整安全重构。

---

# 四、v2.0 产品定位

## 4.1 新定位

```text
rtl-refactor-scan
=
RTL 静态工程审计
+
风险证据管理
+
受控重构计划
+
小步修改门禁
+
回归证据闭环
```

## 4.2 核心适用场景

应触发：

- 评审 RTL 工程成熟度；
- 检查综合、CDC、reset、握手、pipeline drain 等结构风险；
- 对现有模块制定不改变功能的安全重构计划；
- 对 AI 生成或修改的 RTL 执行质量门禁；
- 在提交前确认修改没有引入结构性风险；
- 对已有审计 Finding 执行逐项修复。

## 4.3 明确排除

不负责：

- 新功能设计；
- 从零编写 RTL；
- 单纯编写 testbench；
- 具体板上问题的根因调查；
- 真实布局布线和时序收敛执行；
- 算法正确性验证；
- IP 参数配置；
- 仅加注释或格式化。

其中：

- “板上现象已知、根因未知”应交给未来的 `fpga-diagnostic-loop`；
- “建立回归环境”交给 `build-testbench`；
- “修改完成后提交”交给 `smart-commit`。

## 4.4 不建议立刻拆成两个 Skill

虽然审计和重构是两种行为，但暂时不建议拆成 `rtl-audit` 与 `rtl-refactor` 两个外部 Skill。

原因是二者共享：

- 同一份 DUT 上下文；
- 同一 Finding 模型；
- 同一风险规则；
- 同一验证契约；
- 同一审计报告；
- 同一状态历史。

拆分会增加上下文和产物交接成本。

更好的方式是：

```text
一个公开 Skill
两个严格隔离的运行模式
```

### Audit Mode

只读，不修改代码。

### Refactor Mode

只能基于已有审计 Finding 启动，并要求计划批准和回归入口。

---

# 五、v2.0 核心事实模型

## 5.1 Finding 成为唯一核心事实

当前 Markdown 风险段落应升级为结构化 Finding：

```json
{
  "finding_id": "RTL-CDC-001",
  "rule_id": "CDC-MULTIBIT-DIRECT-001",
  "category": "cdc",
  "title": "多 bit 信号直接跨时钟域",
  "locations": [
    {
      "file": "rtl/foo.v",
      "start_line": 120,
      "end_line": 127
    }
  ],
  "severity": "critical",
  "confidence": "confirmed",
  "evidence_level": "deterministic_static",
  "evidence": [
    {
      "type": "source_relation",
      "description": "wr_data 在 clk_a 域赋值，在 clk_b 域直接使用"
    }
  ],
  "impact": ["data tearing", "metastability"],
  "actionability": "manual_design_required",
  "change_policy": "do_not_auto_fix",
  "verification_obligations": [
    "CDC structure validation",
    "asynchronous clock simulation",
    "existing regression"
  ]
}
```

Markdown 审计报告由 `findings.json` 渲染生成。

## 5.2 风险改为三轴分类

### 轴一：Severity——问题有多严重

```text
critical
high
medium
low
info
```

### 轴二：Confidence——结论有多可信

```text
confirmed
probable
hypothesis
unknown
```

### 轴三：Actionability——现在如何处理

```text
safe_candidate
plan_required
manual_design_required
report_only
out_of_scope
```

这样可以准确表达：

```text
CDC 直接跨域：
severity = critical
confidence = confirmed
actionability = manual_design_required
```

而不是被迫在 A 或 C 中二选一。

## 5.3 A/B/C 仅作为兼容显示层

为保留用户熟悉的阅读体验，报告中仍可展示 A/B/C：

```text
A = critical/high
B = medium
C = low/info
```

但内部机器契约不再依赖 A/B/C。

“是否修改”由 `actionability` 决定，不再由风险字母决定。

---

# 六、证据等级模型

建议冻结以下证据层级：

| 等级 | 名称                 | 含义                                            |
| ---- | -------------------- | ----------------------------------------------- |
| E0   | LLM hypothesis       | 仅基于语义推测                                  |
| E1   | Source evidence      | 有明确源码位置和数据流关系                      |
| E2   | Deterministic static | 脚本或 AST 规则确定识别                         |
| E3   | Tool confirmed       | lint、elaboration、综合、CDC 或 timing 工具确认 |
| E4   | Simulation confirmed | 可复现仿真证据                                  |
| E5   | Implementation/board | 实现报告或板上数据确认                          |

规则示例：

```text
“可能形成长组合路径”
→ E0/E1，不能标为 confirmed

“Verilator 报 UNOPTFLAT”
→ E3

“随机 backpressure 下 tlast 提前”
→ E4

“板上 data FIFO full 且 accepted < cmd_len”
→ E5
```

`rtl-refactor-scan` 的主要责任覆盖 E1–E4。

E5 可以作为输入证据，但根因调查不由本 Skill 主导。

---

# 七、规则体系升级

## 7.1 每条规则必须成为独立规则对象

建议建立：

```text
rules/
├── synthesis/
├── reset/
├── cdc/
├── handshake/
├── pipeline/
├── memory/
├── timing-heuristic/
└── debug/
```

每条规则定义：

```yaml
rule_id: RV-VALID-DEPEND-READY-001
title: valid 组合依赖 ready
category: handshake
default_severity: high
detection:
  deterministic: partial
  semantic_review: required
evidence_required:
  - valid assignment expression
  - ready dependency path
false_positive_conditions:
  - combinational bypass explicitly specified
actionability: manual_design_required
references:
  - ready-valid protocol invariant
```

## 7.2 规则必须区分三种检测方式

### Deterministic

可以可靠脚本化：

- sequential block 中 blocking/non-blocking 混用；
- 多 always 块驱动同一变量；
- 未覆盖的 combinational assignment；
- 明确的 clock signal 直接跨域；
- 无同步器的单 bit CDC 候选；
- 动态 part-select；
- `$clog2`、位宽和 signedness 候选；
- 源码中不适合综合的 construct。

### Tool-assisted

需要外部工具：

- lint；
- elaboration；
- RAM 推断；
- combinational loop；
- CDC；
- timing；
- high fanout；
- implementation utilization。

### Semantic

需要理解设计意图：

- frame_done 是否等待 pipeline drain；
- valid/ready 是否符合模块协议；
- reset 是否应清除数据寄存器；
- 跨帧残留是否构成功能风险；
- registered ready 是否允许增加 latency；
- 错误状态是否应恢复。

---

# 八、安全变换契约

当前 `refactor-patterns.md` 不应再给 Agent“看到模式就套用”的暗示。

每个重构模式应改写成 Transformation Contract：

```yaml
transformation_id: REGISTER_READY-001
purpose: 切断长 ready 组合路径

preconditions:
  - upstream protocol permits one-cycle backpressure latency
  - no combinational same-cycle acceptance requirement
  - buffering capacity is sufficient
  - existing testbench covers stall and drain

forbidden_when:
  - zero-latency ready is part of external contract
  - no skid buffer and data may arrive continuously
  - frame boundary depends on same-cycle ready

observable_changes:
  - ready latency increases by one cycle
  - throughput may change during transition

invariants:
  - no accepted transaction is lost
  - valid remains independent of ready
  - transaction order unchanged
  - frame/tlast semantics unchanged

required_verification:
  - continuous traffic
  - random backpressure
  - pipeline drain
  - frame boundary
  - original regression

rollback:
  - revert change unit CR-XXX
```

只有满足全部前置条件时，才能把该模式列入候选计划。

---

# 九、v2.0 执行状态机

建议替换当前仅存在于 prose 中的 Phase 1–6：

```text
INIT
  ↓
SCOPE_RESOLVED
  ↓
CONTEXT_BUILT
  ↓
EVIDENCE_COLLECTED
  ↓
FINDINGS_GENERATED
  ↓
FINDINGS_VALIDATED
  ↓
AUDIT_READY
  ↓
CHANGE_SELECTED
  ↓
PLAN_READY
  ↓ 用户批准
PLAN_APPROVED
  ↓
CHANGE_APPLIED
  ↓
LOCAL_VERIFY_PASS
  ↓
REGRESSION_PASS
  ↓
CLOSED
```

失败状态：

```text
BLOCKED_SCOPE
BLOCKED_CONTEXT
BLOCKED_TOOL
BLOCKED_VERIFICATION
CHANGE_FAILED
REGRESSION_FAILED
```

## 强制停止条件

以下任一成立，不能进入修改：

- top/module 身份不明确；
- 没有找到相关依赖上下文；
- Finding 只有 hypothesis，没有足够源码证据；
- 修改可能改变外部接口但未授权；
- 修改可能改变 latency 或协议行为但未确认；
- 没有任何可执行回归入口；
- golden/reference model 不明确；
- testbench 当前已经失败；
- 用户指定的冻结文件可能被修改。

---

# 十、建议产物

## 10.1 `audit_request.json`

记录本次范围：

```json
{
  "mode": "audit",
  "targets": ["rtl/foo.v"],
  "related_modules": [],
  "allowed_tools": ["verilator"],
  "regression_command": null,
  "constraints": {
    "external_interface_change": false,
    "latency_change": false
  }
}
```

## 10.2 `rtl_context.json`

记录：

- top/module；
- 文件和依赖；
- clocks/resets；
- ports；
- parameters；
- interface/protocol；
- testbench；
- regression command；
- tool availability；
- 用户已确认事实。

## 10.3 `findings.json`

唯一权威审计结果。

## 10.4 `audit_report.md`

面向用户的派生阅读物。

## 10.5 `change_plan.json`

机器可执行的修改单元：

```json
{
  "change_units": [
    {
      "change_id": "CR-001",
      "finding_ids": ["RTL-SEQ-003"],
      "files": ["rtl/foo.v"],
      "allowed_regions": ["L120-L148"],
      "forbidden_changes": ["port list", "module parameters", "latency"],
      "verification": ["make l1", "make regression"]
    }
  ]
}
```

## 10.6 `result.json`

记录每个 Finding 的最终状态：

```text
OPEN
ACCEPTED_RISK
FIX_PLANNED
FIXED_UNVERIFIED
FIXED_VERIFIED
REJECTED_FALSE_POSITIVE
BLOCKED
```

---

# 十一、推荐目录结构

```text
rtl-refactor-scan/
├── SKILL.md
├── manifest.json
├── agents/
│   └── interface.yaml
├── schemas/
│   ├── audit-request.schema.json
│   ├── rtl-context.schema.json
│   ├── finding.schema.json
│   ├── change-plan.schema.json
│   └── result.schema.json
├── scripts/
│   ├── rtl_audit.py
│   ├── collect_context.py
│   ├── validate_findings.py
│   ├── render_report.py
│   ├── validate_change_plan.py
│   └── compare_behavior_contract.py
├── rules/
│   ├── rules.yaml
│   └── domain/
├── adapters/
│   ├── verilator.py
│   ├── verible.py
│   ├── yosys.py
│   ├── modelsim.py
│   └── timing_report.py
├── references/
│   ├── rule-catalog.md
│   ├── evidence-model.md
│   ├── transformation-contracts.md
│   ├── routing.md
│   └── output-format.md
├── evals/
│   ├── fixtures/
│   ├── rule-evals.json
│   ├── routing-evals.json
│   ├── false-positive-evals.json
│   └── transformation-evals.json
└── tests/
```

---

# 十二、与现有工作流的结合

结合你当前“高智能模型写计划、较低智能模型执行、Codex/第三方模型评审”的工作方式，推荐以下职责分配。

## 12.1 高智能模型

负责：

- 理解模块意图；
- 建立数据流、状态机和协议模型；
- 对 deterministic findings 做语义复核；
- 生成 semantic findings；
- 评估修改风险；
- 编写 `change_plan.json`。

## 12.2 低成本执行模型

只能接收已批准的单个 `change_unit`：

```text
一次只修改一个 Finding
只允许修改指定文件和区域
不得改变禁止项
修改后运行指定局部验证
```

它不重新设计方案，也不扩展修改范围。

## 12.3 独立评审模型

负责：

- 检查 diff 是否严格对应 Finding；
- 检查是否违反接口、latency、协议、reset 不变量；
- 检查验证证据是否足够；
- 判断 Finding 应标记为 `FIXED_VERIFIED` 还是 `FIXED_UNVERIFIED`。

这样可以形成真正的三角色制衡：

```text
审计/规划者
    ↓
边界明确的执行者
    ↓
独立验证者
```

---

# 十三、评测体系升级

## 13.1 当前 eval 不足

现有 eval 主要验证：

- 是否触发；
- 是否包含五个维度；
- 是否生成 A/B/C；
- 是否发现一个已知 fixture 中的若干问题；
- 报告是否通过格式校验。

它不能衡量：

- 漏报率；
- 误报率；
- 行号准确性；
- 证据充分性；
- 风险等级一致性；
- 语义不变量；
- 修改是否真正安全。

## 13.2 v2.0 需要四层 eval

### 第一层：规则单测

每条 deterministic rule 必须有：

```text
positive fixture
negative fixture
edge fixture
```

### 第二层：审计准确性

统计：

```text
precision
recall
severity accuracy
location accuracy
false-positive rate
```

### 第三层：变换安全性

每个 Transformation Contract 都需要：

- 适用 fixture；
- 禁止适用 fixture；
- 修改前后行为回归；
- latency/interface diff；
- 综合或 elaboration 验证。

### 第四层：模型级实证

至少比较：

```text
baseline model
vs
model + rtl-refactor-scan v2
```

评价：

- 关键缺陷发现率；
- 误报数量；
- 无证据断言数量；
- 不安全修改数量；
- 回归成功率。

---

# 十四、升级里程碑

## Milestone 0：规则与边界冻结

目标：解决当前自相矛盾。

完成：

1. 冻结默认模式为 `report/audit`；
2. 冻结 Audit Mode 与 Refactor Mode；
3. 冻结三轴分类模型；
4. 建立唯一规则目录；
5. 修复 variable part-select、CDC 等规则冲突；
6. 明确哪些判断必须依赖 EDA 工具；
7. 收缩“综合/时序/上板诊断”的触发范围。

验收：

- SKILL、interface、manifest、references、eval 不再定义冲突规则；
- 每条规则只有一个 `rule_id` 和一个权威定义。

## Milestone 1：Finding IR

目标：从 Markdown-first 转为 Finding-first。

完成：

1. `finding.schema.json`；
2. `rtl_context.schema.json`；
3. `validate_findings.py`；
4. `render_report.py`；
5. 报告由 Finding 渲染；
6. 旧 A/B/C 只作为显示映射。

验收：

- 任何审计报告都可追溯到 `findings.json`；
- 每个 Finding 都有位置、证据、严重度、置信度和处置策略；
- 无证据的 Finding 不能标为 confirmed。

## Milestone 2：确定性证据层

目标：建立最低可信审计能力。

优先规则：

1. sequential blocking/non-blocking；
2. 多驱动；
3. latch；
4. clock/reset 域提取；
5. CDC candidate；
6. valid/ready 直接依赖；
7. dynamic part-select；
8. signedness/width candidate；
9. unsupported synthesis construct。

验收：

- 每条规则具备正例、反例、边界 fixture；
- deterministic Finding 的行号准确；
- 误报和漏报有可量化基线。

## Milestone 3：安全重构控制

目标：让完整模式真正可控。

完成：

1. `change-plan.schema.json`；
2. Transformation Contract；
3. 修改区域和禁止项；
4. 用户批准记录；
5. 局部验证和完整回归；
6. `result.json`；
7. rollback。

验收：

- 无 approved change plan 不允许修改；
- 无回归入口不能进入 `FIXED_VERIFIED`；
- 每个修改可关联原 Finding；
- 每个修改单元可独立回退。

## Milestone 4：工具适配与生产化

完成：

- Verilator/Verible/Yosys adapter；
- ModelSim 日志 adapter；
- timing report adapter；
- provider-backed model eval；
- 真实项目 regression corpus；
- 规则版本管理；
- 历史 Finding 对比。

---

# 十五、v2.0 发布门槛

满足以下条件后，才建议重新标记为 Production：

1. 所有规则存在唯一权威定义；
2. 默认执行只读 Audit Mode；
3. Finding schema 已冻结；
4. 报告全部从 Finding 渲染；
5. 至少 8 条 deterministic rule 有完整测试；
6. 至少 10 个 RTL fixture；
7. 包含无缺陷 fixture，用于评估误报；
8. 包含多时钟、AXIS、FIFO、frame pipeline fixture；
9. 修改必须依赖 approved change plan；
10. 没有 testbench 时不得宣称重构验证完成；
11. 模型级 eval 验证使用 Skill 后优于 baseline；
12. 当前评分卡不再仅以目录、模板和格式完整度判断成熟度。

---

# 十六、最终推荐

本轮升级不应继续沿用“完善检查清单和报告模板”的思路。

最值得冻结的三个核心决定是：

## 决定一

> **Finding 是唯一权威事实，Markdown 是派生产物。**

## 决定二

> **风险严重度、证据置信度、修改策略必须分离。**

## 决定三

> **Audit 默认只读；Refactor 必须由已验证 Finding、批准计划和回归入口共同解锁。**

完成这三个设计后，`rtl-refactor-scan` 才会从一个“内容很丰富的 RTL 评审提示词”，升级成真正可以进入你 FPGA 工程工作流的：

> **RTL 质量控制面。**
