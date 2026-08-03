# 爆款网文拆解 Skill 库

> 历史设计稿：Milestone 1 的规范入口为 `../SKILL.md`，架构冻结见 `architecture-freeze-m1.md`；冲突时以后者为准。

## 第二阶段下：S5—S9、Q0与共享枚举

# S5 商业卡点 Skill

## 1. Skill 名称与一句话功能

**名称：** S5 商业卡点分析
**功能：** 识别章节的断章驱动力、付费切分价值、追读问题和连续阅读机制。

## 2. 调用时机

- S0文本完成后运行。
- 推荐在 S1、S2、S4完成后运行。
- 两种模式：
  - `incremental`：逐章判断断章与追读机制。
  - `consolidation`：全书汇总付费点规律和追读模式。

- 本 Skill 分析文本机制，不预测真实平台收入。

## 3. 输入格式

```yaml
mode: 【incremental/consolidation】
chapters: 【当前批次文本】
structure_records: 【S1结果】
emotion_records: 【S2结果】
payoff_records: 【S4结果】
platform_context:
  monetization_mode: 【免费转付费/全付费/未知】
  known_paywall_chapter: 【可选】
```

## 4. 核心 Prompt 模板

```text
你是“付费网文商业阅读机制分析师”。

你分析的是文本如何驱动下一章阅读，不预测真实收入、订阅率或平台推荐结果。

【运行模式】
【incremental/consolidation】

【平台背景】
【platform_context】

【S1结构数据】
【structure_records】

【S2情绪数据】
【emotion_records】

【S4爽点数据】
【payoff_records】

【章节文本】
【chapters】

【核心区分】
- 章末钩子：本章结尾留下的具体未完成刺激。
- 追读问题：读者看完后最想获得答案的问题。
- 付费卡点：在读者已经获得足够价值后，于高确定性期待形成处切断。
- 纯打断：仅把完整场景从中间切开，却未形成新的阅读承诺。
- 爽后卡：先兑现部分奖励，再打开更大问题。
- 爽前卡：在即将兑现前切断，短期强但频繁使用容易透支信任。

【断章类型】
危机迫近、行动即将发生、身份将揭露、结果未公布、反转刚发生、
新敌人登场、收益即将兑现、关系即将表态、信息差扩大、
倒计时、场景硬切、自然收束、无明显钩子。

【购买/追读动机】
看结果、看反击、看他人反应、看身份揭露、看收益、看真相、
看关系进展、看危机解决、看新地图、看能力升级、其他。

【分析步骤】
1. 判断本章是否先交付了足够的阅读价值。
2. 提取章末最后一个有效信息或行动。
3. 写出一个具体追读问题，禁止使用“接下来会发生什么”。
4. 判断钩子类型和强度1-10。
5. 判断该切点属于爽前、爽中、爽后还是自然收束。
6. 判断付费适合度：低、中、高。
7. 写出支持和反对设为付费点的理由。
8. 识别本章主要追读机制：未完成目标、信息差、情绪欠账、收益承诺、关系未决或危机。
9. consolidation模式统计高强度卡点的共同位置、类型和兑现距离。
10. 不得把“章节写得精彩”直接等同于“适合付费切分”。

【强度锚点】
1-2：基本无继续动力。
3-4：有轻微未完成信息，但可暂停。
5-6：有明确问题，读者有继续意愿。
7-8：强期待，核心行动、结果或反应尚未出现。
9：高价值兑现临界点或重大反转后果未展开。
10：全书极少数商业峰值，多重期待同时处于临界点。

【防幻觉】
- 仅依据所给文本和结构化结果。
- 不虚构平台规则、真实付费转化率或读者数据。
- 不确定的付费位置标“存疑”。
- 章节没有钩子时必须如实填写。
- 若钩子依赖未提供的前文，应降低置信度。

【输出JSON】
{
  "task_id": "",
  "skill_id": "S5",
  "mode": "",
  "batch_id": "",
  "records": [
    {
      "chapter_id": "",
      "value_delivered_before_break": [],
      "ending_hook": "",
      "cliffhanger_type": "",
      "chapter_break_strength": 0,
      "break_phase": "爽前/爽中/爽后/自然收束",
      "follow_up_question": "",
      "reader_expectation": "",
      "information_gap": "",
      "purchase_motivation": [],
      "commercial_position": "",
      "paywall_suitability": "低/中/高",
      "reason_for_paywall": "",
      "risk_against_paywall": "",
      "expected_resolution_distance": "下一章/1-3章/4章以上/存疑",
      "hook_fairness": "公平/边缘/欺骗风险",
      "core_evidence": [],
      "analysis_confidence": ""
    }
  ],
  "commercial_pattern_summary": {},
  "batch_summary": {},
  "uncertain_items": [],
  "conflicts": [],
  "manual_review_items": []
}
```

## 5. 输出 Schema

示例：

