# context-retrieval-rules.md

> 用途：定义 continuity-keeper / EXTRACT_CONTEXT 的上下文提取策略，确保不遗漏关键信息且不只依赖关键词匹配。
> 读取时机：continuity-keeper 提取上下文，或 chapter-planner、chapter-writer 使用和校验 ContextPack 时，通过各自 SKILL.md 中的相对链接读取。
> 来源：冻结契约 §9（ContextPack）。

## 目录

- [核心原则](#核心原则)
- [必须结合的维度](#必须结合的维度)
- [提取策略](#提取策略)
  - [人物提取（非关键词）](#人物提取非关键词)
  - [地点/规则提取](#地点规则提取)
  - [剧情线提取](#剧情线提取)
  - [时间线约束](#时间线约束)
- [超限时截断优先级](#超限时截断优先级)
- [retrieval_trace 结构](#retrieval_trace-结构)
- [禁止行为](#禁止行为)

## 核心原则

- 不得只依赖关键词匹配。必须结合结构化状态和语义关系进行提取。
- 只包含当前任务直接相关信息（最小上下文包）。
- 事实必须附来源，未知信息必须进入 unknowns。
- 实质内容目标不超过 2,000 中文字符，完整结果不超过 4,000 tokens。

## 必须结合的维度

提取上下文时，必须逐一检查以下维度，不得跳过：

| 维度 | 来源文件 | 提取内容 |
|------|---------|---------|
| 当前章节涉及人物 | chapters/plans/ + characters/ | 出场人物的当前状态、目标、知情范围、关系 |
| 当前地点 | chapters/plans/ + world/locations.md | 地点规则、限制、相关势力 |
| 当前卷/剧情线 | outline/ + architecture/ | 本卷目标、当前阶段、主线推进方向 |
| 章节卡 required_elements | chapters/plans/chapter_XXX.md | 必须包含的情节要素、禁止揭示项 |
| active_open_loops | state/open_loops.md |  urgency=high 的必须包含；medium 按相关性 |
| active_foreshadowing | state/foreshadowing.md | 当前章节需强化/揭示的伏笔及使用约束 |
| knowledge_state | state/knowledge_state.md | 各人物当前知情范围，防止信息泄露 |
| 最近 2~3 章摘要 | state/chapter_summaries.md | 前文结尾状态、未解决冲突、情感延续 |
| 相关 Canon | state/canon.md | 与当前场景直接相关的已确认事实 |
| style_guide | style_guide.md | 全局默认风格 + 篇章 scens 的 relevant_scene_modulations |
| contract_meta | 各种交付物 | schema_version 用于识别 v1.2 vs v1.1 结构 |

## 提取策略

### 人物提取（非关键词）
1. 从章节卡 scenes 中提取所有涉及人物。
2. 对每个人物查询 character_state.md 获取当前状态。
3. 查询 knowledge_state.md 获取该人物知情范围。
4. 查询 relationship_map.md 获取与本章其他人物的关系。
5. 检查是否有该人物相关的 active_open_loops 或 foreshadowing。

### 地点/规则提取
1. 从章节卡 time_and_location 提取地点。
2. 查询 world/locations.md 和 world/power_system.md 获取地点规则。
3. 检查该地点是否有相关 Canon 约束。

### 剧情线提取
1. 从 outline/ 确定当前卷和阶段目标。
2. 从章节卡 chapter_function 确定本章在剧情线中的位置。
3. 检查 prohibited_reveals 确保不提前泄露。

### 时间线约束
1. 从 state/timeline.md 提取当前时间点和最近事件。
2. 确保本章时间不与已确认时间线矛盾。

## 超限时截断优先级

当上下文超出预算时，按以下优先级保留（从高到低）：

1. 硬约束（prohibited_conflicts、timeline_constraints）
2. 相关 Canon
3. 当前状态（时间、地点、冲突、目标）
4. 知识范围（knowledge_state）
5. 活跃伏笔和开放循环
6. 风格提示

被省略但可能相关的内容进入 `omitted_context_refs`。

## retrieval_trace 结构

每次上下文提取必须输出 retrieval_trace，用于审计和调试：

```yaml
retrieval_trace:
  request_id: string
  target_chapter: string
  generated_at: string  # ISO 8601

  dimensions_checked:
    - dimension: "characters"
      sources_read: ["characters/protagonist.md", "state/character_state.md"]
      items_found: 3
      items_included: 3
      items_omitted: 0
    - dimension: "open_loops"
      sources_read: ["state/open_loops.md"]
      items_found: 5
      items_included: 2
      items_omitted: 3
      omission_reason: "urgency=low, not related to current chapter"
    # ... 每个维度一条

  budget:
    substantive_characters: integer
    estimated_tokens: integer
    truncated: boolean
    truncation_point: string | null  # 截断发生在哪个维度

  omitted_context_refs:
    - ref: "state/foreshadowing.md#FS-012"
      reason: "budget_exceeded"
      relevance: "medium"

  unknowns:
    - item: "配角B当前所在地"
      reason: "character_state.md 无记录"
      impact: "可能影响第3场景逻辑"

  confidence_notes:
    - "人物A的知情范围基于第12章末尾推断，非明确叙述"
```

## 禁止行为

- 不得用全文搜索关键词替代结构化查询。
- 不得在 unknowns 有值时假装信息完整。
- 不得省略 retrieval_trace（即使未截断）。
- 不得将 DEPRECATED 状态的 Canon 作为当前事实提供。
- 不得在上下文包中创造正文中未发生的事实。
