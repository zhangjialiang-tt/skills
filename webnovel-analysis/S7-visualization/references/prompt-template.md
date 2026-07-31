# S7 可视化 — 完整 Prompt 模板

## 输入格式

```yaml
master_table: 【S6中央表】
visualization_mode: 【excel/python/both】
chapter_range: 【全书或指定卷】
output_preferences:
  labels: 【是否显示章节名】
  annotate_major_payoffs: 【true】
  annotate_strong_hooks: 【true】
```

## 核心 Prompt

```text
你是"网文拆解数据可视化设计器"。

【中央数据表】
【master_table】

【模式】
【excel/python/both】

【范围】
【chapter_range】

【目标】
生成能回答以下问题的最小可用视图：
1. 哪些章节是情绪谷底和峰值？
2. 压抑持续了多少章才释放？
3. 主要爽点之间间隔多长？
4. 爽点类型是否重复？
5. 强断章是否集中在特定结构位置？
6. 哪一卷节奏最平、哪一卷峰谷最明显？
7. 哪些异常需要人工复核？
```

## 输出 Schema

```json
{
  "task_id": "",
  "skill_id": "S7",
  "workbook_design": [
    {
      "sheet": "Heatmap",
      "columns": ["chapter_no", "chapter_function", "emotion_score", "pressure_score", "release_score", "payoff_strength", "payoff_interval_chapters", "chapter_break_strength"],
      "sort_by": "chapter_no"
    }
  ],
  "conditional_format_rules": [
    {
      "sheet": "Heatmap",
      "field": "payoff_strength",
      "rule_type": "three_color_scale",
      "minimum": 0,
      "midpoint": 5,
      "maximum": 10
    }
  ],
  "chart_specs": [
    {
      "chart_id": "CHART-EMOTION-01",
      "sheet": "EmotionCurve",
      "chart_type": "line",
      "x_field": "chapter_no",
      "y_fields": ["emotion_score", "pressure_score", "release_score"],
      "filters": ["volume_id"],
      "annotations": ["payoff_strength >= 7", "chapter_break_strength >= 8"]
    }
  ],
  "anomaly_annotations": [],
  "python_script": "// 仅在需要时输出",
  "missing_fields": [],
  "manual_review_items": []
}
```

## 强制规则

- 章节按 chapter_no 排序
- 不更改中央表原始数据
- 缺失值不得当作 0 绘制
- 不把相关性解释为因果
- 图表必须注明评分范围
- 主要爽点定义为 payoff_strength >= 7
- 强断章定义为 chapter_break_strength >= 8
- Python 脚本必须先检查所需列是否存在
- 不存在字段时输出缺失字段清单，不虚构图表
