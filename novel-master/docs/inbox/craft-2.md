# novel-master 契约参考手册

> 本文档是 novel-master Skill 组的详细契约参考，定义路由表、输入输出格式和 Skill 接口。
> 高层架构和设计原则见 [craft-1.md](./craft-1.md)。

---

## 1. 统一任务输入契约（TaskEnvelope）

`novel-master` 调用任何子 Skill 时，统一传入 `TaskEnvelope`。

```yaml
task_envelope:
  request_id: string           # 请求唯一标识
  project_id: string           # 项目唯一标识

  user_request: string         # 用户原始请求

  task:
    type: enum                 # 任务类型
    scope: enum                # 影响范围
    mode: enum                 # 执行模式
    risk_level: enum           # 风险等级

  authority:
    operation: enum            # 操作权限
    canon_change_allowed: boolean      # 是否允许修改 Canon
    structural_change_allowed: boolean # 是否允许修改结构
    prose_change_allowed: boolean      # 是否允许修改正文

  context:
    required_files: []         # 必须读取的文件
    optional_files: []         # 可选读取的文件
    context_pack: object | null  # continuity-keeper 生成的上下文包

  constraints:
    must_preserve: []          # 必须保留的内容
    must_include: []           # 必须包含的内容
    must_avoid: []             # 必须避免的内容
    target_length: string | null  # 目标长度
    target_style: string | null   # 目标风格
    viewpoint: string | null      # 视角约束

  output:
    expected_deliverables: []  # 预期交付物
    target_paths: []           # 目标文件路径
```

### 1.1 `task.type` 枚举

```text
INIT_PROJECT          # 初始化新项目
REFINE_BRIEF          # 修改项目简报
DESIGN_STORY          # 设计故事结构
DESIGN_CHARACTER      # 设计人物
DESIGN_WORLD          # 设计世界
PLAN_PLOT             # 规划大纲
PLAN_VOLUME           # 规划分卷
PLAN_CHAPTER          # 规划章节
WRITE_CHAPTER         # 写章节正文
CONTINUE_CHAPTER      # 续写未完成章节
REVIEW_TEXT           # 评审文本
EDIT_TEXT             # 编辑文本
CHECK_CONTINUITY      # 检查一致性
UPDATE_CANON          # 修改 Canon
RETCON                # 推翻旧设定（Retcon）
RESUME_PROJECT        # 恢复长期未写项目
BRAINSTORM            # 头脑风暴
SUMMARIZE_STATE       # 总结当前状态
```

### 1.2 `task.scope` 枚举

```text
SNIPPET       # 片段
SCENE         # 场景
CHAPTER       # 单章
MULTI_CHAPTER # 多章
ARC           # 剧情线
VOLUME        # 分卷
PROJECT       # 整书
```

### 1.3 `task.mode` 枚举

| 模式 | 含义 | 适用场景 |
|------|------|----------|
| `FAST` | 最小流程，跳过非必要检查 | 灵感、低风险任务 |
| `STANDARD` | 标准流程，局部一致性检查 | 日常创作 |
| `STRICT` | 完整检查、审稿和状态更新 | 关键章节、卷末 |
| `ADVISORY` | 只提供建议，不修改正式文件 | 头脑风暴、试探 |

### 1.4 `authority.operation` 枚举

```text
READ_ONLY         # 只读
CREATE_DRAFT      # 创建草稿
EDIT_DRAFT        # 编辑草稿
PROPOSE_CHANGE    # 提出变更建议
COMMIT_STATE      # 提交状态变更（仅 continuity-keeper）
```

**权限层级**：

```
READ_ONLY < CREATE_DRAFT < EDIT_DRAFT < PROPOSE_CHANGE < COMMIT_STATE
```

---

## 2. 统一输出契约（SkillResult）

所有子 Skill 必须返回 `SkillResult`。

```yaml
skill_result:
  skill: string                # Skill 名称
  request_id: string           # 对应请求 ID
  status: enum                 # 执行状态

  summary: string              # 执行摘要

  deliverables:                # 交付物列表
    - type: string             # 交付物类型
      path: string | null      # 文件路径
      content_summary: string  # 内容摘要
      status: draft | confirmed | revised

  state_change_proposals:      # 状态变更建议
    - type: canon_candidate | state_update | deprecation | contradiction
      description: string
      evidence: string
      risk_level: low | medium | high
      requires_user_confirmation: boolean

  proposals:                   # 创作建议
    - description: string
      rationale: string
      impact_scope: string
      recommended: boolean

  issues:                      # 发现的问题
    - severity: info | warning | blocker
      category: string
      description: string
      affected_files: []
      suggested_resolution: string

  handoff:                     # 交接信息
    recommended_next_skill: string | null
    reason: string | null
    required_context: []

  completion:                  # 完成度
    criteria_met: []
    criteria_unmet: []
```

