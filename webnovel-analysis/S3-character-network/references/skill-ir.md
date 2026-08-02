# S3 人物关系网 — Skill IR

> Milestone 1 冻结：内部模块、不可外部路由；硬依赖 `[S0]`，输出由 S6 消费。本文后续“触发”均指根 Skill 的内部调度条件。

## 能力契约

| 字段 | 值 |
|------|------|
| 技能编号 | S3 |
| 一句话功能 | 提取角色实体、叙事功能、目标、阵营和关系变化 |
| 运行模式 | incremental / consolidation |
| 允许写入字段 | pov_character, active_characters, new_characters, character_goal, character_action, relationship_change, faction_change, character_function_notes |

## 触发条件

### 应触发
- "人物关系"、"角色网络"、"角色功能"
- "阵营分析"、"关系变化"、"角色合并"

### 不应触发
- 结构分析 → S1
- 情绪评分 → S2
- 爽点分析 → S4

## 输入依赖
- S0 standardized_chapters
- 前批 existing_character_registry
- 前批 previous_character_states

## 输出消费方
- 下一批 S3（角色注册表）
- S1（卷级人物弧）
- S5（情感追读点）
- S8（角色配方）
- S6（章节活跃角色）

## 失败模式

| 模式 | 后果 | 缓解 |
|------|------|------|
| 职位称呼误建为新角色 | 角色表膨胀 | 建立 canonical_name + aliases |
| 同名角色错误合并 | 关系网络混乱 | 不确定时保留独立实体 |
| 推断动机写入 known_info | 后续分析基于虚假前提 | 区分已知/推测/他人声称 |
| 关系无事件触发变化 | 网络不连续 | 必须有明确的 change_reason |
