你的需求本质上不是“把文档放进目录”，而是解决三个连续问题：

1. **阅读负担**：AI 生成的文档过长，用户每次都要重新理解。
2. **事实漂移**：文档内容随着开发变化，但旧结论仍然存在，难以判断哪个有效。
3. **注意力污染**：草稿、当前版本、历史版本、参考材料混在一起，持续占用认知资源。

因此，这个 Skill 更准确的定位应当是：

> **AI Agent 文档资产与注意力管理器**
> 负责将 AI 生成的长文档转化为可快速理解、可追踪状态、可安全归档的工程资产。

我建议将它命名为：

# `doc-steward`

中文可以称为：**文档管家**或**文档资产治理 Skill**。

它不负责替代其他 Agent 编写 PRD、设计文档或实施计划，而是负责管理这些文档生成之后的生命周期。

---

## 一、Skill 的核心目标

`doc-steward` 应当实现四个核心能力。

### 1. 建立单一阅读入口

用户不应该每次都打开五六份长文档确认项目状态。

Skill 应自动生成一个简短的入口文档，例如：

```text
docs/DOCS_DASHBOARD.md
```

内容只回答：

- 当前正在做什么
- 哪些文档是当前有效版本
- 最近发生了什么变化
- 哪些文档需要用户关注
- 哪些结论已经冻结
- 哪些文档已经失效或归档

用户日常主要阅读这个入口，而不是遍历整个 `docs/`。

---

### 2. 对长文档提供分层阅读

对于每份长文档，Skill 不应只生成一个普通摘要，而应提供四层阅读视图。

#### L0：状态卡片

十几秒内看完：

```markdown
## SYSTEM_DESIGN.md

- 状态：ACTIVE
- 当前版本：r7
- 最后有效更新：2026-07-28
- 用途：描述系统架构及组件边界
- 本轮变化：新增文档生命周期管理组件
- 是否需要关注：是
- 阅读建议：仅阅读 3.2、4.1 和 7.3
```

#### L1：执行摘要

控制在约 300～500 字，说明：

- 文档解决什么问题
- 核心结论是什么
- 对当前开发有什么影响
- 还有什么未决问题

#### L2：变化摘要

只描述相对于上一版本：

- 新增了什么
- 删除了什么
- 修改了什么
- 哪些结论被推翻
- 哪些接口、约束或计划发生变化

#### L3：原始全文

需要深入研究时才阅读。

这能够解决“每次修改以后重新阅读整份文档”的问题。

---

### 3. 管理文档状态和版本

仅依赖 Git 历史是不够的。Git 能告诉你文件发生过变化，但不能告诉你：

- 这个文档现在是否有效
- 是否被另一份文档替代
- 是否已经冻结
- 是否只是研究草稿
- 是否仍然约束当前实现

因此，每份受管理文档都需要明确状态。

推荐生命周期：

```text
DRAFT
  ↓
REVIEWING
  ↓
ACTIVE
  ↓
FROZEN
  ↓
SUPERSEDED
  ↓
ARCHIVED
```

各状态含义如下。

### `DRAFT`

正在生成或讨论，不能作为实现依据。

### `REVIEWING`

内容基本完成，但存在待确认问题。

### `ACTIVE`

当前有效，可以指导开发，但允许继续修改。

### `FROZEN`

已确认的阶段基线。未经显式决策不得修改。

### `SUPERSEDED`

内容曾经有效，但已经被新的文档或版本替代。

### `ARCHIVED`

仅保留历史价值，不应继续参与当前上下文。

这里最关键的是：

> **旧文档失效时不能只是“放着不管”，必须明确标记由什么替代。**

---

## 二、文档身份和元数据

建议每份受管理的 Markdown 文档包含统一 Front Matter：

```yaml
---
doc_id: DOC-SYSTEM-DESIGN
title: System Design
doc_type: system_design

status: ACTIVE
revision: 7

created_at: 2026-07-25
updated_at: 2026-07-28

owner: architecture-agent
source_of_truth: true

supersedes:
  - DOC-SYSTEM-DESIGN@r6

superseded_by: null

depends_on:
  - DOC-PRODUCT-REPOSITIONING@r3
  - DOC-SCHEMA-CONTRACTS@r4

related_docs:
  - DOC-IMPLEMENTATION-PLAN
  - DOC-TEST-STRATEGY

attention:
  level: high
  reason: "本轮修改改变了组件职责边界"

summary_ref: .doc-steward/summaries/DOC-SYSTEM-DESIGN-r7.md
---
```

