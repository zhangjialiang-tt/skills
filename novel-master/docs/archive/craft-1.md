# novel-master 架构总纲

> 本文档是 novel-master Skill 组的高层架构设计，定义系统目标、设计原则、关键决策和落地路径。
> 详细契约参考见 [craft-2.md](./craft-2.md)。

---

## 1. 术语表

| 术语 | 定义 | 示例 |
|------|------|------|
| **Canon** | 已确认、后续必须遵守的正式事实 | "主角出生于临海城"、"魔法消耗精神力" |
| **Proposal** | AI 提出但尚未确认的建议 | "建议反派提前两章登场" |
| **Deprecated** | 已废弃或被新版本取代的内容 | "旧版设定中主角有哥哥" |
| **状态** | 人物/时间线/道具/信息的当前情况 | "主角当前位于基地，左臂受伤" |
| **设定** | 世界观规则、背景、力量体系 | "能力冷却时间为24小时" |
| **上下文包** | continuity-keeper 生成的最小任务上下文 | 包含当前时间、地点、人物状态等 |
| **Skill** | 完成单一职责的专业模块 | chapter-writer、continuity-keeper |
| **编排器** | novel-master 本身，负责路由和协调 | 不直接执行专业任务 |

---

## 2. 系统目标

`novel-master` 是小说创作 Skill 组的总控编排器。

**它不直接承担**：
- 故事设计
- 人物设计
- 章节写作
- 审稿
- 状态管理

**它只负责**：
1. 识别用户当前任务
2. 判断任务范围和风险
3. 选择最小必要的子 Skill
4. 组织 Skill 调用顺序
5. 管理上下文交接
6. 控制 Canon 修改权限
7. 确保状态变更被正确记录
8. 向用户汇总结果和待决策事项

---

## 3. 整体架构

### 3.1 三层架构

```text
novel-master
│
├─ 创作设计层
│  ├─ novel-brief        # 明确作品定位和创作约束
│  ├─ story-architect    # 设计高层故事结构
│  ├─ character-designer # 设计人物和人物关系
│  └─ world-builder      # 设计世界规则和设定
│
├─ 内容生产层
│  ├─ plot-planner       # 规划主线、支线、卷级剧情
│  ├─ chapter-planner    # 将剧情节点拆成章节执行计划
│  └─ chapter-writer     # 根据章节计划创作正文
│
└─ 质量与治理层
   ├─ continuity-keeper  # 管理 Canon、时间线、伏笔和项目状态
   ├─ novel-editor       # 按授权范围修改已有正文
   └─ novel-reviewer     # 只读诊断剧情和文本问题
```

### 3.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个 Skill 只做一件事，用一句话能说清职责 |
| **最小上下文** | 每个 Skill 只读取完成任务所需的最少信息 |
| **提案与确认分离** | Proposal 不等于 Canon，重大变更必须用户确认 |
| **审稿与修改分离** | reviewer 诊断问题，editor 执行修改 |
| **状态单一写入** | 只有 continuity-keeper 能正式更新 Canon |
| **最小路由** | 简单任务不触发完整工作流 |

---

## 4. 关键设计决策记录

### 决策1：Canon 单一写入者模型

**背景**：多 Skill 协作时，如果都能修改状态，容易产生冲突和不一致。

**选项**：
- A. 多写入者 + 冲突检测（复杂，需要锁机制）
- B. 单一写入者 continuity-keeper（简单，中心化）
- C. 用户每次确认所有状态变更（用户负担重）

**选择**：B

**理由**：
- 降低 Skill 间耦合，避免循环依赖
- 用户只需在重大决策时介入，日常创作自动进行
- continuity-keeper 职责明确，易于测试

**风险**：
- continuity-keeper 成为单点瓶颈
- 如果 continuity-keeper 误判，会影响全局

**缓解**：
- continuity-keeper 只读分析时可以并行执行
- 所有关键操作记录到 `workflow/change_log.md`
- 用户可以标记 continuity-keeper 的判断为"误报"

---

### 决策2：chapter-writer 不能修改 Canon

**背景**：写作过程中可能临时产生新设定（如"主角突然想起童年往事"）。

