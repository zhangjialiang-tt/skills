# novel-master 案例分析与优化方向

> 案例：`novel-master/.novel-1/` —《废土灯火》（末世生存长篇）
> 分析来源：ChatGPT 评审 + 逐文件探索
> 时间：2026-07-25

---

## 一、案例全貌

《废土灯火》是一个完整的 novel-master 生成项目，包含：

| 目录 | 内容 | 质量 |
| --- | --- | --- |
| `project_brief.md` | 作品定位、核心钩子、读者承诺、约束、排除项 | ✅ 结构完整，假设与已确认分离 |
| `architecture/story_architecture.md` | 故事骨架 | 存在 |
| `characters/` | protagonist、hope、pillar、artisan、healer + index | ✅ 5 个角色，各有独立文件 |
| `outline/plot_plan.md` | 四卷规划，第一卷详细到每 5 章的事件表 | ⚠️ 更像是事件时间线 |
| `chapters/drafts/` | 三章完整正文，每章约 4000 字 | ✅ 写作质量高 |
| `chapters/plans/` | 三章章节卡 | ✅ 与正文对应 |
| `chapters/contexts/` | 三章上下文包 | ✅ 提取完整 |
| `state/canon.md` | 正式事实 | ✅ 维护良好 |

**第一章《最后半瓶水》** 是一个非常扎实的开章——第三人称有限视角、感官描写丰富、情绪控制精准。从饥饿的身体感受到母亲未回复的语音消息，到走廊遭遇丧尸的紧张节奏，到何卫国的冷漠救援——所有元素在 4200 字中紧凑运行。人物塑造和节奏控制都达到了可读的网文水准。

---

## 二、ChatGPT 分析中的合理判断

### ✅ 判断 1："治理成功、规划不足"——核心诊断准确

当前项目在文件完整性、状态管理、Canon 维护上是成功的：`project_brief.md` 定义了作品定位，`state/canon.md` 区分了已确认和待确认信息，章节卡和正文之间有可追踪的对应关系。

但在规划层面确实存在薄弱之处：

**证据 1：`plot_plan.md` 更像事件时间表而非故事弧线**

```text
# 当前第一卷
核心事件链 = 时间线事件列表：
  1-5章: 断粮→出逃→获救
  6-10章: 逃出公寓→展现观察力
  11-15章: 搜集物资→遇到苏婉清
  ...
  56-60章: 防守尸群→凝聚力
```

这些事件发生了一定的推进，但每段没有回答：
- 这一段的**核心问题**是什么？（不仅仅是"发生什么"）
- 段末的**不可逆变化**是什么？（不仅仅是"到了新地点"或"团队+1人"）
- 读者在段末获得的**新理解**是什么？

**证据 2：人物是功能分工而非持续冲突来源**

```text
characters/
├─ protagonist.md → 林远（观察力、共情、领导力）—— 主角
├─ pillar.md     → 何卫国（老兵、生存专家）     —— 武力和保护
├─ healer.md     → 苏婉清（前护士）              —— 医疗和情感
├─ artisan.md    → 周磊（前修理工）              —— 技术和机械
└─ hope.md       → 小禾（孤儿女孩）              —— 希望和人性
```

这个问题非常典型——五个角色完美覆盖了"武力 + 医疗 + 技术 + 情感 + 人性"的功能矩阵，但没有体现他们之间会因为什么产生根本性的冲突。现在没有：
- `protagonist ↔ pillar` 之间的领导权冲突（何卫国用老派军事思维管理，林远用协商制，这在第一卷 40 章"是否收留幸存者"中暗示了但未发展为结构性冲突）
- `healer ↔ artisan` 之间关于资源公平分配的价值观冲突
- `hope ↔ others` 之间"救助陌生人 vs 保护现有成员"的道德矛盾

**证据 3：`state/canon.md` 中有"未来计划"混入当前事实的风险**

```text
# state/canon.md 中可能包含：
- 轻微变异者的处理方式在未来卷中的走向
- 基地后续扩张的蓝图
```

这些属于 outline/（未来计划），不应进入 state/（已发生）。

### ✅ 判断 2：不要创建独立的 `planning/` 目录

ChatGPT 指出外部建议新增 `planning/` 目录，但应利用已有所有权结构：

