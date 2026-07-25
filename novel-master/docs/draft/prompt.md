## 总体评价

这一版已经修复了上一轮绝大多数问题，尤其是：

- 分离 `PlanningArtifactMeta` 与外部 `PlanRef`，解决自引用哈希。
- 使用 `PlanRef + ItemRef` 表达嵌套规划项。
- Volume、Arc 改为单产物文件，降低无关修改造成的大范围失效。
- 增加 Batch Slot 生命周期。
- 明确 PlanningPack 由确定性脚本构建。
- 为 `plan_progress` 增加幂等更新模型。
- 收敛任务类型，重规划复用现有 `PLAN_PLOT/PLAN_VOLUME`。
- 将读者回报调度延后，避免 v1.3 范围继续膨胀。

我的评分是 **9.3/10**。

已经不需要整体重写，但在进入 Schema 和 Skill 实现前，还需要修正几处明确的不一致。最重要的是**目录所有权回退、引用类型不闭合、FAST 路径断链和规划进度恢复**。

---

# 一、必须修正的阻塞问题

## P0-1：`story_engine.md` 和 `project_spine.md` 的目录违反 v1.2 所有权

当前计划将它们放在：

```text
outline/story_engine.md
outline/project_spine.md
```

但负责人仍是：

```text
story-architect / STORY
```

v1.2 冻结契约明确规定：

- `architecture/` 归 `story-architect / STORY`
- `outline/` 归 `story-architect / PLOT`
- 单次调用不得跨越其他主要负责人的所有权区域。

因此当前路径会出现：

> STORY 模式向 PLOT 所有权区域写文件。

建议恢复：

```text
architecture/
├─ story_engine.md
└─ project_spine.md
```

Volume和Arc继续放：

```text
outline/volumes/
outline/arcs/
```

这样不需要改变 v1.2 文件所有权原则。

---

## P0-2：`PlanningArtifactMeta.artifact_type` 缺少 `CHAPTER_BATCH`

当前定义：

```yaml
artifact_type: STORY_ENGINE | PROJECT_SPINE | VOLUME_ARC | ARC_PLAN
```

但 `ChapterBatch` 又写成：

```yaml
planning_artifact_meta:
  artifact_type: CHAPTER_BATCH
```

Schema会直接冲突。

应统一为：

```text
STORY_ENGINE
PROJECT_SPINE
VOLUME_ARC
ARC_PLAN
CHAPTER_BATCH
```

同时，`PlanRef.artifact_type` 中存在：

```text
CHARACTER_ARC
```

但计划明确说 v1.3 暂不建立正式 CharacterArc 契约，只保留自然语言 `target_step`。

因此建议本版本删除 `CHARACTER_ARC`，避免出现没有文件、Schema和所有权的孤立类型。

---

## P0-3：`PlanRef` 和 `ItemRef` 的组合形式仍不统一

计划在 B2 中定义的是：

```yaml
plan_ref:
  artifact_type: ...
  artifact_id: ...
  path: ...
  revision: ...
  content_hash: ...
  item_ref:
    item_type: ...
    item_id: ...
    json_pointer: ...
```

这是一个“PlanRef可选携带ItemRef”的结构。

但 ChapterBatch 示例又写成：

```yaml
batch_ref: { 完整 PlanRef }
batch_slot_ref: { item_type: BATCH_SLOT, item_id: SLOT-003, ... }
```

而 E 节又声明：

```yaml
batch_slot_ref: PlanRef | null
```

三处语义不一致。

### 建议固定一种正式结构

```yaml
batch_ref:
  artifact_type: CHAPTER_BATCH
  artifact_id: BATCH-001
  path: chapters/batches/batch_001.md
  revision: "3"
  content_hash: sha256:...

batch_slot_ref:
  artifact_type: CHAPTER_BATCH
  artifact_id: BATCH-001
  path: chapters/batches/batch_001.md
  revision: "3"
  content_hash: sha256:...
  item_ref:
    item_type: BATCH_SLOT
    item_id: SLOT-003
    json_pointer: /chapter_batch/chapter_slots/2
```

