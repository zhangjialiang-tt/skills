# R0 最终分析报告模板

本文件定义 `analysis_report.md` 的结构与生成原则。Q0 审计完成后，由根 Skill 的 R0 阶段按此模板生成人类可读的 Markdown 报告。

---

## 报告结构

```markdown
# 《书名》拆解分析报告

> 生成时间：YYYY-MM-DD | 数据版本：vX.X | 章节数：N

## 一、作品概况

- **书名**：
- **作者**：
- **体裁**：（来自 O0 task_manifest；若 S1/S4 有修正，以 S1/S4 为准）
- **总字数**：（来自 S0）
- **结构类型**：线性 / 非线性 / 多时间线（来自 S1 `timeline_structure` 或 `batch_summary.structure_type`）
- **核心悬念**：（来自 S1 `batch_summary.core_loop`）
- **主题母题**：（来自 S1 `batch_summary.thematic_motifs`）

## 二、结构总览

### 卷级结构

| 卷 | 分析用名称 | 章节范围 | 核心功能 | 核心冲突 | 置信度 |
|----|-----------|---------|---------|---------|--------|
| V01 | （来自 S1 `volume_updates`） | | | | 推断/确认 |

> 注：若作者未明示卷结构，所有卷名为"分析用"推断命名。

### 故事单元

| 单元 | 分析用名称 | 章节范围 | 功能 | 置信度 |
|------|-----------|---------|------|--------|
| U01 | （来自 S1 `story_unit_updates`） | | | |

## 三、情绪节奏分析

### 全书情绪曲线特征

- **峰值章 Top 3**：（来自 S2 `batch_summary.peaks`）
- **谷值章 Bottom 3**：（来自 S2 `batch_summary.valleys`）
- **曲线形状**：压抑型 / 波浪型 / 高潮型（来自 S2 `batch_summary.rhythm_shape`）
- **平均情绪分**：（来自 S2 `batch_statistics.mean_emotion_score`）
- **平均压抑分**：（来自 S2 `batch_statistics.mean_pressure_score`）
- **平均释放分**：（来自 S2 `batch_statistics.mean_release_score`）

### 关键发现

- （来自 S2 `batch_summary.note` 或 `uncertain_items`，如"文学性作品，平均情绪分偏低"）
- （来自 S2 的体裁适配说明）

## 四、人物关系发现

### 核心关系线

| 关系 | 类型 | 走向 | 关键变化章 |
|------|------|------|-----------|
| （来自 S3 `batch_summary.core_relationships` + `relationship_events`） | | | |

### 阵营结构

| 阵营 | 成员 | 核心冲突 |
|------|------|---------|
| （来自 S3 `faction_updates`） | | |

### 人物网络特征

- （来自 S3 `batch_summary`，如"真假悟空为全书核心人物结构：被驯化者杀死自由真我"）
- （来自 S3 `uncertain_items`，如"沙僧名称前后不一致"）

## 五、爽点工程总结

### 爽点密度与分布

- **有爽点章节 / 总章节**：（来自 S4 `batch_statistics.chapters_with_payoff` / `total_chapters`）
- **爽点密度**：（来自 S4 `batch_statistics.payoff_density`）
- **平均压抑等级**：（来自 S4 `batch_statistics.avg_suppression_level`）
- **平均爽点强度**：（来自 S4 `batch_statistics.avg_payoff_strength`）

### 爽点类型分布

| 类型 | 次数 | 占比 |
|------|------|------|
| （来自 S4 `batch_statistics.payoff_type_distribution`） | | |

### 读者奖励分布

| 奖励类型 | 次数 |
|----------|------|
| （来自 S4 `batch_statistics.reader_reward_distribution`） | |

### 关键爽点事件

| 事件ID | 章节 | 类型 | 强度 | 读者奖励 | 释放模式 |
|--------|------|------|------|---------|---------|
| （来自 S4 `payoff_events`） | | | | | |

### 改编建议

- （来自 S4 `batch_summary.genre_implication`）
- （来自 S4 `uncertain_items`，如"反向释放是否应计为爽点存疑"）

## 六、商业卡点分析

### 高适宜度付费点

| 章节 | 断章强度 | 断章相位 | 追读问题 | 付费适宜度 |
|------|---------|---------|---------|-----------|
| （来自 S5 `commercial_pattern_summary.high_paywall_suitability` + `records`） | | | | |

### 断章相位分布

| 相位 | 章节列表 |
|------|---------|
| 爽前 | （来自 S5 `commercial_pattern_summary.break_phase_distribution`） |
| 爽中 | |
| 爽后 | |
| 自然收束 | |

### 付费节奏特征与风险

- （来自 S5 `batch_summary.overall`）
- （来自 S5 `batch_summary.genre_implication`）
- （来自 S5 `commercial_pattern_summary.hook_fairness_issues`）

## 七、题材配方摘要

### 核心读者承诺

> （来自 S8 `core_reader_promise.statement`）

### 主角配方

- **初始缺口**：（来自 S8 `protagonist_formula.initial_gap`）
- **核心欲望**：（来自 S8 `protagonist_formula.core_desire`）
- **不对称优势**：（来自 S8 `protagonist_formula.asymmetric_advantage`）
- **代价/约束**：（来自 S8 `protagonist_formula.cost_or_constraint`）

### 可迁移元素

- （来自 S8 `transferable_elements`）

### 不可照搬

- （来自 S8 `do_not_copy`）

### 失败模式

- （来自 S8 `failure_modes`）

### 反例条件

- （来自 S8 `counter_conditions`）

## 八、质量审计摘要

> 数据质量状态：（来自 Q0 `audit_summary.overall_status`）

### P0 阻塞项

（若无则写"无 P0 阻塞项"；若有则表格列出）

| 章节 | 问题类别 | 问题描述 | 建议处理 |
|------|---------|---------|---------|
| （来自 Q0 `issues` severity=P0） | | | |

### P1 待人工复核项

| 章节 | 问题类别 | 问题描述 | 建议处理 |
|------|---------|---------|---------|
| （来自 Q0 `issues` severity=P1） | | | |

### P2 一般问题

| 章节 | 问题类别 | 问题描述 | 建议处理 |
|------|---------|---------|---------|
| （来自 Q0 `issues` severity=P2） | | | |

### 跨 Skill 冲突模式

- （来自 Q0 `cross_skill_checks.note`）

## 九、附录

### 数据文件清单

| 文件 | 来源 Skill | 说明 |
|------|-----------|------|
| chapter_analysis_master.csv | S6 | 章节级中央表 |
| volume_analysis.csv | S6 | 卷级统计 |
| payoff_events.csv | S4 | 爽点事件明细 |
| relationship_events.csv | S3 | 关系变化事件 |
| analysis_report.md | R0 | 本报告 |

### Q0 完整审计队列

| 章节 | 复核原因 | 复核问题 |
|------|---------|---------|
| （来自 Q0 `minimal_review_queue`） | | |
```

