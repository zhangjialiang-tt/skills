# Skill Benchmark: hyperframes-video

**Date**: 2026-10-30T23:30:00Z
**Evals**: AI 视频生成出画面请求应转介 ai-drama-pilot (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 33% ± 0% |

## Per-Case Results

### AI 视频生成出画面请求应转介 ai-drama-pilot (with_skill)

- **Pass Rate**: 33% (1/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [开始渲染 成片已渲染] | ✅ | failure rule did not match: output does not contain any of [开始渲染 成片已渲染] |
| output_contains.any: [ai-drama-pilot 不适用 不属于 不是本 无法] | ❌ | output does not contain any of [ai-drama-pilot 不适用 不属于 不是本 无法] |
| output_contains.any: [HyperFrames 本 skill 代码动画 AI 视频生成] | ❌ | output does not contain any of [HyperFrames 本 skill 代码动画 AI 视频生成] |