### 2.1 `status` 枚举

```text
COMPLETED              # 完全完成
COMPLETED_WITH_WARNINGS  # 完成但有警告
NEEDS_DECISION         # 需要用户决策
BLOCKED                # 被阻塞
FAILED                 # 失败
```

**重要**：`NEEDS_DECISION` 不代表任务完全停止。Skill 应尽可能完成低风险部分，同时把高风险部分列入 `pending_decisions.md`。

---

## 3. `novel-master` 路由决策流程

### 3.1 第一步：识别任务意图

`novel-master` 首先判断用户是在：

| 意图类别 | 典型表达 |
|----------|----------|
| 设计 | "帮我设计..."、"构思一个..." |
| 规划 | "写个大纲"、"规划下一卷" |
| 创作 | "写第12章"、"根据大纲写正文" |
| 续写 | "继续写"、"接上一章" |
| 评审 | "看看这章有什么问题"、"分析一下" |
| 修订 | "帮我改改"、"润色一下" |
| 检查一致性 | "有没有矛盾"、"检查设定" |
| 修改 Canon | "把设定改成..."、"推翻之前的..." |
| 恢复项目 | "继续之前的小说"、"上次那个..." |
| 头脑风暴 | "想想接下来怎么写"、"给我几个方向" |

**规则**：显式请求优先于推断。

- 用户说"不要改正文，只分析问题" → 必须路由到 `novel-reviewer`，不能调用 `novel-editor`
- 用户说"直接续写"，且已有完整章节卡 → 不重复调用 `chapter-planner`

### 3.2 第二步：判断项目阶段

```text
项目不存在
  → 新书初始化流程

项目存在但缺少高层结构
  → 故事设计流程

存在大纲但没有章节卡
  → 章节规划流程

已有章节卡
  → 正文创作流程

已有正文
  → 评审、修订或连续性流程
```

### 3.3 第三步：判断影响范围

| 影响范围 | 典型行为 | 需要的检查 |
|----------|----------|------------|
| 文本级 | 改句式、标点、描写 | 无需额外检查 |
| 场景级 | 调整冲突和信息顺序 | 局部一致性检查 |
| 章节级 | 修改章节结构和结果 | continuity-keeper 检查 |
| 剧情级 | 修改支线、人物关系、阶段目标 | reviewer 前置诊断 |
| 项目级 | 修改主线、世界规则或结局 | reviewer + 用户确认 |

影响范围越大，越需要：
- `novel-reviewer` 前置诊断
- `continuity-keeper` 影响分析
- 用户确认重大决策

### 3.4 第四步：判断是否涉及状态变更

出现以下情况时，任务完成后**必须**路由到 `continuity-keeper`：

- [ ] 创作了正式章节
- [ ] 修改了人物当前状态
- [ ] 新增了正式世界规则
- [ ] 推进了时间线
- [ ] 埋设或回收了伏笔
- [ ] 某人物获得新信息
- [ ] 道具发生转移或损毁
- [ ] 修改了已确认剧情
- [ ] 废弃了旧设定

**不更新状态的情况**：
- 单纯头脑风暴
- 只读评审
- 未采用的方案
- ADVISORY 模式下的试探

### 3.5 第五步：判断是否需要审稿

| 模式 | 审稿策略 |
|------|----------|
| `FAST` | 默认不调用 `novel-reviewer` |
| `STANDARD` | 重要章节或用户明确要求时调用 |
| `STRICT` | 正文完成后必须调用 |
| 卷末复盘 | 必须调用 |
| 大范围重构 | 修改前后都应调用 |

---

## 4. 总路由表

### 4.1 新书与设计任务

| 用户意图 | 主路由 | 后续处理 |
|----------|--------|----------|
| 从一个想法创建新书 | `novel-brief → story-architect` | 根据需要调用人物、世界和大纲设计 |
| 只有题材，没有明确方向 | `novel-brief` | 输出项目简报和待确认分歧 |
| 修改作品定位 | `novel-brief → continuity-keeper` | 分析对现有内容的影响 |
| 设计故事主线 | `story-architect` | 高风险变化交用户确认 |
| 设计结局方向 | `story-architect` | 作为 Proposal，不能静默确认 |
| 设计主角或反派 | `character-designer` | `continuity-keeper` 登记正式人物 |
| 设计人物关系 | `character-designer` | 重大关系变化需确认 |
| 设计世界观 | `world-builder` | 只设计剧情所需部分 |
| 设计力量体系 | `world-builder → continuity-keeper` | 检查规则完整性和冲突 |
| 生成整书大纲 | `story-architect → plot-planner` | `continuity-keeper` 记录已确认结构 |
| 生成分卷大纲 | `plot-planner` | 检查与总纲一致性 |

### 4.2 章节生产任务

