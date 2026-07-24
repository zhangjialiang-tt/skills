# RTL 成熟度审计报告 — sample_fixt_known_defects

> 生成时间: 2026-07-22
> 扫描依据: rtl-refactor-scan
> 分析范围: evals/fixtures/sample_fixt_known_defects.v（约 60 行）
> 相关模块: 上层 N/A，下层 N/A

---

## 一、模块功能概述

最小 Verilog 示例模块，故意植入 6 类已知缺陷，用于验证扫描器是否能识别并分级。包含双时钟域、单时钟 pipeline、unpacked array、variable part-select。

按五大维度扫描：可综合性、可实现性、时序优化、仿真上板一致性、EDA LA 友好性。

## 二、时钟/复位域

| 项目 | 现状 | 评价 |
|------|------|------|
| 时钟 | 双时钟（clk_a / clk_b） | ⚠️ 存在 CDC 风险 |
| 复位 | 异步复位，但跨域 | ⚠️ 复位跨域未同步 |
| 复位范围 | 仅 mixed_reg 被复位，其余寄存器无复位 | ⚠️ 不完整 |

## 三、数据流路径

```
din_data -> mixed_reg (clk_a) -> cdc_bus -> dout_data (clk_b)
         -> no_rst_reg (clk_a)
         -> history[]  (clk_a, unpacked array shift)
din_valid -> cdc_pulse -> dout_valid (clk_b，未同步)
```

## 四、ready/valid 反压路径

无显式 ready-valid 协议，但 cdc_pulse 直通无同步，构成单 bit 跨时钟风险（行 N5）。

## 五、pipeline drain 条件

无显式 frame_done。

## 六、RAM/FIFO 使用情况

| 类型 | 位置 | 说明 |
|------|------|------|
| unpacked reg array | 行 N4 | 16×8b history，EDA 探测不稳定 |

## 七、风险列表

### ⚠️ A 类：必须优先处理

| # | 风险 | 位置 | 严重度 | 说明 |
|---|------|------|--------|------|
| A1 | 混合 blocking/non-blocking 赋值 | L23（`=` 与 `<=` 混用） | MAJOR | 综合结果不确定，仿真/综合不一致 |
| A2 | 多 bit 总线直接打拍跨时钟 | L60（`cdc_bus` clk_a→clk_b） | MAJOR | 多 bit 跨时钟必须经 async FIFO 或握手，禁止直接打拍 |
| A3 | 单 bit 跨时钟无同步器 | L55（`cdc_pulse`） | MAJOR | 必须使用 2-stage synchronizer |
| A4 | 关键路径寄存器缺复位 | L28（`no_rst_reg`） | MAJOR | FPGA 上电后状态 X，仿真默认值掩盖问题 |

### 🔶 B 类：建议优化

| # | 风险 | 位置 | 说明 |
|---|------|------|------|
| B1 | variable part-select | L34（`wide_bus[idx*32 +: 32]`） | 综合可但 EDA debug 困难，建议显式展开 |
| B2 | unpacked array 在 EDA LA 直接探测 | L38-L45 | 建议封装为独立子模块并加 32-bit debug bus |

### 🟢 C 类：只报告，暂不改

| # | 项目 | 位置 | 说明 |
|---|------|------|------|
| C1 | history 规模 ≤16 | L38-L45 | 规模小暂不拆分子模块，重构收益不抵复杂度 |

## 八、上板不一致风险

| # | 风险 | 说明 |
|---|------|------|
| 1 | 多 bit 跨时钟直打 | 仿真大概率 PASS，上板后大概率出现数据错位 |
| 2 | 缺复位寄存器 | 仿真默认初值掩盖上电 X 态 |

## 九、EDA LA/debug 不稳定写法

| # | 写法 | 位置 |
|---|------|------|
| 1 | `wide_bus[idx*32 +: 32]` | L34 |
| 2 | `history[0..15]` unpacked array | L38-L45 |
| 3 | `cdc_bus` 32-bit 内部总线跨域直连 | L60 |

## 十、最小安全重构计划

阶段 1：修复 A1（分离 blocking/non-blocking 赋值）
阶段 2：修复 A2、A3（CDC 同步化）
阶段 3：修复 A4（补复位）
阶段 4：B1/B2 视团队时间再处理

## 十一、推荐回归测试列表

| 测试 | 目录 | 命令 | 验证内容 |
|------|------|------|----------|
| 单元 smoke | evals/fixtures | `make sim` | 不新增 mismatch，无 latch warning |

## 十二、是否建议进入修改阶段

是。A 类 4 条都是必改项；B/C 类视资源决定。
