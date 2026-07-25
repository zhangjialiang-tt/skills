## 核心判断

这个案例非常适合拿来优化 `novel-master`。

它暴露了一个过去不明显的问题：

> 系统已经能生成结构完整、来源清晰、便于持续维护的项目文件，但“文件齐全”并不等于“故事具有长期连载能力”。

《废土灯火》不是生成失败，而是出现了典型的 **治理成功、规划不足**：

- 人物、势力、世界规则都存在；
- Canon、时间线、知识状态也能维护；
- 但缺少持续制造剧情的发动机；
- 卷级结构更像事件时间表；
- 人物更多是功能分工，而不是持续冲突来源；
- 未来计划、已经发生的事实、作者预设答案之间存在混用风险。

这说明 `novel-master` 下一步不仅要有 v1.2 的“章节生产与质量契约”，还需要一条更上游的：

> **长篇故事规划质量契约。**

当前 v1.2 计划主要解决 Planner、Writer、Reviewer 和 Style 之间的章节质量闭环。  
《废土灯火》暴露的则是 `novel-brief → story-architect → PLOT → 初始化确认` 这一段还缺少质量门槛。

---

# 一、不要照搬新的 `planning/` 目录

外部评审建议新增：

```text
planning/
├─ reader_contract.md
├─ story_engine.md
├─ volume_arcs.md
...
```

内容方向正确，但我不建议新增一个顶层 `planning/`。

因为现有架构已经有明确所有权：

- `project_brief.md`：`novel-brief`
- `architecture/`：`story-architect / STORY`
- `characters/`：`story-architect / CHARACTER`
- `world/`：`story-architect / WORLD`
- `outline/`：`story-architect / PLOT`
- `state/`：`continuity-keeper`

再增加 `planning/`，会出现两个问题：

1. 同一类规划内容在 `planning/`、`architecture/`、`outline/` 重复。
2. 文件所有权再次模糊。

v1.1 已经通过 1+7 架构和所有权表解决了这一问题，不应重新引入平行目录。

更合理的目录是：

```text
<project-root>/
├─ project_brief.md
├─ reader_contract.md              # novel-brief
│
├─ architecture/
│  ├─ story_architecture.md
│  ├─ story_engine.md              # STORY
│  └─ themes.md
│
├─ characters/
│  ├─ protagonist.md
│  ├─ character_arcs.md            # CHARACTER
│  └─ conflict_matrix.md           # CHARACTER
│
├─ world/
│  ├─ world_overview.md
│  ├─ world_pressure_model.md      # WORLD，按题材可选
│  └─ outbreak_chain.md            # 末世题材专用，可选
│
└─ outline/
   ├─ master_outline.md
   ├─ volume_arcs.md               # PLOT
   ├─ arc_catalog.md               # PLOT
   ├─ chapter_rhythm.md            # PLOT + novel-style 共同引用
   └─ foreshadowing_plan.md        # 未来计划，不写 state/
```

---

# 二、把三个核心文件变成初始化必需产物

外部评价提出的三个文件，确实是最关键缺口。

## 1. `reader_contract.md`

由 `novel-brief` 负责。

它不能只是“目标读者”和“核心卖点”，还需要回答：

```yaml
reader_contract:
    click_promise: string
    retention_promise: string
    core_gratifications: []
    emotional_contract: []
    differentiation: string
    expected_progression: string
    payoff_cadence:
        short: string
        medium: string
        long: string
    prohibited_failures: []
```

对《废土灯火》来说，可以表达成：

```yaml
click_promise: 普通人在丧尸衰败、旧秩序崩溃后建立新聚居地

retention_promise: 每次外出都会带回资源、人才或新危机，并让基地发生可见变化

core_gratifications:
    - 生存方案落地
    - 团队关系建立
    - 基地逐步点亮
    - 不同治理理念碰撞
```

这会比“末世生存、普通人成长”更可执行。

---

## 2. `story_engine.md`

由 `story-architect / STORY` 负责。

这是本案例最明显的缺口。

建议结构：

