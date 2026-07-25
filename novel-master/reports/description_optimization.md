# novel-master Description Optimization

Winner: `Guardrail`

- current tokens: `45`
- winner tokens: `30`
- baseline tokens: `24`

## Winner

编排和治理长篇网文项目的完整创作生命周期 from 网文创意, 项目简报, 人物设定, 世界设定, 故事大纲, 章节卡, 正文, 评审意见, or 连续性状态. Do not use for 普通文本润色, 第三方作品分析, or 阅读推荐.

## Candidate Ranking

| Candidate | Tokens | Dev FP | Dev FN | Dev Near | Holdout FP | Holdout FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `Guardrail` | 30 | 0 | 0 | 1.0 | 0 | 0 |
| `Balanced` | 31 | 0 | 0 | 1.0 | 0 | 0 |
| `Boundary` | 41 | 0 | 0 | 1.0 | 0 | 0 |
| `Current` | 45 | 0 | 0 | 1.0 | 0 | 0 |
| `Artifact Aware` | 55 | 0 | 0 | 1.0 | 0 | 0 |
| `Minimal` | 16 | 0 | 2 | 1.0 | 0 | 0 |

## Acceptance Gates

| Gate | Winner FP | Winner FN | Current FP | Current FN | Baseline FP | Baseline FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Holdout | 0 | 0 | 0 | 0 | 0 | 0 |
| Blind Holdout | 0 | 0 | 0 | 0 | 0 | 0 |
| Judge Blind Holdout | 0 | 2 | 0 | 2 | 0 | 2 |
| Adversarial Holdout | 0 | 0 | 0 | 0 | 0 | 1 |

## Calibration

| Gate | Winner Gap | Winner Risk | Winner Boundary Rate | Current Gap | Baseline Gap |
| --- | ---: | --- | ---: | ---: | ---: |
| Holdout | 0.279 | healthy | 0.0 | 0.252 | 0.313 |
| Blind Holdout | 0.484 | healthy | 0.0 | 0.441 | 0.336 |
| Adversarial Holdout | 0.197 | tight | 0.143 | 0.178 | 0.06 |

## Judge Blind Summary

| Gate | Winner Agreement | Winner Mean Confidence | Current Agreement | Baseline Agreement |
| --- | ---: | ---: | ---: | ---: |
| Judge Blind Holdout | 0.667 | 0.58 | 0.667 | 0.667 |

## Family Health

| Gate | Winner Clean Families | Winner Weakest Family | Current Clean Families | Baseline Clean Families |
| --- | --- | --- | --- | --- |
| Holdout | 9/9 | third_party_analysis (0 errors) | 9/9 | 9/9 |
| Blind Holdout | 6/6 | blind_prewrite_continuity (0 errors) | 6/6 | 6/6 |
| Judge Blind Holdout | 4/6 | blind_prewrite_continuity (1 errors) | 4/6 | 4/6 |
| Adversarial Holdout | 7/7 | adversarial_style_polish (0 errors) | 7/7 | 6/7 |

## Selection Logic

Ordered by:
- fewest false positives
- fewest false negatives
- highest near-neighbor pass rate
- highest negative pass rate
- highest precision
- highest recall
- shortest description