其中需要重点区分三个概念。

### 逻辑文档身份

```yaml
doc_id: DOC-SYSTEM-DESIGN
```

无论文件修改多少次，逻辑身份保持不变。

### 文档修订版本

```yaml
revision: 7
```

表示同一逻辑文档的第七次受管理修订。

### 生命周期状态

```yaml
status: ACTIVE
```

版本号增加不等于状态发生变化，二者必须分开管理。

---

## 三、Skill 应管理的核心对象

不要把所有文件都纳入重型治理。建议只管理以下对象：

### 正式文档

例如：

- PRD
- 定界文档
- 系统设计
- Schema Contract
- 实施计划
- 测试策略
- ADR
- 阶段诊断报告
- 冻结基线

### 临时文档

例如：

- 评审报告
- 调研材料
- AI 生成的分析草稿
- 问题调查记录
- 方案比较

临时文档也可以登记，但默认不能成为事实来源。

### 派生文档

由 Skill 自动生成：

- 状态面板
- 阅读摘要
- 版本变化摘要
- 文档依赖关系
- 待处理问题
- 归档清单

派生文档必须可以重新生成，不应被视为事实源。

---

## 四、Skill 的核心操作

Skill 不需要一开始实现复杂的数据库，最小版本只需支持七种操作。

## 1. `register`

将新生成的文档纳入管理。

执行内容：

- 判断文档类型
- 分配稳定 `doc_id`
- 添加元数据
- 生成 L0/L1 摘要
- 登记到文档索引
- 标记默认状态为 `DRAFT`

---

## 2. `sync`

分析文档内容和仓库变化，刷新状态。

执行内容：

- 找出新增或修改的文档
- 比较当前内容和上一修订
- 生成变化摘要
- 检查引用关系
- 检查状态是否可能过期
- 更新总览面板

这是最常用的操作。

---

## 3. `focus`

生成当前需要用户关注的最小阅读集。

例如：

```markdown
# 当前关注

## 必须阅读

1. PRODUCT_REPOSITIONING.md
   - 原因：产品边界发生变化
   - 阅读章节：2、4、6

2. SYSTEM_DESIGN.md
   - 原因：新增 DocumentRegistry
   - 阅读章节：3.2、5.1

## 只需了解变化

- IMPLEMENTATION_PLAN.md
- TEST_STRATEGY.md

## 本轮无需阅读

- SCHEMA_CONTRACTS.md
- prd-review-flow.md
```

`focus` 是控制注意力分散的关键，而不仅仅是总结。

---

## 4. `promote`

改变文档状态，例如：

```text
DRAFT → REVIEWING
REVIEWING → ACTIVE
ACTIVE → FROZEN
```

状态晋升不能仅因为 Agent 声称“已完成”。

至少需要记录：

```yaml
decision:
  by: user
  at: 2026-07-28
  reason: "产品边界已经确认"
```

对于关键状态，最好要求用户明确批准。

---

## 5. `supersede`

声明旧文档被新文档替代。

例如：

```text
旧版 PRODUCT_REPOSITIONING.md
    ↓ superseded_by
新版 PRODUCT_REPOSITIONING.md
```

Skill 应同时完成：

- 新文档声明 `supersedes`
- 旧文档标记 `SUPERSEDED`
- 从当前阅读入口移除旧文档
- 保留历史引用
- 检查是否有其他 ACTIVE 文档仍依赖旧版本

---

## 6. `archive`

将不再参与当前开发的文档移出活跃上下文。

归档不是简单移动文件，应生成归档记录：

```yaml
archive_reason: "C1 阶段已经关闭"
archived_at: 2026-07-28
last_status: FROZEN
replacement: DOC-C2-IMPLEMENTATION-PLAN
```

建议的目录结构：

```text
docs/
├── DOCS_DASHBOARD.md
├── active/
├── reference/
└── archive/
    └── 2026/
        └── c1/
```

不过，不必强制修改现有项目结构。Skill 可以通过注册表实现逻辑归档。

