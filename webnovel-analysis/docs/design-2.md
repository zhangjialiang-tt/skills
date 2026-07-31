# 爆款网文拆解 Skill 库

## 第二阶段上：O0、S0—S4 标准化定义

# 0. 全库通用执行契约

## 0.1 通用输入信封

除 S0 外，所有分析 Skill 默认接收：

```yaml
task_manifest:
  task_id: 【任务编号】
  book_id: 【书籍编号】
  book_title: 【书名】
  genre: 【题材】
  source_type: 【合法取得的文本/虚构案例/自有作品】
  analysis_version: 【v1.0】

execution:
  mode: 【incremental/consolidation】
  batch_id: 【BATCH-01】
  chapter_range: 【1-10】
  allowed_write_fields: 【本Skill允许写入的字段】

context:
  previous_batch_summary: 【上一批摘要；首批填“无，这是第一批”】
  confirmed_facts: 【已确认事实】
  character_states: 【角色状态】
  open_loops: 【未关闭悬念】
  recent_major_payoffs: 【最近主要爽点】
  existing_records: 【中央数据表已有字段】

chapters:
  - chapter_id: 【BK001-CH0001】
    chapter_no: 【1】
    chapter_title: 【章节名】
    text: |
      【完整章节文本】
```

## 0.2 通用输出信封

```json
{
  "task_id": "【任务编号】",
  "skill_id": "【Skill编号】",
  "skill_version": "1.0",
  "mode": "incremental",
  "batch_id": "【批次编号】",
  "records": [],
  "batch_summary": {},
  "uncertain_items": [],
  "conflicts": [],
  "manual_review_items": []
}
```

## 0.3 通用防幻觉规则

所有 Prompt 均默认遵循：

1. 仅依据用户提供的文本和结构化数据分析。
2. 不调用对真实作品、作者或平台数据的外部记忆。
3. 原文没有明确支持的结论标记为“推断”或“存疑”。
4. 不得把未出现的角色动机、伏笔、卷规划写成确定事实。
5. 每个重要判断必须附带证据摘要及位置。
6. 没有爽点、钩子或关系变化时，必须填写“无”，不得强行制造。
7. 不修改其他 Skill 已有字段；发现问题写入 `conflicts`。
8. 输出必须满足 Schema，不用散文替代结构化结果。

---

# O0 拆解任务编排 Skill

## 1. Skill 名称与一句话功能

**名称：** O0 拆解任务编排器
**功能：** 将一本待拆解小说转化为可执行的批次计划、Skill 调用图、文件清单与验收标准。

## 2. 调用时机

- 工作流第一个模块。
- 在 S0 之前调用。
- 新建拆解任务、恢复中断任务、改变批次大小或重新分析局部章节时调用。
- 前置条件：至少知道文本规模、章节数量或原始文件情况。

## 3. 输入格式

```yaml
project_request:
  book_title: 【书名】
  genre: 【题材；未知可填存疑】
  purpose: 【竞品拆解/自有作品复盘/结构研究】
  source_files:
    - file_name: 【文件名】
      format: 【txt/md/docx/其他】
      estimated_chapters: 【数量或未知】
  desired_outputs:
    - 【全书逆向大纲】
    - 【情绪-爽点热力图】
    - 【题材套路公式】
    - 【章节分析模板】
  preferred_batch_size: 【默认10】
  available_tools: 【Claude/ChatGPT/Excel/Python等】
  constraints: 【时间、上下文窗口、人工抽检比例】
```

## 4. 核心 Prompt 模板

```text
你是“爆款网文拆解工作流编排器”。

你的任务不是分析小说内容，而是将拆解任务转化为一份可执行、可恢复、可审计的运行计划。

【输入】
项目需求：
【粘贴 project_request】

【工作流模块】
O0 编排
S0 文本预处理
S1 叙事结构拆解
S2 情绪节奏打分
S3 人物关系网
S4 爽点工程
S5 商业卡点
S6 数据聚合
S7 可视化
S8 套路公式提炼
S9 章节模板生成
Q0 质量审计

【强制规则】
1. 仅依据输入规划，不假设不存在的章节数量、卷结构或文本质量。
2. 不确定的信息标记为“存疑”。
3. 默认每批10章，但若单章超过5000字，建议每批5章；若一个完整事件跨越批次边界，应优先保持事件完整。
4. S1、S2、S3、S4可在S0后并行；S5至少读取S1、S2、S4结果；S6在S1-S5后运行。
5. 每批完成后必须运行Q0；全书完成后再运行一次全局Q0。
6. 不设计复杂数据库。默认使用Markdown、CSV/XLSX；仅在规模明显需要时建议Python。
7. 给每个输出文件确定唯一文件名。
8. 计划必须支持失败后从最近完成批次恢复。

【执行步骤】
A. 建立task_id、book_id和版本号。
B. 评估输入文件是否需要合并、清洗、OCR或章节识别。
C. 规划批次，但不虚构具体章节边界。
D. 建立Skill依赖图。
E. 建立每批输入、输出和人工抽检点。
F. 给出运行状态清单。
G. 给出四项最终交付物的验收条件。

【输出】
严格按以下JSON返回：
{
  "task_manifest": {
    "task_id": "",
    "book_id": "",
    "book_title": "",
    "genre": "",
    "analysis_version": "v1.0",
    "default_batch_size": 10,
    "manual_sampling_rate": 0.2
  },
  "source_plan": [],
  "batching_policy": {
    "default_rule": "",
    "boundary_rules": [],
    "estimated_batches": "存疑"
  },
  "execution_graph": [],
  "file_manifest": [],
  "checkpoint_policy": {},
  "manual_review_policy": {},
  "deliverable_acceptance": [],
  "uncertain_items": [],
  "next_action": ""
}
```