| 用户意图 | 主路由 | 后续处理 |
|----------|--------|----------|
| 规划下一章 | `continuity-keeper → chapter-planner` | 获取当前状态后生成章节卡 |
| 根据大纲写一章 | `continuity-keeper → chapter-planner → chapter-writer` | 正文后更新状态 |
| 已有章节卡，直接写正文 | `continuity-keeper → chapter-writer` | 不重复生成章节卡 |
| 续写未完成章节 | `continuity-keeper → chapter-writer` | 保留当前场景状态 |
| 连续写多个章节 | `plot-planner → chapter-planner → chapter-writer` 循环 | 每章更新摘要，阶段结束后集中评审 |
| 根据一段剧情写场景 | `chapter-planner → chapter-writer` | 默认不提升为 Canon |
| 快速试写文风 | `chapter-writer`，`ADVISORY` 模式 | 不写入正式章节和状态 |

### 4.3 评审和修改任务

| 用户意图 | 主路由 | 后续处理 |
|----------|--------|----------|
| 分析章节问题，不修改 | `novel-reviewer` | 只生成评审报告 |
| 润色文字 | `novel-editor` L2 | 含义改变时调用状态检查 |
| 校对错字和标点 | `novel-editor` L1 | 通常不调用状态更新 |
| 调整场景节奏 | `novel-reviewer → novel-editor` L3 | 检查是否改变章节状态 |
| 修改章节剧情 | `novel-reviewer → chapter-planner → novel-editor` L4 | `continuity-keeper` 更新状态 |
| 重写整章 | `novel-reviewer → chapter-planner → chapter-writer` | 旧版标记为 Deprecated |
| 检查 AI 腔 | `novel-reviewer → novel-editor` L2 | 保留剧情和信息 |
| 卷末复盘 | `novel-reviewer → continuity-keeper → plot-planner` | 调整下一卷规划 |
| 全书结构评审 | `novel-reviewer → story-architect → plot-planner` | 修改前先做影响分析 |

### 4.4 连续性与设定任务

| 用户意图 | 主路由 | 后续处理 |
|----------|--------|----------|
| 检查前后矛盾 | `continuity-keeper` | 输出矛盾和解决方案 |
| 整理人物当前状态 | `continuity-keeper` | 更新 `character_state.md` |
| 整理时间线 | `continuity-keeper` | 更新 `timeline.md` |
| 整理伏笔 | `continuity-keeper` | 更新 `foreshadowing.md` |
| 总结已写剧情 | `continuity-keeper` | 生成章节或卷级摘要 |
| 从已有正文建立项目档案 | `continuity-keeper → story-architect` | 先抽取事实，再反推结构 |
| 修改既有 Canon | `continuity-keeper → 对应设计 Skill` | 用户确认后提交 |
| 推翻旧设定 | `continuity-keeper → novel-reviewer → 对应设计 Skill` | 分析受影响章节 |
| 恢复长期未写项目 | `continuity-keeper → novel-master` | 生成恢复上下文包 |

### 4.5 灵感和低风险任务

| 用户意图 | 路由 | 状态处理 |
|----------|------|----------|
| 提供几个情节方向 | `story-architect`，`ADVISORY` | 不写入 Canon |
| 提供人物名字 | `character-designer`，`FAST` | 不建立完整人物档案 |
| 提供世界设定灵感 | `world-builder`，`ADVISORY` | 作为 Proposal |
| 提供章节标题 | `chapter-planner`，`FAST` | 不更新状态 |
| 写一个非正式试验片段 | `chapter-writer`，`ADVISORY` | 不进入正式正文 |
| 讨论某个剧情是否合理 | `novel-reviewer` | 只读分析 |

---

## 5. 路由优先级规则

当一个请求可能匹配多个 Skill 时，按照以下优先级处理。

### 5.1 明确操作优先

用户明确说"只分析""不要修改"，则禁止进入编辑流程。

用户明确说"直接续写"，且已有完整章节卡，则不重复调用 `chapter-planner`。

### 5.2 连续性冲突优先

发现请求与 Canon 冲突时：

```text
continuity-keeper
  → 输出冲突和影响范围
  → novel-master 决定是否进入修改流程
```

不得由 `chapter-writer` 自行解释或覆盖冲突。

### 5.3 上游依赖优先

如果章节写作缺少必要前提：

```text
没有章节目标
  → chapter-planner

没有可执行大纲
  → plot-planner

没有故事主线
  → story-architect

连作品定位都不明确
  → novel-brief
```

但上游 Skill 只补齐必要部分，不自动执行整套新书初始化。

### 5.4 评审与修改分离

默认流程：

```text
发现问题
  → novel-reviewer

执行修改
  → novel-editor / chapter-writer
```

除非任务只是明确的低风险校对，否则不应让修改 Skill 自行完成全面评审。

### 5.5 最小路由原则

不要为了显示流程完整而调用无关 Skill。

例如：

> "把这句话写得更自然。"