**选项**：
- A. chapter-writer 可以直接写入 Canon（灵活但混乱）
- B. chapter-writer 只能输出 Proposal，由 continuity-keeper 审核（严格但安全）
- C. 所有新设定必须用户确认（最安全但最慢）

**选择**：B

**理由**：
- 防止写作 Skill 暗中成为"故事导演"
- continuity-keeper 可以检查新设定与现有 Canon 的冲突
- 用户可以在关键节点批量确认 Proposal

**风险**：
- 如果 continuity-keeper 过于严格，可能阻碍创作流畅性
- 作者可能忘记确认 Proposal，导致设定悬而未决

**缓解**：
- 区分"核心 Canon"和"场景细节"，后者可以自动确认
- 定期提醒用户检查 `workflow/pending_decisions.md`

---

### 决策3：V1 合并部分 Skill

**背景**：完整架构包含 10 个子 Skill，但第一版不需要全部实现。

**合并策略**：

| 完整 Skill | V1 临时归属 | 拆分信号 |
|------------|-------------|----------|
| `character-designer` | `story-architect` 的人物设计模式 | 人物档案超过 10 个，或关系复杂 |
| `world-builder` | `story-architect` 的世界设计模式 | 世界规则频繁冲突 |
| `plot-planner` | `story-architect` 的大纲规划模式 | 大纲任务过重，提示词超过 500 行 |
| `novel-editor` | `chapter-writer` 的修订模式 | 写作和修订职责冲突 |

**理由**：
- 减少 V1 实现负担
- 通过实际运行发现职责冲突，再针对性拆分
- 避免过度设计

---

## 5. 权限模型

### 5.1 三类信息状态

| 状态 | 定义 | 后续 Skill 如何处理 |
|------|------|---------------------|
| **Canon** | 已确认的正式事实 | 必须遵守 |
| **Proposal** | AI 提出但未确认的建议 | 不得当作事实 |
| **Deprecated** | 已废弃的内容 | 只能用于版本追踪，不能重新进入正文 |

### 5.2 重大创作决策清单

以下内容属于高风险决策，子 Skill 可以提出，但不能直接提交为 Canon：

- 主角核心人格改变
- 主要人物死亡、背叛或退场
- 感情关系发生根本变化
- 主线目标改变
- 结局方向改变
- 核心世界规则改变
- 叙事视角整体改变
- 已完成剧情被推翻
- 作品主题或价值立场改变
- 大量已写章节需要返工

### 5.3 Canon 写入权限

```
┌─────────────────────────────────────────────────────────┐
│  只有 continuity-keeper 可以正式修改 state/ 目录中的文件  │
└─────────────────────────────────────────────────────────┘
```

其他子 Skill 只能输出：

```yaml
state_change_proposals:
  - type: canon_candidate
    description: 主角首次获得危险感知能力
    source: chapter_012
    confidence: high
```

---

## 6. 项目目录结构

```text
novel-project/
├─ project_brief.md           # 项目简报
├─ style_guide.md             # 风格指南
│
├─ architecture/              # 故事架构
│  ├─ story_architecture.md
│  ├─ themes.md
│  └─ story_promises.md
│
├─ characters/                # 人物档案
│  ├─ protagonist.md
│  ├─ antagonist.md
│  ├─ supporting_cast.md
│  └─ relationship_map.md
│
├─ world/                     # 世界设定
│  ├─ world_overview.md
│  ├─ factions.md
│  ├─ power_system.md
│  ├─ locations.md
│  └─ glossary.md
│
├─ outline/                   # 大纲
│  ├─ master_outline.md
│  ├─ volume_01.md
│  ├─ volume_02.md
│  └─ subplot_tracker.md
│
├─ chapters/                  # 章节
│  ├─ plans/                  # 章节卡
│  │  ├─ chapter_001.md
│  │  └─ chapter_002.md
│  └─ drafts/                 # 正文草稿
│     ├─ chapter_001.md
│     └─ chapter_002.md
│
├─ reviews/                   # 评审报告
│  ├─ chapter_001_review.md
│  └─ volume_01_review.md
│
├─ state/                     # 项目状态（continuity-keeper 专属）
│  ├─ canon.md
│  ├─ timeline.md
│  ├─ character_state.md
│  ├─ chapter_summaries.md
│  ├─ foreshadowing.md
│  ├─ open_loops.md
│  ├─ knowledge_state.md
│  └─ contradictions.md
│
└─ workflow/                  # 工作流日志
   ├─ route_log.md
   ├─ pending_decisions.md
   └─ change_log.md
```

