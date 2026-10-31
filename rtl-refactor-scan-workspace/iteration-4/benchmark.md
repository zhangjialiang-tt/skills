# Skill Benchmark: rtl-refactor-scan

**Date**: 2026-10-30T21:22:09Z
**Evals**: 注释增强请求应转介 rtl-annotator (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 67% ± 0% |

## Per-Case Results

### 注释增强请求应转介 rtl-annotator (with_skill)

- **Pass Rate**: 67% (2/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [已为每个端口添加注释 注释已添加] | ✅ | failure rule did not match: output does not contain any of [已为每个端口添加注释 注释已添加] |
| output_contains.any: [不属于本 skill 超出本 skill 范围 边界] | ❌ | output does not contain any of [不属于本 skill 超出本 skill 范围 边界] |