```json
{
  "chapter_id": "BK001-CH0001",
  "value_delivered_before_break": ["主角识破账目异常", "完成一次小反制"],
  "ending_hook": "厂长要求立刻搜查林川工位",
  "cliffhanger_type": "危机迫近",
  "chapter_break_strength": 9,
  "break_phase": "爽后",
  "follow_up_question": "林川藏起的原始账本会不会被搜出来",
  "reader_expectation": "主角继续利用信息优势反制搜查",
  "information_gap": "读者知道林川留了原账，但不知道藏在哪里",
  "purchase_motivation": ["看反击", "看危机解决"],
  "paywall_suitability": "高",
  "reason_for_paywall": "先交付小反制，再打开立即发生的新危机",
  "risk_against_paywall": "若下一章继续拖延搜查结果，会削弱信任",
  "expected_resolution_distance": "下一章",
  "hook_fairness": "公平",
  "analysis_confidence": "确定"
}
```

## 6. 质量校验规则

- 追读问题是否具体且可在后续回答。
- 是否只切断动作，却没有建立新期待。
- 付费点前是否已经交付一定价值。
- 是否大量使用爽前卡而长期不兑现。
- 强钩子是否有下一章或短期兑现承诺。
- `chapter_break_strength` 是否因情绪高分而被机械提高。
- 是否虚构真实转化率或平台运营规律。
- 章末钩子是否和原文最后有效段落一致。

## 7. 下游交接

- 章节商业字段 → S6。
- 高强度卡点 → S7标记。
- 付费点类型和兑现距离 → S8商业配方。
- 高质量断章案例 → S9模板示例。
- 欺骗风险 → Q0。

## 8. Claude Skill 写法

```markdown
---
name: webnovel-commercial-hooks
description: Analyze chapter endings, paywall suitability, follow-up questions, information gaps, payoff timing, and continuous-reading mechanisms from supplied web-novel text and S1/S2/S4 records.
---

# Web-Novel Commercial Hooks

Read `references/prompt.md`.

Rules:

- Analyze textual mechanisms, not real revenue.
- Distinguish paywall suitability from chapter quality.
- Require a specific follow-up question.
- Record value delivered before the break.
- Flag delayed or unfair cliffhangers.
- Return evidence-backed chapter records and aggregate patterns.
```

---

# S6 数据聚合 Skill

## 1. Skill 名称与一句话功能

**名称：** S6 数据聚合
**功能：** 将 S0—S5分散输出合并为一章一行的中央数据表，并生成卷级、单元级和全书统计。

## 2. 调用时机

- 每批 S1—S5完成后调用。
- 全书完成后再次执行全局聚合。
- S6不重新做文学判断，只合并、校验和计算派生字段。

## 3. 输入格式

```yaml
task_manifest: 【O0输出】
chapter_index: 【S0】
s1_records: 【S1】
s2_records: 【S2】
s3_records: 【S3】
s4_records: 【S4】
s5_records: 【S5】
existing_master_table: 【已有中央表；首批为空】
merge_mode: 【append/update/rebuild】
```

## 4. 核心 Prompt 模板

```text
你是“网文拆解数据聚合器”。

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
【append/update/rebuild】

【规则】
1. 主键为task_id + chapter_id。
2. 同一Skill同一字段出现多个版本时，优先使用analysis_version更高且状态为已确认的记录。
3. 不同Skill写入同名字段但内容冲突时，不自行选择；写入conflicts。
4. 缺失字段保留为空，不编造默认值。
5. 枚举值必须符合共享枚举；不合规值进入validation_errors。
6. 数值字段检查范围。
7. 计算派生字段：
   - emotion_range = emotion_high - emotion_low
   - payoff_density_flag
   - major_payoff_flag：payoff_strength >= 7
   - strong_hook_flag：chapter_break_strength >= 8
   - review_priority
8. 生成批次摘要、故事单元摘要、卷级摘要和全书统计。
9. 所有汇总必须可以回溯到章节数据。
10. 不把平均值解释为因果关系。

【review_priority规则】
P0：
- 主键重复；
- 章节缺失；
- 评分越界；
- 高强度判断无证据；
- 关键字段在Skill间直接冲突。
P1：
- 极值评分；
- 主要爽点；
- 卷首卷末；
- 高适合度付费点；
- 角色阵营反转；
- 存疑结论。
P2：
- 普通抽样章节。

【输出JSON】
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
    "relationship_events_csv": "relationship_events.csv"
  }
}
```

## 5. 输出 Schema

中央表一行示例：

```json
{
  "task_id": "BK20260731-001",
  "chapter_id": "BK001-CH0001",
  "chapter_no": 1,
  "chapter_function": "建立困境",
  "emotion_score": 5,
  "pressure_score": 7,
  "release_score": 4,
  "payoff_type": "智识碾压",
  "payoff_strength": 5,
  "chapter_break_strength": 9,
  "paywall_suitability": "高",
  "analysis_confidence": "确定",
  "review_priority": "P1"
}
```

卷级统计示例：

