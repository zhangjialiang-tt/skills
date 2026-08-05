# 安全变换契约（Transformation Contract）

> v2.0 要求：每个重构模式必须改写为 Transformation Contract，只有满足全部前置条件时才能列入候选计划。M0-M2 阶段仅冻结契约模板；执行逻辑在 M3 交付。

## 契约模板

每个 Transformation Contract 必须包含以下字段：

| 字段 | 含义 |
|------|------|
| transformation_id | 唯一标识 |
| purpose | 变换目的 |
| preconditions | 全部满足才能列入候选 |
| forbidden_when | 任一成立则禁止 |
| observable_changes | 变换后可观测的行为变化（必须向用户声明） |
| invariants | 变换后必须保持的不变量 |
| required_verification | 变换后必须执行的验证 |
| rollback | 回退方式 |

## 示例：REGISTER_READY-001（寄存器化 ready）

完整内容见 `refactor-patterns.md` §7 的 Transformation Contract 块。核心约束：

- **observable_changes**: ready latency 增加 1 cycle
- **forbidden_when**: 外部契约要求零延迟 ready / 无 skid buffer 且数据可能连续到达
- **invariants**: 不丢失已接受的事务 / valid 不依赖 ready / 事务顺序不变 / 帧语义不变

违反 forbidden_when 或无法保证 invariants 时，该模式不得进入 change_plan。

## 已覆盖契约

| 变换 | 契约位置 | 关键约束 |
|------|----------|----------|
| REGISTER_READY-001 | refactor-patterns.md §7 | ready +1 cycle，禁止零延迟契约场景 |
| DEBUG_BUS-001 | refactor-patterns.md §5 | 新增端口需用户授权 |
| RAM_SUBMODULE-001 | refactor-patterns.md §2 | 读延迟变化需声明 |