或者正式拆为：

```yaml
artifact_ref: PlanRef
item_ref: ItemRef
```

关键要求：

- `batch_slot_ref` 必须包含所属 Batch。
- `batch_slot_ref` 与 `batch_ref` 必须指向同一个 `artifact_id/revision/hash`。
- `phase_ref` 必须指向 `PROJECT_SPINE + PHASE ItemRef`。
- `milestone_ref` 必须指向 `PROJECT_SPINE + MILESTONE ItemRef`。
- `beat_ref` 必须指向 `ARC_PLAN + ARC_BEAT ItemRef`。
- `payoff_ref` 必须指向 `ARC_PLAN + PAYOFF ItemRef`。

否则嵌套对象不能被唯一定位。

---

## P0-4：`json_pointer` 不应成为嵌套项的主身份

例如：

```yaml
item_id: BEAT-002-03
json_pointer: /required_beats/2
```

如果在数组前插入一个 Beat，原对象会变成：

```text
/required_beats/3
```

虽然 `item_id` 没变，所有旧引用仍可能因为 Pointer 变化而失效。

建议规定：

```text
item_id 是规范身份；
json_pointer 只是缓存定位或诊断信息。
```

校验流程：

1. 先按 `item_id` 查找。
2. 检查找到对象的类型。
3. `json_pointer` 一致则通过。
4. Pointer不一致但ID存在时，可更新缓存，不判定规划语义失效。
5. ID不存在才返回 `STALE_PLAN_REF` 或 `ITEM_NOT_FOUND`。

更稳妥的方式是让规划对象采用 ID Map，而不是纯数组：

```yaml
required_beats:
  BEAT-002-03:
    description: string
```

不过这会降低 Markdown 人工可读性，当前使用“数组＋稳定ID”也可以接受。

---

## P0-5：FAST路径不应省略 `planning_execution`

计划的检查点表写着：

> 每章（FAST除外）：Writer返回 `planning_execution`。

这会导致FAST正式章节出现断链：

```text
章节被 ACCEPTED
→ novel-master 需要更新 plan_progress
→ 没有 planning_execution
→ 无法判断Beat、Milestone和偏差
```

FAST可以省略 Reviewer，但不应省略最小执行报告。

建议规则：

| 场景         | PlanningExecution                  |
| ------------ | ---------------------------------- |
| FAST正式章节 | 必须输出最小版                     |
| STANDARD     | 必须输出完整版                     |
| STRICT       | 必须输出完整版并调用PLAN_ALIGNMENT |
| ADVISORY试写 | 可以不输出或标记非正式             |

FAST最小版至少包括：

```yaml
planning_execution:
  beat_execution: []
  actual_deviations: []
```

如果 Writer报告了 `TACTICAL/STRATEGIC` 偏差，则即使是FAST，也必须升级到 Reviewer或检查点流程。

---

## P0-6：`plan_progress` 仍在使用裸字符串引用

当前：

```yaml
active_volume: string
active_arc: string
```

这会重新引入 v1.3 正在解决的问题：

- 不知道引用哪个 revision。
- 不知道上游文件是否已更新。
- 不能验证生命周期是否 ACTIVE。
- 无法构建可靠 PlanningPack。

建议修改为：

```yaml
active_phase_ref: PlanRef
active_volume_ref: PlanRef
active_arc_ref: PlanRef
active_batch_ref: PlanRef | null
```

其他集合也应结构化：

```yaml
completed_milestones:
  - milestone_ref: PlanRef
    completed_by_acceptance_ref: string
    completed_at_chapter_ref: object
```

```yaml
deviations:
  - deviation_id: string
    source_acceptance_ref: string
    assessment: object
    resolution_status: RECORDED | REPLANNED | APPROVED | REJECTED
```

