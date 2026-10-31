# Skill Benchmark: openviking-agent-onboarding

**Date**: 2026-10-30T18:58:17Z
**Evals**: MCP 通但会话不落库应诊断缺 hooks 层, 接入前应先做只读探测, 服务端运维请求应转介 openviking-server-ops (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 56% ± 42% |

## Per-Case Results

### MCP 通但会话不落库应诊断缺 hooks 层 (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [重新安装 MCP 就能解决] | ✅ | failure rule did not match: output does not contain any of [重新安装 MCP 就能解决] |
| output_contains{any:[hooks hook 同步层]} | ✅ | output satisfies all contains checks (any:[hooks hook 同步层]) |
| output_contains{any:[MCP]} | ✅ | output satisfies all contains checks (any:[MCP]) |
| output_contains{any:[只读层 两层 分层 只做 MCP]} | ✅ | output satisfies all contains checks (any:[只读层 两层 分层 只做 MCP]) |

### 接入前应先做只读探测 (with_skill)

- **Pass Rate**: 67% (2/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [已经接好了] | ✅ | failure rule did not match: output does not contain any of [已经接好了] |
| output_contains.any: [probe 探测 先] | ❌ | output does not contain any of [probe 探测 先] |
| output_contains{any:[ov-agent-probe 配置 hooks MCP]} | ✅ | output satisfies all contains checks (any:[ov-agent-probe 配置 hooks MCP]) |

### 服务端运维请求应转介 openviking-server-ops (with_skill)

- **Pass Rate**: 0% (0/0)

