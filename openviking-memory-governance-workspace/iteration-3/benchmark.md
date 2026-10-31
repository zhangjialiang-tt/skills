# Skill Benchmark: openviking-memory-governance

**Date**: 2026-10-30T20:01:09Z
**Evals**: 治理请求应启动七步流程且体检基线先行, events 瘦身应指出 L1 去 ChatLog 是主收益, 评审结论/用户裁定类事件不得合并删减, sessions 处置应按分级保留 (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 100% ± 0% |

## Per-Case Results

### 治理请求应启动七步流程且体检基线先行 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [已删除全部旧记忆 开始批量删除] | ✅ | failure rule did not match: output does not contain any of [已删除全部旧记忆 开始批量删除] |
| output_contains{any:[体检 基线 七步]} | ✅ | output satisfies all contains checks (any:[体检 基线 七步]) |
| output_contains{any:[events sessions peer 写入侧]} | ✅ | output satisfies all contains checks (any:[events sessions peer 写入侧]) |

### events 瘦身应指出 L1 去 ChatLog 是主收益 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [直接全部清空] | ✅ | failure rule did not match: output does not contain any of [直接全部清空] |
| output_contains{any:[ChatLog L1]} | ✅ | output satisfies all contains checks (any:[ChatLog L1]) |
| output_contains{any:[主收益 收益 大头]} | ✅ | output satisfies all contains checks (any:[主收益 收益 大头]) |

### 评审结论/用户裁定类事件不得合并删减 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [可以合并删除] | ✅ | failure rule did not match: output does not contain any of [可以合并删除] |
| output_contains{any:[L3 禁区 不能 不建议 不要合并]} | ✅ | output satisfies all contains checks (any:[L3 禁区 不能 不建议 不要合并]) |
| output_contains{any:[评审结论 用户裁定]} | ✅ | output satisfies all contains checks (any:[评审结论 用户裁定]) |

### sessions 处置应按分级保留 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [全部删除] | ✅ | failure rule did not match: output does not contain any of [全部删除] |
| output_contains{any:[分级 保留 分层]} | ✅ | output satisfies all contains checks (any:[分级 保留 分层]) |
| output_contains{any:[sessions]} | ✅ | output satisfies all contains checks (any:[sessions]) |

