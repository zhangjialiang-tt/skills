# Skill Benchmark: ai-drama-pilot

**Date**: 2026-10-30T20:30:36Z
**Evals**: 直接要 MP4 成片时应转介 hyperframes-video (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 100% ± 0% |

## Per-Case Results

### 直接要 MP4 成片时应转介 hyperframes-video (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [阶段 A 已完成 剧本已产出] | ✅ | failure rule did not match: output does not contain any of [阶段 A 已完成 剧本已产出] |
| output_contains{any:[hyperframes]} | ✅ | output satisfies all contains checks (any:[hyperframes]) |
| output_contains{any:[前期资料 离线资料 生产包]} | ✅ | output satisfies all contains checks (any:[前期资料 离线资料 生产包]) |

