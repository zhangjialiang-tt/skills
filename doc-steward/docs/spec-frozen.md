# doc-steward 冻结设计规格（Frozen Design Spec）

> 本文件冻结 `doc-steward` 的三项核心设计，作为后续实现的契约。
> 它们直接决定：`registry.yaml` Schema、脚本允许/拒绝执行的条件、哪些状态需用户批准、Dashboard 生成方式、快照/替代/归档处理。
> 本文件本身是派生设计物，非代码；事实以其中条款为准，后续若需修订应走 `supersede` 流程。

## 决策记录（Frozen Decisions）

```yaml
next_phase: freeze_design          # 已完成；下一相位: SKILL.md → Schema → 确定性脚本 → 测试夹具 → MVP 闭环

scope:
  skill_type: generic              # 通用 Skill，管理调用时所在项目的文档
  default_document_root: docs/      # 默认扫描 docs/；可由配置覆盖
  config_override:                  # 项目可覆盖扫描根与排除项
    document_roots: [docs, design, plans]
    exclude: [docs/archive, docs/generated]

metadata:
  source_of_truth: .doc-steward/registry.yaml   # 唯一权威元数据源
  front_matter_required: false
  front_matter_authoritative: false             # Front Matter 仅为可选镜像/人工提示
  drift_policy: report_only                     # registry 与 FM 不一致 → 报告漂移，不自动覆盖

implementation:
  language: python
  invocation: manual                             # MVP 仅手动调用，自动触发为后续增强
  archive_default: logical_only                  # 默认仅逻辑归档，不移动/删除用户文件
  archive_physical_move: explicit_opt_in         # 物理移动须显式操作，避免破坏链接/仓库结构
  derived_docs_are_source_of_truth: false
```

---

## §1 文档生命周期与状态迁移规则

### 1.1 状态定义（精确、可验证）

| 状态 | 含义 | 可否指导开发 | 内容可否改 |
|------|------|--------------|------------|
| `DRAFT` | 正在生成或讨论，未定型 | 否 | 是 |
| `REVIEWING` | 内容基本完成，存在待确认问题 | 否（待评审） | 是 |
| `ACTIVE` | 当前有效，可指导开发 | 是 | 是（改后须生成新 revision 快照） |
| `FROZEN` | 已确认的阶段基线，未经显式决策不得修改 | 是 | 否（须先迁回 ACTIVE） |
| `SUPERSEDED` | 曾有效，已被新文档/版本替代 | 否 | 否 |
| `ARCHIVED` | 仅保留历史价值，不应参与当前上下文 | 否 | 否 |

### 1.2 状态不变量（Invariants）

- **I1** 每份受管文档在任一时刻恰好一个 `status`。
- **I2** 注册（`register`）初始状态恒为 `DRAFT`。
- **I3** `SUPERSEDED` 文档必须设置 `superseded_by`，指向有效 `doc_id@revision`。
- **I4** `ARCHIVED` 文档必须记录 `archive_reason` 与 `archived_at`，并保留 `last_status`。
- **I5** `FROZEN` 文档允许被外部修改（用户/Agent/其他工具），但 `doc-steward` 不得静默接受、登记或将其视为有效修订；检测到内容 hash 变化后必须标记 `content_drift=true`，阻止 `sync --apply`，要求用户先 `unfreeze`。
- **I6** 有效性仅由 registry 元数据 + 已记录决策决定，**绝不**依据文件 mtime / git commit time。

### 1.3 允许的状态迁移（Transition Matrix）

| 从 → 到 | 触发操作 | 用户批准要求 | 前置条件 |
|---------|----------|--------------|----------|
| `DRAFT → REVIEWING` | promote | 需用户确认（`decision.by=user`） | 无 |
| `REVIEWING → ACTIVE` | promote | 需用户确认 | 无未决阻断问题（可记录） |
| `ACTIVE → FROZEN` | promote | **需用户明确批准（Tier2）** | 内容评审完成 |
| `FROZEN → ACTIVE` | demote/unfreeze | **需用户明确批准（Tier2）** | 记录解冻原因 |
| `ACTIVE → SUPERSEDED` | supersede | **需用户明确批准（Tier2）** | 存在替代文档 B 且其 `supersedes` 含 A |
| `REVIEWING → SUPERSEDED` | supersede | **需用户明确批准（Tier2）** | 同上 |
| `DRAFT → SUPERSEDED` | supersede | **需用户明确批准（Tier2）** | 同上 |
| `* → ARCHIVED`（DRAFT/REVIEWING/ACTIVE/FROZEN/SUPERSEDED） | archive | 需用户显式发起 | `archive_reason` 必填 |

