# RTL 风险分类标准（v2.0 三轴模型）

> **权威源**：所有规则的分级定义在 `rules/rules.yaml`，这是唯一权威定义来源。本文件仅说明 A/B/C 兼容显示层如何从三轴派生，不再独立定义规则。

## 三轴分类模型

v2.0 将单一 A/B/C 分级拆为三个独立轴（详见 `schemas/risk-axes.schema.json`）：

| 轴 | 含义 | 取值 |
|----|------|------|
| severity | 问题有多严重 | critical / high / medium / low / info |
| confidence | 结论有多可信 | confirmed / probable / hypothesis / unknown |
| actionability | 现在如何处理 | safe_candidate / plan_required / manual_design_required / report_only / out_of_scope |

**"是否修改"由 actionability 决定，不再由风险字母决定。**

## A/B/C 兼容显示层映射

为保留用户熟悉的阅读体验，报告中仍可展示 A/B/C，但内部机器契约不再依赖它：

| 显示 | severity 映射 |
|------|---------------|
| ⚠️ A 类 | critical / high |
| 🔶 B 类 | medium |
| 🟢 C 类 | low / info |

## 关键冲突裁决记录（v1 → v2 迁移）

以下规则在 v1 中存在跨文件分级冲突，v2 已在 rules.yaml 冻结：

| 规则 | v1 冲突 | v2 冻结三轴值 |
|------|---------|---------------|
| variable part-select | risk-classification=A 类 vs evals=B 类 | severity=medium, actionability=plan_required |
| CDC 多 bit 直跨 | risk-classification=C 类 vs evals=A 类 | severity=critical, actionability=manual_design_required |
| CDC 单 bit 无同步 | 隐含 A 类 | severity=critical, actionability=manual_design_required |
| 宽 mux 阈值 | >8:1 vs >32:1 | 统一 >32:1（TIM-WIDE-MUX-001） |

CDC 的裁决体现了三轴模型的核心价值：severity=critical（严重）与 actionability=manual_design_required（不应自动改）可以并存，而旧 A/B/C 模型无法表达这一事实。
