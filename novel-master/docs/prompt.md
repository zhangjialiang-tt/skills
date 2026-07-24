# `novel-master` V1 实施层补充与最小骨架建设 Prompt

## 1. 任务背景

当前项目已经完成两份冻结基线文档：

- `novel-master-architecture-v1.0.1-frozen.md`
- `novel-master-contracts-v1.0.1-frozen.md`

这两份文档定义了：

- `novel-master` 的 1 个编排器 + 6 个子 Skill 架构。
- 子 Skill 的职责、模式、文件所有权和输入输出契约。
- Canon、Proposal、Deprecated、Unknown 状态。
- 章节生命周期。
- `ApprovalRef`。
- `ChangeSet`。
- `ContextPack`。
- 路由规则、权限模型和风险分级。
- 状态单一写入者模型。
- 分阶段实施和测试策略。

本次任务不是重新设计架构，也不是修改冻结契约，而是：

> 基于冻结文档补充实施层规范，创建可供后续开发使用的目录骨架、共享规范、Schema、模板、辅助脚本框架和最小回归样例。

---

# 2. 输入文件

必须先完整阅读：

```text
novel-master-architecture-v1.0.1-frozen.md
novel-master-contracts-v1.0.1-frozen.md
```

如果项目中存在以下文件，也应先阅读：

```text
AGENTS.md
CONTEXT.md
README.md
已有 Skill 编写规范
已有测试约定
```

冻结文档是本任务的上位规范。

如果实现要求与冻结文档发生冲突：

1. 不得静默选择。
2. 不得直接修改冻结文档。
3. 将冲突记录到实施说明中的“待决策项”。
4. 采用最小、可逆、不会破坏冻结契约的实现方式。

---

# 3. 总体目标

完成以下四类工作：

1. 创建实施说明文档。
2. 创建 Skill 组目录和共享 reference 骨架。
3. 创建契约 Schema 和辅助脚本骨架。
4. 建立最小可运行的单章创作闭环结构和回归样例。

本次不要求一次性完成全部业务 Skill 的成熟提示词，也不要求实现所有复杂功能。

---

# 4. 严格边界

## 4.1 不允许修改

不得修改或覆盖：

```text
novel-master-architecture-v1.0.1-frozen.md
novel-master-contracts-v1.0.1-frozen.md
```

不得直接创建新的冻结版本。

如发现问题，只记录到：

```text
docs/implementation-known-issues.md
```

---

## 4.2 不允许扩展架构

不得：

- 新增子 Skill。
- 改变 1+6 架构。
- 拆分 `story-architect`。
- 拆分 `chapter-writer / EDIT`。
- 增加市场研究、平台运营、封面、漫剧或发布能力。
- 引入跨项目共享世界观。
- 修改 Canon 单一写入者模型。
- 绕过章节接受闸门。
- 绕过 `ApprovalRef` 或 `ChangeSet`。

---

## 4.3 不允许用提示词假装实现确定性能力

以下能力必须由脚本或校验逻辑承担，不得仅依赖 Skill 自我约束：

- JSON Schema 校验。
- 项目路径越界校验。
- 文件所有权校验。
- revision 和 hash 计算。
- stale context 校验。
- `ApprovalRef` 有效性校验。
- `ChangeSet` 提交流程。
- Canon 删除拦截。
- 多文件状态写入回滚。
- 单项目写锁。

如果当前阶段只创建脚本骨架，必须明确标注未实现，不得声称已具备完整事务能力。

---

# 5. 先进行能力调查

在创建文件前，先检查当前运行环境和仓库，输出简短调查结论：

```text
- 当前 Skill 使用平台或目标平台。
- Skill 是否支持直接调用其他 Skill。
- 是否支持执行 Python 或 Node 脚本。
- 是否支持项目文件读写。
- 是否已有 Skill 模板。
- 是否已有 JSON Schema 或测试框架。
- 是否已有统一的命令入口。
```

将调查结论写入：

```text
docs/novel-master-implementation-guide-v1.md
```