**显式禁止的迁移：**
- 任何跳级晋升（如 `DRAFT→ACTIVE`、`REVIEWING→FROZEN`）——不允许。
- `SUPERSEDED` / `ARCHIVED → DRAFT`——不允许（避免复活已失效事实）；恢复只能到 `SUPERSEDED`。
- 任何无 `decision` 记录的迁移——不允许。

### 1.4 决策记录（Decision Record）

每次迁移在 registry 写入：
```yaml
decision:
  by: user            # 不得为 Skill / Agent 自身
  at: 2026-07-28      # ISO 日期
  reason: "<字符串>"
```
约束：Agent 只能"建议"状态变化，不能"认定"用户已批准。`ACTIVE→FROZEN` 尤其须经用户明确批准。

## §1.5 仓库观察与输出派生标志

不要继续使用模糊的 `stale` 单一字段。三类概念必须分开：

### 1.5.1 治理生命周期（权威）

`status` 字段，由状态迁移规则定义。

### 1.5.2 仓库观察（派生）

```yaml
observations:
  content_drift: true      # live hash != registry hash
  missing: false           # 文件不存在
  path_changed: false      # 文件路径改变
  stale_dependency: false  # 依赖被替代
```

由 `sync` 计算后写回，不依赖人工填写。

### 1.5.3 输出层（派生）

```yaml
derived:
  needs_attention: true
  attention_priority: "must_read" | "change_only" | "no_need"
```

由 §3.2 算法现场计算，不持久化。

## §1.6 与防御规则的对应

所有操作都必须经过以下阶段：

```
PRECHECK      → 检查 registry 存在、Schema 合法、PROJECT_ROOT/SKILL_ROOT 有效
     ↓
INSPECT       → 只读扫描，收集 new/modified/missing/drift
     ↓
PLAN          → 生成 change set（不写盘）
     ↓
APPROVAL      → 用户确认 change set（Tier2 必须显式批准）
     ↓
APPLY         → 执行内存变更
     ↓
VERIFY        → 重新读取 registry 和文件，校验不变量
     ↓
REPORT        → 输出结果
```

约束：
- `INSPECT` 和 `PLAN` 永远只读。
- 没有确定性后端时只能执行到 `PLAN`（READ_ONLY_ADVISORY 模式）。
- Tier2 没有用户批准时不能进入 `APPLY`。
- `APPLY` 后必须重新读取 registry 和文件进行 `VERIFY`。

---

## §2 事实源判定、冲突与替代规则

### 2.1 事实源定义

- 权威元数据源 = `.doc-steward/registry.yaml`（唯一）。
- 每份文档可在 registry 声明：`source_of_truth: bool` 与 `domain: [<领域键>]`。
- 文档内 Front Matter **非权威**；registry 为准。两者冲突 → 报告 `DRIFT`，不自动覆盖 registry。

### 2.2 冲突判定

- 对每个 `domain d`，统计所有 `status ∈ {ACTIVE, FROZEN}` 且 `source_of_truth=true` 的文档集合 `S_d`。
- 若 `|S_d| ≥ 2` → **冲突**，必须报告；Skill 不得自行选择其一。
- `DRAFT` / `REVIEWING` / `SUPERSEDED` / `ARCHIVED` 文档不计入 `S_d`（不主张当前权威）。
- 冲突报告须列出参与文档 `doc_id@revision` 及各自声明。

### 2.3 替代（Supersede）语义

当文档 B 替代文档 A，Skill 须**原子地**完成：
1. `A.status → SUPERSEDED`
2. `A.superseded_by = B.doc_id@B.revision`
3. `B.supersedes` 追加 `A.doc_id@A.revision`
4. `A` 从活跃阅读集移除（dashboard 不再以有效文档呈现）
5. 历史引用保留：`diffs/` `summaries/` 中指向 `A@rN` 的链接保持有效
6. 依赖检查：对任意 `ACTIVE`/`FROZEN` 文档 C，若 `C.depends_on` 含 `A.doc_id` → 标记 C 的 `stale_dependency=true`
7. 若 A 原是 domain `d` 的唯一 `source_of_truth`，且 B 也声明 `d` → 替代后 B 成为 `d` 的 `source_of_truth`，冲突由此消解（registry 中 A 的 `source_of_truth` 置 false，B 置 true）
- 替代需用户明确批准（Tier2）。

### 2.4 派生文档非事实源

- `summaries/` `diffs/` `DOCS_DASHBOARD.md` 均为派生，可完整重新生成。
- 每份派生文档**必须**包含 provenance 行：`派生阅读物，事实以 <doc_id>@r<N> 为准`。
- 若任何派生文档被当作事实引用，Skill 须警告。
- 验证：生成脚本必须写入 provenance；缺失则视为生成失败。

### 2.5 有效性判定（替代 mtime）

文档"当前有效/权威" iff：
```
status ∈ {ACTIVE, FROZEN}
AND (若 source_of_truth，则其为所属各 domain 的唯一权威)
AND status ≠ SUPERSEDED
AND status ≠ ARCHIVED
```