否则 PlanProgress虽然有幂等事务，却仍然缺少可追踪引用。

---

## P0-7：缺少 `plan_progress` 的重建路径

计划已经正确规定：

- 进度更新失败不回滚已提交事实。
- 失败时记录 `SYNC_PENDING`。

但之后如何恢复没有定义。

由于 `plan_progress` 是派生数据，应明确支持从以下来源重建：

- ACCEPTED/PUBLISHED章节。
- ChapterPlan。
- ChapterReport中的 `planning_execution`。
- ReviewReport中的 `deviation_assessment`。
- 有效 PlanRef。

建议增加确定性脚本：

```text
scripts/rebuild_plan_progress.py
```

或者复用：

```text
CHECK_PLAN_PROGRESS + repair_mode: REBUILD
```

必须保证：

```text
SYNC_PENDING
→ 重试同一幂等更新
→ 失败时全量重建
```

否则系统出现一次同步失败后，后续 PlanningPack 都可能基于过期进度。

---

# 二、规划生命周期还需补一个原子激活协议

当前生命周期规则已经比较完整，但实际激活一个新 revision 时至少涉及：

```text
旧 ACTIVE → SUPERSEDED
新 APPROVED → ACTIVE
索引更新
plan_progress active ref 更新
workflow 日志更新
```

这些操作不能分开完成，否则中间可能出现：

- 两个 ACTIVE。
- 没有 ACTIVE。
- 索引指向旧版本。
- PlanProgress指向已SUPERSEDED版本。

建议增加：

```yaml
planning_activation_change:
  activation_id: string
  artifact_id: string
  previous_active_ref: PlanRef | null
  new_active_ref: PlanRef
  base_revisions: object
  status: PREPARED | VALIDATED | COMMITTED | ROLLED_BACK | FAILED
```

由 `novel-master` 执行原子更新：

```text
验证 ApprovalRef
→ 验证同Scope唯一性
→ 旧版标记SUPERSEDED
→ 新版标记ACTIVE
→ 更新索引
→ 更新workflow日志
```

这不是 `state/ChangeSet`，而是独立的规划工作流事务。

---

# 三、初始化范围还少了当前 ArcPlan

计划规定初始化 ApprovalRef 覆盖：

- StoryEngine。
- ProjectSpine。
- 当前 VolumeArc。

但 STANDARD/STRICT章节只能引用 ACTIVE规划，而 ChapterBatch又必须基于当前 ArcPlan生成。

因此初始化结束后如果没有当前 Active ArcPlan，仍然不能进入正式章节生产。

建议二选一：

## 方案A：完整初始化包含当前Arc

初始化确认覆盖：

```text
StoryEngine
ProjectSpine
当前VolumeArc
当前ArcPlan
StyleGuide
```

之后再由 ChapterPlanner生成首个Batch。

## 方案B：分两道闸门

```text
INITIALIZATION_REVIEW
→ 激活StoryEngine/Spine/Volume

PLOT_CURRENT_ARC_REVIEW
→ 激活当前ArcPlan

chapter-planner
→ 创建并激活首个Batch
```

更推荐方案A，用户在开书时通常需要看到首个剧情弧是否成立。

ChapterBatch不一定要进入初始Canon确认，但正式写第一章前必须至少是 `ACTIVE` 或处于明确的批准流程中。

---

# 四、上游更新后的“过期”规则需要区分未来计划和历史证据

当前规则是：

> 上游PlanRef被更新时，章节卡标记 `STALE_PLAN_REF`。

不能对所有章节卡一概处理。

建议：