```text
novel-brief           → project_brief.md + reader_contract.md
STORY                 → architecture/story_architecture.md + story_engine.md
CHARACTER             → characters/ + conflict_matrix.md
WORLD                 → world/ + rule_stress_tests
PLOT                  → outline/ + volume_arcs.md
continuity-keeper     → state/（仅已发生）
```

这个判断完全正确。v1.1 已经通过 1+7 架构和 `file-ownership.md` 解决了所有权问题。新增平行目录会破坏这个治理结构。所有规划增强应放入已有目录并由已有 Skill 负责。

### ✅ 判断 3：三个核心文件是规划层面的关键缺口

1. **`reader_contract.md`**（novel-brief）：当前 `project_brief.md` 有"核心钩子"和"期望读者感受"，但缺少 `retention_promise`（长期阅读承诺）、`core_gratifications`（读者每次打开新章能得到什么）、`payoff_cadence`（短期/中期/长期兑现节奏）。

2. **`story_engine.md`**（STORY）：当前《废土灯火》没有定义故事发动机——什么循环在驱动剧情？ChatGPT 建议的"压力→目标→准备→对抗→代价决策→资源/信息获得→基地变化→新压力"循环精准描述了废土建设类作品的驱动模式。

3. **`volume_arcs.md`**（PLOT）：当前 `plot_plan.md` 把每一卷定义为"状态起点 + 事件链 + 状态终点"，没有一个**卷级核心问题**。例如：
   - 卷一的核心问题可以表述为"能否找到足够的可信同伴摆脱孤立？"，而不仅仅是"五人聚齐+到达李家村"。
   - 卷二的核心问题应该在卷一的基础上**升级**，而不是"再扩展基地+遇到新势力"。

### ✅ 判断 4：人物设计需要"可持续制造剧情"的字段

当前 `characters/protagonist.md` 可能有：
- 性格：观察力强、共情
- 创伤：幸存者愧疚
- 秘密：无

但这些字段**不能驱动剧情**。ChatGPT 建议的 `character_drive` 和 `conflict_edges` 是具体的、可执行的设计升级。

**以林远为例的具体化**：

```yaml
character_drive:
    active_desire: "重建一个不需要谎言也能运转的社区"
    concrete_competence: "能快速整理资源、人力、风险信息，并制定可执行方案"
    decision_flaw: "为免伤害任何人而延迟关键决定，最终让团体承受更大代价"
    moral_boundary: "不牺牲仍在战斗中的同伴来换取资源"
    pressure_response: "在重大压力下倾向于分析和协商，而非自动指挥"

conflict_edges:
    - with_character: 何卫国
      surface_conflict: "民主协商 vs 军事命令"
      value_conflict: "个体意志的尊严 vs 生存效率的最大化"
      resource_conflict: "何卫国的经验和威信受到林远决策能力的挑战"
```

这组字段的作用是——每一章 Writer 都能从"林远的 decision_flaw 在当前的场景中如何体现"出发来推动剧情，而不是依赖 Planner 为每章独立发明冲突。

### ✅ 判断 5："未来计划"和"已发生事实"需要严格分离

《废土灯火》的 `state/canon.md` 应该只包含已出现在 ACCEPTED 正文中的事实：
- ✅ 林远被困公寓 30 天，最后半瓶水消耗完毕
- ✅ 何卫国在走廊中救下林远
- ✅ 五名初始角色已介绍

以下不应出现在 state/：
- ❌ "轻微变异者最终被林远人道处理"（未来事件，应在 outline/）
- ❌ "基地最终迁往山谷"（未来事件）

ChatGPT 建议在 outline/ 中增加 `foreshadowing_plan.md` 专门存放**计划中但尚未埋设的伏笔候选人**，这是精准的分离策略。

### ✅ 判断 6：`INITIALIZATION_REVIEW` 需要从"文件存在性检查"升级为"规划就绪性评估"

当前 V1.2 的初始化流程是：

```text
novel-brief → STORY → CHARACTER → WORLD → PLOT → novel-style → INITIALIZATION_REVIEW → 用户确认
```

