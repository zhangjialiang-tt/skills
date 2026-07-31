# S8 题材套路公式提炼 — 完整 Prompt 模板

## 输入格式

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

## 核心 Prompt

```text
你是"网文商业结构配方提炼师"。

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
建立一份可用于新书选题和结构规划的"题材配方"，包含：
1. 核心读者承诺
2. 主角初始缺口、核心优势和长期欲望
3. 开篇启动机制
4. 基础叙事循环
5. 卷级升级阶梯
6. 压抑—释放公式
7. 主要爽点组合
8. 角色功能组合
9. 关系推进机制
10. 付费和追读机制
11. 节奏参数
12. 可迁移项、依赖项和不可照搬项
13. 常见失败模式
14. 用于新书设计的参数化模板
```

## 输出 Schema（YAML）

```yaml
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
parameterized_recipe: ""
transferable_elements: []
dependent_elements: []
do_not_copy: []
failure_modes: []
counter_conditions: []
confidence: ""
uncertain_items: []
```

## 质量校验规则

- 是否只是剧情摘要，没有抽象成变量
- 是否把作品特有名词直接当作公式
- 每个规律是否有章节次数和间隔证据
- 是否把单书结论夸大为题材普遍真理
- 是否明确依赖条件
- 参数能否替换到其他人物、行业和世界设定
- 公式是否保留"读者奖励"而非只有事件流程
- 是否列出不能照搬的内容
