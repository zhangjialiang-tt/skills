# S9 章节分析模板生成 — 完整 Prompt 模板

## 输入格式

```yaml
template_mode: 【generic/genre-specific】
central_schema: 【中央数据表字段】
genre_formula: 【S8输出；generic模式可为空】
high_quality_examples: 【经Q0和人工确认的典型章节】
target_tool: 【Excel/WPS/CSV/Notion/Markdown】
```

## 核心 Prompt

```text
你是"网文章节拆解模板设计器"。

你的目标是生成一份可反复用于不同书籍、不同批次的单章分析模板，不重新分析原作品。

【模板模式】
【generic/genre-specific】

【中央Schema】
【central_schema】

【题材配方】
【genre_formula】

【已确认典型章节】
【high_quality_examples】

【目标工具】
【target_tool】
```

## 输出 Schema

```json
{
  "task_id": "",
  "skill_id": "S9",
  "template_mode": "",
  "target_tool": "",
  "field_dictionary": [
    {
      "field_name": "payoff_strength",
      "display_name": "爽点强度",
      "definition": "本章主要已兑现爽点的综合强度",
      "data_type": "integer",
      "required": true,
      "allowed_values": "0-10",
      "owner_skill": "S4",
      "empty_value_rule": "无爽点填0",
      "good_example": 7,
      "bad_example": "很爽"
    }
  ],
  "full_header": [],
  "required_header": [],
  "manual_review_view": [],
  "blank_csv_header": "",
  "example_row": {},
  "enumeration_reference": {},
  "usage_instructions": [],
  "genre_specific_extensions": [],
  "deprecated_fields": []
}
```

## 质量校验规则

- 是否真正做到一章一行
- 字段是否可统计，而非全是长文本
- 是否说明必填、类型和允许值
- 是否遗漏证据与置信度
- 题材定制字段是否污染通用核心表
- 示例行是否与字段定义一致
- 空值、无事件和存疑的填写规则是否明确
- 是否出现无法由现有 Skill 生成的字段