如果平台能力无法确认，采用以下默认假设：

```text
- Skill 本身负责语义推理与生成。
- Python 脚本负责确定性验证和文件操作。
- novel-master 通过工作流说明编排子 Skill。
- 子 Skill 不假设平台原生支持互相调用。
```

---

# 6. 目标目录结构

基于仓库现有约定调整具体顶层路径，但目标结构应等价于：

```text
novel-master/
├─ SKILL.md
├─ references/
│  ├─ common-rules.md
│  ├─ routing-table.md
│  ├─ file-ownership.md
│  ├─ fact-extraction-rules.md
│  ├─ error-codes.md
│  ├─ style-guide-template.md
│  ├─ context-retrieval-rules.md
│  └─ lifecycle-and-approval.md
│
├─ schemas/
│  ├─ task-envelope.schema.json
│  ├─ skill-result.schema.json
│  ├─ approval-ref.schema.json
│  ├─ changeset.schema.json
│  ├─ context-pack.schema.json
│  ├─ master-result.schema.json
│  └─ recovery-report.schema.json
│
├─ scripts/
│  ├─ validate_contract.py
│  ├─ validate_paths.py
│  ├─ compute_revision.py
│  ├─ validate_approval.py
│  ├─ project_lock.py
│  └─ commit_changeset.py
│
├─ templates/
│  └─ novel-project/
│     ├─ project.yaml
│     ├─ project_brief.md
│     ├─ style_guide.md
│     ├─ architecture/
│     ├─ characters/
│     ├─ world/
│     ├─ outline/
│     ├─ chapters/
│     │  ├─ plans/
│     │  └─ drafts/
│     ├─ reviews/
│     ├─ state/
│     │  └─ archives/
│     └─ workflow/
│        ├─ runs/
│        ├─ approvals/
│        ├─ changesets/
│        ├─ backups/
│        ├─ route_log.md
│        ├─ pending_decisions.md
│        └─ change_log.md
│
├─ examples/
│  ├─ valid/
│  └─ invalid/
│
└─ tests/
   ├─ test_schemas.py
   ├─ test_paths.py
   ├─ test_approval.py
   ├─ test_lifecycle.py
   └─ test_changeset.py

novel-brief/
└─ SKILL.md

story-architect/
└─ SKILL.md

chapter-planner/
└─ SKILL.md

chapter-writer/
└─ SKILL.md

novel-reviewer/
└─ SKILL.md

continuity-keeper/
└─ SKILL.md

docs/
├─ novel-master-implementation-guide-v1.md
├─ implementation-known-issues.md
└─ implementation-progress.md
```

如果仓库已有统一的 Skill 目录，遵循仓库现有规范，不重复创建无意义的顶层目录。

---

# 7. 实施说明文档

创建：

```text
docs/novel-master-implementation-guide-v1.md
```

文档至少包含以下章节。

## 7.1 运行模型

说明：

- Skill 与脚本的职责边界。
- `novel-master` 如何路由。
- 子 Skill 是否由平台直接调用，还是通过主 Agent 串行执行。
- 机器协议和用户可见输出如何分离。

采用原则：

```text
LLM 负责语义判断和创作。
脚本负责确定性校验和文件事务。
```

---

## 7.2 机器输出与用户输出分离

明确规定：

### 用户可见输出

只显示：

- 本次完成内容。
- 当前章节生命周期。
- 已确认变化。
- 待确认事项。
- 风险和阻塞项。
- 下一步。

### 机器协议输出

保存到：

```text
workflow/runs/<request_id>/
```

包括：

```text
task-envelope.yaml
route-plan.yaml
step-XX-result.yaml
master-result.yaml
diagnostics.log
```

不得默认把完整 `TaskEnvelope` 和 `SkillResult` 倾倒给用户。

---

## 7.3 文件版本策略

明确：

- revision 的格式。
- hash 使用 SHA-256。
- 文件变化时如何更新 revision。
- 如何校验 stale context。
- 是否依赖 Git。
- 不依赖 Git 时如何维护内部 revision。