## 5. 输出 Schema

| 字段                     | 定义                     |
| ------------------------ | ------------------------ |
| `task_manifest`          | 任务身份、版本和默认参数 |
| `source_plan`            | 原始文件的处理方式       |
| `batching_policy`        | 批次规模与边界规则       |
| `execution_graph`        | Skill调用顺序和依赖      |
| `file_manifest`          | 输入、过程、结果文件     |
| `checkpoint_policy`      | 中断恢复规则             |
| `manual_review_policy`   | 人工抽检范围             |
| `deliverable_acceptance` | 四项交付物验收标准       |

示例：

```json
{
  "task_manifest": {
    "task_id": "BK20260731-001",
    "book_id": "BK001",
    "book_title": "重生后我接管旧厂",
    "genre": "都市重生逆袭",
    "analysis_version": "v1.0",
    "default_batch_size": 10,
    "manual_sampling_rate": 0.2
  },
  "next_action": "调用S0处理原始文本"
}
```

## 6. 质量校验规则

抽检时确认：

- 是否遗漏用户要求的最终交付物。
- 是否把 S5 放在 S1/S2/S4 之前。
- 是否有批次检查点和失败恢复方式。
- 是否机械地每10章切分，而未保留事件完整性规则。
- 是否要求人工逐章审核，违背80%自动化目标。
- 是否出现不存在的章节数或卷数。

## 7. 下游交接

O0 输出：

- `task_manifest.yaml` → 所有 Skill。
- `execution-plan.yaml` → 调用器或人工操作清单。
- `file-manifest.yaml` → S0。
- `review-policy.yaml` → Q0。

## 8. Claude Skill 写法

目录：

```text
O0-orchestrator/
├─ SKILL.md
└─ references/
   └─ prompt.md
```

`SKILL.md`：

```markdown
---
name: webnovel-analysis-orchestrator
description: Create an executable batch plan for a web-novel analysis project. Use when starting, resuming, repartitioning, or validating an S0-S9 novel-analysis workflow.
---

# Web-Novel Analysis Orchestrator

Read `references/prompt.md` and execute it.

Rules:

- Do not analyze the literary content.
- Produce task IDs, batch policy, dependencies, checkpoints, file names, and acceptance criteria.
- Preserve complete story units when defining batch boundaries.
- Mark unavailable facts as `存疑`.
- Return only the required structured output.
```

非 Skill 平台：直接复制本节“核心 Prompt 模板”。

---

# S0 文本预处理 Skill

## 1. Skill 名称与一句话功能

**名称：** S0 文本预处理
**功能：** 将格式混乱的小说文本清洗、切章、编号并打包为稳定的分析批次。

## 2. 调用时机

- O0 之后。
- S1—S5 之前。
- 原始文本新增、章节顺序变化、章节识别失败或批次重划时重新调用。

## 3. 输入格式

支持：

- TXT、Markdown或复制粘贴文本。
- 单文件全书、多文件分章。
- 输入时提供 O0 的 `task_manifest` 和预期批次策略。

```yaml
task_manifest: 【O0输出】
source:
  file_name: 【novel.txt】
  encoding: 【UTF-8/未知】
  raw_text: |
    【原始文本】
chapter_detection:
  known_pattern: 【如“第X章”或未知】
  preserve_author_notes: 【false】
batching:
  default_size: 【10】
  max_characters_per_batch: 【可选】
```

## 4. 核心 Prompt 模板

```text
你是“网文文本预处理器”。你只处理文本结构，不分析情节质量。

【任务信息】
【粘贴task_manifest】

【原始文本】
【粘贴原始文本】

【章节识别提示】
已知章节标题模式：【填写；未知则填“未知”】
默认批次大小：【10】
是否保留作者感言、广告和求票信息：【是/否】

【处理目标】
1. 识别章节边界。
2. 删除与正文分析无关的重复站点信息、广告、乱码和无意义空行。
3. 不删除正文、对话、场景分隔符、时间跳转或作者有意设置的符号。
4. 为每章生成稳定chapter_id。
5. 统计清洗前后字数。
6. 检查缺章、重章、标题跳号、异常短章和异常长章。
7. 按故事单元完整性优先、章节数量其次进行批次建议。
8. 输出标准章节文本、章节索引和批次清单。

【防幻觉规则】
- 仅依据所给文本。
- 无法确认章节边界时标记“存疑”，不得自行补标题。
- 不重写、概括、润色正文。
- 不修复看似不合理的情节。
- 疑似乱码必须保留原片段到issues中，不能无声删除。
- 章节编号缺失时可生成内部编号，但要保留原始标题。

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

【输出】
返回：
A. preprocessing_report
B. chapter_index
C. batch_manifest
D. issues
E. 标准化章节文本

严格输出JSON元数据，正文放入standardized_chapters：
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
  "chapter_index": [],
  "batch_manifest": [],
  "issues": [],
  "standardized_chapters": []
}
```

