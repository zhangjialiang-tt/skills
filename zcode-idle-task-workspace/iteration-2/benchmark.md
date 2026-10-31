# Skill Benchmark: zcode-idle-task

**Date**: 2026-10-30T20:14:03Z
**Evals**: 立即分析请求不应生成交付合同 (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 100% ± 0% |

## Per-Case Results

### 立即分析请求不应生成交付合同 (with_skill)

- **Pass Rate**: 100% (2/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [任务合同如下 已生成任务合同 闲时任务指令如下 夜间执行计划如下] | ✅ | failure rule did not match: output does not contain any of [任务合同如下 已生成任务合同 闲时任务指令如下 夜间执行计划如下] |
| output_contains{any:[目录 结构 分析]} | ✅ | output satisfies all contains checks (any:[目录 结构 分析]) |