推荐默认：

```text
revision = 单调递增整数或 ISO 时间戳 + 短 hash
content_hash = SHA-256
```

---

## 7.4 单项目写锁

设计：

```text
workflow/.write.lock
```

至少记录：

```yaml
request_id: string
created_at: string
process_id: string | null
```

定义：

- 获取锁。
- 检测陈旧锁。
- 释放锁。
- 写入失败时清理。
- 同一项目同一时间只允许一个状态写事务。

---

## 7.5 ChangeSet 简化实现

说明 V1 本地文件系统事务不是数据库级全局原子事务。

推荐流程：

```text
1. 校验锁
2. 校验 base revision/hash
3. 创建 PREPARED ChangeSet
4. 备份原文件
5. 写入 *.tmp
6. 校验临时文件
7. 使用 os.replace 替换正式文件
8. 更新 revision/hash
9. 更新 change_log
10. 标记 COMMITTED
```

失败时：

```text
- 从 backups 恢复。
- 标记 ROLLED_BACK。
- 回滚失败则标记 ROLLBACK_FAILED。
- 禁止继续后继写操作。
```

不得声称多文件替换在所有平台上绝对原子。

---

## 7.6 ApprovalRef 生成规则

明确：

- 子 Skill 不得自行创建用户授权。
- 只有 `novel-master` 或授权脚本可以生成 `ApprovalRef`。
- 必须基于用户明确确认。
- 必须绑定 revision/hash。
- 高风险审批不可由模糊积极反馈代替。

明确区分：

```text
“可以，按这个执行” → 可视为明确批准
“这个方向不错” → 不构成批准
“先看看” → 不构成批准
“继续” → 只批准当前明确步骤
“你决定” → 只能生成范围受限的授权
```

---

## 7.7 自动接受策略

V1 默认：

```yaml
auto_accept:
  enabled: false
```

可以保留接口，但首个实现不默认启用。

自动接受必须在以下情况中止：

- 存在 HIGH 风险计划偏离。
- 存在 Canon 冲突。
- 新增核心能力或世界规则。
- 主要人物死亡、退场或根本关系变化。
- Reviewer 返回 blocker。
- 关键上下文为 UNKNOWN。
- revision 已变化。
- 章节计划核心目标未完成。

---

## 7.8 已知限制

至少记录：

- Skill 平台是否原生支持 Skill 间调用。
- 多文件事务只能通过备份和恢复近似实现。
- 文风质量需要人工评估。
- 最小上下文包可能遗漏远距离隐含约束。
- V1 暂不支持跨项目读取。
- V1 暂不开放自动日更默认授权。
- V1 不实现完整 Retcon 自动重写。

---

# 8. 共享 reference 内容要求

## 8.1 `common-rules.md`

只保留所有子 Skill 都需要的最小规则：

- Canon/Proposal/Deprecated/Unknown。
- 不得静默扩大范围。
- 不得伪造缺失上下文。
- 重大决策归用户。
- 输出新增事实候选。
- 只写所属区域。
- 显式只读优先。
- 所有正式产物带来源和 revision。

不要复制整份冻结契约。

---

## 8.2 `routing-table.md`

把冻结文档中的路由表整理成紧凑、可测试的规则。

至少包含：

- 显式只读。
- 新书初始化。
- 章节规划。
- 默认章节写作。
- 严格章节写作。
- 章节修订。
- Canon 修改。
- 冲突检查。
- 断更恢复。
- 低风险 Advisory。

每条规则建议采用：

```yaml
- route_id: WRITE_CHAPTER_WITH_PLAN
  when:
    task_type: WRITE_CHAPTER
    chapter_plan_exists: true
  steps:
    - skill: continuity-keeper
      mode: EXTRACT_CONTEXT
    - skill: chapter-writer
      mode: WRITE
  approval_gate: ACCEPT_CHAPTER
  state_commit:
    after: ACCEPTED
```

---

## 8.3 `file-ownership.md`