```json
{
  "volume_id": "V01",
  "chapter_count": 38,
  "mean_emotion_score": 5.9,
  "mean_pressure_score": 6.1,
  "major_payoff_count": 9,
  "mean_major_payoff_interval": 3.8,
  "strong_hook_count": 11,
  "dominant_payoff_types": ["智识碾压", "利益获得"]
}
```

## 6. 质量校验规则

- 章节数是否与 S0索引一致。
- 主键是否重复。
- 每个字段是否由正确 Skill 写入。
- 缺失值是否被错误填成0。
- 数字范围是否合法。
- 同一章是否因重新运行而出现两行。
- 派生字段能否由原始字段重新计算。
- 汇总章节范围是否包含未分析章节。

## 7. 下游交接

- `chapter_analysis_master.xlsx` → S7、S8、S9、Q0。
- `volume_analysis.csv` → 交付物①。
- `payoff_events.csv` → S7、S8。
- `relationship_events.csv` → S8。
- 验证错误 → Q0。

## 8. Claude Skill 写法

```markdown
---
name: webnovel-analysis-aggregator
description: Merge S0-S5 web-novel analysis outputs into a validated chapter-level master table and derived batch, story-unit, volume, and book statistics.
---

# Web-Novel Analysis Aggregator

Read `references/prompt.md`.

Requirements:

- Merge only by task_id and chapter_id.
- Never revise literary judgments.
- Preserve missing values.
- Validate enum and numeric ranges.
- Emit conflicts instead of silently choosing.
- Produce export-ready master and summary records.
```

---

# S7 可视化 Skill

## 1. Skill 名称与一句话功能

**名称：** S7 情绪—爽点可视化
**功能：** 将中央表转化为可快速发现峰谷、长压抑、爽点密度和断章规律的热力图与曲线。

## 2. 调用时机

- S6后。
- 每完成一卷可运行一次。
- 全书完成后生成正式版。
- 默认采用 Excel/WPS条件格式；Python仅作增强。

## 3. 输入格式

```yaml
master_table: 【S6中央表】
visualization_mode: 【excel/python/both】
chapter_range: 【全书或指定卷】
output_preferences:
  labels: 【是否显示章节名】
  annotate_major_payoffs: 【true】
  annotate_strong_hooks: 【true】
```

## 4. 推荐最省事实方案

使用 Excel/WPS生成一个主视图：

| 行       | 列                                                                     |
| -------- | ---------------------------------------------------------------------- |
| 每章一行 | 章节号、章节功能、情绪分、压力分、释放分、爽点强度、爽点间隔、断章强度 |

条件格式建议：

- `emotion_score`：1红—5白—10绿。
- `pressure_score`：1白—10深红。
- `release_score`：0白—10深绿。
- `payoff_strength`：0白—10橙色高亮。
- `chapter_break_strength`：1白—10紫色高亮。
- `payoff_interval_chapters >= 5`：黄色预警。
- `analysis_confidence = 存疑`：灰色标记。

## 5. 核心 Prompt 模板

```text
你是“网文拆解数据可视化设计器”。

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

【默认输出】
A. Excel/WPS工作表设计。
B. 条件格式规则。
C. 图表字段映射。
D. 异常标注规则。
E. 若模式包含Python，输出可直接运行的Python脚本。

【工作表】
1. Heatmap：章节级热力图。
2. EmotionCurve：emotion_score、pressure_score、release_score折线。
3. PayoffTimeline：主要爽点事件时间线。
4. VolumeSummary：卷级统计。
5. ReviewQueue：需要人工复核的章节。

【强制规则】
- 章节按chapter_no排序。
- 不更改中央表原始数据。
- 缺失值不得当作0绘制。
- 不把相关性解释为因果。
- 图表必须注明评分范围。
- 主要爽点定义为payoff_strength >= 7。
- 强断章定义为chapter_break_strength >= 8。
- Python脚本必须先检查所需列是否存在。
- 不存在字段时输出缺失字段清单，不虚构图表。

【Excel条件格式】
emotion_score：1红、5白、10绿。
pressure_score：1白、10深红。
release_score：0白、10深绿。
payoff_strength：0白、10橙色。
chapter_break_strength：1白、10紫色。
analysis_confidence为存疑：灰色。
manual_review_required为1：加粗边框。

【输出JSON】
{
  "task_id": "",
  "skill_id": "S7",
  "workbook_design": [],
  "conditional_format_rules": [],
  "chart_specs": [],
  "anomaly_annotations": [],
  "python_script": "仅在需要时输出",
  "missing_fields": [],
  "manual_review_items": []
}
```

## 6. 输出 Schema

图表规格示例：

```json
{
  "chart_id": "CHART-EMOTION-01",
  "sheet": "EmotionCurve",
  "chart_type": "line",
  "x_field": "chapter_no",
  "y_fields": ["emotion_score", "pressure_score", "release_score"],
  "filters": ["volume_id"],
  "annotations": ["payoff_strength >= 7", "chapter_break_strength >= 8"]
}
```

条件格式示例：