| 章节/计划状态          | 上游规划被替换后的处理          |
| ---------------------- | ------------------------------- |
| PLANNED章节卡          | 标记STALE，要求重规划           |
| DRAFT正文对应章节卡    | 标记STALE，禁止直接接受，需复核 |
| REVIEWED正文           | 标记STALE，重新评审或确认       |
| ACCEPTED/PUBLISHED章节 | 保留历史PlanRef，不标记为错误   |
| 已完成Batch Slot       | 保留历史映射                    |
| 未执行Batch Slot       | 新Batch revision可替换          |

已经接受的章节是在当时有效规划下执行的历史证据，不能因为后来改了大纲，就把旧章节判定为“引用错误”。

只有高风险Retcon时，才通过影响分析处理历史章节。

---

# 五、哈希规则还需要冻结

当前已经解决了自引用，但仍未规定：

- 使用哪种算法。
- 是否对整个Markdown文件计算。
- CRLF/LF是否导致不同Hash。
- YAML字段顺序是否影响Hash。
- 索引或生成时间是否包含在Hash中。
- 非语义排版变化是否导致PlanRef过期。

建议采用：

```yaml
hash_policy:
  algorithm: SHA-256
  encoding: UTF-8
  line_endings: LF
  source: canonical_payload
  excluded_fields:
    - generated_at
    - display_metadata
```

更推荐对结构化 YAML Payload规范化后计算，而不是对整份Markdown展示文件计算。

例如：

```text
Markdown front matter/YAML结构
→ 解析
→ 删除非语义字段
→ 键排序
→ 规范JSON序列化
→ SHA-256
```

这样换行、排版和注释变化不会让所有引用失效。

---

# 六、Reader回报延后是合理的，但 `payoff_cadence` 需要避免成为孤立字段

计划已经将正式读者回报调度延后到 v1.3.1，这是合理收敛。

但本版仍新增：

```yaml
project_brief.payoff_cadence
```

同时 ArcPlan仍有：

```yaml
payoffs: []
```

ChapterBatch仍有：

```yaml
payoff_plan: [PlanRef, ...]
```

这实际上已经存在一条基础回报链：

```text
Project Brief cadence
→ Arc payoffs
→ Batch payoff_plan
→ Writer payoff_consumption
```

因此无需删除，但应明确v1.3只做：

> 回报引用和执行追踪，不做自动密度优化。

建议把本版本边界写成：

```text
v1.3.0：
- 允许项目声明回报节奏
- 允许Arc定义Payoff
- 允许Batch分配Payoff
- Writer报告Payoff是否提前或完成
- 不自动判断“爽点密度是否最优”

v1.3.1：
- ReaderReward分类
- 跨章回报调度
- 密度与重复模式分析
```

这样当前字段就不会成为没有明确用途的半成品。

---

# 七、测试体系仍缺语义规划Eval

当前阶段4主要是：

- 26条确定性测试。
- A/B发布门槛。

确定性测试很完整，但不足以证明规划质量真实提高。

例如系统可以做到：

- 所有章节都引用一个Batch Slot。
- 所有PlanRef都合法。
- 没有任何Stale引用。
- 但Batch本身规划得很差。

建议恢复语义Eval，至少加入：

| Eval          | 判断                                                      |
| ------------- | --------------------------------------------------------- |
| `PL-EVAL-001` | StoryEngine是否真的能持续生成不同剧情，而非循环同一种事件 |
| `PL-EVAL-002` | ProjectSpine的不可变锚点是否足够稳定但不过度约束          |
| `PL-EVAL-003` | VolumeArc是否具有独立问题、代价和不可逆变化               |
| `PL-EVAL-004` | ChapterBatch是否在写作前协调了连续章节，而非事后补引用    |
| `PL-EVAL-005` | Batch Slot之间是否存在铺垫、升级和兑现关系                |
| `PL-EVAL-006` | LOCAL偏差是否保留创作弹性                                 |
| `PL-EVAL-007` | TACTICAL重规划是否能修复剩余Batch而不推翻已接受章节       |
| `PL-EVAL-008` | 三个题材是否都能使用该模型，而非只适合升级或建设文        |
| `PL-EVAL-009` | v1.3是否减少长期漂移，同时没有明显增加模板感              |
| `PL-EVAL-010` | 发生战略偏离后，影响分析能否定位所有下游规划产物          |

