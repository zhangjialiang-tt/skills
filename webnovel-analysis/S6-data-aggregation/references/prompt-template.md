# S6 数据聚合 — 完整 Prompt 模板

## 输入格式

```yaml
task_manifest: 【O0输出】
chapter_index: 【S0】
s1_records: 【S1】
s2_records: 【S2】
s3_records: 【S3，包含以下子结构】
  chapter_records: 【章节级：pov_character, active_characters, narrative_functions 等，按 chapter_id 合并入中央表】
  character_registry_updates: 【角色级：全书角色档案增量更新，不合并入章节中央表，输出到 character_registry_snapshot.yaml】
  relationship_events: 【事件级：关系变化事件流，按 chapter_id 溯源，输出到 relationship_events.csv】
  faction_updates: 【阵营级：阵营结构增量更新，输出到 faction_analysis.csv】
s4_records: 【S4】
s5_records: 【S5】
existing_master_table: 【已有中央表；首批为空】
merge_mode: 【append/update/rebuild】
```

**注意**：S3 的四种数据结构具有不同的数据层级（章节级 / 角色级 / 事件级 / 阵营级），必须按上述规则分别消费，不可统一按 chapter_id 合并入中央表。

## 核心 Prompt

```text
你是"网文拆解数据聚合器"。

你的任务是按task_id + chapter_id合并数据，不得自行修改文学分析结论。

【任务清单】
【task_manifest】

【S0章节索引】
【chapter_index】

【S1输出】
【s1_records】

【S2输出】
【s2_records】

【S3输出】
【s3_records】

【S4输出】
【s4_records】

【S5输出】
【s5_records】

【已有中央数据表】
【existing_master_table】

【合并模式】
【merge_mode】

【报告语言】
中文
```

## 输出 Schema

```json
{
  "task_id": "",
  "skill_id": "S6",
  "merge_mode": "",
  "master_records": [],
  "batch_statistics": {},
  "story_unit_statistics": [],
  "volume_statistics": [],
  "book_statistics": {},
  "validation_errors": [],
  "conflicts": [],
  "manual_review_items": [],
  "export_plan": {
    "master_csv": "chapter_analysis_master.csv",
    "master_xlsx": "chapter_analysis_master.xlsx",
    "volume_csv": "volume_analysis.csv",
    "payoff_events_csv": "payoff_events.csv",
    "relationship_events_csv": "relationship_events.csv",
    "analysis_report_md": "analysis_report.md"
  }
}
```

## 质量校验规则

- 章节数是否与 S0 索引一致
- 主键是否重复
- 每个字段是否由正确 Skill 写入
- 缺失值是否被错误填成 0
- 数字范围是否合法
- 同一章是否因重新运行而出现两行
- 派生字段能否由原始字段重新计算
- 汇总章节范围是否包含未分析章节

## 报告生成指引

聚合完成后，基于合并数据生成 `analysis_report.md`。报告面向作者/编辑/研究人员，中文输出。

**完整模板**：`references/report-template.md`

模板定义了：
- 报告九节结构（概况/结构/情绪/人物/爽点/商业/配方/审计/附录）
- 生成原则（数据驱动、不重复JSON、中文流畅、保留歧义、体裁自觉）
- 缺失处理规则
- 文件引用规范

**注意**：模板中的 `字段占位符` 需替换为 S1-S5+Q0 实际数据，禁止保留占位符文本。
