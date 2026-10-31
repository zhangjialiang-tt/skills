# Skill Benchmark: hyperframes-video

**Date**: 2026-10-30T23:28:48Z
**Evals**: 视频生产请求应启动 HyperFrames 生产线流程, AI 视频生成出画面请求应转介 ai-drama-pilot, 内容三件套产出（语速预算/事实核查/时长闭合） (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 78% ± 31% |

## Per-Case Results

### 视频生产请求应启动 HyperFrames 生产线流程 (with_skill)

- **Pass Rate**: 100% (5/5)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.files_not_exist | ✅ | all checks passed |
| failure: output_contains.any: [final.mp4 已生成 成片已渲染] | ✅ | failure rule did not match: output does not contain any of [final.mp4 已生成 成片已渲染] |
| output_contains{any:[HyperFrames hyperframes]} | ✅ | output satisfies all contains checks (any:[HyperFrames hyperframes]) |
| output_contains{any:[阶段 Phase 门禁 冒烟 勘察]} | ✅ | output satisfies all contains checks (any:[阶段 Phase 门禁 冒烟 勘察]) |
| output_contains{any:[渲染 check 环境]} | ✅ | output satisfies all contains checks (any:[渲染 check 环境]) |

### AI 视频生成出画面请求应转介 ai-drama-pilot (with_skill)

- **Pass Rate**: 33% (1/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [开始渲染 成片已渲染] | ✅ | failure rule did not match: output does not contain any of [开始渲染 成片已渲染] |
| output_contains.any: [ai-drama-pilot 不适用 不属于 不是本 无法] | ❌ | output does not contain any of [ai-drama-pilot 不适用 不属于 不是本 无法] |
| output_contains.any: [HyperFrames 本 skill 代码动画 AI 视频生成] | ❌ | output does not contain any of [HyperFrames 本 skill 代码动画 AI 视频生成] |

### 内容三件套产出（语速预算/事实核查/时长闭合） (with_skill)

- **Pass Rate**: 100% (2/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.files_not_exist | ✅ | all checks passed |
| script: C:\Users\zhangjl\AppData\Local\Temp\zhangjl-skills-eval-sandbox\hyperframes-video\evals\fixtures\scripts\check_content.cmd | ✅ | ALL PASS: 内容三件套契约齐全 |

