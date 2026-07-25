# Output Execution Runs

This report records how output-eval variants were produced and whether timing or token evidence is observed or estimated.

- Cases: `6`
- Variant runs: `12`
- Command executed: `0`
- Model executed: `0`
- Recorded fixtures: `12`
- Timing observed: `0`
- Token observed: `0`
- Token estimated: `12`
- Delta: `100.0`
- Gate pass: `True`

No model-executed runs are recorded yet.

Use `python3 scripts/yao.py output-exec --provider-runner openai` or `--runner-command` with a reviewed provider-backed runner to replace recorded fixtures with real model output evidence.

## Runs

| Case | Variant | Mode | Model | Duration ms | Tokens | Score | Status |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| readonly-review-no-state-write | baseline | recorded_fixture |  |  | 16 | 0.0 | pass |
| readonly-review-no-state-write | with_skill | recorded_fixture |  |  | 56 | 100.0 | pass |
| conflict-blocks-writer | baseline | recorded_fixture |  |  | 13 | 0.0 | pass |
| conflict-blocks-writer | with_skill | recorded_fixture |  |  | 62 | 100.0 | pass |
| draft-cannot-commit-facts | baseline | recorded_fixture |  |  | 13 | 0.0 | pass |
| draft-cannot-commit-facts | with_skill | recorded_fixture |  |  | 64 | 100.0 | pass |
| l2-preserves-confirmed-facts | baseline | recorded_fixture |  |  | 15 | 0.0 | pass |
| l2-preserves-confirmed-facts | with_skill | recorded_fixture |  |  | 65 | 100.0 | pass |
| ordinary-object-not-persistent-fact | baseline | recorded_fixture |  |  | 14 | 0.0 | pass |
| ordinary-object-not-persistent-fact | with_skill | recorded_fixture |  |  | 57 | 100.0 | pass |
| secret-creates-knowledge-proposal | baseline | recorded_fixture |  |  | 13 | 0.0 | pass |
| secret-creates-knowledge-proposal | with_skill | recorded_fixture |  |  | 69 | 100.0 | pass |

## Next Fixes

- Keep recorded fixtures as reproducible baselines, but do not describe them as model-executed evidence.
- Use `scripts/provider_output_eval_runner.py` for provider-backed holdout cases when release confidence depends on real generation behavior.
- Compare timing, token cost, and assertion deltas before promoting a skill to governed reuse.