## 5. 输出 Schema

### `chapter_index`

| 字段                  | 定义         |
| --------------------- | ------------ |
| `chapter_id`          | 稳定章节编号 |
| `chapter_no`          | 分析顺序     |
| `original_title`      | 原始标题     |
| `normalized_title`    | 标准标题     |
| `word_count`          | 正文字数     |
| `boundary_confidence` | 边界置信度   |
| `source_location`     | 原文件位置   |
| `issue_flags`         | 异常标记     |

示例：

```json
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
```

### `batch_manifest`

```json
{
  "batch_id": "BATCH-01",
  "chapter_ids": ["BK001-CH0001", "BK001-CH0002"],
  "reason": "连续开篇事件单元",
  "estimated_characters": 4620,
  "boundary_confidence": "推断"
}
```

## 6. 质量校验规则

- 章节总数是否与明显标题数量大致一致。
- 开头、结尾和随机一章是否丢正文。
- 广告删除是否误删角色对话。
- 是否存在同一段落重复出现在两个章节。
- `chapter_id` 是否唯一且稳定。
- 批次是否拆开同一冲突的压抑和兑现。
- “存疑边界”是否进入人工复核清单。

## 7. 下游交接

输出：

- `standardized_chapters.md` → S1—S5。
- `chapter_index.csv` → S1—S7。
- `batch_manifest.yaml` → O0和各分析 Skill。
- `preprocessing_issues.csv` → Q0。

## 8. Claude Skill 写法

```markdown
---
name: webnovel-text-preprocessor
description: Clean, split, index, and batch raw web-novel text without interpreting the story. Use when novel text must be normalized before structural, emotional, character, payoff, or commercial analysis.
---

# Web-Novel Text Preprocessor

Read `references/prompt.md`.

Required behavior:

- Preserve all正文 content.
- Never rewrite or summarize chapters.
- Assign stable chapter IDs.
- Flag uncertain boundaries, missing chapters, duplicates, garbled text, and abnormal chapter lengths.
- Produce chapter index, batch manifest, issues, and standardized text.
```

---

# S1 叙事结构拆解 Skill

## 1. Skill 名称与一句话功能

**名称：** S1 叙事结构拆解
**功能：** 将章节还原为“事件—单元—卷”三级结构，识别每章功能、因果链、开放悬念和结构钩子。

## 2. 调用时机

- S0 后。
- 可与 S2、S3、S4 并行。
- 两种模式：
  - `incremental`：逐批分析章节。
  - `consolidation`：全书批次完成后，统一确认卷和故事单元。

## 3. 输入格式

```yaml
mode: 【incremental/consolidation】
task_manifest: 【O0输出】
chapter_index: 【S0输出】
chapters: 【当前批次正文】
previous_batch_summary: 【前批结构摘要】
open_loops: 【累计开放悬念】
existing_structure_records: 【已有S1结果】
```

## 4. 核心 Prompt 模板

```text
你是“网文叙事结构分析师”。你的任务是逆向恢复作品的结构设计，而不是评价文笔。

【运行模式】
【incremental 或 consolidation】

【任务信息】
【task_manifest】

【已有上下文】
上一批摘要：
【previous_batch_summary】

累计开放悬念：
【open_loops】

已有结构记录：
【existing_structure_records】

【本次章节】
【chapters】

【核心定义】
- 章节功能：本章对整体叙事承担的首要作用。
- 故事单元：围绕一个局部目标、阻力和结果形成的连续章节集合。
- 卷功能：一卷在主角长期变化和商业阅读体验中的主要任务。
- 开放悬念：文本提出但尚未回答的问题或承诺。
- 钩子：促使读者继续阅读的具体未完成刺激。
- 事件不等于结构功能；同一事件可能承担“建立困境”“展示能力”等不同功能。

【章节功能枚举】
建立困境、提出目标、引入角色、展示能力、积累资源、制造误解、
升级冲突、设置任务、调查取证、关系推进、揭露信息、兑现承诺、
阶段高潮、制造新危机、后果结算、过渡换场、世界观展开、其他。

【钩子类型】
危机、悬念、反转、承诺、信息差、身份秘密、目标未完成、
收益预告、关系未决、倒计时、敌人登场、无明显钩子。

【分析步骤】
1. 用一句话概括每章主事件。
2. 识别该事件从前文何处产生，又对后文产生什么影响。
3. 为每章选择一个主功能，最多两个次功能。
4. 记录本章新增和关闭的开放悬念。
5. 分别识别开头、中段、结尾钩子；不存在时填“无”。
6. 判断当前章节是否形成完整故事单元。
7. incremental模式只提交卷候选，不得过早确认全书卷结构。
8. consolidation模式根据全部章节重新划分故事单元和卷，并说明边界证据。
9. 发现前批错误时，不直接覆盖，在conflicts中提出修订建议。
10. 所有关键结论附证据摘要和位置。

【防幻觉】
- 仅依据所给文本。
- 作者没有明示的卷名，可生成“分析用卷名”，但标记为“推断命名”。
- 未来剧情不能凭套路预测为事实。
- 伏笔只有在后文获得回收证据后才能确认；此前称“疑似伏笔”。
- 无法判断时标“存疑”。

【输出JSON】
{
  "task_id": "",
  "skill_id": "S1",
  "mode": "",
  "batch_id": "",
  "records": [
    {
      "chapter_id": "",
      "main_event": "",
      "chapter_function": "",
      "secondary_functions": [],
      "cause_from_previous": "",
      "effect_on_next": "",
      "plot_progress_type": "",
      "chapter_goal": "",
      "chapter_result": "",
      "open_loop_added": [],
      "open_loop_closed": [],
      "opening_hook": "",
      "mid_hook": "",
      "ending_hook": "",
      "ending_hook_type": "",
      "story_unit_id": "",
      "story_unit_status": "候选/确认/存疑",
      "volume_id": "",
      "volume_status": "候选/确认/存疑",
      "core_evidence": [],
      "evidence_location": [],
      "analysis_confidence": "确定/推断/存疑"
    }
  ],
  "story_unit_updates": [],
  "volume_updates": [],
  "batch_summary": {},
  "uncertain_items": [],
  "conflicts": [],
  "manual_review_items": []
}
```

