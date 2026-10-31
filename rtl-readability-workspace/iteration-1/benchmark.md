# Skill Benchmark: rtl-readability

**Date**: 2026-10-30T20:52:55Z
**Evals**: 可读性请求应输出逐条建议, 默认只读不修改 RTL, 功能缺陷请求应转介 rtl-refactor-scan, implicit 契约建议补注释而非判缺失 (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 75% ± 43% |

## Per-Case Results

### 可读性请求应输出逐条建议 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [已修改 counter.v 已重命名] | ✅ | failure rule did not match: output does not contain any of [已修改 counter.v 已重命名] |
| output_contains{any:[行 line 建议 发现]} | ✅ | output satisfies all contains checks (any:[行 line 建议 发现]) |
| output_contains{any:[只读 不改 确认]} | ✅ | output satisfies all contains checks (any:[只读 不改 确认]) |

### 默认只读不修改 RTL (with_skill)

- **Pass Rate**: 0% (0/0)

### 功能缺陷请求应转介 rtl-refactor-scan (with_skill)

- **Pass Rate**: 100% (2/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [已修复 CDC 已解决] | ✅ | failure rule did not match: output does not contain any of [已修复 CDC 已解决] |
| output_contains{any:[rtl-refactor-scan CDC 功能缺陷]} | ✅ | output satisfies all contains checks (any:[rtl-refactor-scan CDC 功能缺陷]) |

### implicit 契约建议补注释而非判缺失 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [属于缺失 就是缺陷] | ✅ | failure rule did not match: output does not contain any of [属于缺失 就是缺陷] |
| output_contains{any:[implicit 不 补注释 契约注释]} | ✅ | output satisfies all contains checks (any:[implicit 不 补注释 契约注释]) |
| output_contains{any:[L0 注释]} | ✅ | output satisfies all contains checks (any:[L0 注释]) |