---

## 7. `query`

允许用户通过自然语言查询文档状态，例如：

- 当前有效的系统设计是哪份？
- 哪些文档仍然依赖旧 PRD？
- 上次修改实施计划时改变了什么？
- 哪些文档已经超过两周没有同步？
- 哪些结论还没有被正式确认？
- 当前我只需要阅读哪三份文档？

这比让用户自己在目录中检索有效得多。

---

# 五、建议的文件结构

MVP 阶段可以采用纯文件方案：

```text
project/
├── docs/
│   ├── DOCS_DASHBOARD.md
│   ├── PRODUCT_REPOSITIONING.md
│   ├── SYSTEM_DESIGN.md
│   └── IMPLEMENTATION_PLAN.md
│
└── .doc-steward/
    ├── registry.yaml
    ├── state.json
    ├── summaries/
    │   ├── DOC-SYSTEM-DESIGN-r7.md
    │   └── DOC-IMPLEMENTATION-PLAN-r4.md
    ├── diffs/
    │   └── DOC-SYSTEM-DESIGN-r6-to-r7.md
    ├── snapshots/
    │   └── DOC-SYSTEM-DESIGN/
    │       └── r6.md
    └── archive-log.yaml
```

### `registry.yaml`

记录文档身份、位置和状态：

```yaml
documents:
  DOC-PRODUCT-REPOSITIONING:
    path: docs/PRODUCT_REPOSITIONING.md
    type: boundary
    status: FROZEN
    revision: 3

  DOC-SYSTEM-DESIGN:
    path: docs/SYSTEM_DESIGN.md
    type: system_design
    status: ACTIVE
    revision: 7
```

### `state.json`

用于记录文件哈希、最近同步时间和工具内部状态，不要求用户直接阅读。

---

# 六、完整工作流

建议采用下面的闭环。

```text
AI Agent 生成或修改文档
        ↓
doc-steward 检测变化
        ↓
识别逻辑文档身份和文档类型
        ↓
生成快照与版本差异
        ↓
生成 L0 状态卡、L1 摘要、L2 变化摘要
        ↓
检查依赖、冲突和失效关系
        ↓
更新文档状态面板
        ↓
向用户展示最小关注集
        ↓
用户确认状态变化
        ↓
正式归档或冻结
```

其中，Skill 面向用户的默认输出不应是一大段分析，而应该类似：

```markdown
## 本轮文档同步结果

检测到 5 份受管理文档，其中 3 份发生变化。

### 需要关注

1. PRODUCT_REPOSITIONING.md
   - 状态：REVIEWING
   - 变化：产品目标从单一评审扩展为通用文档工作流
   - 影响：SYSTEM_DESIGN 和 IMPLEMENTATION_PLAN 需要同步修改

2. SYSTEM_DESIGN.md
   - 状态：可能过期
   - 原因：仍引用旧产品边界

### 无需阅读全文

- SCHEMA_CONTRACTS.md：仅增加字段，无行为变化
- TEST_STRATEGY.md：测试范围同步更新

### 建议操作

先冻结 PRODUCT_REPOSITIONING.md，再更新 SYSTEM_DESIGN.md。
```

用户只有在需要时才展开详细差异。

---

# 七、关键约束

这个 Skill 是否可靠，主要取决于以下防御规则。

## 1. 不根据文件修改时间判断有效性

“最后修改时间最新”不代表“当前有效”。

有效状态必须来自：

- 明确元数据
- 用户确认
- 可追踪的替代关系
- 正式决策记录

---

## 2. 不静默覆盖旧版本

修改受管理文档前必须：

- 保存上一修订快照，或
- 确认 Git 中存在可恢复版本

否则拒绝执行覆盖。

---

## 3. 不自动宣布文档冻结

Agent 可以建议：

```text
建议将文档从 REVIEWING 提升为 FROZEN
```

但不能自行认定用户已经批准。

---

## 4. 不允许存在两个未解释的事实源

如果两份文档都声明：

```yaml
source_of_truth: true
```

且覆盖同一领域，Skill 必须报告冲突。

例如：

```text
SYSTEM_DESIGN.md 和 ARCHITECTURE_V2.md
均声明为系统架构事实源。
```

不能自行选择其中一个。

---