但 `INITIALIZATION_REVIEW` 主要检查文件是否存在。ChatGPT 建议增加 `planning_readiness` 检查——不仅问"文件是否齐全"，还问"规划是否足够支持连载"。这八个维度精准覆盖了《废土灯火》暴露的所有规划缺口。

---

## 三、可优化的部分

### ⚠️ 优化 1：`story_engine.md` 的 cycle 需要避免过度规定

ChatGPT 建议的八步循环：

```text
pressure → goal → preparation → confrontation → costly_choice → gain → settlement_change → next_pressure
```

对《废土灯火》的废土建设题材很契合，但当应用到玄幻升级流或悬疑推理时，循环结构会有很大不同：
- 玄幻：`瓶颈期 → 获得线索 → 奇遇 → 突破 → 新能力的代价 → 更高等级的威胁 → ...`
- 悬疑：`发现异常 → 收集线索 → 误判 → 反转 → 真实 → 隐藏代价 → ...`

建议 `story_engine.cycle` 设计为**题材无关的抽象槽位**，由具体 STORY Skill 按题材填充，而不是写死一种循环。

### ⚠️ 优化 2：`reader_contract` 需要和 v1.2 的 `reader_experience` 形成可追溯链

ChatGPT 已经提到这一点——v1.2 的 `reader_experience` 应该在章节层面**向下引用** `reader_contract` 中定义的全书承诺。建议在 `reader_experience` 中增加：

```yaml
reader_experience:
    source_refs:
        reader_contract_ref: string | null   # 本书承诺
        story_engine_ref: string | null      # 叙事发动机
        volume_arc_ref: string | null        # 当前卷目标
```

这样 Planner 产出的章节质量目标就不是凭空发明的——它能够被追溯到全书读者承诺 → 故事发动机 → 当前卷目标 → 当前章节体验。

### ⚠️ 优化 3：`conflict_edges` 需要包含冲突的启动时机

当前 ChatGPT 建议的 `conflict_edges` 是静态的——它定义了谁和谁有什么冲突，但没有说**这个冲突在什么时候变得尖锐**。

建议增加：

```yaml
conflict_edges:
    - with_character: 何卫国
      activation_trigger: "团队首次面对是否收留外人的决定"
      escalation_trigger: "外部压力增加导致基地资源紧张"
      peak_trigger: "一次决策中林远的延迟导致伤亡"
      resolution_type: GRADUAL | CRISIS | UNRESOLVED
```

这比单独的"他们有价值观冲突"更可执行——Writer 知道在哪个章节节点上推动这个冲突。

### ⚠️ 优化 4：`rule_stress_tests` 需要与 reviewer 产生具体的交互

ChatGPT 建议 WORLD 输出 `rule_stress_tests`，这是很好的想法，但仅作为 WORLD 的自我检查还不够。建议将它也纳入 `INITIALIZATION_REVIEW` 的评估维度——如果 `rule_stress_tests` 中的某个 mismatch 是 blocker 级别的，初始化就不应该通过。

例如：
- "感染时间 2-72 小时 + 丧尸速度 + 城市崩溃时间"组合的结果与"爆发后第 30 天城市已空"的设定不一致 → 阻止进入写作阶段

### ⚠️ 优化 5：应先做 `废土灯火` 的 v1.2 Planning Eval，再发 v1.3

ChatGPT 建议将《废土灯火》做成 `evals/cases/wasteland-lights/`。但我建议先用 v1.2 的现有能力重跑一次《废土灯火》——用 reader_experience、target_execution、dimension_results 重新生成三章，然后和 v1.1 的旧版做 A/B。这既验证了 v1.2 章节质量契约的效果，又积累了 v1.3 规划契约需要的对比数据。

旧版第一章已经写得很好——这正好是一个严格的 A/B 测试：v1.2 的 reader_experience 能否在"已经不错"的基准上再改善？

---

## 四、ChatGPT 分析中的不足

### ❌ 不足 1：没有具体引用 v1.2 的已存在能力

ChatGPT 的分析完全聚焦在 v1.3 规划层面，但没有利用 v1.2 已经落地的 reader_experience、target_execution、dimension_results 来分析《废土灯火》的三章是否能通过这些新结构得到改善。分析中缺少：

