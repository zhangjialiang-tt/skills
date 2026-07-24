# fact-extraction-rules.md

> 用途：定义哪些内容应进入状态候选（state_change_proposals），指导 chapter-writer 和 continuity-keeper 的事实提取行为。
> 读取时机：chapter-writer 报告新增事实、continuity-keeper 生成状态候选时，通过各自 SKILL.md 中的相对链接读取。
> 来源：冻结契约 §6（SkillResult.state_change_proposals）、§8（ChangeSet）、§12.4（chapter_report）。

## 必须提取（进入 state_change_proposals）

以下变化在章节写作/修订中一旦出现，必须在 chapter_report 中报告并作为 state_change_proposals 输出：

### 人物状态变化
- 人物死亡、受伤、康复、失踪
- 人物关系确立、破裂、转变（同盟→敌对等）
- 人物获得/失去能力、物品、身份
- 人物目标发生明确转变
- 人物获知新信息（改变 knowledge_state）

### 时间线事件
- 明确的时间推进（"三天后"、季节变化）
- 关键事件发生（战斗、会议、仪式）
- 事件因果链建立

### 世界/规则变化
- 新规则被引入或旧规则被打破
- 地点状态变化（城市被毁、新地点出现）
- 势力格局变化

### 伏笔与悬念
- 新伏笔植入（planted）
- 伏笔被强化（reinforced）
- 伏笔部分揭示（partially_revealed）
- 伏笔完全兑现（resolved）
- 新开放循环打开
- 开放循环关闭

### 剧情偏离
- 与章节卡的任何偏离（deviations_from_plan）
- 计划外新增事实（new_facts_introduced）
- 连续性风险（possible_continuity_risks）

## 默认不提取

以下内容不进入 state_change_proposals：

- 纯修辞/文风变化（L1/L2 编辑且不改变含义）
- 环境描写中的氛围细节（除非暗示剧情）
- 角色内心独白中未外化的想法（除非改变 knowledge_state）
- 已在 Canon 中记录的事实重复出现
- 过渡性动作（走路、吃饭等无状态变化的日常）
- 读者已知信息的回顾性提及

## 提取格式

每条 state_change_proposal 必须包含：

```yaml
- type: canon_candidate | state_update | deprecation | contradiction
  description: "简明描述变化内容"
  evidence: "正文中的具体文本证据或章节卡引用"
  source_ref: "chapter_XXX / deliverable_id / revision"
  risk_level: LOW | MEDIUM | HIGH
  requires_user_confirmation: boolean
```

## 提取约束

1. 未接受章节（DRAFT/REVIEWED）的变化只能进入 proposals，不得进入 committed_updates。
2. 只有 ACCEPTED/PUBLISHED 章节的变化才能通过 COMMIT_CHAPTER_STATE 正式提交。
3. 无法确定来源的变化标记为 UNKNOWN，不得伪造证据。
4. 与现有 Canon 矛盾的变化必须同时登记为 contradiction。
5. 推断性变化（非正文明确表述）必须标注 confidence 并降低 risk_level 评估。
6. 每条提取必须可回查到具体正文段落或章节卡条目。