## 5. 摘要不能成为新的事实源

摘要必须明确标注：

```text
这是派生阅读材料，原始事实以 SYSTEM_DESIGN.md@r7 为准。
```

否则摘要和原文会逐渐分叉。

---

## 6. 归档不等于删除

默认只允许：

- 标记归档
- 移出活跃阅读集
- 移动到归档目录
- 保留索引和引用

不自动删除文件。

---

# 八、触发条件

建议 Skill 在以下场景自动触发：

### 强触发

- Agent 新生成一份超过指定长度的 Markdown 文档
- 修改了 `ACTIVE` 或 `FROZEN` 文档
- 用户要求“根据某份冻结文档更新其他设计文档”
- 新文档与已有文档名称或职责相似
- 文档声明替代旧方案
- 一次任务修改了三份以上设计文档

### 弱触发

- 一轮开发任务结束
- 用户要求阶段总结
- Git diff 中出现大量文档变更
- 文档长时间未验证

### 不触发

- 简短聊天
- 临时命令说明
- 小于一定长度的普通说明
- 代码内注释修改
- 用户明确表示不需要归档的临时草稿

---

# 九、Skill 的边界

`doc-steward` 不应该承担以下职责：

- 不负责判断产品方案本身是否正确
- 不负责替代专业评审 Skill
- 不负责直接编写全部设计文档
- 不负责管理源代码版本
- 不负责把每一句对话都永久保存
- 不负责主动修改冻结文档内容
- 不负责维护复杂知识图谱

它负责的是：

> **什么文档存在、当前是否有效、与什么有关、发生了什么变化、用户现在需要关注什么。**

---

# 十、是否需要拆分为多个 Skill

当前阶段不建议拆分。

一个 `doc-steward` Skill 可以承担编排职责，底层使用几个脚本完成确定性操作：

```text
doc-steward/
├── SKILL.md
├── scripts/
│   ├── scan_docs.py
│   ├── update_registry.py
│   ├── snapshot_doc.py
│   ├── generate_diff.py
│   └── validate_links.py
└── references/
    ├── metadata-schema.md
    ├── lifecycle.md
    └── output-format.md
```

其中：

- Skill 负责判断何时执行、向用户展示什么、什么时候要求确认。
- 脚本负责哈希、快照、版本号、索引更新等确定性工作。
- 大模型负责摘要、变化解释、依赖关系识别和风险提示。

只有当它未来发展到跨项目、多人协作或独立服务时，再考虑拆成：

```text
doc-ingest
doc-lifecycle
doc-review
doc-retrieval
```

现在拆分会增加编排负担，反而违背“减少注意力分散”的初衷。

---

# 十一、建议的 MVP

第一版只实现以下闭环：

1. 扫描指定文档目录。
2. 给文档分配稳定 `doc_id`。
3. 维护 `registry.yaml`。
4. 为长文档生成状态卡和执行摘要。
5. 对修改文档生成版本差异摘要。
6. 支持 `DRAFT / ACTIVE / FROZEN / SUPERSEDED / ARCHIVED`。
7. 生成统一的 `DOCS_DASHBOARD.md`。
8. 在覆盖文档前保存快照。
9. 用户确认后才能冻结或替代。
10. 输出“本轮只需阅读哪些内容”。

暂时不要实现：

- 向量数据库
- Web 管理界面
- 跨仓库知识图谱
- 多用户权限
- 自动合并冲突文档
- 复杂审批流
- 所有文档的全文语义索引

这样第一版不会过重。

---

# 十二、一句话设计目标

可以将这个 Skill 的正式目标暂定为：

> `doc-steward` 用于管理 AI Agent 在工程协作中生成和修改的长文档，通过稳定身份、生命周期状态、版本快照、变化摘要和统一阅读入口，确保用户能够快速识别当前有效事实、需要关注的变化以及应被归档的历史内容，从而降低文档阅读负担和注意力分散。

从产品结构上看，它不是普通的“文档归档 Skill”，而是一个轻量级的：

> **文档事实控制面 + 用户注意力过滤器。**

下一步最合理的工作不是直接编写 `SKILL.md`，而是先冻结三项设计：**文档生命周期、事实源判定规则、用户默认看到的输出格式**。这三项一旦确定，后续实现会比较稳定。
