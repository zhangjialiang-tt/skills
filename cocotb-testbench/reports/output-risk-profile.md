# Output Risk Profile — cocotb-testbench

生成物面向用户的最终交付是「可运行的 sim 框架 + 验证报告」。预测的主要错误面：

| 风险 | 触发场景 | 已有防线 |
|---|---|---|
| 夸大验证结论 | 把 smoke/characterization 说成功能正确 | Stage gates 表 + Output contract 强制 Verification basis 字段 + Non-goals |
| 端口启发式静默出错 | 复位极性/同步复位/双向口分类错 | 生成物内注释显式标注假设 + 报告 classification_assumptions 字段 + troubleshooting 修正路径 |
| 生成代码 API 幻觉 | 模板偏离真实 cocotb 2.x API | 模板 grounding 于官方 simple_dff 示例；v1.0 已在 Windows+Icarus+cocotb 2.1.0 实跑 smoke/functional 全绿（reports/ 本文件同目录可复现流程） |
| timescale/路径类首跑失败 | RTL 无 timescale、多根相对路径 | 已实测复现并把修复固化进生成器（默认 timescale、sources 绝对化），并登记 troubleshooting |
| golden 被弱化凑 PASS | 对拍失败后放宽容差/改期望 | verification-policy 第 4/5 条 + failure policy |
| 覆盖用户已有文件 | sim/<top> 已存在 | 生成器硬拒绝 + existing_sim_policy 输入 |
| 报告淹没在过程日志 | pytest+仿真双层输出混杂 | Output contract 固定字段，逐用例以 result.xml 为准 |

## 不防御项（v1 有意边界）

- VHDL 端口自动解析（手写 ports.json，next-iteration）
- cocotb `_pytest` 插件路线（官方警告 breaking，故意不采用）
- Verilator smoke 语义（2-state，probe 结果仅作 functional 备用）
