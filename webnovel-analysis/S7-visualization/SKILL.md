---
name: webnovel-analysis-visualization
description: 将中央表转化为可快速发现峰谷、长压抑、爽点密度和断章规律的热力图与曲线。在 S6 之后调用。触发场景：情绪热力图、爽点分布图、节奏曲线、断章强度可视化、卷级对比、ReviewQueue 生成。当用户说"可视化"、"热力图"、"节奏曲线"、"爽点分布"、"数据图表"、"生成图表"时使用。不适用于：数据分析（用 S6）、公式提炼（用 S8）。
---

# S7 情绪—爽点可视化

将中央表转化为可快速发现峰谷、长压抑、爽点密度和断章规律的热力图与曲线。不更改中央表原始数据。

## 何时触发

- S6 后
- 每完成一卷可运行一次
- 全书完成后生成正式版
- 默认采用 Excel/WPS 条件格式；Python 仅作增强

## 执行

1. 读取 `references/prompt-template.md` 获取完整 Prompt 模板
2. 按模板设计工作表和图表

## 工作表设计

| 工作表 | 内容 |
|--------|------|
| Heatmap | 章节级热力图（情绪/压力/释放/爽点/断章） |
| EmotionCurve | emotion/pressure/release 折线图 |
| PayoffTimeline | 主要爽点事件时间线 |
| VolumeSummary | 卷级统计 |
| ReviewQueue | 需人工复核的章节 |

## 条件格式规则速查

| 字段 | 最小值 | 最大值 |
|------|--------|--------|
| emotion_score | 1 红 | 10 绿 |
| pressure_score | 1 白 | 10 深红 |
| release_score | 0 白 | 10 深绿 |
| payoff_strength | 0 白 | 10 橙色 |
| chapter_break_strength | 1 白 | 10 紫色 |
| confidence = 存疑 | 灰色 | - |
| payoff_interval >= 5 | 黄色预警 | - |

## 下游交接

- 热力图 → 交付物②
- 峰谷章节和异常 → Q0 人工抽检
- 卷级曲线特征 → S8
- 典型高峰章节 → S9

## 禁止事项

- 修改中央表原始数据
- 把缺失值画成 0
- 虚构不存在的字段
