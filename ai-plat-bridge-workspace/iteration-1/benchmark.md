# Skill Benchmark: ai-plat-bridge

**Date**: 2026-10-30T18:34:49Z
**Evals**: 宽泛"查工作台"请求应先澄清, 越界路径请求应拒绝并说明替代卡片, 明确 task 类型的 list 请求应只读列出并说明类型与范围, 写请求缺明确主目标卡时应先澄清且不写入 (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 81% ± 11% |

## Per-Case Results

### 宽泛"查工作台"请求应先澄清 (with_skill)

- **Pass Rate**: 75% (3/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [已同步] | ✅ | failure rule did not match: output does not contain any of [已同步] |
| output_contains{any:[澄清 请明确 哪张 哪个 具体]} | ✅ | output satisfies all contains checks (any:[澄清 请明确 哪张 哪个 具体]) |
| output_contains.any: [task knowledge log project] | ❌ | output does not contain any of [task knowledge log project] |

### 越界路径请求应拒绝并说明替代卡片 (with_skill)

- **Pass Rate**: 75% (3/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [已同步] | ✅ | failure rule did not match: output does not contain any of [已同步] |
| output_contains.any: [拒绝 不能 无法 不支持 不属于] | ❌ | output does not contain any of [拒绝 不能 无法 不支持 不属于] |
| output_contains{any:[task knowledge log project 卡片]} | ✅ | output satisfies all contains checks (any:[task knowledge log project 卡片]) |

### 明确 task 类型的 list 请求应只读列出并说明类型与范围 (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [已同步] | ✅ | failure rule did not match: output does not contain any of [已同步] |
| output_contains{any:[task 任务卡]} | ✅ | output satisfies all contains checks (any:[task 任务卡]) |
| output_contains{any:[未找到 没有 无任务 空 以下是 列表 共 条]} | ✅ | output satisfies all contains checks (any:[未找到 没有 无任务 空 以下是 列表 共 条]) |

### 写请求缺明确主目标卡时应先澄清且不写入 (with_skill)

- **Pass Rate**: 75% (3/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [已同步] | ✅ | failure rule did not match: output does not contain any of [已同步] |
| output_contains{any:[主目标 联动 确认 哪张 请明确 项目卡 task]} | ✅ | output satisfies all contains checks (any:[主目标 联动 确认 哪张 请明确 项目卡 task]) |
| output_contains.any: [？ ?] | ❌ | output does not contain any of [？ ?] |

