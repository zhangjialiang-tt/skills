# Skill Benchmark: cocotb-testbench

**Date**: 2026-10-30T22:55:58Z
**Evals**: cocotb 框架请求应启动框架生成流程, ModelSim 原生 TB 请求应转介 build-testbench, cocotb 框架生成与 characterization 降级措辞 (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 67% ± 47% |

## Per-Case Results

### cocotb 框架请求应启动框架生成流程 (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.files_not_exist | ✅ | all checks passed |
| failure: output_contains.any: [无法 不能帮 做不到] | ✅ | failure rule did not match: output does not contain any of [无法 不能帮 做不到] |
| output_contains{any:[cocotb pytest 测试框架]} | ✅ | output satisfies all contains checks (any:[cocotb pytest 测试框架]) |
| output_contains{any:[corr_match RTL rtl 文件 路径 哪]} | ✅ | output satisfies all contains checks (any:[corr_match RTL rtl 文件 路径 哪]) |

### ModelSim 原生 TB 请求应转介 build-testbench (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.files_not_exist | ✅ | all checks passed |
| failure: output_contains.any: [test_counter.py 已生成 已生成 cocotb 框架] | ✅ | failure rule did not match: output does not contain any of [test_counter.py 已生成 已生成 cocotb 框架] |
| output_contains{any:[build-testbench]} | ✅ | output satisfies all contains checks (any:[build-testbench]) |

### cocotb 框架生成与 characterization 降级措辞 (with_skill)

- **Pass Rate**: 0% (0/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ❌ | output contains forbidden keyword "功能正确" |
| script: evals/fixtures/scripts/check_cocotb_framework.cmd | ⏭️ SKIP | not evaluated: expect gate failed |