```yaml
story_engine:
    primary_engine:
        name: string
        cycle:
            - pressure
            - goal
            - preparation
            - confrontation
            - costly_choice
            - resource_or_information_gain
            - settlement_state_change
            - next_pressure

    secondary_engines: []

    escalation_axes:
        resource_scale: string
        social_scale: string
        moral_scale: string
        geographic_scale: string

    refresh_mechanisms: []
    failure_modes: []
    long_term_transformation: string
```

《废土灯火》的核心循环就可以是：

```text
基地出现生存问题
→ 团队制定有限方案
→ 外出寻找资源或人才
→ 遭遇环境、丧尸或势力
→ 做出带代价的决定
→ 带回资源、成员或麻烦
→ 基地发生结构变化
→ 新问题升级
```

关键不是写出这一段，而是后续 PLOT 和 ChapterPlan 都必须引用它。

---

## 3. `volume_arcs.md`

由 `story-architect / PLOT` 负责。

每一卷不能只有时间范围和主要事件，至少应包含：

```yaml
volume_arc:
    volume_id: string
    core_question: string
    external_goal: string
    primary_opposition: string
    internal_conflict: string
    protagonist_growth_task: string
    midpoint_reversal: string
    lowest_point: string
    climax_choice: string
    climax_cost: string
    reader_payoff: string
    irreversible_change: string
    next_volume_pressure: string
```

最重要的是：

> 每卷必须解决一个问题，同时制造一个更高层级的问题。

这样才能防止四卷只是“地图越来越大、敌人越来越强”。

---

# 三、给人物设计增加“可持续制造剧情”的字段

当前人物设计容易生成：

- 性格。
- 创伤。
- 技能。
- 秘密。
- 人物弧。

但《废土灯火》说明，这些字段还不足以确保人物在几十万字中持续主动行动。

建议 `CHARACTER` 模式增加：

```yaml
character_drive:
    active_desire: string
    concrete_competence: string
    transferable_value: string
    decision_flaw: string
    moral_boundary: string
    pressure_response: string
    agency_ladder: []
    irreversible_choice_nodes: []

conflict_edges:
    - with_character: string
      surface_conflict: string
      value_conflict: string
      resource_conflict: string
      expected_evolution: string
```

关键变化是：

## 具体能力，而非抽象优点

林远不能只写：

```text
观察力强、共情力强
```

而应写成：

```text
能快速整理资源、人力和风险信息，并把不同人的专长组织成可执行方案
```

这样 Writer 才知道如何通过行动表现他的能力。

## 缺陷必须能造成剧情后果

不能只写：

```text
自我怀疑
```

而应写：

```text
为了避免伤害任何人而延迟决策，最终让所有人承担更大风险
```

这是可以进入具体场景的缺陷。

## 队伍必须形成冲突网络

不只是：

```text
战士 + 医生 + 技术员 + 侦察 + 领导
```

而是：

```text
服从效率 vs 协商认可
医疗公平 vs 资源效率
个体自由 vs 基地安全
救援陌生人 vs 保护现有成员
```

人物冲突应成为故事发动机的一部分。

---

# 四、WORLD 模式需要增加“规则压力测试”

《废土灯火》的感染时间、传播方式、丧尸速度、腐败时间和城市崩溃速度之间存在可疑组合。

这不是简单的设定缺失，而是当前 WORLD Skill 主要检查：

- 能力是否有代价。
- 规则是否服务剧情。
- 是否存在矛盾。

但还缺少：

> 多条规则同时运行时，世界会不会得到作者预期的结果？

建议 WORLD 输出增加：

```yaml
rule_stress_tests:
    - scenario: string
      assumptions: []
      derived_result: string
      intended_result: string
      mismatch: string | null
      required_decision: string | null

scale_checks:
    population_base: integer | null
    rare_group_ratio: number | null
    estimated_count: integer | null
    narrative_positioning: string

causal_event_chain:
    - time
    - event
    - system_failure
    - consequence
```

例如自动检查：

```text
人口 200 万 × 抗体比例 0.1%
= 理论约 2000 人
```

然后提出：

> 这是否仍符合“极稀有、传说级个体”的叙事定位？

这个计算结果不是 Canon，而是设计风险。

---

# 五、必须严格分离“未来计划”和“已经发生”

这是《废土灯火》案例中最值得警惕的地方。

当前文件可能把以下内容混在一起：

