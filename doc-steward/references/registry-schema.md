# registry.yaml Schema 契约

> 本文件定义 `.doc-steward/registry.yaml` 的字段结构与约束，是 `doc-steward` 的**元数据权威格式**。
> 它直接由 [spec-frozen.md](../docs/spec-frozen.md) §1（生命周期）、§2（事实源）约束，并供未来的
> `scripts/update_registry.py`、`validate_links.py` 等确定性脚本校验。
> 机器可读版本见 [../schema/registry.schema.json](../schema/registry.schema.json)；完整示例见
> [../examples/registry.example.yaml](../examples/registry.example.yaml)。
>
> **原则**：registry 是唯一权威元数据源；文档内 Front Matter 非权威（spec §2.1）。本 Schema 不含任何
> 文件 mtime / git commit time 字段（不变量 I6：有效性绝不依据文件修改时间）。

## 1. 顶层结构

```yaml
version: "1.0"            # registry 格式版本（语义化主.次，本文件定义 1.0）
config:                  # 项目级扫描配置，可覆盖默认
  document_roots: [docs] # 默认扫描根；SPEC 决策 document_roots 可配 [docs, design, plans]
  exclude: []            # 排除路径/通配，如 [docs/archive, docs/generated]
documents:               # 受管文档条目数组，每条一个 doc_id
  - <document>
```

- `version` / `config` / `documents` 三者在顶层**必填**。
- `documents` 中每个 `doc_id` **全局唯一**（不变量 I1：每份文档恰好一个身份；同 doc_id 不得重复）。

## 2. document 字段表

| 字段 | 类型 | 必填 | 约束 / 说明 | 对应 spec |
|------|------|------|-------------|-----------|
| `doc_id` | string | 是 | 稳定逻辑身份，格式 `^[A-Z][A-Z0-9-]+$`（如 `DOC-SYSTEM-DESIGN`）。文件改多少次都不变 | 概念模型 §概念模型 |
| `title` | string | 否 | 人类可读标题 | L0 卡 §3.1 |
| `path` | string | 是 | 相对项目根的文档路径（如 `docs/system-design.md`） | — |
| `type` | enum | 否 | `design`/`prd`/`plan`/`spec`/`adr`/`note`/`other`；默认 `other` | — |
| `status` | enum | 是 | `DRAFT`/`REVIEWING`/`ACTIVE`/`FROZEN`/`SUPERSEDED`/`ARCHIVED` | §1.1 |
| `revision` | integer≥1 | 是 | 第 N 次受管理修订；递增 ≠ 状态变化 | §概念模型 |
| `content_hash` | string | 是 | `^[0-9a-f]{64}$`，文档内容 SHA-256；`sync` 据此算 `stale` | §1.5 |
| `created_at` | date | 否 | 首次登记日期（ISO `YYYY-MM-DD`），registry 记录、非文件 mtime | I6 |
| `updated_at` | date | 是 | 本 registry 条目最近更新日期（ISO），非文件 mtime | I6 |
| `assigned_domain` | string[] | 否 | 声明所属领域键；参与同 domain 冲突判定 | §2.1/§2.2 |
| `source_of_truth` | bool | 否 | 是否主张该 domain 当前权威；默认 `false` | §2.1 |
| `superseded_by` | string\|null | 条件 | 见 §3 条件约束（I3） | §2.3 |
| `supersedes` | string[] | 否 | 本档替代过的 `doc_id@revision` 列表；默认 `[]` | §2.3 |
| `depends_on` | string[] | 否 | 依赖的 `doc_id` 列表；被替代时标记 `stale_dependency` | §2.3(6) |
| `stale` | bool | 否 | 派生标志：内容 hash 变但 revision 未增、status 未变 → `true`；默认 `false` | §1.5 |
| `stale_dependency` | bool | 否 | 派生标志：依赖项被 `supersede` → `true`；默认 `false` | §2.3(6) |
| `purpose` | string | 否 | L0 卡「解决什么问题」 | §3.1 |
| `reading_hint` | string | 否 | L0 卡「推荐阅读章节/提示」 | §3.1 |
| `attention` | object | 否 | `{ level: normal|high, note?: string }`；`level==high` 强制 `needs_attention` | §3.2 |
| `archive` | object | 条件 | 见 §3 条件约束（I4） | §1.4 |
| `decision` | object | 是 | 最近一次状态迁移决策；结构见 §4 | §1.4 |

> 字段 `stale` / `stale_dependency` / `needs_attention` 为**派生标志**：由 `sync` 计算后写回，不依赖人工填写；
> `needs_attention` 本身不持久化（输出时由 §3.2 算法现场计算），不列入本 Schema 存储字段。

## 3. 条件约束（JSON Schema `if/then` 实现）

- **I3 — SUPERSEDED 必含 superseded_by**：当 `status == SUPERSEDED` 时，`superseded_by` 必填且格式 `^.+@r\d+$`（如 `DOC-OLD@r3`）。
- **I4 — ARCHIVED 必含归档三元组**：当 `status == ARCHIVED` 时，`archive` 必填且含 `reason`（字符串）、`archived_at`（date）、`last_status`（枚举）。
- **I2 — 初始状态**：`register` 写入的新条目 `status` 必须为 `DRAFT`（由 `update_registry.py` 保证；Schema 不反向限制历史条目）。
- **I5 — FROZEN 内容锁定**：Schema 层不存储内容；由脚本在执行"修改内容"操作前检查 `status==FROZEN` → 拒绝，除非先 `FROZEN→ACTIVE`（且 `decision.by==user`）。
- **I6 — 无 mtime**：本 Schema 全表无文件修改时间字段，从结构上杜绝"依据 mtime 判有效性"。

## 4. decision 对象（每次迁移必写）

```yaml
decision:
  by: user          # 枚举唯一值 user；Agent/Skill 自身不得作为 by（spec §1.4）
  at: 2026-07-28    # ISO 日期，即决策生效日
  reason: "<字符串>" # 人类可读的迁移原因
```

- `by` **只允许 `user`**：Agent 只能"建议"状态变化，不能"认定"已批准（spec §1.4）。因此 registry 中落盘的 `decision.by` 恒为 `user`。
- 每次 `promote`/`supersede`/`demote`/`archive`/`restore` 必须覆盖写最新 `decision`；缺少 `decision` 的迁移不被允许（核心契约速查表"停止"项）。
- **Tier2 批准要求**：`ACTIVE→FROZEN`、解冻、`supersede`、`restore` 必须存在用户明确批准证据（`by==user` + `reason` 非空），否则脚本拒绝（spec §1.3 / §2.3）。

## 5. 冲突与事实源（供 `validate_links.py`）

- 对每个 `domain d`，取 `status ∈ {ACTIVE, FROZEN}` 且 `source_of_truth==true` 的文档集合 `S_d`。
- 若 `|S_d| ≥ 2` → **冲突**，必须报告，Skill 不得自行二选一（spec §2.2）。
- `DRAFT`/`REVIEWING`/`SUPERSEDED`/`ARCHIVED` 不计入 `S_d`。
- `supersede` 是消解同 domain 冲突的正当途径：替代后新文档 `source_of_truth` 置 `true`、旧文档置 `false`（spec §2.3(7)）。

## 6. 版本策略

- `version` 标识 **registry 格式**版本，与单文档 `revision` 无关。
- 本 Schema 为 `1.0`；未来字段增删走 `supersede` 式修订并在本文件记录，不静默破坏旧 registry。
- 脚本应先校验 `version` 兼容性再读写。