只需直接处理或调用轻量编辑模式，不需要：

```text
novel-brief
→ story-architect
→ continuity-keeper
→ novel-editor
```

---

## 6. 用户意图识别指南

### 6.1 模糊请求处理

| 用户表达 | 可能意图 | novel-master 应对 |
|----------|----------|-------------------|
| "这章感觉平" | 节奏问题/冲突不足 | 先调用 novel-reviewer 诊断 |
| "帮我改改" | 范围不明 | 默认 L2 编辑，询问用户是否涉及剧情 |
| "主角太弱" | 设定/写作/剧情 | 先问：是能力设定问题还是表现问题？ |
| "接下来怎么写" | 灵感/规划 | 进入 ADVISORY 模式，提供方向 |
| "这个设定合理吗" | 一致性检查 | 调用 continuity-keeper 检查 |
| "帮我续写" | 正文创作 | 检查是否有章节卡，有则直接写 |

### 6.2 确认策略

| 风险等级 | 确认方式 | 示例 |
|----------|----------|------|
| 高风险 | 必须显式确认 | "确认修改结局吗？这将影响后续10章。" |
| 中风险 | 说明影响后默认执行 | "将修改第12章，影响后续3章。继续吗？" |
| 低风险 | 直接执行，报告结果 | "已润色文字，未改变剧情。" |

---

## 7. `continuity-keeper` 上下文包契约

在章节规划、写作和修改前，`continuity-keeper` 应生成最小上下文包。

```yaml
context_pack:
  project_snapshot:
    title: string              # 作品名
    genre: string              # 题材
    current_volume: string     # 当前卷
    current_chapter: string    # 当前章节
    current_story_phase: string # 当前故事阶段

  current_state:
    time: string               # 当前时间
    location: string           # 当前地点
    active_conflict: string    # 当前冲突
    protagonist_goal: string   # 主角当前目标

  relevant_characters:         # 相关人物（最多5个）
    - name: string
      current_status: string   # 当前状态
      current_goal: string     # 当前目标
      known_information: []    # 已知信息
      relationship_changes: [] # 关系变化

  relevant_canon:              # 相关 Canon（最多10条）
    - id: string
      statement: string

  active_open_loops:           # 活跃伏笔（最多5个）
    - id: string
      description: string
      urgency: string          # 紧急程度

  active_foreshadowing:        # 活跃预示（最多5个）
    - id: string
      status: planted | reinforced | partially_revealed
      usage_constraint: string

  timeline_constraints: []     # 时间线约束

  prohibited_conflicts:        # 禁止出现的冲突
    - description: string

  style_constraints: []        # 风格约束

  source_refs: []              # 来源引用
```

**大小限制**：上下文包不超过 **2000 字**。超过时只保留高优先级信息。

---

## 8. 子 Skill 契约

### 8.1 `novel-brief`

**职责**：将模糊创意转化为明确的作品定义。

**触发条件**：
- 创建新小说
- 修改作品定位
- 题材明确但读者体验不明确
- 用户对自己想写什么仍比较模糊

**输入**：

```yaml
required:
  user_request: string

optional:
  platform: string
  genre: string
  target_length: string
  target_reader: string
  reference_preferences: []
  exclusions: []
  existing_project_brief: file
```

**输出**：

```yaml
deliverables:
  - project_brief

project_brief:
  genre: string                # 题材
  subgenre: string             # 子题材
  target_reader: string        # 目标读者
  target_platform: string | null  # 目标平台
  core_hook: string            # 核心卖点
  protagonist_promise: string  # 主角承诺
  primary_conflict: string     # 主要冲突
  intended_reader_experience: []  # 预期读者体验
  length_and_pacing: string    # 篇幅与节奏
  creative_constraints: []     # 创作约束
  exclusions: []               # 排除项
  unresolved_decisions: []     # 待确认问题
```

**可写文件**：`project_brief.md`

**禁止事项**：
- 写完整大纲
- 设计详细世界观
- 直接写正文
- 声称作品一定能成为爆款
- 擅自确定结局和人物命运

**完成标准**：
- 能用一句话说明作品是什么
- 能说明目标读者获得什么体验
- 能区分已确认项与待确认项
- 没有将低置信度推断写成事实

**默认后继 Skill**：`story-architect`

---

### 8.2 `story-architect`

**职责**：设计小说的高层故事结构。

**触发条件**：
- 设计主线
- 设计故事阶段
- 设计核心冲突
- 调整故事方向
- 设计高潮和结局方向

**输入**：

```yaml
required:
  project_brief: file

optional:
  existing_architecture: file
  current_canon: file
  existing_outline: file
  user_story_ideas: []
```

**输出**：

