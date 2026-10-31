# Skill Benchmark: rtl-readability

**Date**: 2026-10-30T21:06:12Z
**Evals**: 默认只读不修改 RTL (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 100% ± 0% |

## Per-Case Results

### 默认只读不修改 RTL (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [已重命名信号 已修改 RTL] | ✅ | failure rule did not match: output does not contain any of [已重命名信号 已修改 RTL] |
| output_contains{any:[只读 确认 建议]} | ✅ | output satisfies all contains checks (any:[只读 确认 建议]) |

