# S5 商业卡点分析 — Skill IR

## 能力契约

| 字段 | 值 |
|------|------|
| 技能编号 | S5 |
| 一句话功能 | 识别章节的断章驱动力、付费切分价值、追读问题和连续阅读机制 |
| 运行模式 | incremental / consolidation |
| 允许写入字段 | commercial_position, paywall_suitability, chapter_break_strength, follow_up_question, reader_expectation, information_gap, cliffhanger_type, purchase_motivation |

## 触发条件

### 应触发
- "商业卡点"、"付费点"、"断章分析"
- "追读机制"、"章末钩子强度"、"付费切分"

### 不应触发
- 结构分析 → S1
- 情绪评分 → S2
- 爽点事件拆解 → S4

## 输入依赖
- S0 standardized_chapters
- S1 structure_records
- S2 emotion_records
- S4 payoff_records

## 输出消费方
- S6（中央表）
- S7（标记高强度卡点）
- S8（商业配方）
- S9（高质量断章案例）
- Q0（欺骗风险）

## 失败模式

| 模式 | 后果 | 缓解 |
|------|------|------|
| 把"写得精彩"当付费点 | 付费位置失真 | 付费点前必须已交付价值 |
| 爽前卡频繁使用 | 读者信任透支 | 标记 hook_fairness="欺骗风险" |
| 追读问题泛化 | S6 字段不可用 | 禁止"接下来会发生什么" |
| 虚构转化率 | 决策依据失真 | 不预测真实收入/订阅率 |