```json
{
  "sheet": "Heatmap",
  "field": "payoff_strength",
  "rule_type": "three_color_scale",
  "minimum": 0,
  "midpoint": 5,
  "maximum": 10
}
```

## 7. 质量校验规则

- 章节是否按正确顺序。
- 缺失值是否被画成0分谷底。
- 图表是否因列过多不可读。
- 爽点和情绪是否使用不同指标。
- 卷界是否有明显标记。
- 极值点能否定位到原章节。
- ReviewQueue是否包含存疑和冲突章节。
- 是否只做漂亮图，而未支持具体决策。

## 8. 下游交接

- 热力图 → 交付物②。
- 峰谷章节和异常 → Q0人工抽检。
- 卷级曲线特征 → S8。
- 典型高峰章节 → S9。

## 9. Claude Skill 写法

```markdown
---
name: webnovel-analysis-visualization
description: Convert a validated chapter-analysis table into Excel/WPS heatmaps, emotion curves, payoff timelines, volume summaries, review queues, and optional Python visualization code.
---

# Web-Novel Analysis Visualization

Read `references/prompt.md`.

Requirements:

- Prefer a simple Excel/WPS implementation.
- Preserve missing values.
- Do not modify source data.
- Mark volume boundaries, major payoffs, strong hooks, and review items.
- Produce Python only when requested.
```

---

# S8 套路公式提炼 Skill

## 1. Skill 名称与一句话功能

**名称：** S8 题材套路公式提炼
**功能：** 将单书结构数据压缩为可迁移的“题材配方”，同时标明证据、适用边界和不可照搬部分。

## 2. 调用时机

- S6全书聚合完成后。
- 推荐先运行全局Q0，确保数据基本可信。
- 输入至少包含全书中央表、卷级表、爽点事件和角色关系数据。

## 3. 输入格式

```yaml
book_profile: 【书名、题材、篇幅】
master_table: 【S6中央表】
volume_analysis: 【S1/S6卷级表】
payoff_events: 【S4事件表】
character_registry: 【S3】
relationship_events: 【S3】
commercial_patterns: 【S5】
audit_summary: 【Q0】
```

## 4. 核心 Prompt 模板

```text
你是“网文商业结构配方提炼师”。

你的任务是从这一部作品的数据中提炼可迁移方法，不得把单书观察伪装成整个题材的普遍规律。

【作品信息】
【book_profile】

【章节中央表】
【master_table】

【卷级结构】
【volume_analysis】

【爽点事件】
【payoff_events】

【角色和关系】
【character_registry】
【relationship_events】

【商业卡点】
【commercial_patterns】

【审计摘要】
【audit_summary】

【输出目标】
建立一份可用于新书选题和结构规划的“题材配方”，包含：
1. 核心读者承诺。
2. 主角初始缺口、核心优势和长期欲望。
3. 开篇启动机制。
4. 基础叙事循环。
5. 卷级升级阶梯。
6. 压抑—释放公式。
7. 主要爽点组合。
8. 角色功能组合。
9. 关系推进机制。
10. 付费和追读机制。
11. 节奏参数。
12. 可迁移项、依赖项和不可照搬项。
13. 常见失败模式。
14. 用于新书设计的参数化模板。

【强制方法】
A. 每条配方必须引用数据证据：
   - 支持章节；
   - 出现次数；
   - 典型间隔；
   - 所属卷或单元。
B. 区分：
   - 作品事实；
   - 分析推断；
   - 可迁移建议。
C. 不得用一个案例宣称“该题材必须如此”。
D. 样本不足时降低置信度。
E. 将表面设定和底层机制分开。
   例如：“旧厂经营”是表面设定；
   “利用信息差获得稀缺资源，再通过公开结果获得认可”是底层机制。
F. 公式必须可替换变量，不能只复述原剧情。
G. 不复制专有角色名、地点名和独特情节组合到新书配方。
H. 给出至少三条反例条件：什么情况下不应使用该公式。

【配方表达格式】
当【主角初始缺口】遭遇【高压触发事件】，
主角利用【差异化优势】完成【第一次可见反制】，
获得【阶段资源/身份变化】，
同时打开【更高层冲突】。
之后以每【N】章一次【主要奖励】、
每【M】章一次【关系或信息变化】、
每卷完成一次【不可逆身份升级】维持追读。

【输出YAML】
formula_id: ""
source_scope:
  book_id: ""
  chapter_count: 0
  data_quality: ""
core_reader_promise:
  statement: ""
  evidence: []
protagonist_formula:
  initial_gap: ""
  core_desire: ""
  asymmetric_advantage: ""
  cost_or_constraint: ""
opening_engine:
  trigger: ""
  first_goal: ""
  first_visible_payoff: ""
  expected_chapter_window: ""
narrative_loop:
  steps: []
  average_cycle_length: ""
volume_escalation:
  - volume_function: ""
    opening_state: ""
    closing_state: ""
    irreversible_change: ""
pressure_payoff_formula:
  typical_suppression_level: ""
  major_payoff_interval: ""
  dominant_release_modes: []
  dominant_reader_rewards: []
payoff_portfolio: []
character_function_set: []
relationship_engine: []
commercial_engine:
  dominant_hook_types: []
  preferred_break_phase: ""
  typical_resolution_distance: ""
parameterized_recipe: ""
transferable_elements: []
dependent_elements: []
do_not_copy: []
failure_modes: []
counter_conditions: []
confidence: ""
uncertain_items: []
```