- 如果第一章有 `reader_experience`，Planner 会如何定义"断粮→出逃→获救"这三个场景的质量目标？
- 现在的 `chapter_report` 只有"执行情况"，没有 `target_execution` 逐项追踪——如果 Writer 能用 evidence_ref 绑定正文段落来证明林远的观察力（concrete_competence）在哪些段落被展示了，会有多好？
- Reviewer 现在用通用 overall_assessment——如果改为 `dimension_results` 的 READER_EXPERIENCE 维度诊断第一章的情感拱（despair→tension→rescue→first warmth），会暴露什么新问题？

这些都是 v1.2 能力可以直接应用的领域，但分析中没有提及。

### ❌ 不足 2：`volume_arcs` 的字段缺乏优先级

ChatGPT 建议的 `volume_arc` 有 13 个字段。但实际运行中，Planer 和 Writer 可能只需要其中的 5-6 个关键字段来驱动章节生产：
- `core_question`（卷的核心问题）
- `primary_opposition`（主要对抗力量）
- `protagonist_growth_task`（主角本卷需要学会什么）
- `midpoint_reversal`（转折点）
- `irreversible_change`（卷末不可逆变化）
- `next_volume_pressure`（对下一卷的推动力）

建议在 RC 阶段先实现精简版，在 A/B 测试中验证哪些字段真正产生了改善，再补全。

### ❌ 不足 3：`knowledge_entry` 的 epistemic_state 枚举过于庞大

ChatGPT 建议 6 种认知状态：`KNOWS | BELIEVES | SUSPECTS | MISUNDERSTANDS | DENIES | UNKNOWN`。但 `concealed_from` 已经在 `character_drive` 层面被覆盖。建议 v1.3 先精简为 4 种核心状态：`KNOWS | BELIEVES | SUSPECTS | UNKNOWN`，将 `MISUNDERSTANDS` 作为 `BELIEVES` 的注释字段，将 `DENIES` 作为角色性格而非事实认知来处理。

### ❌ 不足 4：没有考虑规划过度的风险

分析聚焦于"规划不足"的问题，但没有反过来警告过度规划的风险。如果在初始化阶段就需要填写 story_engine、volume_arcs、conflict_matrix、reader_contract、rule_stress_tests 五个新结构，可能会出现"写三个月的规划文档才开始第一章"的极端情况。v1.3 需要明确哪些是初始化必填、哪些是渐进式填写的。

---

## 五、综合优化方向

### 立即（在 v1.2.0 基础上）

1. **补 reader_experience 的 source_refs 字段**——为 v1.3 预留桥梁（不阻塞 v1.2）

### v1.3 规划质量契约

2. **novel-brief** + `reader_contract.md`（读者承诺 + 兑现节奏）
3. **STORY** + `story_engine.md`（叙事发动机 + 循环结构，题材无关的抽象槽位）
4. **PLOT** + `volume_arcs.md`（卷级问题 + 不可逆变化，字段分阶段：RC 仅 6 个核心字段）
5. **CHARACTER** + `conflict_edges`（含启动/升级/高峰触发时机）+ `concrete_competence`（具体能力而非抽象优点）
6. **WORLD** + `rule_stress_tests`（多规则并发结果校验，纳入 INITIALIZATION_REVIEW）
7. **INITIALIZATION_REVIEW** + `planning_readiness`（8 维度就绪性评估）

### Eval 基础设施

8. 《废土灯火》 → `evals/cases/wasteland-lights/`（固定回归 + A/B 对比）
9. 增加玄幻升级流 + 悬疑推理两个额外题材的 planning case（防治过拟合）
10. 明确初始化必填 vs 渐进式填写边界（防止规划过度）

---

## 六、ChatGPT 分析总体评价

**评分：8.5/10**

分析准确抓住了《废土灯火》的核心问题——系统已经能够产出高质量的单章，但缺少支撑几十万字持续创作的规划层。不创建独立 `planning/` 目录、利用已有所有权结构、分离未来和已发生、升级 INITIALIZATION_REVIEW 等判断都是精准的。

主要不足是不理解 v1.2 已经落地了什么能力，因此无法将分析有效地连接到已有系统。最优先的三个改动（reader_contract + story_engine + volume_arcs）方向正确，但需要先经过精简 RC → A/B 测试的闭环，而不是直接作为 v1.3 的完整输出。
