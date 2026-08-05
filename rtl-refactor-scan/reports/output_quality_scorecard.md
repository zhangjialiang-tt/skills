# rtl-refactor-scan — 成熟度质量评分卡 (v2.0 M0-M2)

> 评估方式：yao-meta-skill · Skill OS 2.0 评估门 + v2.0 提案里程碑验收
> 评估范围：`rtl-refactor-scan`
> 评估日期：2026-08-05（v2.0 M0-M2 完成）
> 状态：**v2.0 三轴模型 + Finding IR + 确定性证据层已就绪**

---

## 一、总览

| 维度 | v1 评分 | v2 评分 | 关键结论 |
|------|---------|---------|----------|
| Skill IR / 路由质量 | 8/10 | 9/10 | Finding-first 流程；状态机视角；模式冻结为 quick/audit/refactor |
| Trigger Eval | 8/10 | 9/10 | 修复 trigger-eval.md L42 矛盾；默认模式统一 audit |
| Output Eval | 8/10 | 9/10 | Finding IR schema 冻结；E0 不能 confirmed；50 测试通过 |
| Conformance | 9/10 | 9/10 | 新增 schemas/ rules/ 目录；manifest v2.0.0 |
| Trust / Governance | 8/10 | 8/10 | 仍非 provider-backed；明确声明证据边界 |

**综合判定**：v2.0 确定性证据层（E2）已就绪。provider-backed 模型实证（E4+）仍为后续（M4）。

---

## 二、v2.0 M0-M2 完成项

### M0：规则与边界冻结 ✅
- evidence-model schema E0-E5
- 三轴分类模型（severity/confidence/actionability）
- finding.schema.json（核心 IR，E0 不能 confirmed）
- rules.yaml 唯一权威源（13 条规则，修复全部 8 处冲突）
- 模式冻结：默认 audit（只读），refactor M3 交付
- risk-classification.md 降为显示层映射
- scan-checklist.md 每项标注证据等级 E1/E3
- refactor-patterns.md 3 个 Transformation Contract

### M1：Finding IR ✅
- rtl-context.schema.json
- collect_context.py（源码提取 clocks/resets/module）
- render_report.py（Finding→Markdown，A/B/C 派生）
- SKILL.md Finding-first 流程（状态机视角）
- manifest.json v2.0.0
- evals.json Finding-first（期望 rule_id/severity/actionability）
- 旧 v1 资产清理（scan_check.py、sample_audit_report.md 删除）

### M2：确定性证据层 ✅
- rule_engine.py（加载 rules.yaml，过滤 deterministic）
- 8 条 deterministic 检测器全部实现：
  - SYN-MIXED-BLOCKING-001
  - SYN-VARIABLE-PART-SELECT-001
  - SYN-LATCH-001
  - SYN-MULTI-DRIVER-001
  - SYN-UNSUPPORTED-CONSTRUCT-001
  - RST-MISSING-001
  - CDC-SINGLEBIT-DIRECT-001
  - CDC-MULTIBIT-DIRECT-001
- audit_files() 编排主入口
- clean_module.v 无缺陷 fixture（误报基线零 finding）
- smoke_runner.py 重写为 Finding 全链路
- 全 fixture 矩阵回归测试

---

## 三、证据边界声明

> smoke_runner 提供的是**确定性脚本链路证据**（collect→audit→validate→render 全链路可机检），证明确定性脚本能从 RTL 源码产出合法 findings（E2）。
>
> **非 provider-backed 模型实证**：模型级 with-skill vs baseline 对比、LLM 语义审查准确率（semantic findings）需 M4 接 provider runner。

---

## 四、测试覆盖

- **50 个测试全部通过**
- 每条 deterministic rule 配备正/反/边界 fixture
- 干净模块零误报基线
- e2e 测试验证 validate_findings 通过

---

## 五、未完成项（明确声明）

| 里程碑 | 状态 | 依赖 |
|--------|------|------|
| M3 refactor 执行逻辑 | 未开始 | change_plan.schema + Transformation Contract 执行 |
| M4 EDA 工具 adapter | 未开始 | Verilator/Yosys/ModelSim 环境 |
| M4 provider 模型实证 | 未开始 | provider credentials |
| M4 变换安全性回归 | 未开始 | testbench 回归环境 |

---

## 六、晋升路径

```
v1: Library（内容强 + 格式契约证据）
  │  v2.0 M0-M2 完成
  ▼
v2: 确定性证据层就绪（E2，50 测试，8 条规则，误报基线）
  │  M3-M4 待完成
  ▼
Production（含 refactor 执行 + provider 实证 + EDA adapter）
```
