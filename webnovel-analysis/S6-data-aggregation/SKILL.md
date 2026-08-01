---
name: webnovel-analysis-aggregator
description: 将 S0-S5 分散输出合并为一章一行的中央数据表，生成卷级、单元级和全书统计，并输出人类可读的 Markdown 分析报告。在每批 S1-S5 完成后调用。触发场景：数据合并、中央表生成、卷级汇总、全书统计、数据导出、字段冲突检测、生成分析报告、汇总报告。当用户说"聚合数据"、"合并中央表"、"生成汇总表"、"数据合并校验"、"导出数据"、"生成报告"、"分析报告"时使用。不适用于：文学分析（用 S1-S5）、可视化（用 S7）、公式提炼（用 S8）。
---

# S6 数据聚合

将 S0-S5 分散输出合并为一章一行的中央数据表，生成卷级、单元级和全书统计，并输出人类可读的 Markdown 分析报告。不重新做文学判断，只合并、校验、计算派生字段和格式化输出。

## 何时触发

- 每批 S1-S5 完成后调用
- 全书完成后再次执行全局聚合

## 执行

1. 读取 `references/prompt-template.md` 获取完整 Prompt 模板
2. 读取 `references/report-template.md` 获取分析报告模板
3. 读取 `../../schemas/enums.yaml` 获取枚举值
4. 按模板执行合并，输出标准信封格式
5. 合并完成后，按 `report-template.md` 生成 `analysis_report.md`

## 合并规则

1. 主键为 task_id + chapter_id
2. 同一 Skill 同一字段出现多个版本时，优先使用 analysis_version 更高且状态为已确认的记录
3. 不同 Skill 写入同名字段但内容冲突时，不自行选择；写入 conflicts
4. 缺失字段保留为空，不编造默认值
5. 枚举值必须符合共享枚举；不合规值进入 validation_errors
6. 数值字段检查范围
7. 计算派生字段：emotion_range, payoff_density_flag, major_payoff_flag, strong_hook_flag, review_priority
8. **payoff_nature 处理**：从 S4 读取 `payoff_nature` 字段。`reverse` 类事件保留在 master_records 中，但 `payoff_density_flag` 和 `major_payoff_flag` 仅对 `commercial` / `literary` 类置 true；`reverse` 类事件单独标记 `reverse_payoff_flag`

### S3 角色数据消费规则

S3 输出包含四种数据结构，消费方式不同：

| S3 字段 | 数据层级 | 消费方式 | 输出目标 |
|---------|---------|---------|---------|
| `chapter_records` | 章节级 | 按 chapter_id 合并入中央表（pov_character, active_characters, narrative_functions） | `chapter_analysis_master` |
| `character_registry_updates` | 角色级（跨章节） | 更新角色档案快照，**不**合并入章节中央表 | `character_registry_snapshot.yaml` → 报告第四节 |
| `relationship_events` | 事件级（跨章节） | 追加到关系事件流，直接导出 | `relationship_events.csv` → 报告第四节 |
| `faction_updates` | 阵营级（跨章节） | 更新阵营结构，直接导出 | `faction_analysis.csv` → 报告第四节 |

**关键约束**：
- `character_registry_updates` 是角色档案（全书维度），**不可**按 chapter_id 写入主表
- `relationship_events` 是事件流，每条含 chapter_id 用于溯源，但本身是独立实体
- S3 批次间的 `character_registry_updates` 采用增量合并：同 character_id 覆盖，新 character_id 追加
- 报告中"核心关系线"表格需从 `relationship_events` 聚合生成，而非简单罗列

## review_priority 规则

**P0（阻塞）：** 主键重复、章节缺失、评分越界、高强度判断无证据、关键字段直接冲突
**P1（必须人工复核）：** 极值评分、主要爽点、卷首卷末、高适合度付费点、角色阵营反转、存疑结论
**P2（抽样复核）：** 普通抽样章节

## 下游交接

- `chapter_analysis_master.xlsx` → S7、S8、S9、Q0
- `volume_analysis.csv` → 交付物①
- `payoff_events.csv` → S7、S8
- `relationship_events.csv` → S8
- `analysis_report.md` → 交付物⑤（人类可读汇总报告）
- 验证错误 → Q0

## 分析报告生成规则

聚合完成后，基于合并数据生成 `analysis_report.md`。报告面向作者/编辑/研究人员，中文输出。

**模板位置**：`references/report-template.md`

模板定义了：
- 报告九节结构（概况/结构/情绪/人物/爽点/商业/配方/审计/附录）
- 生成原则（数据驱动、不重复JSON、中文流畅、保留歧义、体裁自觉）
- 缺失处理规则
- 文件引用规范

**注意**：模板中的 `字段占位符` 需替换为 S1-S5+Q0 实际数据，禁止保留占位符文本。

## 禁止事项

- 修改 S1-S5 的文学分析结论
- 编造默认值填充缺失字段
- 静默解决跨 Skill 冲突
- 在报告中隐藏 Q0 标记的冲突项