## 5. 输出 Schema

示例节选：

```yaml
formula_id: urban-rebirth-factory-v1
source_scope:
  book_id: BK001
  chapter_count: 120
  data_quality: 中高
core_reader_promise:
  statement: 主角利用前世信息修正失败人生，并把隐性能力转化为公开地位
  evidence:
    - 第1-3章完成首次避坑
    - 第18章获得第一项可控制资源
narrative_loop:
  steps:
    - 出现资源或制度困境
    - 主角发现他人忽略的信息差
    - 小范围试探
    - 对手公开压制
    - 主角用结果反制
    - 获得资源并引出更高层利益冲突
  average_cycle_length: 4-6章
pressure_payoff_formula:
  typical_suppression_level: 2-3
  major_payoff_interval: 3-5章
  dominant_release_modes:
    - 部分释放
    - 连锁释放
parameterized_recipe: 当被低估的专业型主角遭遇职业清算时，利用时间或知识优势保存关键筹码，以可验证结果完成首次反制，并将个人翻身升级为资源经营和秩序竞争。
confidence: 推断
```

## 6. 质量校验规则

- 是否只是剧情摘要，没有抽象成变量。
- 是否把作品特有名词直接当作公式。
- 每个规律是否有章节次数和间隔证据。
- 是否把单书结论夸大为题材普遍真理。
- 是否明确依赖条件。
- 参数能否替换到其他人物、行业和世界设定。
- 公式是否保留“读者奖励”而非只有事件流程。
- 是否列出不能照搬的内容。

## 7. 下游交接

- `genre_formula.yaml` → 新书选题和大纲设计。
- 主要节奏参数 → S9生成定制分析模板。
- 高置信机制 → Skill库中的题材参考资产。
- 低置信规律 → 后续多书横向比较，不作为定论。

## 8. Claude Skill 写法

```markdown
---
name: webnovel-genre-formula
description: Extract an evidence-backed, parameterized genre recipe from completed S1-S7 web-novel analysis without overgeneralizing one book into a universal rule.
---

# Web-Novel Genre Formula

Read `references/prompt.md`.

Requirements:

- Separate story facts, inference, and transferable advice.
- Cite chapters, counts, intervals, and volume positions.
- Abstract mechanisms rather than copying proprietary plot details.
- State dependencies, counter-conditions, failure modes, and confidence.
- Produce a parameterized YAML recipe.
```

---

# S9 章节分析模板生成 Skill

## 1. Skill 名称与一句话功能

**名称：** S9 章节分析模板生成
**功能：** 根据题材配方和已验证字段，生成可批量复用的单章拆解表、填写说明和示例行。

## 2. 调用时机

- 基础版可在中央Schema冻结后运行。
- 题材定制版在 S8后运行。
- 每次修改中央字段或评分体系后重新生成。

## 3. 输入格式

```yaml
template_mode: 【generic/genre-specific】
central_schema: 【中央数据表字段】
genre_formula: 【S8输出；generic模式可为空】
high_quality_examples: 【经Q0和人工确认的典型章节】
target_tool: 【Excel/WPS/CSV/Notion/Markdown】
```

## 4. 核心 Prompt 模板

```text
你是“网文章节拆解模板设计器”。

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
【Excel/WPS/CSV/Notion/Markdown】

【模板必须包含】
1. 基础索引。
2. 结构功能。
3. 因果与开放悬念。
4. 人物与关系变化。
5. 情绪、压力和释放评分。
6. 压抑与爽点事件。
7. 章末钩子和追读问题。
8. 文本证据。
9. 置信度和人工复核状态。
10. 题材定制字段，但不得破坏通用核心字段。

【设计原则】
- 一章一行。
- 主要字段适合筛选和统计。
- 长文本字段单独放末尾。
- 使用固定枚举，减少自由描述。
- 每个字段给出定义、数据类型、是否必填、允许值和错误示例。
- 给出一行完整示例。
- 生成空白CSV表头。
- 生成适合人工抽检的简版视图。
- genre-specific模式只新增题材字段，不删除通用字段。
- 不把作品专有角色名写入通用模板。

【防幻觉】
- 仅根据给定Schema和题材配方设计字段。
- 不发明未被分析验证的商业指标。
- 不输出真实平台收入字段，除非用户有真实数据。
- 无法确定是否需要的字段标为“可选”。

【输出】
{
  "task_id": "",
  "skill_id": "S9",
  "template_mode": "",
  "target_tool": "",
  "field_dictionary": [],
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

## 5. 输出 Schema

字段字典示例：

```json
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
```

示例行：

```json
{
  "chapter_id": "BK001-CH0001",
  "chapter_no": 1,
  "chapter_function": "建立困境",
  "main_event": "主角保住异常采购账本",
  "emotion_score": 5,
  "pressure_score": 7,
  "release_score": 4,
  "suppression_level": 3,
  "payoff_type": "智识碾压",
  "payoff_strength": 5,
  "ending_hook_type": "危机",
  "chapter_break_strength": 9,
  "analysis_confidence": "确定"
}
```

## 6. 质量校验规则

- 是否真正做到一章一行。
- 字段是否可统计，而非全是长文本。
- 是否说明必填、类型和允许值。
- 是否遗漏证据与置信度。
- 题材定制字段是否污染通用核心表。
- 示例行是否与字段定义一致。
- 空值、无事件和存疑的填写规则是否明确。
- 是否出现无法由现有 Skill生成的字段。

## 7. 下游交接

- 模板本身即交付物④。
- `field_dictionary.json` → 所有 Skill保持字段一致。
- `blank_template.csv` → 新书分析项目。
- `manual_review_view` → 创作者抽检。
- 枚举表 → Q0验证。

## 8. Claude Skill 写法

```markdown
---
name: webnovel-chapter-analysis-template
description: Generate reusable generic or genre-specific chapter-analysis tables, field dictionaries, validation rules, empty headers, review views, and example rows from the shared schema and S8 formula.
---