```yaml
story_architecture:
  premise: string              # 故事命题
  thematic_question: string    # 主题问题
  protagonist_core_desire: string  # 主角核心欲望
  central_opposition: string   # 主要阻力
  story_promise: string        # 故事承诺
  causal_chain: []             # 因果链
  major_phases: []             # 主要阶段
  major_turning_points: []     # 重大转折
  climax_direction: string     # 高潮方向
  ending_direction: string     # 结局方向
  main_subplots: []            # 主要支线
  structural_risks: []         # 结构性风险
```

**可写文件**：
- `architecture/story_architecture.md`
- `architecture/themes.md`
- `architecture/story_promises.md`

**禁止事项**：
- 细化所有章节
- 编写正式正文
- 用结构模型强制套用所有作品
- 静默改变已确认的结局
- 替人物设计 Skill 完成全部人物档案

**完成标准**：
- 主角目标、阻力和后果形成因果链
- 故事各阶段不是事件堆砌
- 高层结构能够被 `plot-planner` 继续拆解
- 重大方向变化已经标记为 Proposal

**默认后继 Skill**：`character-designer`、`world-builder`、`plot-planner`

---

### 8.3 `character-designer`

**职责**：设计人物、人物弧和人物关系。

**输入**：

```yaml
required:
  project_brief: file
  story_architecture: file

optional:
  existing_characters: []
  existing_relationship_map: file
  canon: file
  role_requirement: string
```

**输出**：

```yaml
character_profile:
  identity:
    name: string
    role: string
    age: string | null

  narrative_function: string   # 叙事功能
  external_goal: string        # 外在目标
  internal_need: string        # 内在需求
  fear: string                 # 恐惧
  flaw: string                 # 缺陷
  strengths: []                # 优点
  behavioral_logic: string     # 行为逻辑
  moral_boundary: string       # 道德边界
  secrets: []                  # 秘密
  knowledge_state: []          # 知识状态
  voice_characteristics: []    # 声音特征
  relationships: []            # 关系
  arc:
    starting_state: string     # 起始状态
    pressure_points: []        # 压力点
    possible_change: string    # 可能变化
    ending_state: string | null  # 结束状态
  canon_candidates: []        # Canon 候选
```

**可写文件**：
- `characters/*.md`
- `characters/relationship_map.md`

**禁止事项**：
- 擅自改变主线
- 擅自决定主要人物死亡
- 为了弧光强行修改结局
- 创造与剧情无关的大量人物
- 把"人物应该如此"当成已经发生的事实

**完成标准**：
- 人物有可解释的行动逻辑
- 人物目标与主线发生关系
- 主要人物之间存在合作、冲突或资源依赖
- 人物声音具有一定区分度
- Canon 候选已经单独列出

**默认后继 Skill**：`plot-planner`、`continuity-keeper`

---

### 8.4 `world-builder`

**职责**：设计剧情需要的世界规则。

**输入**：

```yaml
required:
  project_brief: file
  story_architecture: file

optional:
  character_requirements: []
  plot_requirements: []
  existing_world_files: []
  canon: file
```

**输出**：

```yaml
world_design:
  core_world_rules: []         # 核心世界规则
  social_structure: []         # 社会结构
  factions: []                 # 势力
  locations: []                # 地点
  resources_and_economy: []    # 资源与经济
  technology_or_power_system:  # 技术或力量体系
    source: string             # 来源
    capabilities: []           # 能力
    costs: []                  # 代价
    limits: []                 # 限制
    counters: []               # 反制
    progression: []            # 成长
  terminology: []              # 术语
  unresolved_rules: []         # 未解决规则
  contradiction_risks: []      # 矛盾风险
```

**可写文件**：`world/*.md`

**禁止事项**：
- 无限扩展设定
- 添加与剧情无关的百科内容
- 设计没有代价和限制的能力
- 静默修改正文已经使用的规则
- 让世界设定替代人物冲突

**完成标准**：
- 每项核心设定能够服务剧情
- 能力具有来源、能力、代价、限制和反制方式
- 世界规则内部不存在明显矛盾
- 新规则已经标记为 Canon 候选或 Proposal

**默认后继 Skill**：`plot-planner`、`continuity-keeper`

---

### 8.5 `plot-planner`

**职责**：把故事架构转化为主线、支线和卷级规划。

**输入**：

```yaml
required:
  story_architecture: file
  relevant_characters: []
  relevant_world_rules: []

optional:
  existing_outline: file
  current_story_state: file
  open_loops: file
  foreshadowing: file
  target_volume_length: string
```

**输出**：

```yaml
plot_plan:
  scope: project | volume | arc
  start_state: string          # 起始状态
  end_state: string            # 结束状态
  phase_goal: string           # 阶段目标
  main_conflict: string        # 主要冲突
  event_chain:                 # 事件链
    - event: string
      cause: string
      consequence: string
      next_pressure: string
  subplot_movements: []        # 支线推进
  character_progression: []    # 人物进展
  reveals: []                  # 信息揭示
  foreshadowing_actions: []    # 预示行动
  escalation_curve: []         # 升级曲线
  climax: string               # 高潮
  transition_to_next_phase: string  # 过渡
  risks: []                    # 风险
```

