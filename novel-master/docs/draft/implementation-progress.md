# novel-master V1 实施进度

> 最后更新：2026-07-25
> 本页区分“实施层质量修复”和冻结架构中的业务阶段，避免把 Skill 骨架误报为完整运行时能力。

## 阶段 1：契约与项目骨架

| 任务 | 状态 |
| --- | --- |
| 平台能力调查 | DONE |
| 实施说明文档 | DONE |
| 目录骨架 | DONE |
| 共享 references（8 文件） | DONE |
| JSON Schema（7 类） | DONE |
| 合法/非法样例（7/10） | DONE |
| 辅助脚本（7 个） | DONE |
| 1+6 Skill.md 与 agents/openai.yaml | DONE |
| 小说项目模板 | DONE |
| 固定 Prompt 回归样例（10 条） | DONE |
| Prompt 回归校验与人工复核报告接口 | DONE |
| 运行测试 | DONE（见下方验证基线） |

## 实施层质量修复

| 阶段 | 状态 | 结果 |
| --- | --- | --- |
| 阶段一：事务与授权安全 | DONE | ApprovalRef、ChangeSet、路径、生命周期、锁与回滚测试闭环 |
| 阶段二：Schema 与样例严格化 | DONE | 7 类 Schema 严格字段策略及合法/非法样例闭环 |
| 阶段三：Skill 包规范化 | DONE | 7/7 官方 quick_validate、真实 references 链和 UI 元数据 |
| 阶段四：固定行为回归 | DONE | 10 条 Prompt 回归、确定性对比器和人工复核清单 |

## v1.2.0 章节生产与质量契约

| 阶段 | 状态 | 结果 |
| --- | --- | --- |
| 阶段 -1：仓库现实检查 | DONE | `docs/reality-check-report.md`；测试基线 108→168 |
| 阶段 0：质量基线 | DONE | 10/10 基线样本（均分 23.9/30，范围 22-27），Rubric 冻结 |
| 阶段 1：v1.2.0-rc1 契约 | DONE | 架构 RC1 + 契约 RC1 + ADR |
| 阶段 2A：确认修改落点 | DONE | `docs/stage-2a-checklist.md`（13 项操作） |
| 阶段 2B：Schema/校验器/Registry | DONE | 5 业务 Schema + 4 defs + context-pack 更新 + validate_quality_contract.py |
| 阶段 3：纵向 Skill 实现 | DONE | 6 个 Skill 全部更新（novel-style → chapter-planner → chapter-writer → novel-reviewer → novel-master + routing-table） |
| 阶段 4：测试 | DONE | 确定性契约测试：30 条（168 总测试全部通过）；A/B 手动对比：3/3 WIN（100%），达到 WIN+TIE≥70%、WIN≥40%、LOSS≤30% 门槛。holdout 评估待模型运行。 |
| 阶段 5：冻结 v1.2.0 | READY | RC1 测试和手动 A/B 均已通过，可进入冻结 |

## 当前验证基线

- `python -m pytest tests -q`：**168 passed**（2026-07-25）。
- v1.2 新增测试 30 条：18 条 Reader Experience/ChapterPlan/Report/Review/StyleGuide Schema 测试 + 12 条跨对象 validate_quality_contract 脚本测试。

## 当前验证基线

- `python -m pytest tests -q`：**168 passed**（2026-07-25）。
- `python scripts/check_prompt_regressions.py evals/evals.json`：固定回归集结构校验。
- `python scripts/validate_quality_contract.py validate-all --chapter-plan <plan> --style-guide <sg> --task-envelope <te>`：跨对象质量契约校验。
- v1.2 新增测试 30 条（`tests/test_quality_contract.py`）。

## 冻结架构业务阶段

- 阶段 2（最小创作闭环）：待启动
- 阶段 3（项目初始化与只读评审）：待启动
- 阶段 4（异常、恢复与回归）：固定回归集已完成；冲突检测、两阶段恢复、派生状态重建、上下文降级和归档仍待实现