# Web-Novel Chapter Analysis Template

Read `references/prompt.md`.

Requirements:

- Keep one chapter per row.
- Preserve universal core fields.
- Add genre-specific fields only as extensions.
- Define type, required status, allowed values, empty rules, and examples.
- Include evidence, confidence, and review fields.
```

---

# Q0 质量审计 Skill

## 1. Skill 名称与一句话功能

**名称：** Q0 质量审计器
**功能：** 自动寻找格式错误、证据不足、跨Skill冲突、异常评分和疑似幻觉，并生成最小人工复核队列。

## 2. 调用时机

- 每批 S6后运行。
- 每卷结束运行一次。
- S8之前运行全局审计。
- Q0只标记问题，不静默修改原始分析。

## 3. 输入格式

```yaml
audit_scope: 【batch/volume/book】
task_manifest: 【O0】
chapter_index: 【S0】
master_table: 【S6】
payoff_events: 【S4】
relationship_events: 【S3】
source_chapters: 【仅需复核范围原文】
previous_audit: 【上一轮审计结果】
```

## 4. 核心 Prompt 模板

```text
你是“网文拆解数据质量审计器”。

你不负责重新分析整本书，而是寻找高风险错误，并把人工工作压缩到最少。

【审计范围】
【batch/volume/book】

【任务信息】
【task_manifest】

【章节索引】
【chapter_index】

【中央数据表】
【master_table】

【爽点事件】
【payoff_events】

【关系事件】
【relationship_events】

【原文】
【source_chapters】

【上一轮审计】
【previous_audit】

【审计维度】

A. 完整性
- S0章节是否全部进入中央表。
- 必填字段是否缺失。
- 是否有重复主键或跳号。

B. Schema
- 数值范围是否正确。
- 枚举值是否合规。
- 空值是否被错误填0。
- 日期、ID和版本格式是否一致。

C. 证据
- 高强度结论是否有原文证据。
- 证据是否真的支持结论。
- 是否出现原文没有的角色、事件、动机和结果。

D. 跨Skill一致性
- S2低释放但S4高爽点。
- S1无明显钩子但S5断章强度极高。
- S3角色未出现却记录关系变化。
- S1悬念已关闭但S5仍视为核心信息差。

E. 跨章节和跨批次一致性
- 角色状态倒退且没有剧情原因。
- 已关闭悬念重新变为未解决。
- 同一爽点的setup_start变化。
- 卷和故事单元出现重叠或断裂。

F. 评分异常
- 大量章节集中在同一分数。
- 9-10分过多。
- 相邻章节巨幅跳变而无事件证据。
- 长期无爽点却未标为有意压抑段。

G. 商业风险
- 强钩子长期不兑现。
- 连续使用同一断章方式。
- 频繁爽前卡。
- 付费点前没有交付价值。

【严重度】
P0 阻塞：
主键、章节缺失、越界、明显幻觉、关键字段直接冲突。

P1 必须人工复核：
极值评分、卷边界、主要爽点、角色反转、高付费适合度、
高强度钩子、证据较弱的核心结论。

P2 抽样复核：
一般一致性问题、重复度风险、措辞或分类边界问题。

【规则】
1. 仅依据原文和已有输出。
2. 不静默修改任何字段。
3. 可以给出建议值，但必须放在suggested_resolution中。
4. 每个问题必须指出记录、字段、证据和影响。
5. 相同根因的问题应合并，避免生成几十条重复报告。
6. 输出最小人工复核集合，优先选能同时验证多个问题的章节。
7. 如果没有发现问题，明确输出“未发现阻塞项”，但不能声称分析绝对正确。

