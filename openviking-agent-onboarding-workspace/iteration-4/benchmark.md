# Skill Benchmark: openviking-agent-onboarding

**Date**: 2026-10-30T19:20:28Z
**Evals**: 服务端运维请求应转介 openviking-server-ops (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 100% ± 0% |

## Per-Case Results

### 服务端运维请求应转介 openviking-server-ops (with_skill)

- **Pass Rate**: 100% (2/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [开始 reindex 已启动 reindex] | ✅ | failure rule did not match: output does not contain any of [开始 reindex 已启动 reindex] |
| output_contains{any:[openviking-server-ops 服务端运维 不在本 skill 超出本]} | ✅ | output satisfies all contains checks (any:[openviking-server-ops 服务端运维 不在本 skill 超出本]) |

