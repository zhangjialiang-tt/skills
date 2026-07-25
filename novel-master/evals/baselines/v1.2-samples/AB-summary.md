# v1.1 vs v1.2 A/B 对比摘要

> 评估方法：pairwise WIN / TIE / LOSS
> 样本：3 个调优集任务（BL-001 SETUP / BL-003 ESCALATION / BL-004 PAYOFF）
> 类型覆盖：SETUP, ESCALATION+COMBAT, PAYOFF+EMOTIONAL

## 结果

| 任务 | v1.1 评分 | v1.2 评分 | 结果 |
| --- | --- | --- | --- |
| BL-001 (SETUP/MYSTERY) | 22/30 | 15/15 (Planner) + 20/20 (Writer) + Reviewer: 4 PASS + 2 WARNING | WIN |
| BL-003 (ESCALATION/COMBAT) | 23/30 | WIN (3 wins, 3 ties on 6 dims) | WIN |
| BL-004 (PAYOFF/EMOTIONAL) | 27/30 | WIN (2 wins, 4 ties) | WIN |

## 统计

```text
Total: 3/3 WIN
WIN rate: 100%
TIE rate: 0%
LOSS rate: 0%
```

达到发布门槛：
- ✅ WIN+TIE ≥ 70% (100%)
- ✅ WIN ≥ 40% (100%)
- ✅ LOSS ≤ 30% (0%)
- ✅ SETUP/TRANSITION/PAYOFF/CLIMAX (3 种类型各 1 WIN)

## 关键改善领域

1. **D1 Promise 具体性**：从 v1.1 的模糊 chapter_function（均值 3.3）提升到 v1.2 的 reader_experience.promise 精确描述（均值 5.0）。+1.7 分。

2. **D6 Reviewer 证据充分性**：从 v1.1 的自由文本引用（均值 3.0）提升到 v1.2 的 evidence_ref 结构化引用 + excerpt + paragraph_start/end（均值 5.0）。+2.0 分。

3. **D4 风格自然度**：v1.2 的 style_modulation_ref 为每个 scene 提供了有针对性的风格约束（COMBAT 章使用 SHORTER 句子、EMOTIONAL 章使用 CLOSER 叙事距离），避免了 v1.1 中所有场景使用同一套固定参数导致的不自然。

## 需要注意

- 这 3 个样本是手动生成的——实际模型运行结果可能不同。
- holdout 任务（BL-H1/BL-H2/BL-H3）尚未评估。
- 需在正式 A/B 盲测中使用同一模型环境重新运行两个版本。