## 5. 输出 Schema

### 章节记录

| 字段                  | 定义             |
| --------------------- | ---------------- |
| `main_event`          | 本章最主要事件   |
| `chapter_function`    | 首要结构功能     |
| `cause_from_previous` | 前因             |
| `effect_on_next`      | 后果或推进       |
| `open_loop_added`     | 新开放问题       |
| `open_loop_closed`    | 已回答问题       |
| `ending_hook`         | 章末未完成刺激   |
| `story_unit_id`       | 所属局部事件单元 |
| `volume_id`           | 所属分析卷       |

示例：

```json
{
  "chapter_id": "BK001-CH0001",
  "main_event": "林川重生后保住异常采购账本",
  "chapter_function": "建立困境",
  "secondary_functions": ["展示信息优势"],
  "open_loop_added": ["谁伪造了账本"],
  "open_loop_closed": [],
  "ending_hook": "厂长要求他立即交出原账本",
  "ending_hook_type": "危机",
  "story_unit_id": "U01",
  "story_unit_status": "候选",
  "analysis_confidence": "确定"
}
```

### 卷级记录

```json
{
  "volume_id": "V01",
  "analysis_name": "绝境翻盘",
  "name_type": "推断命名",
  "chapter_range": "1-38",
  "volume_function": "让主角从被开除危机转为获得立足资源",
  "opening_state": "被动受害",
  "closing_state": "取得旧厂控制权",
  "central_conflict": "主角与厂内利益链的对抗",
  "boundary_evidence": [],
  "confidence": "推断"
}
```

## 6. 质量校验规则

- 主事件是否只是章节摘要，而非虚构主题。
- 每章是否被强行赋予多个主功能。
- 单元边界是否有“目标建立—阻碍—结果”证据。
- 是否在只读10章时断言全书共有几卷。
- `open_loop_closed` 是否真的在文本中回答。
- 章末钩子是否具体，而不是“让人想看下去”。
- 卷首状态与卷末状态是否形成可验证变化。

## 7. 下游交接

- 章节结构字段 → S5、S6。
- `story_unit_updates` → S4统计单元爽点分布。
- `volume_updates` → S6生成全书逆向大纲。
- 开放悬念 → 下一批 S1、S5。
- 章节功能 → S8提炼题材结构公式。

## 8. Claude Skill 写法

```markdown
---
name: webnovel-narrative-structure
description: Reverse-engineer chapter, story-unit, and volume structure from supplied web-novel text. Use when identifying chapter functions, causal chains, open loops, structural hooks, unit boundaries, or volume functions.
---

# Web-Novel Narrative Structure

Read `references/prompt.md`.

Requirements:

- Support incremental and consolidation modes.
- Do not confirm full-book volume structure from a partial batch.
- Separate explicit facts, inference, and uncertainty.
- Attach evidence to hooks, functions, unit boundaries, and volume boundaries.
- Return chapter records plus story-unit and volume updates.
```

---

# S2 情绪节奏打分 Skill

## 1. Skill 名称与一句话功能

**名称：** S2 情绪节奏打分
**功能：** 把每章的压抑、释放和章末情绪状态量化为可跨章节比较的1—10分数据。

## 2. 调用时机

- S0 后。
- 可与 S1、S3、S4 并行。
- 批次分析时必须读取相邻章节，避免孤立评分。
- 全书完成后可再次运行 `calibration` 模式校准评分分布。

## 3. 输入格式

```yaml
mode: 【incremental/calibration】
chapters: 【当前批次，建议含前后各1章摘要】
previous_scores: 【前批末3章评分】
genre_context: 【题材，仅用于理解读者情绪，不用于套结论】
known_turning_points: 【S1已有信息，可选】
```

