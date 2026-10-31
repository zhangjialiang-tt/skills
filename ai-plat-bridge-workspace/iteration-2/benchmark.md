# Skill Benchmark: ai-plat-bridge

**Date**: 2026-10-30T18:43:12Z
**Evals**: 宽泛"查工作台"请求应先澄清, 越界路径请求应拒绝并说明替代卡片, 明确 task 类型的 list 请求应只读列出并说明类型与范围, 写请求缺明确主目标卡时应先澄清且不写入 (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 75% ± 43% |

## Per-Case Results

### 宽泛"查工作台"请求应先澄清 (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [已同步] | ✅ | failure rule did not match: output does not contain any of [已同步] |
| output_contains{any:[澄清 请明确 哪张 哪个 具体]} | ✅ | output satisfies all contains checks (any:[澄清 请明确 哪张 哪个 具体]) |
| output_contains{any:[task knowledge log project 哪一类 卡片类型]} | ✅ | output satisfies all contains checks (any:[task knowledge log project 哪一类 卡片类型]) |

### 越界路径请求应拒绝并说明替代卡片 (with_skill)

- **Pass Rate**: 0% (0/0)

### 明确 task 类型的 list 请求应只读列出并说明类型与范围 (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [已同步] | ✅ | failure rule did not match: output does not contain any of [已同步] |
| output_contains{any:[task 任务卡]} | ✅ | output satisfies all contains checks (any:[task 任务卡]) |
| output_contains{any:[未找到 没有 无任务 空 以下是 列表 共 条]} | ✅ | output satisfies all contains checks (any:[未找到 没有 无任务 空 以下是 列表 共 条]) |

### 写请求缺明确主目标卡时应先澄清且不写入 (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [已同步] | ✅ | failure rule did not match: output does not contain any of [已同步] |
| output_contains{any:[主目标 联动 确认 哪张 请明确 项目卡 task]} | ✅ | output satisfies all contains checks (any:[主目标 联动 确认 哪张 请明确 项目卡 task]) |
| output_contains{any:[确认 先 1. 2. 3.]} | ✅ | output satisfies all contains checks (any:[确认 先 1. 2. 3.]) |

