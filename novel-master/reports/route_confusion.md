# Route Scorecard

- total cases: `15`
- accuracy: `1.0`
- ambiguous cases: `0`
- no-route accuracy: `1.0`

## Route Metrics

| Route | Expected | Predicted | Precision | Recall | Avg Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| `novel-master` | 6 | 6 | 1.0 | 1.0 | 0.254 |
| `novel-brief` | 1 | 1 | 1.0 | 1.0 | 0.708 |
| `story-architect` | 1 | 1 | 1.0 | 1.0 | 0.782 |
| `chapter-planner` | 1 | 1 | 1.0 | 1.0 | 0.737 |
| `chapter-writer` | 1 | 1 | 1.0 | 1.0 | 0.737 |
| `novel-reviewer` | 1 | 1 | 1.0 | 1.0 | 0.782 |
| `continuity-keeper` | 1 | 1 | 1.0 | 1.0 | 0.96 |
| `no_route` | 3 | 3 | 1.0 | 1.0 | - |

## Confusion Matrix

| Expected \ Predicted | `novel-master` | `novel-brief` | `story-architect` | `chapter-planner` | `chapter-writer` | `novel-reviewer` | `continuity-keeper` | `no_route` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `novel-master` | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `novel-brief` | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| `story-architect` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| `chapter-planner` | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| `chapter-writer` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `novel-reviewer` | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| `continuity-keeper` | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| `no_route` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |

## Ambiguous Cases

| Family | Expected | Predicted | Margin |
| --- | --- | --- | ---: |
| - | - | - | - |
