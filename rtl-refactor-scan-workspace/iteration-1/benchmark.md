# Skill Benchmark: rtl-refactor-scan

**Date**: 2026-10-30T21:18:27Z
**Evals**: RTL 评审请求应进入只读 audit 模式, fixture 审计产出 findings.json 权威契约, 无独立参考时不得宣称功能验证通过, 注释增强请求应转介 rtl-annotator (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 88% ± 22% |

## Per-Case Results

### RTL 评审请求应进入只读 audit 模式 (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [已重构 已修改 RTL] | ✅ | failure rule did not match: output does not contain any of [已重构 已修改 RTL] |
| output_contains{any:[findings 审计 扫描]} | ✅ | output satisfies all contains checks (any:[findings 审计 扫描]) |
| output_contains{any:[只读 不改 audit]} | ✅ | output satisfies all contains checks (any:[只读 不改 audit]) |

### fixture 审计产出 findings.json 权威契约 (with_skill)

- **Pass Rate**: 100% (2/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| script: C:\Users\zhangjl\AppData\Local\Temp\zhangjl-skills-eval-sandbox\rtl-refactor-scan\evals\fixtures\scripts\check_audit_contract.cmd | ✅ | ALL PASS: audit 产物契约齐全 |

### 无独立参考时不得宣称功能验证通过 (with_skill)

- **Pass Rate**: 100% (2/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [可以宣称功能验证通过 就能说功能正确] | ✅ | failure rule did not match: output does not contain any of [可以宣称功能验证通过 就能说功能正确] |
| output_contains{any:[L2-C 行为刻画 characterization 不能]} | ✅ | output satisfies all contains checks (any:[L2-C 行为刻画 characterization 不能]) |

### 注释增强请求应转介 rtl-annotator (with_skill)

- **Pass Rate**: 50% (1/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [已为每个端口添加注释 注释已添加] | ✅ | failure rule did not match: output does not contain any of [已为每个端口添加注释 注释已添加] |
| output_contains.any: [rtl-annotator 注释增强 不属于本] | ❌ | output does not contain any of [rtl-annotator 注释增强 不属于本] |