## 4. 评分锚点

`emotion_score` 表示读者在章节结束时获得的综合情绪满足度，不表示文学质量。

| 分数 | 锚点                                           |
| ---: | ---------------------------------------------- |
|    1 | 极强压抑或毁灭性失败，几乎无希望、补偿或掌控感 |
|    2 | 严重受挫、羞辱或损失，读者明显憋屈             |
|    3 | 显著压抑，虽有行动空间但未形成有效反制         |
|    4 | 轻度受阻、焦虑或铺垫，负面略占优势             |
|    5 | 中性过渡，正负大致平衡，无明显奖励或打击       |
|    6 | 轻微正反馈，小进展、小认可、小期待兑现         |
|    7 | 清晰爽感或情绪满足，主要目标取得阶段性成果     |
|    8 | 强烈释放，重要反击、收益或关系兑现             |
|    9 | 高潮级释放，长期积累得到高强度回报             |
|   10 | 全书罕见峰值，多条积累同时兑现并改变长期局势   |

附加评分：

- `pressure_score`：本章读者承受的压迫强度，1—10。
- `release_score`：本章对既有压抑的释放程度，0—10。
- `emotion_volatility`：章内高低差，0—9。

## 5. 核心 Prompt 模板

```text
你是“网文章节情绪节奏评分器”。

你要评估的是目标读者的情绪体验，不是文学质量、思想深度或个人喜好。

【题材】
【genre_context】

【前批评分】
【previous_scores】

【章节文本】
【chapters】

【评分体系】
emotion_score：
1 极强压抑且几乎无希望；
2 严重受挫或羞辱；
3 显著压抑但仍有行动空间；
4 轻度受阻，负面略占优势；
5 中性过渡；
6 小幅正反馈；
7 清晰的阶段性满足；
8 强烈释放；
9 高潮级兑现；
10 全书罕见峰值，多线积累同时兑现。

pressure_score：
1 几乎无压力，10 极端压力或重大不可逆威胁。

release_score：
0 无释放，10 对长期重大压抑完成充分兑现。

【分析步骤】
1. 确定章节开头、最低点、最高点和结尾的情绪状态。
2. 分别给emotion_start、emotion_low、emotion_high、emotion_end打1-10分。
3. 给整章emotion_score、pressure_score、release_score评分。
4. 输出emotion_curve，例如“平→压→识破→小释放→新危机”。
5. 标出主导情绪和关键转折点。
6. 与相邻章节比较，避免全批次普遍给7-8分。
7. 10分必须是全书罕见峰值；只分析局部批次时原则上不得轻易给10。
8. 若本章同时“过程很爽但结尾陷入危机”，应分别记录高点和结尾，不用一个分数抹平。
9. 为高点、低点和最终评分分别提供证据。
10. 无法判断目标读者感受时标记“存疑”。

【防幻觉】
- 仅依据所给文本。
- 不因出现争吵就自动判为高压。
- 不因主角赢了一次对话就自动判为高爽。
- 角色高兴不等于读者爽；必须说明读者得到何种情绪回报。
- 不得用后续未知剧情反向合理化当前评分。

【输出JSON】
{
  "task_id": "",
  "skill_id": "S2",
  "mode": "",
  "batch_id": "",
  "records": [
    {
      "chapter_id": "",
      "emotion_start": 0,
      "emotion_low": 0,
      "emotion_high": 0,
      "emotion_end": 0,
      "emotion_score": 0,
      "pressure_score": 0,
      "release_score": 0,
      "emotion_volatility": 0,
      "emotion_curve": "",
      "dominant_emotion": "",
      "emotion_turning_point": "",
      "reader_reward": [],
      "low_point_evidence": "",
      "high_point_evidence": "",
      "final_score_reason": "",
      "analysis_confidence": "确定/推断/存疑"
    }
  ],
  "batch_statistics": {
    "mean_emotion_score": 0,
    "mean_pressure_score": 0,
    "mean_release_score": 0,
    "highest_chapter": "",
    "lowest_chapter": "",
    "flat_rhythm_warning": false
  },
  "batch_summary": {},
  "uncertain_items": [],
  "conflicts": [],
  "manual_review_items": []
}
```

## 6. 输出 Schema

示例：

```json
{
  "chapter_id": "BK001-CH0001",
  "emotion_start": 3,
  "emotion_low": 2,
  "emotion_high": 7,
  "emotion_end": 5,
  "emotion_score": 5,
  "pressure_score": 7,
  "release_score": 4,
  "emotion_volatility": 5,
  "emotion_curve": "低压→识破→小反制→新危机",
  "dominant_emotion": "期待",
  "emotion_turning_point": "林川发现账本重复入账",
  "reader_reward": ["掌控感"],
  "analysis_confidence": "确定"
}
```

## 7. 质量校验规则

- 是否把“故事写得好”当成情绪高分。
- 相邻章节分差是否有文本依据。
- 全书是否大量集中在7—9分，失去区分度。
- 9—10分是否真的有长期积累和格局变化。
- 高压章节是否也可能存在高释放，两个维度不能互相替代。
- `emotion_end` 是否符合断章时的实际状态。
- 转折点能否在原文中定位。