【输出JSON】
{
  "task_id": "",
  "skill_id": "Q0",
  "audit_scope": "",
  "audit_summary": {
    "records_checked": 0,
    "p0_count": 0,
    "p1_count": 0,
    "p2_count": 0,
    "overall_status": "PASS/PASS_WITH_REVIEW/BLOCKED"
  },
  "issues": [
    {
      "issue_id": "",
      "severity": "P0/P1/P2",
      "category": "",
      "chapter_ids": [],
      "fields": [],
      "problem": "",
      "evidence": "",
      "impact": "",
      "suggested_resolution": "",
      "auto_fix_allowed": false
    }
  ],
  "minimal_review_queue": [
    {
      "chapter_id": "",
      "reason": [],
      "questions_for_reviewer": []
    }
  ],
  "distribution_checks": {},
  "cross_skill_checks": {},
  "cross_batch_checks": {},
  "unresolved_items": [],
  "next_action": ""
}
```

## 5. 输出 Schema

问题示例：

```json
{
  "issue_id": "AUD-P1-003",
  "severity": "P1",
  "category": "跨Skill评分冲突",
  "chapter_ids": ["BK001-CH0018"],
  "fields": ["release_score", "payoff_strength"],
  "problem": "S2释放分为2，但S4爽点强度为9",
  "evidence": "本章主要是主角发现线索，尚未产生公开结果",
  "impact": "会抬高热力图峰值并扭曲爽点间隔统计",
  "suggested_resolution": "复核该事件是爽点兑现还是爽点承诺",
  "auto_fix_allowed": false
}
```

最小复核队列示例：

```json
{
  "chapter_id": "BK001-CH0018",
  "reason": ["评分冲突", "主要爽点候选", "付费点候选"],
  "questions_for_reviewer": [
    "本章是否已经兑现明确结果",
    "读者获得的是满足还是期待",
    "下一章是否立即给出结果"
  ]
}
```

## 6. 质量校验规则

- Q0是否越权改写原始结论。
- 每个问题是否能定位到章节和字段。
- 是否生成大量无意义低风险问题。
- P0/P1/P2是否符合严重度。
- 审计是否检查跨Skill矛盾，而不只是格式。
- 最小复核队列是否覆盖多个风险。
- 是否把“可能有误”说成“确定错误”。
- 没问题时是否仍保留有限性说明。

## 7. 下游交接

- P0问题 → 返回对应Skill重新运行。
- P1队列 → 人工抽检。
- 已确认修订 → S6更新中央表。
- 全局审计摘要 → S8判断配方可信度。
- 审计结果 → 项目归档。

## 8. Claude Skill 写法

```markdown
---
name: webnovel-analysis-quality-audit
description: Audit S0-S9 web-novel analysis for schema errors, missing chapters, weak evidence, hallucinations, cross-skill conflicts, score anomalies, unresolved hooks, and minimal human-review selection.
---

# Web-Novel Analysis Quality Audit

Read `references/prompt.md`.

Requirements:

- Never silently modify source records.
- Classify issues as P0, P1, or P2.
- Cite chapter IDs, fields, evidence, and impact.
- Merge issues with the same root cause.
- Produce the smallest useful human-review queue.
- Do not claim absolute correctness when no issue is found.
```

---

# 共享枚举规范

建议保存为 `schemas/enums.yaml`。

```yaml
confidence:
  - 确定
  - 推断
  - 存疑

chapter_position:
  - 开篇
  - 铺垫
  - 升级
  - 高潮
  - 收束
  - 过渡

chapter_function:
  - 建立困境
  - 提出目标
  - 引入角色
  - 展示能力
  - 积累资源
  - 制造误解
  - 升级冲突
  - 设置任务
  - 调查取证
  - 关系推进
  - 揭露信息
  - 兑现承诺
  - 阶段高潮
  - 制造新危机
  - 后果结算
  - 过渡换场
  - 世界观展开
  - 其他

ending_hook_type:
  - 危机
  - 悬念
  - 反转
  - 承诺
  - 信息差
  - 身份秘密
  - 目标未完成
  - 收益预告
  - 关系未决
  - 倒计时
  - 敌人登场
  - 无明显钩子

dominant_emotion:
  - 憋屈
  - 焦虑
  - 紧张
  - 恐惧
  - 好奇
  - 期待
  - 痛快
  - 震惊
  - 感动
  - 安全
  - 希望
  - 失落
  - 平静
  - 其他

payoff_type:
  - 打脸反转
  - 反杀制敌
  - 智识碾压
  - 能力展示
  - 身份揭露
  - 利益获得
  - 资源升级
  - 权力提升
  - 情感认可
  - 正义补偿
  - 秘密揭晓
  - 稀缺获得
  - 群体震惊
  - 危机解除
  - 承诺兑现
  - 其他

release_mode:
  - 即时释放
  - 短延迟释放
  - 中延迟释放
  - 长延迟释放
  - 部分释放
  - 反向释放
  - 连锁释放