**可写文件**：
- `outline/master_outline.md`
- `outline/volume_*.md`
- `outline/subplot_tracker.md`

**禁止事项**：
- 直接写正式章节
- 依赖巧合解决关键冲突
- 为反转而破坏人物动机
- 擅自新增核心人物和世界规则
- 把大纲中的可能性当成已经发生的事实

**完成标准**：
- 事件之间有明确因果
- 每个阶段都改变故事状态
- 主线和支线不会长期互不相关
- 高潮来自前期累积，而不是突然出现
- 可以继续拆解为章节计划

**默认后继 Skill**：`chapter-planner`

---

### 8.6 `chapter-planner`

**职责**：把剧情节点转化为可执行的章节卡。

**输入**：

```yaml
required:
  plot_segment: file
  context_pack: object

optional:
  previous_chapter_summary: string
  previous_chapter_ending: string
  target_word_count: string
  chapter_function: string
```

**输出**：

```yaml
chapter_plan:
  chapter_id: string
  chapter_function: string     # 章节功能
  viewpoint_character: string  # 视角人物
  time_and_location: string    # 时间地点

  opening_state:               # 开场状态
    character_goal: string
    emotional_state: string
    immediate_problem: string

  scenes:                      # 场景列表
    - scene_id: string
      goal: string
      conflict: string
      action: string
      information_revealed: []
      state_change: string
      transition: string

  required_elements: []        # 必须包含的元素
  prohibited_reveals: []       # 禁止提前揭示的信息
  active_foreshadowing: []     # 活跃预示
  chapter_climax: string       # 章节高潮

  ending_state:                # 结束状态
    physical_state: string
    relationship_state: string
    knowledge_change: string
    new_problem: string

  continuity_risks: []         # 连续性风险
```

**可写文件**：`chapters/plans/chapter_*.md`

**禁止事项**：
- 修改总纲
- 新增未经授权的世界规则
- 擅自改变人物长期目标
- 写大量正式正文
- 为每章机械添加悬念断章

**完成标准**：
- 本章具有明确作用
- 章节开始和结束状态不同
- 每个场景存在目标、阻力和结果
- 信息揭示符合人物知情范围
- `chapter-writer` 无需猜测核心剧情方向

**默认后继 Skill**：`chapter-writer`

---

### 8.7 `chapter-writer`

**职责**：根据章节卡创作正式正文。

**输入**：

```yaml
required:
  chapter_plan: file
  context_pack: object

optional:
  previous_chapter_ending: string
  style_guide: file
  reference_excerpt_from_same_project: string
  target_word_count: string
```

**输出**：

```yaml
chapter_draft:
  chapter_id: string
  title: string | null
  body: string                 # 正文内容

chapter_report:
  executed_plan_items: []      # 已执行的计划项
  deviations_from_plan: []     # 偏离计划的内容
  new_facts_introduced: []     # 新增事实
  character_state_changes: []  # 人物状态变化
  timeline_changes: []         # 时间线变化
  knowledge_changes: []        # 知识变化
  foreshadowing_changes: []    # 预示变化
  possible_continuity_risks: []  # 可能的连续性风险
```

**可写文件**：`chapters/drafts/chapter_*.md`

**禁止事项**：
- 修改总纲
- 擅自新增核心能力
- 擅自改变主要人物命运
- 把临时细节直接写入 Canon
- 遇到计划问题时静默改写故事方向
- 模仿特定在世作者的可识别文风

**完成标准**：
- 正文执行章节卡的核心目标
- 视角和时间保持稳定
- 人物行为符合当前目标和认知
- 章末状态清晰
- 所有新增事实和偏离计划之处已经报告

**默认后继 Skill**：
- `novel-reviewer`（严格模式下）
- `continuity-keeper`（所有正式正文模式下）

---

### 8.8 `novel-reviewer`

**职责**：只读诊断作品问题，不修改正文。

**输入**：

```yaml
required:
  review_target: file | text
  review_scope: string

optional:
  project_brief: file
  story_architecture: file
  chapter_plan: file
  context_pack: object
  requested_dimensions: []
```

**输出**：

```yaml
review_report:
  overall_assessment: string   # 总体评估

  confirmed_issues:            # 确认的问题
    - category: string
      severity: string
      evidence: string
      impact: string
      recommended_action: string

  potential_risks: []          # 潜在风险
  preference_based_suggestions: []  # 基于偏好的建议
  strengths_to_preserve: []    # 需要保留的优点
  continuity_flags: []         # 连续性标记
  recommended_edit_level: L1 | L2 | L3 | L4
  recommended_next_skill: string
```

**可写文件**：`reviews/*.md`