- 以后准备埋的伏笔。
- 已经在正文中埋下的伏笔。
- 作者预设的未来答案。
- 角色当前已经知道的事实。
- 预计第三卷发生的人物选择。

应明确：

## `outline/` 管未来

包括：

- 预计开放的问题。
- 计划埋设的伏笔。
- 预计回收窗口。
- 候选结局。
- 尚未发生的人物选择。
- 未冻结的道德难题。

## `state/` 管已发生

包括：

- 已经出现在 `ACCEPTED/PUBLISHED` 正文里的事实。
- 已经埋下的伏笔。
- 已经开启的开放循环。
- 当前人物状态。
- 当前知识状态。

例如：

```text
“轻微变异者最终被林远人道处理”
```

在真正发生前，不能进入 Canon 或正式状态。

更合理的是：

```yaml
dilemma_status: UNRESOLVED
constraints:
    - 仍能表达意愿
    - 具有传播风险
    - 掌握关键情报
required_consequence:
    - 任何选择都必须产生长期代价
```

未来答案留在 PLOT 的 Proposal 中。

---

# 六、重新定义伏笔与开放循环的关系

外部评价这一点是准确的：

- 开放循环是读者等待回答的问题。
- 伏笔是支撑未来回答的证据。
- 两者不是同一个对象。

建议标准化关联：

```yaml
open_loop:
    loop_id: OL-002
    reader_question: string
    opened_ref: string
    importance: SHORT | MEDIUM | LONG
    next_touch_window: string
    payoff_window: string
    status: ACTIVE | RESOLVED | DEPRECATED

foreshadowing:
    foreshadow_id: FS-002-A
    supports_loops:
        - OL-002
    planted_ref: string
    visibility: SUBTLE | NOTICEABLE | EXPLICIT
    status: PLANTED | REINFORCED | PARTIALLY_REVEALED | REVEALED
```

还需要一个规划层对象：

```yaml
planned_foreshadowing:
    target_loop: OL-002
    planned_chapter_window: string
    candidate_content: string
    status: PROPOSAL
```

只有真正写入接受章节后，才迁移到 `state/foreshadowing.md`。

---

# 七、知识状态建议升级，但不要无限加字段

评价中提出：

- `believes`
- `suspects`
- `misunderstands`
- `denies`
- `conceals`

方向正确，但不建议分别维护多个列表。

使用统一的认知状态：

```yaml
knowledge_entry:
    fact_id: string
    character_id: string
    epistemic_state: KNOWS | BELIEVES | SUSPECTS | MISUNDERSTANDS |
        DENIES | UNKNOWN
    source_ref: string
    confidence: LOW | MEDIUM | HIGH | CERTAIN
    concealed_from: []
    concealment_reason: string | null
```

这样 Reviewer 和 ChapterPlanner 可以直接判断：

- 人物能不能说出某件事。
- 人物的错误判断能否推动剧情。
- 谁在主动隐瞒。
- 哪个认知差可以形成下一章冲突。

---

# 八、不要把设计风险写进 `contradictions.md`

外部评价建议把感染时间、气候、统计数量等问题先写成 WARNING。

我同意需要记录，但不建议全部写入 `state/contradictions.md`。

原因是：

- `contradictions.md` 应保存已经存在的来源冲突。
- 当前这些更多是“设计尚未澄清”或“推导结果与目标不匹配”。
- 写入 `state/` 容易让设计建议看起来像已发生事实。

建议新增：

```text
workflow/planning_risks.md
```

由初始化审查或 Reviewer 输出：

```yaml
planning_risk:
    risk_id: PR-001
    category: WORLD_RULE_AMBIGUITY
    description: string
    evidence_refs: []
    severity: INFO | WARNING | BLOCKER
    status: OPEN | RESOLVED | ACCEPTED_RISK
    required_owner: WORLD | STORY | CHARACTER | PLOT
```

只有两个已确认来源互相冲突时，才进入：

```text
state/contradictions.md
```

---

# 九、升级 `INITIALIZATION_REVIEW`

当前新书初始化已经包含：

```text
brief
→ STORY
→ CHARACTER
→ WORLD
→ PLOT
→ novel-style
→ INITIALIZATION_REVIEW
→ 用户确认
→ COMMIT_CANON
```

