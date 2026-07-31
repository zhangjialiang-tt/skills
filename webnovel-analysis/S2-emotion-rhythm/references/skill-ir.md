# S2 情绪节奏打分 — Skill IR

## 能力契约

| 字段 | 值 |
|------|------|
| 技能编号 | S2 |
| 一句话功能 | 把每章的压抑、释放和章末情绪状态量化为可跨章节比较的 1-10 分数据 |
| 运行模式 | incremental / calibration |
| 允许写入字段 | emotion_start, emotion_low, emotion_high, emotion_end, emotion_score, pressure_score, release_score, emotion_volatility, emotion_curve, dominant_emotion, emotion_turning_point, reader_reward |

## 触发条件

### 应触发
- "情绪评分"、"节奏分析"、"爽感量化"
- "情绪曲线"、"压力释放打分"、"读者感受"

### 不应触发
- 结构分析 → S1
- 人物关系 → S3
- 爽点事件拆解 → S4
- 商业卡点 → S5

## 输入依赖
- S0 standardized_chapters
- 前批 previous_scores（用于相邻比较）
- S1 known_turning_points（可选）

## 输出消费方
- S4（判断爽点释放）
- S5（判断追读压力）
- S6（中央表聚合）
- S7（热力图）
- S8（题材节奏公式）

## 失败模式

| 模式 | 后果 | 缓解 |
|------|------|------|
| 评分集中在 7-9 分 | 失去区分度 | 与相邻章节比较，强制分散 |
| 角色情绪=读者情绪 | 评分失真 | 必须说明读者得到何种回报 |
| 单一分数抹平复杂走势 | 峰谷丢失 | 分别记录高点/低点/结尾 |
| 局部批次给 10 分 | 全书峰值贬值 | 局部批次原则上不给 10 |
