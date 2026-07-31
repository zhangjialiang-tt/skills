# Readiness Review 自检清单

本文档是 `webnovel-serial-designer` 阶段 10 的执行参考。
Readiness Review 由 designer 自动生成，不是作者 Gate。结果呈现给 Gate B 供作者确认。

---

## 9 个检查维度

### 1. 上游忠实度（upstream_fidelity）

| 项目 | 内容 |
|------|------|
| **检查内容** | `synopsis-contract.yaml` 中所有 `frozen_facts` 在设计包中有对应实现；`prohibited_directions` 无违反；`expandable_zones` 未被越界 |
| **Pass** | 所有冻结事实可追溯到设计文件；无禁止方向出现 |
| **Block** | 任一 frozen_fact 缺失或被改变；出现 prohibited_direction |
| **可自动修复** | 补充遗漏的 frozen_fact 对应段落（不改变设计，只补充引用） |
| **严重度** | 缺失 = blocking；引用不完整 = major |

---

### 2. 发动机可持续性（engine_sustainability）

| 项目 | 内容 |
|------|------|
| **检查内容** | 五项测试通过记录；循环步骤 ≥4；可变输入 ≥10；升级轴 ≥2；反重复规则 ≥3 条 |
| **Pass** | 五项测试全部通过；组合空间 ≥35 |
| **Block** | 任一测试失败；循环步骤 <4；可变输入 <6 |
| **可自动修复** | 反重复规则不足（可从设计文件推导补充） |
| **严重度** | 测试失败 = blocking；规则不足 = major |

---

### 3. 分卷完整性（volume_completeness）

| 项目 | 内容 |
|------|------|
| **检查内容** | 每卷有：目标、冲突、揭示、高潮、不可逆变化、卷末钩子；章数总和在目标 ±10%；卷间升级递进 |
| **Pass** | 所有卷 6 项完整；章数在范围内；无空卷 |
| **Block** | 缺少整卷设计；章数偏差 >15%；存在无高潮的卷 |
| **可自动修复** | 章数微调（±10% 内）；补充缺失的卷末钩子 |
| **严重度** | 缺卷 = blocking；单项缺失 = major |

---

### 4. 人物弧光分布（character_arc_distribution）

| 项目 | 内容 |
|------|------|
| **检查内容** | 主角每卷有 arc_checkpoint（belief + forced_choice + cost）；配角有明确连载功能；对手有独立时间线 |
| **Pass** | 主角弧光覆盖所有卷；无"消失 2 卷以上"的核心配角；对手时间线 ≥5 节点 |
| **Block** | 主角有卷无弧光节点；核心角色无连载功能定义 |
| **可自动修复** | 补充配角连载功能标签（从已有设计中推导） |
| **严重度** | 主角弧光断裂 = blocking；配角问题 = major |

---

### 5. 爽点可执行性（payoff_executability）

| 项目 | 内容 |
|------|------|
| **检查内容** | 前 10 章有 ≥2 个明确兑现；正常连载期最小间隔有定义；每卷 ≥1 个大兑现；无"无代价爽点" |
| **Pass** | 密度规则覆盖全部卷；兑现类型 ≥3 种；代价机制存在 |
| **Block** | 前 10 章无兑现设计；存在连续 3 卷无大兑现 |
| **可自动修复** | 补充代价描述；调整兑现间隔 |
| **严重度** | 前期无爽点 = blocking；间隔问题 = major |

---

### 6. 伏笔可执行性（mystery_executability）

| 项目 | 内容 |
|------|------|
| **检查内容** | 每个真相有 ≥3 条公平线索；线索分布在不同卷；错误解释有逻辑基础；回收位置在终局前 |
| **Pass** | 所有真相可追溯线索链；无"凭空揭示"；错误解释 ≥2 个 |
| **Block** | 存在无线索的揭示；回收位置在终局后 |
| **可自动修复** | 补充线索分布（从已有设计中提取）；调整揭示位置 |
| **严重度** | 凭空揭示 = blocking；线索不足 = major |

---

### 7. 篇幅可信度（volume_credibility）