推荐异常规则：

```text
emotion_high - emotion_low >= 7：人工检查是否夸大
emotion_score >= 9 且 release_score < 7：人工检查
pressure_score >= 8 且没有压力证据：人工检查
连续5章 emotion_score 波动小于1：检查节奏是否真的平坦
```

## 8. 下游交接

- 章节情绪字段 → S4判断爽点释放。
- `emotion_end` 和 `pressure_score` → S5判断追读压力。
- 批次统计 → S6。
- 全书评分 → S7热力图。
- 峰谷分布 → S8题材节奏公式。

## 9. Claude Skill 写法

```markdown
---
name: webnovel-emotion-rhythm
description: Score chapter-level emotional pressure, release, payoff, and end-state on a calibrated 1-10 scale. Use when building emotion curves, comparing adjacent chapters, detecting flat rhythm, or preparing an emotion-payoff heatmap.
---

# Web-Novel Emotion Rhythm

Read `references/prompt.md`.

Rules:

- Score reader experience, not literary quality.
- Use the published anchors consistently.
- Keep pressure and release as separate dimensions.
- Compare adjacent chapters.
- Reserve scores 9-10 for evidence-backed peaks.
- Attach evidence for lows, highs, and final scores.
```

---

# S3 人物关系网 Skill

## 1. Skill 名称与一句话功能

**名称：** S3 人物关系网
**功能：** 提取角色实体、叙事功能、目标、阵营和关系变化，形成可持续更新的人物网络。

## 2. 调用时机

- S0 后，与 S1、S2、S4并行。
- 每批更新一次。
- 全书完成后运行 `consolidation`，合并别名并确认长期关系弧。

## 3. 输入格式

```yaml
mode: 【incremental/consolidation】
chapters: 【当前批次】
existing_character_registry: 【已有角色表】
existing_relationships: 【已有关系边】
previous_character_states: 【上一批角色状态】
```

## 4. 核心 Prompt 模板

```text
你是“网文角色与关系网络分析师”。

【运行模式】
【incremental/consolidation】

【已有角色注册表】
【existing_character_registry】

【已有关系】
【existing_relationships】

【上一批角色状态】
【previous_character_states】

【本批章节】
【chapters】

【任务】
1. 识别明确出现或被明确提及的角色。
2. 合并同一角色的简称、职位称呼和全名；不确定时保留独立实体并标“疑似同一人”。
3. 记录角色当前目标、行动、资源、信息和状态变化。
4. 判断角色在本批承担的叙事功能。
5. 记录关系变化事件，而不只给静态标签。
6. 记录阵营加入、退出、背叛、合作和隐性利益关联。
7. 标记POV角色和本章活跃角色。
8. 将“角色自称”“他人评价”“文本已证实事实”分开。
9. consolidation模式合并全书别名并输出长期关系弧。
10. 为每个关系变化提供发生章节和证据。

【角色功能枚举】
主角行动发动机、核心对手、阶段对手、资源提供者、信息提供者、
能力导师、情感支点、价值观镜像、见证者、喜剧调节、危机制造者、
任务发布者、世界观入口、奖励确认者、其他。

【关系类型】
亲属、伴侣、朋友、师徒、同事、上下级、交易、合作、竞争、
敌对、控制、利用、债务、秘密关联、单向崇拜、单向警惕、未知。

【关系强度】
-3 生死敌对
-2 明确敌对
-1 警惕或冲突
0 中立或未知
1 轻度合作
2 稳定信任
3 核心同盟或亲密关系

【防幻觉】
- 仅依据给定文本。
- 同场出现不等于关系。
- 对话礼貌不等于信任。
- 反派身份、恋爱倾向、血缘或背叛只有明确证据才能确认。
- 不把读者推测写成角色已知信息。
- 无变化时填写“无关系变化”。

【输出JSON】
{
  "task_id": "",
  "skill_id": "S3",
  "mode": "",
  "batch_id": "",
  "chapter_records": [
    {
      "chapter_id": "",
      "pov_character": "",
      "active_characters": [],
      "new_characters": [],
      "character_goal": {},
      "character_action": {},
      "relationship_change": [],
      "faction_change": [],
      "core_evidence": [],
      "analysis_confidence": "确定/推断/存疑"
    }
  ],
  "character_registry_updates": [
    {
      "character_id": "",
      "canonical_name": "",
      "aliases": [],
      "first_appearance": "",
      "current_role": "",
      "narrative_functions": [],
      "current_goal": "",
      "known_information": [],
      "suspected_information": [],
      "resources": [],
      "current_status": "",
      "faction_ids": [],
      "confidence": ""
    }
  ],
  "relationship_events": [
    {
      "event_id": "",
      "chapter_id": "",
      "source_character_id": "",
      "target_character_id": "",
      "relationship_type_before": "",
      "relationship_type_after": "",
      "strength_before": 0,
      "strength_after": 0,
      "change_reason": "",
      "evidence": "",
      "confidence": ""
    }
  ],
  "faction_updates": [],
  "batch_summary": {},
  "uncertain_items": [],
  "conflicts": [],
  "manual_review_items": []
}
```

