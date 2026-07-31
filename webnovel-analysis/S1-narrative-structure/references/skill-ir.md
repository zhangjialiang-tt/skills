# S1 叙事结构拆解 — Skill IR

## 能力契约

| 字段 | 值 |
|------|------|
| 技能编号 | S1 |
| 一句话功能 | 将章节还原为"事件—单元—卷"三级结构，识别每章功能、因果链、开放悬念和结构钩子 |
| 运行模式 | incremental / consolidation |
| 允许写入字段 | volume_id, story_unit_id, chapter_function, main_event, cause_from_previous, effect_on_next, plot_progress_type, chapter_goal, chapter_result, open_loop_added, open_loop_closed, opening_hook, mid_hook, ending_hook, ending_hook_type, structure_confidence |

## 触发条件

### 应触发
- "结构拆解"、"分析章节功能"、"逆向大纲"
- "单元划分"、"卷结构"、"章节承担什么作用"
- "故事单元"、"开放悬念"、"章末钩子"

### 不应触发
- 情绪评分 → S2
- 人物关系 → S3
- 爽点分析 → S4
- 商业卡点 → S5
- 文本清洗 → S0

## 输入依赖
- O0 task_manifest
- S0 chapter_index + standardized_chapters
- 前批 previous_batch_summary
- 累计 open_loops

## 输出消费方
- S5（付费点判断需要结构信息）
- S6（中央表聚合）
- S8（题材公式提炼）

## 失败模式

| 模式 | 后果 | 缓解 |
|------|------|------|
| 仅读10章就断言全书卷数 | 卷结构错误 | incremental 只提交候选 |
| 把疑似伏笔标为确定 | 后续分析基于虚假前提 | 无回收证据称"疑似伏笔" |
| 虚构作者未明的卷名 | 分析标签不统一 | 标记"推断命名" |
| 主事件写成主题而非事件 | 粒度失真 | 一句话概括本章主事件 |