阶段0只生成前5章章节卡略少。要验证滚动规划，至少应生成：

```text
2个ChapterBatch
≥10章章节卡
```

或者使用预设的偏差模拟集，不必真的生成完整正文。

---

# 八、建议增加的确定性测试

在现有26条基础上，再增加：

```text
PC-027：STORY不能写入outline/，PLOT不能写入architecture/
PC-028：PlanningArtifactMeta允许CHAPTER_BATCH，拒绝未注册CHARACTER_ARC
PC-029：batch_slot_ref必须与batch_ref属于同一artifact_id/revision
PC-030：ItemRef按item_id解析，JSON Pointer变化不使对象无故失效
PC-031：FAST正式章节仍输出最小planning_execution
PC-032：plan_progress的active_phase/volume/arc/batch全部使用PlanRef
PC-033：SYNC_PENDING可通过幂等重试或重建恢复
PC-034：新Arc revision激活时旧ACTIVE与新ACTIVE原子切换
PC-035：上游规划更新不会将ACCEPTED/PUBLISHED章节标记为STALE
PC-036：当前ArcPlan未ACTIVE时禁止创建正式STANDARD/STRICT Batch
```

---

# 九、不要移动v1.2 frozen原文件

计划最后写：

> v1.2.0 frozen移入 `docs/archive/`。

不建议这样做。

v1.2的：

- 内部相对链接。
- 测试引用。
- ADR引用。
- 历史审计记录。
- 旧项目的契约链接。

都可能依赖原路径。

建议：

```text
保留原冻结文档原路径且不可修改
新增 docs/archive/index.md 进行版本索引
v1.3 文档通过 supersedes 指向 v1.2
```

可以复制一份到archive用于浏览，但不要移动或删除原文件。

---

# 十、建议的最终修订清单

## 实施前必须完成

- [ ] `story_engine/project_spine`恢复到 `architecture/`。
- [ ] `PlanningArtifactMeta`加入 `CHAPTER_BATCH`。
- [ ] 删除未实现的`CHARACTER_ARC`类型。
- [ ] 统一PlanRef/ItemRef和`batch_slot_ref`结构。
- [ ] ItemRef以`item_id`为规范身份，Pointer仅作定位。
- [ ] FAST正式章节保留最小`planning_execution`。
- [ ] PlanProgress中的活动规划全部改为PlanRef。
- [ ] 增加PlanProgress重建/恢复流程。
- [ ] 初始化覆盖当前ArcPlan或增加独立Arc激活闸门。
- [ ] 明确历史Accepted章节不因新大纲而变成STALE。

## 强烈建议完成

- [ ] 定义规范化Hash策略。
- [ ] 增加规划激活原子事务。
- [ ] 增加语义规划Eval。
- [ ] 阶段0基线至少覆盖两个Batch。
- [ ] 保留v1.2冻结文档原路径。

# 最终结论

这一版已经把 v1.3 的主要架构搭建完整：

```text
长期规划产物
→ 独立版本与生命周期
→ 滚动ChapterBatch
→ 单章引用Batch Slot
→ Writer报告规划执行
→ Reviewer确认偏差
→ 接受后幂等更新进度
→ 检查点触发重规划
```

剩余问题已经不是方向问题，而是几个**引用和工作流边界的最后不一致**。

其中最优先处理的是：

1. 恢复 STORY 文件的正确所有权目录。
2. 统一 `PlanRef + ItemRef`。
3. 修复 FAST 和 PlanProgress 的执行断链。
4. 补齐初始化Arc激活和进度恢复。

修正以后，这份计划可以视为 **v1.3.0-final 候选实施计划**，进入 RC 契约设计和 Schema 实现阶段。
