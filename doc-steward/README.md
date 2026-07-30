# doc-steward — 文档资产与注意力管理器

> 管理 AI Agent 在工程协作中生成/修改的长文档生命周期：稳定身份、版本快照、状态生命周期、变化摘要、统一阅读入口与注意力分级 —— **「文档事实控制面 + 用户注意力过滤器」**。

`doc-steward` 不负责撰写 PRD、设计文档或实施计划，而是负责管理这些文档**生成之后的状态**，让用户快速识别「当前有效事实 / 需要关注的变化 / 应归档的历史」，降低阅读负担和注意力分散。

权威契约见 [`docs/spec-frozen.md`](docs/spec-frozen.md)（生命周期、事实源、输出格式已冻结），设计背景见 [`docs/design.md`](docs/design.md)。

---

## 目录

- [核心概念](#核心概念)
- [七种操作](#七种操作)
- [状态生命周期](#状态生命周期)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [注意力分级](#注意力分级)
- [事实源与冲突](#事实源与冲突)
- [脚本入口（规划中）](#脚本入口规划中)
- [参考](#参考)

---

## 核心概念

三件事必须分开，不可混用：

| 概念 | 说明 | 示例 |
|------|------|------|
| **逻辑文档身份 `doc_id`** | 文件改多少次都不变 | `DOC-SYSTEM-DESIGN` |
| **修订版本 `revision`** | 同一逻辑文档的第 N 次受管理修订 | `r1`、`r2`、`r3` |
| **生命周期状态 `status`** | `DRAFT / REVIEWING / ACTIVE / FROZEN / SUPERSEDED / ARCHIVED` | `ACTIVE` |

**权威元数据源 = `.doc-steward/registry.yaml`**，唯一。文档内的 Front Matter 仅作可选镜像/人工提示，非权威；两者不一致时报告 DRIFT，registry 优先。

---

## 七种操作

| 操作 | 说明 |
|------|------|
| `register` | 纳入新文档：分配 `doc_id`、初始化元数据、生成 L0/L1 摘要。初始状态恒为 `DRAFT`。 |
| `sync` | 刷新状态：检测新增/修改 → 比对上一修订 → 生成变化摘要 → 更新 Dashboard。最常用。 |
| `focus` | 生成最小阅读集：必须阅读 / 只需了解变化 / 本轮无需阅读。 |
| `promote` | 状态晋升：`DRAFT→REVIEWING`、`REVIEWING→ACTIVE`、`ACTIVE→FROZEN`，每次需用户确认。 |
| `supersede` | 声明替代：旧文档 `SUPERSEDED` + 设 `superseded_by`，原子完成。需用户批准。 |
| `archive` | 逻辑归档：默认仅标记 + 移出活跃集 + 保留索引，不移动/删除文件。 |
| `query` | 自然语言查询：如"当前有效系统设计是哪份？""哪些文档依赖旧 PRD？" |

---

## 状态生命周期

```
DRAFT → REVIEWING → ACTIVE → FROZEN → SUPERSEDED → ARCHIVED
```

| 状态 | 含义 | 可否指导开发 | 内容可否改 |
|------|------|:---:|:---:|
| `DRAFT` | 正在生成或讨论，未定型 | 否 | 是 |
| `REVIEWING` | 内容基本完成，存在待确认问题 | 否 | 是 |
| `ACTIVE` | 当前有效，可指导开发 | 是 | 是 |
| `FROZEN` | 已确认的阶段基线 | 是 | 否（须先迁回 ACTIVE） |
| `SUPERSEDED` | 已被新文档/版本替代 | 否 | 否 |
| `ARCHIVED` | 仅保留历史价值 | 否 | 否 |

**铁律：**
- 禁止跳级晋升（如 `DRAFT→ACTIVE`）。
- 禁止复活已失效文档（`SUPERSEDED`/`ARCHIVED→DRAFT` 不允许）。
- `FROZEN` 文档内容不可直接修改；修改前必须先 `FROZEN→ACTIVE` 并记录解冻原因。
- 有效性**绝不**依据文件 mtime / git commit time。

完整迁移矩阵与不变量（I1–I6）见 [`docs/spec-frozen.md`](docs/spec-frozen.md)。

---

## 项目结构

```
doc-steward/
├── SKILL.md                        # 操作指南（本 Skill 的主文件）
├── docs/
│   ├── spec-frozen.md              # 冻结设计规格（权威契约）
│   └── design.md                   # 设计背景与定位
├── references/
│   └── registry-schema.md          # registry.yaml 字段契约（权威说明）
├── schema/
│   └── registry.schema.json        # 机器可读 JSON Schema（供脚本校验）
├── examples/
│   └── registry.example.yaml       # 覆盖各状态的完整 registry 示例
├── evals/
│   └── evals.json                  # 行为评测用例
└── scripts/                        # MVP 后端（规划中）
    ├── scan_docs.py                # 扫描 document_roots
    ├── update_registry.py          # 维护 registry.yaml
    ├── snapshot_doc.py             # 保存上一修订快照
    ├── generate_diff.py            # 生成 revision 间变化摘要
    └── validate_links.py           # 校验依赖与替代关系、发现冲突/漂移
```

---

## 快速开始

### 1. 作为 Skill 调用

将 `doc-steward` 安装到项目的 `.claude/skills/` 或对应 Skill 目录。当 AI Agent 生成/修改长文档后，用自然语言触发：

- "帮我把这份新设计文档登记管理"
- "同步一下文档状态，我只需知道哪些必须看"
- "冻结当前发布计划，作为 v1.0 基线"
- "旧的 PRD 已被新版替代，处理一下"
- "当前哪些文档是有效的？"

### 2. 手动使用

无需脚本就绪。按照 `SKILL.md` 与 `spec-frozen.md` 的契约手动执行等效步骤即可。禁止以「脚本未实现」为由放宽停止/批准规则。

### 3. registry 示例

参见 [`examples/registry.example.yaml`](examples/registry.example.yaml)，覆盖六种状态及冲突示意。

---

## 注意力分级

分层阅读等级：

- **L0 状态卡**：结构化字段（`doc_id`, `title`, `status`, `revision`, `updated_at`, `purpose`, `this_round_change`, `needs_attention`, `reading_hint`），用于 Dashboard。
- **L1 执行摘要**：300–500 字中文，含解决什么问题 / 核心结论 / 对当前开发影响 / 未决问题。
- **L2 变化摘要**：相对于上一 revision 的新增 / 删除 / 修改 / 被推翻结论 / 变化的接口·约束·计划。
- **L3 原始全文**：仅深研时阅读。

`needs_attention = true` 当且仅当满足任一：
- `status == REVIEWING`
- 本轮 `status` 或 `revision` 变化
- `attention.level == high`
- 存在 `stale_dependency`（依赖被替代）
- `sync` 标记 `stale`（内容变而 revision 未增）

**默认输出必须先呈现「需要关注」集**，完整差异仅在用户请求时展开。

---

## 事实源与冲突

- registry 唯一权威。每份文档可声明 `source_of_truth` 与 `domain`。
- 若同一 `domain` 出现 ≥2 个 `ACTIVE`/`FROZEN` 且 `source_of_truth=true` 的文档 → **必须报告冲突、不得自行二选一**。
- `supersede` 是消解同 domain 冲突的正当途径（替代后新文档成为该 domain 事实源）。
- 派生文档（`summaries/`、`diffs/`、`DOCS_DASHBOARD.md`）**永不为事实源**，必须含 provenance 行：`派生阅读物，事实以 <doc_id>@r<N> 为准`。

---

## 脚本入口（规划中）

确定性操作建议落到 `scripts/` 下脚本，Skill 负责判断何时执行、展示什么、何时要求确认。脚本就绪前可按 `spec-frozen.md` 规则手动执行等效步骤。

| 脚本 | 职责 |
|------|------|
| `scan_docs.py` | 扫描 `document_roots`，识别新增/修改文档 |
| `update_registry.py` | 维护 `registry.yaml`（doc_id / revision / status / 依赖） |
| `snapshot_doc.py` | 保存上一修订快照（覆盖前的安全网） |
| `generate_diff.py` | 生成 revision 间变化摘要 |
| `validate_links.py` | 校验依赖与替代关系、发现冲突/漂移 |

---

## 参考

| 文件 | 内容 |
|------|------|
| [`docs/spec-frozen.md`](docs/spec-frozen.md) | 冻结设计规格（生命周期 / 事实源 / 输出格式，权威契约） |
| [`references/registry-schema.md`](references/registry-schema.md) | `registry.yaml` 字段契约（映射 spec 条款） |
| [`schema/registry.schema.json`](schema/registry.schema.json) | 机器可读 JSON Schema（供脚本校验） |
| [`examples/registry.example.yaml`](examples/registry.example.yaml) | 覆盖各状态的完整示例 |
| [`docs/design.md`](docs/design.md) | 设计背景与定位 |
| [`evals/evals.json`](evals/evals.json) | 行为评测用例 |

---

## 许可与版本

- **版本**：`0.1.0`
- **registry schema 版本**：`1.0`
- 本文件是操作指南；规则冲突时以 `docs/spec-frozen.md` 为准。