列出每个 Skill：

- 可读区域。
- 可写区域。
- 禁止区域。
- 跨区域时的拆分规则。

该文件必须与路径校验脚本保持一致。

---

## 8.4 `fact-extraction-rules.md`

定义哪些内容应进入状态候选。

必须提取：

- 人物位置、伤势、资源和能力变化。
- 人物关系变化。
- 人物知情范围变化。
- 关键道具获得、转移和损毁。
- 明确时间推进。
- 世界规则首次确认。
- 伏笔埋设、强化、揭露和回收。
- 开放循环新增或关闭。
- 后续必须保持一致的身份或限制。

默认不提取：

- 一次性氛围描写。
- 普通动作。
- 无后续意义的普通物件。
- 修辞性描述。
- 可自由变化的环境细节。
- 没有跨场景影响的微小动作。

---

## 8.5 `error-codes.md`

建立统一错误码，至少包括：

```text
INVALID_SKILL_MODE
PATH_OUTSIDE_PROJECT
OWNERSHIP_VIOLATION
SCHEMA_INVALID
STALE_CONTEXT
INVALID_APPROVAL
LIFECYCLE_VIOLATION
CANON_CONFLICT
WRITE_LOCKED
CHANGESET_INVALID
ROLLBACK_FAILED
UNKNOWN_REQUIRED_CONTEXT
```

每个错误码说明：

- 对应状态。
- 含义。
- 是否可重试。
- 推荐恢复动作。

不得让子 Skill 自由发明错误码。

---

## 8.6 `context-retrieval-rules.md`

上下文提取不得只依赖关键词。

至少结合：

```text
当前章节涉及人物
当前地点
当前卷/剧情线
章节卡 required_elements
active_open_loops
active_foreshadowing
knowledge_state
最近 2～3 章摘要
相关 Canon
style_guide
```

定义 `retrieval_trace`：

```yaml
retrieval_trace:
  queried_entities: []
  queried_story_threads: []
  searched_files: []
  omitted_due_to_budget: []
```

---

## 8.7 `style-guide-template.md`

至少定义：

- 叙事视角。
- 叙事距离。
- 句式节奏。
- 描写密度。
- 对话规则。
- 角色声音。
- 信息说明策略。
- 章节目标字数。
- Hook 原则。
- 回顾策略。
- 常见 AI 腔规避项。

不得固化某一题材的风格。

---

# 9. Schema 实现要求

根据冻结契约实现 JSON Schema。

必须覆盖：

```text
TaskEnvelope
SkillResult
ApprovalRef
ChangeSet
ContextPack
MasterResult
RecoveryReport
```

要求：

1. 使用 JSON Schema Draft 2020-12，除非仓库已有其他规范。
2. 必填字段与冻结文档一致。
3. 枚举值与冻结文档一致。
4. 设置 `additionalProperties` 策略。
5. 对条件权限使用 `if/then/else` 或等价机制。
6. 对 `COMMIT_STATE` 目标 Skill 进行条件校验。
7. 对章节生命周期进行枚举校验。
8. 对 `COMMIT_CHAPTER_STATE` 的来源状态限制为 `ACCEPTED | PUBLISHED`。
9. 保留冻结契约中明确要求的兼容字段。
10. 不擅自删除旧字段。

至少提供：

```text
examples/valid/
examples/invalid/
```

合法和非法样例。

---

# 10. 辅助脚本要求

Python 优先，除非仓库已有统一语言。

## 10.1 `validate_contract.py`

功能：

- 加载指定 Schema。
- 校验 YAML 或 JSON 文件。
- 输出清晰错误路径。
- 返回非零退出码。
- 不修改输入文件。

---

## 10.2 `validate_paths.py`

功能：

- 确认路径位于 `root_path` 内。
- 防止 `..`、符号链接和路径规范化逃逸。
- 校验目标路径是否属于目标 Skill 所有权区域。
- 检测跨项目访问。

---

## 10.3 `compute_revision.py`

功能：

