# Skill Benchmark: no-gui-debug

**Date**: 2026-10-30T20:35:50Z
**Evals**: 握手卡死症状应路由到 ILA 链, 丢包与帧率异常症状应路由到 tshark 链, 成像撕裂症状应路由到上位机链, 改 RTL 后直接烧旧 bit 应被提醒先重编, sim 全绿板上出错应给出多链路差异排查方案 (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 100% ± 0% |

## Per-Case Results

### 握手卡死症状应路由到 ILA 链 (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| failure: output_contains.any: [打开 Vivado Hardware Manager GUI] | ✅ | failure rule did not match: output does not contain any of [打开 Vivado Hardware Manager GUI] |
| output_contains{any:[ILA ila]} | ✅ | output satisfies all contains checks (any:[ILA ila]) |
| output_contains{any:[波形 CSV 抓波 探针]} | ✅ | output satisfies all contains checks (any:[波形 CSV 抓波 探针]) |

### 丢包与帧率异常症状应路由到 tshark 链 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [打开 Wireshark GUI] | ✅ | failure rule did not match: output does not contain any of [打开 Wireshark GUI] |
| output_contains{any:[tshark dumpcap pcap]} | ✅ | output satisfies all contains checks (any:[tshark dumpcap pcap]) |
| output_contains{any:[丢包 间隔 block_id 每帧包数 重传]} | ✅ | output satisfies all contains checks (any:[丢包 间隔 block_id 每帧包数 重传]) |

### 成像撕裂症状应路由到上位机链 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [打开 Wireshark GUI 打开 Vivado Hardware Manager] | ✅ | failure rule did not match: output does not contain any of [打开 Wireshark GUI 打开 Vivado Hardware Manager] |
| output_contains{any:[上位机 gige_cli capture_frames RAW]} | ✅ | output satisfies all contains checks (any:[上位机 gige_cli capture_frames RAW]) |
| output_contains{any:[对拍 counter dump manifest]} | ✅ | output satisfies all contains checks (any:[对拍 counter dump manifest]) |

### 改 RTL 后直接烧旧 bit 应被提醒先重编 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [直接烧就行 没有问题] | ✅ | failure rule did not match: output does not contain any of [直接烧就行 没有问题] |
| output_contains{any:[mtime 重新编译 重编 旧比特 旧 bit]} | ✅ | output satisfies all contains checks (any:[mtime 重新编译 重编 旧比特 旧 bit]) |
| output_contains{any:[假结论 不 风险 错误 先]} | ✅ | output satisfies all contains checks (any:[假结论 不 风险 错误 先]) |

### sim 全绿板上出错应给出多链路差异排查方案 (with_skill)

- **Pass Rate**: 100% (3/3)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| failure: output_contains.any: [仿真过了就没问题 不用查了] | ✅ | failure rule did not match: output does not contain any of [仿真过了就没问题 不用查了] |
| output_contains{any:[ILA 上位机 tshark]} | ✅ | output satisfies all contains checks (any:[ILA 上位机 tshark]) |
| output_contains{any:[交叉 组合 多链路 证据链]} | ✅ | output satisfies all contains checks (any:[交叉 组合 多链路 证据链]) |

