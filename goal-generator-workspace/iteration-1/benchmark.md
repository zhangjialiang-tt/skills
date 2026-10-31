# Skill Benchmark: goal-generator

**Date**: 2026-10-31T00:13:04Z
**Evals**: 显式 Goal 请求应输出 /goal 契约, 弱信号调试请求不应生成 /goal, Standard Goal 契约含全部标准标签, Diagnostic Goal 契约含诊断区块且事实假设分离, 用户给 baseline 未给目标时不得编造阈值 (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 80% ± 40% |

## Per-Case Results

### 显式 Goal 请求应输出 /goal 契约 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_contain | ✅ | all checks passed |
| failure: output_contains.any: [已添加 argparse 已修改脚本 脚本已创建] | ✅ | failure rule did not match: output does not contain any of [已添加 argparse 已修改脚本 脚本已创建] |
| output_contains{all:[/goal Verification Constraints Boundaries Stop]} | ✅ | output satisfies all contains checks (all:[/goal Verification Constraints Boundaries Stop]) |

### 弱信号调试请求不应生成 /goal (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.all: missing [/goal Verification（验证）] | ✅ | failure rule did not match: output does not contain required keywords: [/goal Verification（验证）] |
| output_contains{any:[复现 调试 tb testbench 波形 测试 信号]} | ✅ | output satisfies all contains checks (any:[复现 调试 tb testbench 波形 测试 信号]) |

### Standard Goal 契约含全部标准标签 (with_skill)

- **Pass Rate**: 100% (5/5)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_contain | ✅ | all checks passed |
| failure: output_contains.any: [已修改 已实现 已添加] | ✅ | failure rule did not match: output does not contain any of [已修改 已实现 已添加] |
| output_contains{all:[Verification（验证） Constraints（约束） Boundaries（边界） Stop when（完成条件） Pause if（暂停条件）]} | ✅ | output satisfies all contains checks (all:[Verification（验证） Constraints（约束） Boundaries（边界） Stop when（完成条件） Pause if（暂停条件）]) |
| output_contains{any:[report.py JSON]} | ✅ | output satisfies all contains checks (any:[report.py JSON]) |
| output_contains{any:[现有 回归 tests]} | ✅ | output satisfies all contains checks (any:[现有 回归 tests]) |

### Diagnostic Goal 契约含诊断区块且事实假设分离 (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_contain | ✅ | all checks passed |
| failure: output_contains.any: [根因是 status FIFO 根因就是 status FIFO] | ✅ | failure rule did not match: output does not contain any of [根因是 status FIFO 根因就是 status FIFO] |
| output_contains{all:[【当前事实】 【待验证假设】 【验收证据】 【必须保持】 【工作边界】 【阻塞与停止】]} | ✅ | output satisfies all contains checks (all:[【当前事实】 【待验证假设】 【验收证据】 【必须保持】 【工作边界】 【阻塞与停止】]) |
| output_contains{any:[data FIFO]} | ✅ | output satisfies all contains checks (any:[data FIFO]) |

### 用户给 baseline 未给目标时不得编造阈值 (with_skill)

- **Pass Rate**: 0% (0/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_contain | ❌ | output does not contain "/goal" |
| failure rule 1 | ⏭️ SKIP | not evaluated: expect gate failed |
| success rule 1 | ⏭️ SKIP | not evaluated: expect gate failed |

