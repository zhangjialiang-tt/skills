# Skill Benchmark: no-gui-debug

**Date**: 2026-11-01T02:40:27Z
**Evals**: 打包 IP 上板 0 包应先把打包与前置分流, 板测前应做 bit 溯源而不只看 mtime (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 100% ± 0% |

## Per-Case Results

### 打包 IP 上板 0 包应先把打包与前置分流 (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [打包肯定有问题 直接改 RTL 重打包就行] | ✅ | failure rule did not match: output does not contain any of [打包肯定有问题 直接改 RTL 重打包就行] |
| output_contains{any:[等价 LUT WNS WHS]} | ✅ | output satisfies all contains checks (any:[等价 LUT WNS WHS]) |
| output_contains{any:[bit 源 bit溯源 溯源 sha256 入口 verify-ip 平铺]} | ✅ | output satisfies all contains checks (any:[bit 源 bit溯源 溯源 sha256 入口 verify-ip 平铺]) |
| output_contains{any:[TPG 校准 calib SCP0 复位]} | ✅ | output satisfies all contains checks (any:[TPG 校准 calib SCP0 复位]) |

### 板测前应做 bit 溯源而不只看 mtime (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [看时间就行 只看 mtime mtime 就够] | ✅ | failure rule did not match: output does not contain any of [看时间就行 只看 mtime mtime 就够] |
| output_contains{any:[入口 verify-ip 平铺 ipverify]} | ✅ | output satisfies all contains checks (any:[入口 verify-ip 平铺 ipverify]) |
| output_contains{any:[sha256 哈希 日志标记 工程名 provenance 溯源]} | ✅ | output satisfies all contains checks (any:[sha256 哈希 日志标记 工程名 provenance 溯源]) |
| output_contains{any:[mtime 时间]} | ✅ | output satisfies all contains checks (any:[mtime 时间]) |