## 5. 输出 Schema

### 角色实体表示例

```json
{
  "character_id": "C001",
  "canonical_name": "林川",
  "aliases": ["小林", "林技术员"],
  "first_appearance": "BK001-CH0001",
  "current_role": "主角",
  "narrative_functions": ["主角行动发动机"],
  "current_goal": "保住账本并查清陷害者",
  "known_information": ["前世自己被赵海陷害"],
  "suspected_information": ["采购账可能牵涉厂领导"],
  "resources": ["前世记忆", "原始账本"],
  "current_status": "被调查",
  "faction_ids": [],
  "confidence": "确定"
}
```

### 关系事件表示例

```json
{
  "event_id": "REL-E001",
  "chapter_id": "BK001-CH0001",
  "source_character_id": "C001",
  "target_character_id": "C002",
  "relationship_type_before": "上下级",
  "relationship_type_after": "隐性敌对",
  "strength_before": 0,
  "strength_after": -2,
  "change_reason": "赵海试图迫使林川交出异常账本",
  "evidence": "赵海拒绝解释账目并公开威胁开除",
  "confidence": "确定"
}
```

## 6. 质量校验规则

- 是否把职位称呼误建为新角色。
- 同名角色是否错误合并。
- 是否把“推断动机”写进 `known_information`。
- 关系变化是否有事件触发，而非无缘无故改变。
- 阵营与关系是否混为一谈。
- 角色功能是否随章节证据更新，而非一次定终身。
- 主角之外是否出现大量没有作用的角色标签。

## 7. 下游交接

- `character_registry_updates` → 下一批 S3。
- 关系变化 → S1卷级人物弧、S5情感追读点。
- 阵营结构 → S8角色配方。
- 章节活跃角色 → S6中央表。
- 关系网络数据 → S7可选人物网络图。

## 8. Claude Skill 写法

```markdown
---
name: webnovel-character-network
description: Build and update character entities, aliases, goals, factions, narrative functions, and evidence-backed relationship changes from supplied web-novel chapters.
---

# Web-Novel Character Network

Read `references/prompt.md`.

Requirements:

- Maintain stable character IDs.
- Separate facts, suspicions, and other characters' claims.
- Record relationship change events rather than only static labels.
- Do not merge uncertain aliases without evidence.
- Return chapter records, character updates, relationship events, and faction updates.
```

---

# S4 爽点工程 Skill

## 1. Skill 名称与一句话功能

**名称：** S4 爽点工程
**功能：** 把“压抑积累—触发—释放—读者奖励”拆成事件级数据，并统计爽点类型、强度、间隔和重复度。

## 2. 调用时机

- S0 后，可与 S1—S3并行。
- 若已有 S2 结果，应一并输入以提高稳定性。
- S4批次结果完成后交给 S5判断商业卡点。
- 全书完成后运行 `consolidation` 统计规律。

## 3. 输入格式

```yaml
mode: 【incremental/consolidation】
chapters: 【当前批次文本】
emotion_records: 【S2结果；可为空】
story_units: 【S1结果；可为空】
previous_payoffs:
  last_major_payoff: 【最近主要爽点】
  rolling_payoff_events: 【最近5个爽点】
```

## 4. 分类和锚点

### 压抑等级

| 等级 | 定义                                           |
| ---: | ---------------------------------------------- |
|    0 | 无明显压抑，仅有普通任务或信息                 |
|    1 | 轻微不便、质疑、小阻碍                         |
|    2 | 明确受阻、利益受损、被低估                     |
|    3 | 持续羞辱、重大威胁、资源或关系危机             |
|    4 | 长期重压、不可逆损失风险、生死或核心价值被摧毁 |

### 爽点类型

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

### 释放方式

- 即时释放：同章压抑、同章兑现。
- 短延迟释放：1—3章内兑现。
- 中延迟释放：4—10章内兑现。
- 长延迟释放：超过10章或跨单元兑现。
- 部分释放：只解决部分矛盾。
- 反向释放：先给奖励，再引入更大代价。
- 连锁释放：一次行动连续兑现多个奖励。

## 5. 核心 Prompt 模板

