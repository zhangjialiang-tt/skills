---
name: webnovel-analysis
description: 对已提供的网文正文、章节样本或既有拆书材料进行系统拆书分析，覆盖叙事结构、情绪节奏、人物关系、爽点工程、商业钩子、结构化汇总、质量审计与最终报告。用户提到拆书、网文分析、小说结构分析、爽点或商业钩子拆解时使用；不用于创作正文、生成章节卡或仅做普通书评。
---

# Webnovel Analysis

这是 `webnovel-analysis` 包的唯一外部入口。所有 O0、S0-S9、Q0 均为内部模块，不得被宿主直接安装、发现或路由。

## 工作流

1. 读取用户提供的文本、路径与分析范围；没有正文或可读取材料时，说明缺失输入，不编造分析证据。
2. 由 O0 生成任务与批次计划，S0 建立标准化章节和索引。
3. 按 [execution-dag.yaml](references/execution-dag.yaml) 调度内部模块；只有依赖满足时才执行下游。
4. 每个模块输出必须使用 [output-envelope.schema.json](schemas/output-envelope.schema.json) 的公共信封，并满足对应 `schemas/modules/*.schema.json`。
5. S6 只做结构化聚合；Q0 只做质量审计；R0 根据审计后的结构化产物生成最终报告。
6. P0 问题必须阻断下游；P1 是否阻断按风险与任务要求判定，并在 `manual_review_items` 中说明。

## 路由与模块

- 外部路由边界见 [route-policy.md](references/route-policy.md)。
- 内部模块清单见 [internal-module-registry.yaml](references/internal-module-registry.yaml)。
- R0 职责见 [r0-final-report.md](references/r0-final-report.md)。

## 输出约束

模型只生成以下公共字段；运行时校验状态、哈希与失效信息不属于模型输出：

```yaml
task_id: TASK-001
batch_id: BOOK
skill_id: S1
skill_version: 1.0.0
schema_version: 1.0.0
operation: analyze
payload: {}
uncertain_items: []
conflicts: []
manual_review_items: []
```

领域结果全部置于 `payload`。不得输出 `output_hash`、`validated_at`、`invalidated_by` 或 `status`。

## Milestone 1 边界

本里程碑冻结包结构、路由、Schema、模块依赖和 S6/R0 职责。它不提供可执行 runner、持久化状态机、哈希/断点恢复、模型调用器或全书规模证明。
