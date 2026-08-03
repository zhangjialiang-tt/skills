# Milestone 1 Architecture Freeze

状态：已实现并由契约测试约束。

## 冻结决策

- 唯一外部入口：`webnovel-analysis/SKILL.md`。
- O0、S0-S9、Q0：内部模块，入口名为 `MODULE.md`，不参与外部路由。
- R0：内部最终报告阶段，不是独立 Skill。
- 公共模型输出只含 `task_id`、`batch_id`、`skill_id`、`skill_version`、`schema_version`、`operation`、`payload`、`uncertain_items`、`conflicts`、`manual_review_items`。
- 运行时状态、哈希、校验时间和失效原因不进入模型输出。
- S6 只做结构化聚合；Q0 审计后，R0 才生成最终报告。
- P0 阻断；P1 采用 `risk_based_blocking`。
- NineD 保留为轻量路由策略，不引入额外编排层。

## DAG

规范图见 `../references/execution-dag.yaml`。S1/S2/S3 并行；S4 依赖 S2；S5 依赖 S1/S2/S4；S6 依赖 S1-S5；Q0 位于 S6 之后。

## 非目标

Milestone 1 不实现 runner、持久化运行状态、artifact registry、哈希、断点恢复、真实模型调用、CI、100/500 章规模回归或新的 golden fixture。
