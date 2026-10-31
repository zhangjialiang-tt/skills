# Skill Benchmark: smart-commit

**Date**: 2026-10-30T18:27:18Z
**Evals**: 生成 message 不执行 commit 且格式合规 (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 100% ± 0% |

## Per-Case Results

### 生成 message 不执行 commit 且格式合规 (with_skill)

- **Pass Rate**: 100% (2/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| script: C:\Users\zhangjl\AppData\Local\Temp\zhangjl-skills-eval-sandbox\smart-commit\evals\fixtures\scripts\check_git_state.cmd | ✅ | ALL PASS: git 状态判定通过 |