### 文件所有权

| 文件区域 | 主要负责人 | 其他 Skill 权限 |
|----------|-----------|----------------|
| `project_brief.md` | `novel-brief` | 只读或提交修改建议 |
| `architecture/` | `story-architect` | 提交 Proposal |
| `characters/` | `character-designer` | 提交人物状态建议 |
| `world/` | `world-builder` | 提交设定建议 |
| `outline/` | `plot-planner` | `chapter-planner` 只读 |
| `chapters/plans/` | `chapter-planner` | `chapter-writer` 只读 |
| `chapters/drafts/` | `chapter-writer`、`novel-editor` | 其他 Skill 只读 |
| `reviews/` | `novel-reviewer` | 只读 |
| `state/` | `continuity-keeper` | **禁止直接写入** |
| `workflow/` | `novel-master` | 子 Skill 可提交状态 |

---

## 7. V1 最小落地组合

### 7.1 V1 Skill 列表

第一版先实现 6 个核心 Skill：

```text
novel-master         # 编排器
novel-brief          # 项目定义
story-architect      # 故事设计（合并人物、世界、大纲）
chapter-planner      # 章节规划
chapter-writer       # 正文写作（合并编辑模式）
novel-reviewer       # 评审诊断
continuity-keeper    # 状态管理
```

### 7.2 V1 实施计划

#### 阶段1：契约先行（1-2天）

- [ ] 定义 TaskEnvelope 和 SkillResult 的 JSON Schema
- [ ] 定义项目目录模板
- [ ] 编写 3 个最小测试用例（初始化、单章创作、冲突检测）

#### 阶段2：核心 Skill 实现（3-5天）

- [ ] 实现 `continuity-keeper` 的 EXTRACT_CONTEXT 模式
- [ ] 实现 `chapter-planner`
- [ ] 实现 `chapter-writer`
- [ ] 实现 `novel-master` 路由（仅支持单章创作流程）

#### 阶段3：集成测试（2-3天）

- [ ] 测试"从大纲到正文"完整流程
- [ ] 测试 Canon 冲突检测
- [ ] 测试上下文包是否最小且完整
- [ ] 测试 Proposal 不会被错误提升为 Canon

#### 阶段4：用户测试（2-3天）

- [ ] 用真实小说项目测试
- [ ] 收集用户反馈
- [ ] 记录职责冲突信号

### 7.3 拆分判断标准

出现以下信号时，从 `story-architect` 拆出独立 Skill：

| 信号 | 阈值 | 拆分动作 |
|------|------|----------|
| story-architect 提示词行数 | > 500 行 | 拆出 character-designer |
| 人物档案数量 | > 10 个 | 拆出 character-designer |
| 世界规则数量 | > 20 条 | 拆出 world-builder |
| 大纲中事件数量 | > 50 个 | 拆出 plot-planner |
| 写作任务频繁被修订需求打断 | 每周 > 3 次 | 拆出 novel-editor |

---

## 8. 性能约束

### 8.1 上下文包大小限制

- `context_pack` 不超过 **2000 字**
- 超过时只保留"当前章节直接相关"的内容
- 其余信息通过"需要时读取"机制按需加载

### 8.2 状态文件分卷

- 每 **50 章** 生成一个 `state/summary_volume_XX.md`
- 早期章节的详细状态归档，只保留摘要
- continuity-keeper 维护"当前活跃状态"和"历史归档"两层

### 8.3 增量更新

- continuity-keeper 只输出变更部分，不重复已有状态
- chapter-writer 只报告新增事实，不重复已知信息
- 路由日志只记录关键决策，不记录完整上下文

---

## 9. 失败模式与降级策略