**禁止事项**：
- 直接重写正文
- 把个人审美包装成客观错误
- 只给出笼统评价
- 为追求爽点忽视作品定位
- 声称作品必然成功或失败

**完成标准**：
- 问题有明确证据
- 区分事实问题、潜在风险和审美偏好
- 每个重要问题都有可执行建议
- 明确推荐修改层级

**默认后继 Skill**：`novel-editor`、`chapter-planner`、`plot-planner`、`story-architect`

---

### 8.9 `novel-editor`

**职责**：按明确授权修改已有正文。

**编辑等级**：

| 等级 | 修改范围 | 典型操作 |
|------|----------|----------|
| `L1` | 错字、标点、格式和病句 | 修正错别字、统一标点 |
| `L2` | 句式、描写、对话和文风 | 优化句子、增强描写 |
| `L3` | 场景节奏、冲突和信息顺序 | 调整场景顺序、增强冲突 |
| `L4` | 章节结构、剧情和人物关系 | 修改场景、调整剧情 |

**输入**：

```yaml
required:
  source_text: file | text
  edit_level: L1 | L2 | L3 | L4
  edit_objectives: []

optional:
  review_report: file
  chapter_plan: file
  context_pack: object
  must_preserve: []
  style_guide: file
```

**输出**：

```yaml
edited_text:
  body: string                 # 修改后的正文

edit_report:
  edit_level: string
  changes_made: []             # 修改内容
  preserved_elements: []       # 保留的元素
  meaning_changes: []          # 含义变化
  plot_changes: []             # 剧情变化
  new_facts_introduced: []     # 新增事实
  state_changes: []            # 状态变化
  continuity_risks: []         # 连续性风险
```

**可写文件**：
- 修订后的 `chapters/drafts/*.md`
- 旧版应保留版本或标记 Deprecated

**禁止事项**：
- 超出授权等级修改
- 在 L1/L2 中改变剧情
- 在 L3 中改变整卷结构
- 在没有影响分析时执行 L4
- 静默删除重要伏笔
- 不说明重大修改

**完成标准**：
- 所有修改均符合授权等级
- 必须保留的内容没有被破坏
- 所有剧情和事实变化都已列出
- 修改结果可以交给 `continuity-keeper` 更新状态

**默认后继 Skill**：`continuity-keeper`

---

### 8.10 `continuity-keeper`

**职责**：管理项目事实、时间线和连续性，是状态系统唯一正式写入者。

**运行模式**：

```text
EXTRACT_CONTEXT      # 提取上下文包
CHECK_CONTRADICTIONS # 检查矛盾
COMMIT_CHAPTER_STATE # 提交章节状态
COMMIT_CANON         # 提交 Canon 变更
IMPACT_ANALYSIS      # 影响分析
GENERATE_SUMMARY     # 生成摘要
RESTORE_PROJECT      # 恢复项目
```

**输入**：

```yaml
required:
  operation_mode: string
  source_material: []
  current_state_files: []

optional:
  state_change_proposals: []
  user_confirmed_decisions: []
  target_chapter: string
  affected_scope: string
```

**输出**：

```yaml
continuity_result:
  context_pack: object | null  # 上下文包

  contradictions:              # 矛盾列表
    - id: string
      description: string
      evidence_a: string
      evidence_b: string
      severity: string
      resolution_options: []

  committed_updates:           # 已提交的更新
    canon: []
    timeline: []
    character_state: []
    knowledge_state: []
    foreshadowing: []
    open_loops: []
    chapter_summaries: []

  pending_updates: []          # 待处理的更新
  deprecated_items: []         # 废弃项
  impact_analysis: []          # 影响分析
```

**可写文件**：
- `state/canon.md`
- `state/timeline.md`
- `state/character_state.md`
- `state/chapter_summaries.md`
- `state/foreshadowing.md`
- `state/open_loops.md`
- `state/knowledge_state.md`
- `state/contradictions.md`

**禁止事项**：
- 创造剧情
- 为解决矛盾而擅自改写正文
- 把 Proposal 自动提交为 Canon
- 删除冲突记录以假装问题不存在
- 在没有证据时推断人物已经知道某事
- 承担故事审美评审工作

**完成标准**：
- 所有状态更新都有来源
- Canon、Proposal 和 Deprecated 明确区分
- 时间线和人物状态可以被后续章节读取
- 冲突没有被静默覆盖
- 上下文包保持最小且任务相关

**默认后继 Skill**：由 `novel-master` 根据任务决定

---

## 9. 典型组合工作流

### 9.1 新书初始化

```text
novel-master
  → novel-brief
  → story-architect
  → character-designer（可与 world-builder 并行）
  → world-builder
  → plot-planner
  → continuity-keeper
```

**最终交付**：
- 项目简报
- 故事架构
- 主要人物
- 必要世界规则
- 主线或首卷大纲
- 初始 Canon

### 9.2 标准单章创作