- 计算 SHA-256。
- 读取或生成 revision。
- 内容变化时更新 revision。
- 内容未变化时不递增。
- 输出结构化结果。

---

## 10.4 `validate_approval.py`

功能：

- 校验状态是否 ACTIVE。
- 校验 operation。
- 校验 scope。
- 校验 revision/hash。
- 校验一次性授权是否已使用。
- 输出 `INVALID_APPROVAL` 具体原因。

---

## 10.5 `project_lock.py`

功能：

- 获取锁。
- 释放锁。
- 检测锁归属。
- 检测超时或陈旧锁。
- 不自动删除仍可能有效的锁。
- 提供 `--force`，但必须记录操作理由。

---

## 10.6 `commit_changeset.py`

第一版实现最小安全版本：

- 只允许修改 `state/` 和 `workflow/change_log.md`。
- 先校验 Schema、路径、锁、revision 和 ApprovalRef。
- 创建备份。
- 写临时文件。
- 校验临时结果。
- 原子替换单文件。
- 多文件失败时尝试恢复全部备份。
- 记录 ChangeSet 状态。
- Canon 项不允许通过 DELETE 移除。
- 不声称具备数据库事务级保证。

---

# 11. 各 Skill.md 的实现要求

本次只创建**可执行骨架**，不要写成超长提示词。

每个 `SKILL.md` 应包含：

```text
名称
职责
何时触发
何时不触发
激活模式
必需输入
允许读取
允许写入
操作步骤
禁止事项
输出
完成标准
阻塞条件
相关 references
```

---

## 11.1 `novel-master/SKILL.md`

只负责：

- 意图识别。
- 项目定位。
- 权限判定。
- 风险推导。
- 路由。
- Approval Gate。
- 结果汇总。

禁止直接生成：

- 项目简报。
- 故事架构。
- 人物档案。
- 世界设定。
- 章节卡。
- 正文。
- 评审报告。
- Canon 更新。

---

## 11.2 子 Skill

本次至少为六个子 Skill 创建边界清晰的骨架。

不要把完整冻结文档复制进去。

通过 references 引用共享规则。

尤其注意：

- `story-architect` 一次只能激活一个模式。
- `chapter-writer / WRITE` 输出必须是 DRAFT。
- `chapter-writer` 不得修改 Canon。
- `novel-reviewer` 不得修改评审对象。
- `continuity-keeper` 是 `state/` 唯一写入者。
- `COMMIT_CHAPTER_STATE` 只接受 ACCEPTED/PUBLISHED。
- `READ_ONLY` 与派生报告权限按细粒度权限执行。

---

# 12. 首个最小闭环

本次只要求结构上支持以下闭环：

```text
已有项目与大纲
→ continuity-keeper / EXTRACT_CONTEXT
→ chapter-planner
→ chapter-writer / WRITE
→ 章节状态 DRAFT
→ 用户人工接受
→ 章节状态 ACCEPTED
→ continuity-keeper / COMMIT_CHAPTER_STATE
```

必须明确：

- `WRITE` 后不得自动提交状态。
- 人工接受必须绑定当前 revision/hash。
- 接受后才允许生成和执行 ChangeSet。
- 状态提交必须增量更新。
- stale revision 必须阻塞。

本次不要求完整实现：

- 自动接受。
- L3/L4 编辑。
- Retcon。
- 两阶段恢复。
- 自动归档。
- 多项目并发。
- 跨项目检索。

可以创建接口和占位说明，但不得声称完成。

---

# 13. 测试要求

## 13.1 Schema 测试

至少覆盖：

1. 合法 TaskEnvelope。
2. 缺少 request_id。
3. 非法枚举。
4. COMMIT_STATE 指向非 continuity-keeper。
5. READ_ONLY 试图修改状态。
6. 非 ACCEPTED 章节提交状态。
7. ApprovalRef revision 不匹配。
8. 路径越出项目根目录。
9. Skill 写入非所有权区域。
10. Proposal 出现在 committed_updates。

---

## 13.2 生命周期测试

