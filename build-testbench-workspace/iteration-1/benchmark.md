# Skill Benchmark: build-testbench

**Date**: 2026-10-30T22:03:46Z
**Evals**: 无 .git 的 workspace 应停止并要求确认根目录, 同名模块歧义应暴露候选不静默选择, L1 smoke 仿真框架生成（目录契约校验）, cocotb 请求应转介 cocotb-testbench (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 25% ± 43% |

## Per-Case Results

### 无 .git 的 workspace 应停止并要求确认根目录 (with_skill)

- **Pass Rate**: 0% (0/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.files_not_exist | ❌ | file "sim" should not exist but does |
| failure rule 1 | ⏭️ SKIP | not evaluated: expect gate failed |
| success rule 1 | ⏭️ SKIP | not evaluated: expect gate failed |
| success rule 2 | ⏭️ SKIP | not evaluated: expect gate failed |

### 同名模块歧义应暴露候选不静默选择 (with_skill)

- **Pass Rate**: 0% (0/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.files_not_exist | ❌ | file "sim" should not exist but does |
| failure rule 1 | ⏭️ SKIP | not evaluated: expect gate failed |
| success rule 1 | ⏭️ SKIP | not evaluated: expect gate failed |
| success rule 2 | ⏭️ SKIP | not evaluated: expect gate failed |

### L1 smoke 仿真框架生成（目录契约校验） (with_skill)

- **Pass Rate**: 0% (0/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ❌ | output contains forbidden keyword "[SIM_RESULT] L1 PASS" |
| script: evals/fixtures/scripts/check_l1_framework.cmd | ⏭️ SKIP | not evaluated: expect gate failed |

### cocotb 请求应转介 cocotb-testbench (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.files_not_exist | ✅ | all checks passed |
| failure: output_contains.any: [[SIM_RESULT] L1 PASS] | ✅ | failure rule did not match: output does not contain any of [[SIM_RESULT] L1 PASS] |
| output_contains{any:[cocotb]} | ✅ | output satisfies all contains checks (any:[cocotb]) |
| output_contains{any:[cocotb-testbench Python python]} | ✅ | output satisfies all contains checks (any:[cocotb-testbench Python python]) |

