# S4 爽点工程 — Skill IR

> Milestone 1 冻结：内部模块、不可外部路由；硬依赖 `[S2]`，S1 为可选上下文，输出由 S5、S6 消费。本文后续“触发”均指根 Skill 的内部调度条件。

## 能力契约

| 字段 | 值 |
|------|------|
| 技能编号 | S4 |
| 一句话功能 | 把"压抑积累—触发—释放—读者奖励"拆成事件级数据 |
| 运行模式 | incremental / consolidation |
| 允许写入字段 | suppression_level, suppression_source, suppression_target, payoff_present, payoff_type, payoff_strength, payoff_interval_chapters, payoff_novelty, reader_reward |

## 触发条件

### 应触发
- "爽点分析"、"压抑释放"、"爽点工程"
- "打脸分析"、"爽感强度"、"爽点间隔"

### 不应触发
- 结构分析 → S1
- 情绪评分 → S2
- 人物关系 → S3
- 商业卡点 → S5

## 输入依赖
- S0 standardized_chapters
- S2 emotion_records（可选但推荐）
- S1 story_units（可选）
- 前批 previous_payoffs

## 输出消费方
- S5（付费点和追读机制）
- S6（中央表）
- S7（热力图）
- S8（题材爽点公式）
- S9（示例模板）

## 失败模式

| 模式 | 后果 | 缓解 |
|------|------|------|
| 每章强行判有爽点 | 爽点贬值 | 允许 payoff_present=false |
| 爽点承诺算作兑现 | 间隔统计失真 | 区分已兑现/承诺 |
| 高爽点低压抑 | 强度失真 | 检查前置积累 |
| 重复类型不标记 | 套路化未被识别 | 比较最近5次爽点 |