至少覆盖：

```text
PLANNED → DRAFT
DRAFT → REVIEWED
DRAFT → ACCEPTED
REVIEWED → DRAFT
REVIEWED → ACCEPTED
ACCEPTED → SUPERSEDED
ACCEPTED → DEPRECATED
ACCEPTED → PUBLISHED
```

并确认未列出的状态转换被拒绝。

---

## 13.3 ChangeSet 测试

至少覆盖：

- 正常提交。
- revision 过期。
- 临时文件校验失败。
- 第二个文件替换失败后的恢复。
- Canon DELETE 被拒绝。
- change_log 更新失败后的回滚。
- 无锁提交被拒绝。
- 锁被其他 request 占用。

---

## 13.4 Skill 回归样例

至少创建以下 prompt regression 样例：

1. 用户要求“只分析”，不得修改源文件和状态。
2. 用户要求“不要修改任何东西”，不得保存评审报告。
3. Writer 不得把 DRAFT 直接提交状态。
4. Writer 发现大纲与 Canon 冲突时返回 NEEDS_DECISION。
5. Reviewer 只诊断，不重写正文。
6. Story Architect 未声明模式时拒绝。
7. Story Architect 声明多个模式时拒绝。
8. L2 润色不得改变事实。
9. 章节中出现普通杯子，不应默认提取为状态候选。
10. 人物得知关键秘密，应提取为 knowledge state 变化。

---

# 14. 文档和代码质量要求

- 路径、文件名、字段名使用冻结文档中的标准命名。
- 代码包含合理类型标注。
- 代码包含明确错误处理。
- 不引入不必要依赖。
- 优先使用标准库。
- YAML 依赖如有必要，应记录安装方式。
- 不生成伪造测试结果。
- 未实现能力使用 `TODO` 和明确说明。
- 不使用“已完成事务安全”等未经测试的表述。
- 不为未来能力过度设计复杂框架。

---

# 15. 执行顺序

按照以下顺序工作：

```text
1. 阅读冻结文档和仓库规范
2. 调查当前平台和仓库能力
3. 创建实施说明
4. 创建目录骨架
5. 创建共享 references
6. 创建 JSON Schema
7. 创建合法/非法样例
8. 创建辅助脚本
9. 创建 Skill.md 骨架
10. 创建项目模板
11. 创建测试
12. 运行测试
13. 修复问题
14. 输出实施报告
```

不要先写六个完整 Skill，再补 Schema 和脚本。

---

# 16. 完成标准

任务完成必须满足：

- [ ] 未修改两份冻结文档。
- [ ] 创建实施说明。
- [ ] 创建目标目录骨架。
- [ ] 创建所有要求的 reference 文件。
- [ ] 创建七类 Schema。
- [ ] 创建合法和非法样例。
- [ ] 创建辅助脚本骨架或实现。
- [ ] 创建 1+6 Skill.md 骨架。
- [ ] 创建小说项目模板。
- [ ] 创建最小单章闭环说明。
- [ ] 创建并运行基础测试。
- [ ] 真实报告测试 PASS/FAIL。
- [ ] 未完成项明确列出。
- [ ] 没有声称实现未验证能力。

---

# 17. 最终输出

完成后提供：

## 17.1 文件变更清单

列出：

```text
新增文件
修改文件
未修改的冻结文件
```

## 17.2 实施摘要

说明：

- 实现了哪些内容。
- 哪些是完整实现。
- 哪些只是骨架。
- 哪些能力推迟到后续阶段。

## 17.3 测试结果

提供实际执行命令和真实结果：

```text
PASS
FAIL
SKIPPED
```

禁止只写“测试应该通过”。

## 17.4 已知限制

列出：

- 平台限制。
- 事务限制。
- 未实现模式。
- 仍需用户决策的内容。

## 17.5 下一步建议

只推荐一个最自然的下一步：

> 完成并验证“已有大纲 → 章节卡 → DRAFT → 人工 ACCEPT → 增量状态提交”的首个端到端真实用例。