### 2.6 漂移（Drift）处理

- 若文档含 Front Matter 且与 registry 元数据不一致 → 报告 `DRIFT`。
- registry 始终优先；不自动改写任一处（与 2.1 一致）。

---

## §3 用户默认输出与注意力分级格式

### 3.1 分层阅读等级

- **L0 状态卡**：结构化字段（`doc_id`, `title`, `status`, `revision`, `updated_at`, `purpose`, `this_round_change`, `needs_attention`, `reading_hint`）。机器可读，用于 dashboard。
- **L1 执行摘要**：300–500 字中文，含：解决什么问题 / 核心结论 / 对当前开发影响 / 未决问题。
- **L2 变化摘要**：相对于上一 revision 的 新增 / 删除 / 修改 / 被推翻结论 / 变化的接口·约束·计划。
- **L3 原始全文**：仅深研时阅读。

### 3.2 注意力分级算法（确定性）

`needs_attention = true` 当且仅当满足任一：
- `status == REVIEWING`
- 本轮 `status` 或 `revision` 变化
- `registry.attention.level == high`
- 存在 `stale_dependency`（依赖被替代）
- `sync` 标记 `stale`（内容变而 revision 未增）

否则：
- 若 `revision` 增加但无行为/接口变化 → 归入"只需了解变化"
- 其余稳定文档 → 归入"本轮无需阅读"

**输出顺序约束**：默认输出必须先呈现"需要关注"集；完整差异仅在用户请求时展开，不得默认倾销长分析。

### 3.3 默认输出结构（sync / 操作后）

```markdown
## 本轮文档同步结果

受管理文档总数：N，本轮变化：M

### 需要关注
1. <doc>
   - 状态：<status>
   - 变化：<一句话>
   - 影响：<一句话>

### 只需了解变化
- <doc>：<一句话>

### 本轮无需阅读
- <doc>

### 建议操作
- <具体建议，如"先冻结 X，再更新 Y">
```

### 3.4 Dashboard（`DOCS_DASHBOARD.md`）

- 生成时间、文档总数、按状态计数
- 当前有效文档（`ACTIVE`+`FROZEN`）以 L0 卡呈现
- 待关注（`REVIEWING` + 被标记项）
- 已替代 / 已归档（含替代 / 恢复引用）
- 待处理问题清单
- provenance 行：`本文件为派生阅读物，事实以各文档 registry 记录为准`
- 可完整重新生成（删除不损失信息）

### 3.5 `focus` 输出（最小阅读集）

- **必须阅读**：`doc` + 原因 + 推荐章节
- **只需了解变化**：`doc` 列表
- **本轮无需阅读**：`doc` 列表

---

## §4 验收映射（本规格如何被未来测试覆盖）

| 规格条款 | 可测试不变量（未来脚本/夹具） |
|----------|------------------------------|
| I1 / I2 | `register` 新文档 → `status == DRAFT`；同文档同一时刻仅一个 status |
| 1.3 跳级禁止 | `promote(DRAFT→ACTIVE)` 必须拒绝并报告 |
| 1.3 Tier2 | `ACTIVE→FROZEN` 无用户批准时必须拒绝；有批准且 `decision.by=user` 才成功 |
| 1.5 stale | 内容变化但 revision 未增 → `stale=true` 且进入"需要关注" |
| I5 | 修改 `FROZEN` 文档内容 → 拒绝，除非先 `FROZEN→ACTIVE` |
| 2.2 冲突 | 构造两份 `ACTIVE`+`source_of_truth` 同 domain → `sync` 报告冲突且不自动选 |
| 2.3 替代 | `supersede` 后 A=`SUPERSEDED`+`superseded_by` 设置、B=`supersedes` 含 A、A 移出活跃集、依赖 C 标 `stale_dependency` |
| 2.4 provenance | 生成的摘要缺 provenance 行 → 视为生成失败 |
| 2.6 drift | 文档 FM 与 registry 不一致 → 报告 DRIFT，registry 不被改写 |
| 3.2 grading | 给定输入（status/revision/attention/stale）→ 断言 `needs_attention` 分类正确 |
| archive 默认 | `archive` 后原文件路径仍存在（逻辑归档）；物理移动需显式 |
| 3.4 dashboard | 重新生成后内容一致；含 provenance 行 |

---

## 后续相位（非本文件范围）

`SKILL.md` → `registry.yaml` Schema → 确定性脚本（`scan_docs.py` / `update_registry.py` / `snapshot_doc.py` / `generate_diff.py` / `validate_links.py`）→ 测试夹具 → MVP 闭环。
本规格为上述每一项的输入契约；实现时不得放宽本文件的禁止项与 Tier2 批准要求。