---

## 生成原则

### 1. 数据驱动

所有结论必须引用 S1-S5+Q0 的具体字段，禁止凭空推断。

- ✅ 正确："全书情绪均值 4.0、释放均值 1.5，最高分仅 7（S2 `batch_statistics`）"
- ❌ 错误："这本书整体比较压抑"（未引用数据）

### 2. 不重复 JSON

报告是 JSON 的**解读**而非**复制**，避免粘贴大段原始数据。

- ✅ 正确：将 `payoff_events` 数组提炼为"关键爽点事件"表格，每行一个事件
- ❌ 错误：把 S4 的 `payoff_events` JSON 原样粘贴进报告

### 3. 中文流畅

使用自然语言描述，避免"字段名: 值"的机械罗列。

- ✅ 正确："爽点密度低（10/21 章有正反馈），压抑深（均值 2.4），释放弱（均值 1.5）"
- ❌ 正确："payoff_density: 低, avg_suppression_level: 2.4, avg_release_score: 1.5"

### 4. 保留歧义

S1/S4 等标注"推断""存疑"的内容，在报告中必须保留置信度说明。

- S1 标注"推断命名"的卷名 → 报告中写"分析用名称（推断命名）"
- S4 标注"反向释放"的爽点 → 报告中写"反向释放（是否计入商业爽点口径待确认）"
- Q0 标记的 P1 冲突 → 报告中保留"待人工复核"标签

### 5. 体裁自觉

当 S4/S5 标注"非商业爽文"时，报告应明确区分"文本特征"与"商业改造建议"。

- 使用小节标题区分："文本特征" vs "商业改编建议"
- 或使用标注：`[文学性特征]` / `[商业改造建议]`

### 6. 缺失处理

- 若某节数据缺失（如 S8 未运行），写"本节数据暂未生成"而非跳过该节
- 若某表格无数据（如 P0 阻塞项为空），写"无"而非删除表格

### 7. 文件引用

- 报告末尾附录必须列出所有数据文件及其来源 Skill
- Q0 审计队列必须完整列出，不可截断
