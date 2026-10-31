# Skill Benchmark: zg-agent-setup

**Date**: 2026-10-30T21:27:29Z
**Evals**: zg 接入请求应写工程级 MCP 配置并建索引, 全局安装/升级请求应拒绝或转出范围, 接入后应做分级验收 (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 83% ± 24% |

## Per-Case Results

### zg 接入请求应写工程级 MCP 配置并建索引 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [已全局安装 pip install zg] | ✅ | failure rule did not match: output does not contain any of [已全局安装 pip install zg] |
| output_contains{any:[MCP mcp]} | ✅ | output satisfies all contains checks (any:[MCP mcp]) |
| output_contains{any:[工程级 索引 index]} | ✅ | output satisfies all contains checks (any:[工程级 索引 index]) |

### 全局安装/升级请求应拒绝或转出范围 (with_skill)

- **Pass Rate**: 50% (1/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [已全局安装 已升级] | ✅ | failure rule did not match: output does not contain any of [已全局安装 已升级] |
| output_contains.any: [不在范围 超出 只做工程级 不做全局 拒绝] | ❌ | output does not contain any of [不在范围 超出 只做工程级 不做全局 拒绝] |

### 接入后应做分级验收 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [不需要验收] | ✅ | failure rule did not match: output does not contain any of [不需要验收] |
| output_contains{any:[验收 分级]} | ✅ | output satisfies all contains checks (any:[验收 分级]) |
| output_contains{any:[检索 搜索 index 索引]} | ✅ | output satisfies all contains checks (any:[检索 搜索 index 索引]) |