| 项目 | 内容 |
|------|------|
| **检查内容** | 目标章数 × 单章字数 = 总字数在合理范围；每卷章数与内容量匹配；无"注水卷"（内容不足以支撑章数） |
| **Pass** | 每卷内容密度合理（目标、冲突、揭示足以支撑章数）；总字数与平台预期匹配 |
| **Block** | 存在明显注水卷（内容 < 章数 × 50%）；总字数偏差 >20% |
| **可自动修复** | 章数微调；补充卷内事件密度 |
| **严重度** | 注水卷 = blocking；轻微偏差 = supporting |

---

### 8. 中期重复风险（mid_serial_repetition）

| 项目 | 内容 |
|------|------|
| **检查内容** | 反重复规则覆盖 5 种重复模式；卷间冲突类型不重复；情绪曲线有变化；场景多元化 |
| **Pass** | 连续 3 卷无相同冲突类型；情绪轮换有设计；反重复规则可执行 |
| **Block** | 连续 2 卷结构高度相似（冲突类型 + 解决方式 + 情绪相同） |
| **可自动修复** | 调整情绪轮换；补充场景多样化约束 |
| **严重度** | 连续 3 卷重复 = blocking；2 卷相似 = major |

---

### 9. 终局收束自然性（endgame_convergence）

| 项目 | 内容 |
|------|------|
| **检查内容** | 收束条件可验证；结局与上游一致；伏笔在终局前回收；最后 10-20 章有方向；无"突然结局" |
| **Pass** | 收束条件 ≥3 条且可判定；结局忠实上游；回收位置合理 |
| **Block** | 收束条件模糊（"主角变强后"）；结局偏离上游；存在未回收的核心伏笔 |
| **可自动修复** | 明确收束条件的判定标准；补充伏笔回收位置 |
| **严重度** | 结局偏离 = blocking；条件模糊 = major |

---

## 严重度分类

| 严重度 | 含义 | 对 verdict 的影响 |
|--------|------|-------------------|
| **blocking** | 设计包不可交付，必须修复 | 任一存在 → verdict = `block` |
| **major** | 设计包可交付但有显著风险 | 未修复 ≥2 项 → verdict = `revise` |
| **supporting** | 改善建议，不影响交付 | 不影响 verdict |

---

## Verdict 判定逻辑

```
if any(item.severity == "blocking" and item.status != "fixed"):
    verdict = "block"
elif count(item.severity == "major" and item.status != "fixed") >= 2:
    verdict = "revise"
else:
    verdict = "pass"
```

- `block`：不进入 Gate B，先修复后重新生成 Readiness Review
- `revise`：进入 Gate B，作者可选择 `revise`（修复后重审）或 `approve_and_freeze`（接受风险）
- `pass`：进入 Gate B，作者可直接 `approve_and_freeze`

---

## 自动修复范围

以下问题 designer 可自行修复（L0/L1），不需要作者介入：
- 补充遗漏的引用和交叉参考
- 章数微调（±10% 内）
- 补充代价描述、卷末钩子
- 调整线索分布位置
- 补充配角连载功能标签
- 明确模糊的收束条件判定标准

以下问题**不可**自动修复，必须升级：
- 改变发动机核心循环
- 增加/删除整卷
- 改变主角弧光节点
- 修改上游冻结事实
- 改变核心真相揭示卷

---

## 输出格式

Readiness Review 结果写入 `reviews/readiness-review.yaml`，结构：

```yaml
review_id: RR-<design-id>-<NNN>
generated_at: <ISO 8601>
verdict: pass | revise | block

dimensions:
  - id: upstream_fidelity
    status: pass | fail | fixable
    findings:
      - severity: blocking | major | supporting
        description: <问题描述>
        location: <design/XX.md#section>
        auto_fixed: true | false
        fix_description: <修复说明（如已修复）>

summary:
  total_checks: <N>
  passed: <N>
  auto_fixed: <N>
  remaining_major: <N>
  remaining_blocking: <N>
  risks_for_author:
    - <需要作者注意的风险>
```
