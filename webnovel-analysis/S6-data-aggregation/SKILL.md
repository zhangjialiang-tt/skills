---
name: webnovel-analysis-aggregator
description: 将 S0-S5 分散输出合并为一章一行的中央数据表，并生成卷级、单元级和全书统计。在每批 S1-S5 完成后调用。触发场景：数据合并、中央表生成、卷级汇总、全书统计、数据导出、字段冲突检测。当用户说"聚合数据"、"合并中央表"、"生成汇总表"、"数据合并校验"、"导出数据"时使用。不适用于：文学分析（用 S1-S5）、可视化（用 S7）、公式提炼（用 S8）。
---

# S6 数据聚合

将 S0-S5 分散输出合并为一章一行的中央数据表，并生成卷级、单元级和全书统计。不重新做文学判断，只合并、校验和计算派生字段。

## 何时触发

- 每批 S1-S5 完成后调用
- 全书完成后再次执行全局聚合

## 执行

1. 读取 `references/prompt-template.md` 获取完整 Prompt 模板
2. 读取 `../../schemas/enums.yaml` 获取枚举值
3. 按模板执行合并，输出标准信封格式

## 合并规则

1. 主键为 task_id + chapter_id
2. 同一 Skill 同一字段出现多个版本时，优先使用 analysis_version 更高且状态为已确认的记录
3. 不同 Skill 写入同名字段但内容冲突时，不自行选择；写入 conflicts
4. 缺失字段保留为空，不编造默认值
5. 枚举值必须符合共享枚举；不合规值进入 validation_errors
6. 数值字段检查范围
7. 计算派生字段：emotion_range, payoff_density_flag, major_payoff_flag, strong_hook_flag, review_priority

## review_priority 规则

**P0（阻塞）：** 主键重复、章节缺失、评分越界、高强度判断无证据、关键字段直接冲突
**P1（必须人工复核）：** 极值评分、主要爽点、卷首卷末、高适合度付费点、角色阵营反转、存疑结论
**P2（抽样复核）：** 普通抽样章节

## 下游交接

- `chapter_analysis_master.xlsx` → S7、S8、S9、Q0
- `volume_analysis.csv` → 交付物①
- `payoff_events.csv` → S7、S8
- `relationship_events.csv` → S8
- 验证错误 → Q0

## 禁止事项

- 修改 S1-S5 的文学分析结论
- 编造默认值填充缺失字段
- 静默解决跨 Skill 冲突
