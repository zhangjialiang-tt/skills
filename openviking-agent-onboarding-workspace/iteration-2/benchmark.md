# Skill Benchmark: openviking-agent-onboarding

**Date**: 2026-10-30T19:08:03Z
**Evals**: 接入前应先做只读探测, 服务端运维请求应转介 openviking-server-ops (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 75% ± 25% |

## Per-Case Results

### 接入前应先做只读探测 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [已经接好了] | ✅ | failure rule did not match: output does not contain any of [已经接好了] |
| output_contains{any:[probe 探测 先 分层验证 接入状态 活性 已经完整接入]} | ✅ | output satisfies all contains checks (any:[probe 探测 先 分层验证 接入状态 活性 已经完整接入]) |
| output_contains{any:[ov-agent-probe 配置 hooks MCP]} | ✅ | output satisfies all contains checks (any:[ov-agent-probe 配置 hooks MCP]) |

### 服务端运维请求应转介 openviking-server-ops (with_skill)

- **Pass Rate**: 50% (1/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [开始 reindex 已启动 reindex] | ✅ | failure rule did not match: output does not contain any of [开始 reindex 已启动 reindex] |
| output_contains.any: [openviking-server-ops 服务端运维 不在本 skill 超出本] | ❌ | output does not contain any of [openviking-server-ops 服务端运维 不在本 skill 超出本] |