reader_reward:
  - 掌控感
  - 优越感
  - 正义补偿
  - 安全感
  - 希望感
  - 归属感
  - 认可感
  - 复仇满足
  - 财富想象
  - 权力想象
  - 知识满足
  - 情感慰藉
  - 其他

payoff_novelty:
  - 新颖
  - 变体
  - 重复
  - 过度重复

paywall_suitability:
  - 低
  - 中
  - 高

hook_fairness:
  - 公平
  - 边缘
  - 欺骗风险

manual_review_status:
  - 未复核
  - 已确认
  - 已修订
  - 保留存疑

audit_severity:
  - P0
  - P1
  - P2

payoff_nature:
  - commercial
  - literary
  - reverse

character_narrative_function:
  - 主角行动发动机
  - 核心对手
  - 阶段对手
  - 资源提供者
  - 信息提供者
  - 能力导师
  - 情感支点
  - 价值观镜像
  - 见证者
  - 喜剧调节
  - 危机制造者
  - 任务发布者
  - 世界观入口
  - 奖励确认者
  - 其他

relationship_type:
  - 亲属
  - 伴侣
  - 朋友
  - 师徒
  - 同事
  - 上下级
  - 交易
  - 合作
  - 竞争
  - 敌对
  - 控制
  - 利用
  - 债务
  - 秘密关联
  - 单向崇拜
  - 单向警惕
  - 未知

cliffhanger_type:
  - 危机迫近
  - 行动即将发生
  - 身份将揭露
  - 结果未公布
  - 反转刚发生
  - 新敌人登场
  - 收益即将兑现
  - 关系即将表态
  - 信息差扩大
  - 倒计时
  - 场景硬切
  - 自然收束
  - 无明显钩子

purchase_motivation:
  - 看结果
  - 看反击
  - 看他人反应
  - 看身份揭露
  - 看收益
  - 看真相
  - 看关系进展
  - 看危机解决
  - 看新地图
  - 看能力升级
  - 其他

break_phase:
  - 爽前
  - 爽中
  - 爽后
  - 自然收束

suppression_level:
  - 0
  - 1
  - 2
  - 3
  - 4

publicness:
  - 私下
  - 小范围
  - 公开
  - 全局

irreversibility:
  - 低
  - 中
  - 高

expected_resolution_distance:
  - 下一章
  - 1-3章
  - 4章以上
  - 存疑

plot_progress_type:
  - 新事件
  - 旧事件升级
  - 揭密
  - 关系变化
  - 资源变化

story_unit_status:
  - 候选
  - 确认
  - 存疑

volume_status:
  - 候选
  - 确认
  - 存疑

execution_mode:
  - incremental
  - consolidation
  - calibration
```

---

# 推荐目录结构

```text
webnovel-analysis-skills/
├─ skills/
│  ├─ O0-orchestrator/
│  │  ├─ SKILL.md
│  │  └─ references/prompt.md
│  ├─ S0-text-preprocess/
│  ├─ S1-narrative-structure/
│  ├─ S2-emotion-rhythm/
│  ├─ S3-character-network/
│  ├─ S4-payoff-engineering/
│  ├─ S5-commercial-hooks/
│  ├─ S6-data-aggregation/
│  ├─ S7-visualization/
│  ├─ S8-genre-formula/
│  ├─ S9-chapter-template/
│  └─ Q0-quality-audit/
├─ schemas/
│  ├─ chapter-analysis-schema.md
│  ├─ output-envelope.schema.json
│  └─ enums.yaml
├─ templates/
│  ├─ task-manifest.yaml
│  ├─ batch-context-pack.yaml
│  └─ chapter-analysis-master.csv
└─ projects/
   └─ 【book_id】/
      ├─ source/
      ├─ batches/
      ├─ outputs/
      ├─ reviews/
      └─ final/
```

# 最小运行顺序

```text
O0
 ↓
S0
 ↓
S1 ─┐
S2 ─┼─ 可并行
S3 ─┤
S4 ─┘
 ↓
S5
 ↓
S6
 ↓
Q0
 ↓
人工只复核P0/P1与20%抽样
 ↓
S7
 ↓
全书S1 consolidation
 ↓
全局S6 + Q0
 ↓
S8
 ↓
S9
```

# 每批完成条件

一批章节只有同时满足以下条件，才可以进入下一批：

```yaml
batch_acceptance:
  s0_chapters_complete: true
  s1_completed: true
  s2_completed: true
  s3_completed: true
  s4_completed: true
  s5_completed: true
  s6_merged: true
  q0_p0_count: 0
  previous_batch_summary_generated: true
  character_states_updated: true
  open_loops_updated: true
  recent_payoffs_updated: true
```

# 全书完成条件

```yaml
book_acceptance:
  all_chapters_in_master_table: true
  volume_structure_consolidated: true
  unresolved_p0_issues: 0
  required_manual_reviews_completed: true
  reverse_outline_generated: true
  heatmap_generated: true
  genre_formula_generated: true
  chapter_template_generated: true
  all_major_conclusions_traceable: true
```
