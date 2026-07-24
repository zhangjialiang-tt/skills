# novel-master 独立前向抽测报告

> 日期：2026-07-25  
> 范围：`NM-REG-001` 至 `NM-REG-010`  
> 性质：独立 Agent 的只读语义抽测，不替代真实小说项目端到端验收。

## 测试方法

- 测试 Agent 只读取 `SKILL.md` 和任务所需的直接 references。
- 不向测试 Agent 提供 `evals/evals.json`、测试断言或预期答案。
- 不允许修改项目文件。
- 自动断言与人工语义复核分开记录。
- 第一次 C 组抽测因搜索命令意外暴露 eval 线索而作废；最终结果来自严格限定可读文件后的全新重跑。

## 结果

| 编号 | 观察结果 | 结论 |
| --- | --- | --- |
| NM-REG-001 | 路由 `novel-reviewer`；源文件、状态和报告持久化权限均为 false | PASS |
| NM-REG-002 | 仅返回内联诊断；不保存报告或修改任何文件 | PASS |
| NM-REG-003 | Writer 只产出 DRAFT 和 Proposal，停在接受闸门前 | PASS |
| NM-REG-004 | 直接调用 Writer 时识别 Canon 冲突，正文生成与文件修改均未执行 | PASS |
| NM-REG-005 | 总控拆为 `novel-reviewer → chapter-writer/EDIT`；Reviewer 诊断，Writer 执行修改 | PASS |
| NM-REG-006 | 缺少模式时返回 `BLOCKED / INVALID_SKILL_MODE`，无交付物 | PASS |
| NM-REG-007 | 多模式时返回 `BLOCKED / INVALID_SKILL_MODE`，建议拆分调用 | PASS |
| NM-REG-008 | L2 只调整表达；两项 `must_preserve` 均保持，状态候选为空 | PASS |
| NM-REG-009 | 普通杯子被识别为过渡性日常动作，状态候选为空 | PASS |
| NM-REG-010 | 顾青获知秘密被提取为 `state_update` Proposal，DRAFT 未正式提交 | PASS |

## 迭代记录

前向抽测纠正了 `NM-REG-005` 的初始断言：复合请求不能整体停留在 Reviewer；应由总控拆成 Reviewer 只读诊断和 Writer 独立编辑两个步骤。回归集已按该组件边界更新。

## 尚未覆盖

- 未使用完整小说项目文件验证远距离连续性检索。
- 未评价正文文风和审美质量。
- 未执行真实 L3/L4 授权写入、两阶段恢复或派生状态重建。
