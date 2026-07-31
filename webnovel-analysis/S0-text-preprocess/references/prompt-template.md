# S0 文本预处理 — 完整 Prompt 模板

## 输入格式

```yaml
task_manifest: 【O0输出】
source:
  file_name: 【novel.txt】
  encoding: 【UTF-8/未知】
  raw_text: |
    【原始文本】
chapter_detection:
  known_pattern: 【如"第X章"或未知】
  preserve_author_notes: 【false】
batching:
  default_size: 【10】
  max_characters_per_batch: 【可选】
```

## 核心 Prompt

```text
你是"网文文本预处理器"。你只处理文本结构，不分析情节质量。

【任务信息】
【粘贴task_manifest】

【原始文本】
【粘贴原始文本】

【章节识别提示】
已知章节标题模式：【填写；未知则填"未知"】
默认批次大小：【10】
是否保留作者感言、广告和求票信息：【是/否】

【章节标准格式】
<chapter>
chapter_id: 【内部ID】
chapter_no: 【序号】
original_title: 【原始标题】
normalized_title: 【标准标题】
boundary_confidence: 【确定/推断/存疑】
text:
【正文原样保留】
</chapter>
```

## 输出 Schema

```json
{
  "task_id": "",
  "skill_id": "S0",
  "source_file": "",
  "preprocessing_report": {
    "raw_character_count": 0,
    "clean_character_count": 0,
    "chapter_count": 0,
    "removed_content_types": [],
    "text_modified_beyond_cleaning": false
  },
  "chapter_index": [
    {
      "chapter_id": "BK001-CH0001",
      "chapter_no": 1,
      "original_title": "第一章 醒来",
      "normalized_title": "醒来",
      "word_count": 2380,
      "boundary_confidence": "确定",
      "source_location": "novel.txt:1-187",
      "issue_flags": []
    }
  ],
  "batch_manifest": [
    {
      "batch_id": "BATCH-01",
      "chapter_ids": ["BK001-CH0001", "BK001-CH0002"],
      "reason": "连续开篇事件单元",
      "estimated_characters": 4620,
      "boundary_confidence": "推断"
    }
  ],
  "issues": [],
  "standardized_chapters": []
}
```

## 质量校验规则

- 章节总数是否与明显标题数量大致一致
- 开头、结尾和随机一章是否丢正文
- 广告删除是否误删角色对话
- 是否存在同一段落重复出现在两个章节
- `chapter_id` 是否唯一且稳定
- 批次是否拆开同一冲突的压抑和兑现
- "存疑边界"是否进入人工复核清单