因此不需要新增 Skill，只需要让初始化评审不再只检查“文件是否存在”，还检查“规划是否足够支持长篇连载”。

建议输出：

```yaml
planning_readiness:
    status: READY | CONDITIONAL | NOT_READY

    checks:
        reader_contract: PASS | WARNING | FAIL
        story_engine: PASS | WARNING | FAIL
        volume_arcs: PASS | WARNING | FAIL
        protagonist_agency: PASS | WARNING | FAIL
        ensemble_conflict: PASS | WARNING | FAIL
        world_rule_coherence: PASS | WARNING | FAIL
        payoff_cadence: PASS | WARNING | FAIL
        future_state_separation: PASS | WARNING | FAIL

    blockers: []
    warnings: []
    unresolved_decisions: []
```

建议将以下情况视为 `NOT_READY`：

- 没有主故事发动机。
- 卷级结构只有事件列表，没有卷级问题和不可逆变化。
- 主角只有抽象优点，没有可重复使用的具体能力。
- 未来结局或人物选择已经错误写入当前状态。
- 世界核心规则之间存在阻塞级冲突。

这不是质量状态机，而是一次初始化就绪性判断。

---

# 十、把《废土灯火》做成正式 Eval Fixture

它不应只作为一次人工点评，而应变成长期回归样例。

建议目录：

```text
evals/cases/wasteland-lights/
├─ seed-brief.md
├─ v1.1-output/
├─ expected-risks.yaml
├─ planning-rubric.md
└─ assertions.yaml
```

建议断言：

```yaml
assertions:
    - story_engine_exists
    - volume_arcs_have_distinct_core_questions
    - each_volume_has_irreversible_change
    - protagonist_has_concrete_competence
    - protagonist_flaw_causes_decision_failure
    - ensemble_contains_value_conflicts
    - infection_rules_pass_timeline_check
    - rare_population_scale_is_explained
    - open_loops_link_to_foreshadowing
    - short_medium_long_payoff_mix_exists
    - planned_future_not_committed_to_state
```

但不要只用《废土灯火》优化系统，否则会过拟合末世题材。

后续至少再增加：

- 玄幻升级流。
- 都市情感或职场。
- 悬疑推理。

分别检查：

- 升级发动机。
- 关系发动机。
- 揭秘发动机。

---

# 十一、与 v1.2 的关系

我不建议把这些内容全部塞入正在规划的 v1.2.0。

v1.2 当前目标已经比较清晰：

> 章节层面的读者体验、执行追踪、分层评审和场景风格调制。

《废土灯火》暴露的是更上游的长篇规划问题，适合成为下一条版本主线：

```text
v1.2.0：章节生产与质量契约
v1.3.0：长篇故事规划质量契约
```

不过可以在 v1.2 中预留一条桥梁：

```yaml
reader_experience:
    source_refs:
        reader_contract_ref: string | null
        story_engine_ref: string | null
        volume_arc_ref: string | null
```

这样 v1.2 的章节质量目标不是 Planner 临时编出来的，而是能够追溯到：

```text
全书读者承诺
→ 故事发动机
→ 当前卷目标
→ 当前章节体验
```

在 v1.3 文件尚未存在时，这些字段可以为空；v1.3 落地后，STANDARD/STRICT 再逐步要求必填。

---

# 推荐路线

当前最合适的路线是：

```text
继续完成 v1.2 章节质量契约
        ↓
将《废土灯火》整理成 planning eval fixture
        ↓
起草 v1.3 长篇规划质量契约
        ↓
增强 novel-brief / STORY / CHARACTER / WORLD / PLOT
        ↓
升级 INITIALIZATION_REVIEW
        ↓
重新生成《废土灯火》并与旧版本 A/B 对比
```

## 最优先的三个改动

1. `novel-brief` 增加 `reader_contract`。
2. `STORY` 增加 `story_engine`。
3. `PLOT` 增加结构化 `volume_arcs`。

这三个改动对《废土灯火》的提升会最大，而且不会改变现有 1+7 架构。

**一句话总结：**

> v1.2 解决“每一章如何写得更值得读”；《废土灯火》说明 v1.3 还必须解决“几十万字为什么能够不断产生值得写的新章节”。