| 失败场景 | 检测方式 | 降级策略 |
|----------|----------|----------|
| continuity-keeper 误报冲突 | 用户反馈 | 允许用户标记为"误报"，记录到 `contradictions.md` |
| 上下文包超过 token 限制 | 字数统计 | 只保留高优先级信息，其余标记为"需手动查阅" |
| 项目文件损坏 | 启动时校验 | 从 `chapter_summaries.md` 和 `canon.md` 重建最小状态 |
| 用户要求推翻大量 Canon | 影响分析 | 生成"影响范围报告"，分批执行而非一次性修改 |
| Skill 执行超时 | 超时机制 | 返回已完成部分，标记未完成任务，用户可选择重试 |
| 路由死循环 | 调用深度限制 | 超过 5 层嵌套调用时强制终止，报告循环路径 |

---

## 10. 测试策略

### 10.1 单元测试（每个 Skill 独立）

| Skill | 测试内容 | 预期结果 |
|-------|----------|----------|
| `novel-brief` | 输入模糊创意 | 输出区分"已确认"和"待确认" |
| `story-architect` | 输入项目简报 | 输出包含因果链的故事架构 |
| `chapter-planner` | 输入大纲片段 | 输出章节卡，包含场景和状态变化 |
| `chapter-writer` | 输入章节卡 | 输出正文和 chapter_report |
| `continuity-keeper` | 输入矛盾 Canon | 正确标记冲突，不自动修复 |
| `novel-reviewer` | 输入问题章节 | 输出区分"事实问题"和"审美偏好" |
| `novel-editor` | 输入原文和编辑等级 | 不超出授权等级修改 |

### 10.2 集成测试（Skill 组合）

| 测试用例 | 流程 | 验证点 |
|----------|------|--------|
| 新书初始化 | brief → architect → continuity-keeper | 生成完整项目结构 |
| 单章创作 | continuity-keeper → planner → writer → continuity-keeper | 状态正确更新 |
| Canon 冲突检测 | 故意制造冲突 | continuity-keeper 拦截并报告 |
| Proposal 隔离 | writer 产生新设定 | 不会自动成为 Canon |
| 路由异常 | 缺少必要文件 | 优雅降级，不伪造信息 |

### 10.3 回归测试

- 固定测试用例集，每次修改 Skill 后自动运行
- 特别关注：Proposal 是否被错误提升为 Canon
- 关注：简单任务是否触发了不必要的工作流

---

## 11. 验收标准

整套 Skill 组达到以下条件，才算边界设计合格：

- [ ] `novel-master` 不直接生成专业交付物
- [ ] 每个子 Skill 能用一句话说明职责
- [ ] 每个子 Skill 有明确输入、输出和禁止事项
- [ ] 每个文件区域有唯一主要负责人
- [ ] 只有 `continuity-keeper` 能正式更新 Canon
- [ ] Proposal 不会被后续 Skill 当成事实
- [ ] 审稿和修改默认分离
- [ ] 简单任务不会触发完整工作流
- [ ] 正式章节完成后会更新项目状态
- [ ] 重大结构变化会先进行影响分析
- [ ] 缺少上下文时不会伪造前文
- [ ] 任一产物都能追踪其来源和变更原因
- [ ] 子 Skill 可以独立测试
- [ ] 路由流程可以通过固定案例回归验证
- [ ] 上下文包大小不超过 2000 字
- [ ] 失败时有明确的降级策略

---

## 12. 后续扩展（非 V1）

以下能力不属于小说创作内核，后续可作为外围 Skill 添加：

### 小说运营系统
- `market-researcher`：市场分析
- `platform-adapter`：平台适配
- `publishing-manager`：发布管理

### IP 改编系统
- `novel-adapter`：小说改编
- `script-writer`：剧本写作
- `storyboard-designer`：分镜设计

三个系统可以交换资料，但不要混成一个 Skill 包。

---

## 13. 核心设计原则摘要

```text
novel-master 负责路由，不负责专业创作。

设计、规划、写作、审稿、修改、状态管理相互分离。

所有子 Skill 使用统一 TaskEnvelope 和 SkillResult。

Canon 采用单一写入者模型。

创作 Skill 只能提出状态变更，不直接提交状态。

审稿负责诊断，编辑负责执行。

路由采用最小必要原则。

风险越高，越需要影响分析和用户决策。

正式创作依赖最小上下文包，而不是读取整个项目。

每次创作完成后，必须明确新增事实和状态变化。

失败时有明确的降级策略，不会静默损坏项目。
```