```text
你是“网文爽点工程分析师”。

【运行模式】
【incremental/consolidation】

【前序爽点记录】
【previous_payoffs】

【S2情绪数据】
【emotion_records】

【S1故事单元】
【story_units】

【章节文本】
【chapters】

【目标】
将每个主要爽点拆成：
压抑来源 → 压抑对象 → 压抑等级 → 读者期待
→ 触发条件 → 释放动作 → 直接结果 → 读者奖励
→ 后续代价或新问题。

【判断原则】
1. “主角得到信息”不一定是爽点，除非给读者带来明确奖励。
2. “反派吃亏”不一定是强爽点，要看前置压抑和损失程度。
3. 一章可以没有爽点。
4. 同一事件可以包含多个奖励，但应指定一个主类型。
5. 爽点强度根据前置积累、兑现幅度、公开性、不可逆性和局势改变综合评分。
6. 爽点强度0表示无爽点；1-3轻微；4-6中等；7-8强；9高潮；10全书罕见峰值。
7. 爽点间隔按“主要爽点”统计，轻微正反馈不重置主要爽点计数。
8. 重复度要比较最近5次爽点：新颖、变体、重复、过度重复。
9. consolidation模式统计各卷平均间隔、类型占比和高峰位置。
10. 所有判断必须附文本证据。

【压抑等级】
0无；1轻；2中；3重；4极重。

【爽点类型】
打脸反转、反杀制敌、智识碾压、能力展示、身份揭露、利益获得、
资源升级、权力提升、情感认可、正义补偿、秘密揭晓、稀缺获得、
群体震惊、危机解除、承诺兑现、其他。

【读者奖励】
掌控感、优越感、正义补偿、安全感、希望感、归属感、认可感、
复仇满足、财富想象、权力想象、知识满足、情感慰藉、其他。

【防幻觉】
- 仅依据提供文本。
- 不因主角占上风就自动判定爽点。
- 不虚构前置压抑。
- 无法找到压抑对象或读者奖励时，降低置信度。
- 后续尚未兑现的期待只能记录为“爽点承诺”，不能记录为已兑现爽点。

【输出JSON】
{
  "task_id": "",
  "skill_id": "S4",
  "mode": "",
  "batch_id": "",
  "chapter_records": [
    {
      "chapter_id": "",
      "suppression_level": 0,
      "suppression_source": [],
      "suppression_target": [],
      "payoff_present": false,
      "primary_payoff_event_id": "",
      "payoff_type": "",
      "payoff_strength": 0,
      "payoff_interval_chapters": null,
      "payoff_novelty": "",
      "reader_reward": [],
      "unfulfilled_payoff_promises": [],
      "analysis_confidence": ""
    }
  ],
  "payoff_events": [
    {
      "payoff_event_id": "",
      "chapter_id": "",
      "setup_start_chapter": "",
      "suppression_level": 0,
      "suppression_source": "",
      "suppression_target": "",
      "reader_expectation": "",
      "payoff_trigger": "",
      "release_action": "",
      "payoff_result": "",
      "payoff_type": "",
      "release_mode": "",
      "payoff_strength": 0,
      "publicness": "私下/小范围/公开/全局",
      "irreversibility": "低/中/高",
      "reader_reward": [],
      "new_cost_or_problem": "",
      "evidence": [],
      "confidence": ""
    }
  ],
  "batch_statistics": {},
  "batch_summary": {},
  "uncertain_items": [],
  "conflicts": [],
  "manual_review_items": []
}
```

## 6. 输出 Schema

示例：

```json
{
  "payoff_event_id": "PAY-E001",
  "chapter_id": "BK001-CH0001",
  "setup_start_chapter": "BK001-CH0001",
  "suppression_level": 3,
  "suppression_source": "厂长公开指控林川弄丢采购账本",
  "suppression_target": "林川的职位和名誉",
  "reader_expectation": "主角利用重生信息避免再次背锅",
  "payoff_trigger": "林川提前保留原始账本并交出复印件",
  "release_action": "用账目异常反问厂长",
  "payoff_result": "暂时保住证据并迫使对方暴露急迫性",
  "payoff_type": "智识碾压",
  "release_mode": "部分释放",
  "payoff_strength": 5,
  "publicness": "小范围",
  "irreversibility": "中",
  "reader_reward": ["掌控感"],
  "new_cost_or_problem": "厂长转而要求立即搜查工位",
  "confidence": "确定"
}
```

## 7. 质量校验规则

- 是否每章都被强行判定有爽点。
- 爽点是否有明确前置期待。
- `payoff_strength` 是否与S2的 `release_score`严重矛盾。
- 只发生口头争执是否被夸大成打脸。
- 相同类型连续出现时是否标记重复度。
- 爽点间隔是否只计算主要爽点。
- 未兑现承诺是否错误计入爽点事件。
- 长延迟爽点能否追溯到最初设置章节。

异常规则：

```text
payoff_strength >= 8 且 suppression_level <= 1：人工检查
payoff_present = true 且 reader_reward为空：人工检查
连续3个主要爽点类型完全相同：重复风险
超过5章无任何正反馈：检查是否为有意长压抑
```

## 8. 下游交接

- 爽点事件 → S5分析付费点和追读机制。
- 章节爽点字段 → S6中央表。
- 类型、强度和间隔 → S7热力图。
- 卷级分布 → S8提炼题材爽点公式。
- 高表现爽点章节 → S9示例模板。

## 9. Claude Skill 写法

```markdown
---
name: webnovel-payoff-engineering
description: Decompose web-novel payoff events into suppression, expectation, trigger, release, result, reader reward, strength, interval, and novelty. Use when analyzing 爽点 density, delayed payoff, repetition, or payoff engineering.
---

# Web-Novel Payoff Engineering

Read `references/prompt.md`.

Requirements:

- Allow chapters with no payoff.
- Separate payoff promises from completed payoff events.
- Track setup start and payoff interval.
- Evaluate reader reward, not only protagonist success.
- Compare with recent payoff types for novelty.
- Attach evidence to every major payoff event.
```