```text
novel-master
  → continuity-keeper / EXTRACT_CONTEXT
  → chapter-planner
  → chapter-writer
  → continuity-keeper / COMMIT_CHAPTER_STATE
```

适合日常创作。

### 9.3 严格单章创作

```text
novel-master
  → continuity-keeper / EXTRACT_CONTEXT
  → chapter-planner
  → chapter-writer
  → novel-reviewer
  → 必要时 novel-editor
  → continuity-keeper / COMMIT_CHAPTER_STATE
```

适合：
- 关键转折章
- 高潮章
- 新卷开篇
- 重要人物登场
- 重大伏笔回收

### 9.4 章节局部润色

```text
novel-master
  → novel-editor L1/L2
  → 如果含义未改变：结束
  → 如果含义改变：continuity-keeper
```

### 9.5 章节结构修改

```text
novel-master
  → novel-reviewer
  → continuity-keeper / IMPACT_ANALYSIS
  → chapter-planner
  → novel-editor L4 或 chapter-writer
  → continuity-keeper / COMMIT_CHAPTER_STATE
```

### 9.6 大纲重构

```text
novel-master
  → novel-reviewer
  → continuity-keeper / IMPACT_ANALYSIS
  → story-architect
  → plot-planner
  → 用户确认重大变化
  → continuity-keeper / COMMIT_CANON
```

已经完成的章节不自动重写，而是生成受影响章节列表。

### 9.7 断更后恢复创作

```text
novel-master
  → continuity-keeper / RESTORE_PROJECT
  → 输出：
      当前故事状态
      主要人物状态
      最近剧情摘要
      未解决冲突
      活跃伏笔
      下一阶段大纲
  → chapter-planner
```

---

## 10. 路由异常处理

### 10.1 缺少项目文件

处理顺序：

1. 读取现有正文或用户提供的信息
2. 让 `continuity-keeper` 抽取最小状态
3. 缺少的信息标记为 Unknown
4. 继续完成不会造成重大偏差的部分
5. **不伪造缺失的前文设定**

### 10.2 两份资料互相冲突

必须输出：

```yaml
status: NEEDS_DECISION

issues:
  - severity: blocker
    category: canon_conflict
    description: 两份人物档案对主角年龄定义不一致
    affected_files:
      - characters/protagonist.md
      - state/canon.md
    suggested_resolution: 选择其中一个版本，另一个标记为 Deprecated
```

在用户未决定前，可以继续处理与该冲突无关的部分。

### 10.3 子 Skill 试图越权

例如 `chapter-writer` 输出了结局修改建议。

`novel-master` 应将该内容降级为 Proposal：

```yaml
proposals:
  - description: 建议将当前结局改为开放式结局
    source_skill: chapter-writer
    requires_user_confirmation: true
```

不得直接进入 Canon。

### 10.4 修改范围不明确

`novel-master` 应采用最低安全权限：

```text
"帮我优化这一章"
默认解释为：
  novel-reviewer
  → novel-editor L2

不默认进入 L3 或 L4。
```

如果问题只有修改剧情才能解决，应先报告问题和建议，而不是静默扩大权限。

### 10.5 路由死循环

如果 Skill 调用链超过 **5 层嵌套**，`novel-master` 应强制终止，输出：

```yaml
status: FAILED
issues:
  - severity: blocker
    category: routing_loop
    description: 检测到路由死循环
    affected_files: [...]
    suggested_resolution: 检查 Skill 的 handoff 逻辑，避免循环调用
```

---

## 11. `novel-master` 自身输出契约

完成整个工作流后，`novel-master` 应向用户输出统一结果。

```yaml
master_result:
  request_summary: string       # 请求摘要
  route_executed:               # 执行的路由
    - skill: string
      purpose: string
      status: string

  deliverables:                 # 交付物
    - name: string
      path: string
      summary: string

  confirmed_changes: []         # 已确认的变更
  pending_decisions: []         # 待决策事项
  warnings: []                  # 警告
  recommended_next_action: string | null  # 推荐下一步
```

**面向用户的结果应回答**：

1. 本次完成了什么
2. 使用了哪些流程
3. 哪些内容已经正式生效
4. 哪些仍然只是建议
5. 是否发现矛盾或风险
6. 下一步最自然的工作是什么

**不得向用户倾倒所有内部路由日志**。

---

## 12. 文档维护说明

| 文档 | 职责 | 读者 |
|------|------|------|
| `craft-1.md` | 架构总纲、设计原则、关键决策、落地路径 | 架构师、产品经理 |
| `craft-2.md`（本文档） | 契约参考、路由表、输入输出格式 | Skill 开发者、测试人员 |

**修改规则**：
- 高层设计原则变更 → 修改 craft-1.md
- 路由逻辑、输入输出格式变更 → 修改 craft-2.md
- 避免在两个文档中重复描述同一内容
