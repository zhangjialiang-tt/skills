# Skill Benchmark: ai-drama-pilot

**Date**: 2026-10-31T00:03:43Z
**Evals**: 正触发但缺故事基线时应先问一次, 直接要 MP4 成片时应转介 hyperframes-video, 屏幕文字应建议后期制作而非模型直出, 45 秒 ≤10 镜成本约束生产包端到端产出 (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 100% ± 0% |

## Per-Case Results

### 正触发但缺故事基线时应先问一次 (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [阶段 A 已完成 剧本已产出] | ✅ | failure rule did not match: output does not contain any of [阶段 A 已完成 剧本已产出] |
| output_contains{any:[故事基线 题材 必须保留的情节点]} | ✅ | output satisfies all contains checks (any:[故事基线 题材 必须保留的情节点]) |
| output_contains{any:[？ ?]} | ✅ | output satisfies all contains checks (any:[？ ?]) |

### 直接要 MP4 成片时应转介 hyperframes-video (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [阶段 A 已完成 剧本已产出] | ✅ | failure rule did not match: output does not contain any of [阶段 A 已完成 剧本已产出] |
| output_contains{any:[hyperframes]} | ✅ | output satisfies all contains checks (any:[hyperframes]) |
| output_contains{any:[前期资料 离线资料 生产包]} | ✅ | output satisfies all contains checks (any:[前期资料 离线资料 生产包]) |

### 屏幕文字应建议后期制作而非模型直出 (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [完全可行 直接生成即可] | ✅ | failure rule did not match: output does not contain any of [完全可行 直接生成即可] |
| output_contains{any:[后期]} | ✅ | output satisfies all contains checks (any:[后期]) |
| output_contains{any:[乱码 必然 不可靠]} | ✅ | output satisfies all contains checks (any:[乱码 必然 不可靠]) |

### 45 秒 ≤10 镜成本约束生产包端到端产出 (with_skill)

- **Pass Rate**: 100% (2/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| script: C:\Users\zhangjl\AppData\Local\Temp\zhangjl-skills-eval-sandbox\ai-drama-pilot\evals\fixtures\scripts\check_e2e.cmd | ✅ | FOUND root=the-alone-clause\pilot-01
ALL PASS: e2e 生产包校验通过（10 镜） |

