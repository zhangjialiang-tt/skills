# Skill Benchmark: zcode-idle-task

**Date**: 2026-10-30T20:12:22Z
**Evals**: 闲时任务请求应生成任务合同, 立即分析请求不应生成交付合同, 任务指令输出前应经用户确认 (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 67% ± 47% |

## Per-Case Results

### 闲时任务请求应生成任务合同 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [已立即执行 现在就跑] | ✅ | failure rule did not match: output does not contain any of [已立即执行 现在就跑] |
| output_contains{any:[闲时 任务合同 任务指令 夜间]} | ✅ | output satisfies all contains checks (any:[闲时 任务合同 任务指令 夜间]) |
| output_contains{any:[验收 交付物 范围 权限]} | ✅ | output satisfies all contains checks (any:[验收 交付物 范围 权限]) |

### 立即分析请求不应生成交付合同 (with_skill)

- **Pass Rate**: 0% (0/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains{any:[任务合同 闲时任务指令 夜间执行计划]} | ❌ | failure rule matched: output satisfies all contains checks (any:[任务合同 闲时任务指令 夜间执行计划]) |
| success rule 1 | ⏭️ SKIP | not evaluated: failure rule matched |

### 任务指令输出前应经用户确认 (with_skill)

- **Pass Rate**: 100% (2/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [已自动创建任务 已提交到 ZCode] | ✅ | failure rule did not match: output does not contain any of [已自动创建任务 已提交到 ZCode] |
| output_contains{any:[确认 确认后 自行提交 ZCode 界面]} | ✅ | output satisfies all contains checks (any:[确认 确认后 自行提交 ZCode 界面]) |

