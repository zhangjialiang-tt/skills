---
name: doc-steward
version: "0.1.0"
description: >
  管理 AI Agent 在工程协作中生成/修改的长文档生命周期：稳定身份、版本快照、状态生命周期、
  变化摘要、统一阅读入口与注意力分级——「文档事实控制面 + 用户注意力过滤器」。
  当用户新生成或大幅修改 Markdown 设计文档、要求「整理文档 / 冻结基线 / 归档旧方案 /
  当前哪些文档有效 / 文档改了什么 / 我只需看哪几份」、一次改动多份设计文档、或修改 ACTIVE/FROZEN 文档时触发。
  不用于：实际撰写/重写 PRD、设计文档或代码；管理源代码版本（Git commit/branch/PR）；
  通用 Markdown 编辑或格式转换；纯聊天式摘要；用户明确不要管理的临时草稿。
  即使未显式说「文档管家」，只要涉及长文档的状态、版本、有效性或阅读负担，也应使用本 Skill。
output_contract:
  artifacts:
    - "本轮文档同步/操作结果（内联输出，先呈现需关注集）"
    - "DOCS_DASHBOARD.md（派生阅读入口，可重新生成）"
    - "summaries/ 与 diffs/（派生摘要，可重新生成）"
  format: "markdown"
  constraints:
    - "不修改受管文档内容，除非用户明确授权对应的状态迁移"
    - "任何状态迁移必须记录用户 decision，Agent 只能建议不能认定"
    - "归档默认仅逻辑归档，不移动/删除用户文件"
---

# doc-steward — 文档资产与注意力管理器

管理 AI 生成的长文档在生成之后的生命周期，让用户快速识别「当前有效事实 / 需要关注的变化 / 应归档的历史」，降低阅读负担和注意力分散。它不替代其他 Agent 编写 PRD、设计文档或实施计划，而是管理这些文档生成之后的状态。

权威契约见 [docs/spec-frozen.md](docs/spec-frozen.md)（生命周期、事实源、输出格式三节已冻结），设计背景见 [docs/design.md](docs/design.md)。本文件是操作指南；遇到规则冲突以 `spec-frozen.md` 为准。

## 触发边界（何时用 / 何时不用）

**应使用本 Skill：**
- 新生成或大幅修改 Markdown 设计/方案类文档，需要纳入管理
- 要求整理文档状态、冻结基线、归档旧方案
- 询问「当前哪些文档有效 / 文档改了什么 / 我只需看哪几份」
- 一次改动多份设计文档，或要修改 `ACTIVE`/`FROZEN` 文档

**不应路由到这里（near-neighbors）：**
- 实际撰写/重写 PRD、设计文档、代码或普通文案（本 Skill 管理已有文档，不创作内容）
- 管理源代码版本（Git commit/branch/PR 用 smart-commit 等）
- 通用 Markdown 编辑或格式转换
- 纯聊天式摘要、知识问答
- 小于阈值的临时说明、代码内注释修改、用户明确不要管理的草稿

## 核心契约速查（停止 / 提醒 / 需批准 / 可执行）

| 情况 | 动作 |
|------|------|
| 修改 `FROZEN` 文档内容 | **停止**：先 `FROZEN→ACTIVE`（需用户批准），再改 |
| 任何状态迁移缺少用户 `decision` | **停止**：Agent 只能「建议」，不能「认定」已批准 |
| `ACTIVE→FROZEN` / 解冻 / `supersede` / `restore` | **需用户明确批准**（Tier2） |
| 覆盖受管文档前无可恢复快照（无 snapshot 且 Git 无可恢复版本） | **停止**：先保存快照 |
| 两份 `ACTIVE`/`FROZEN` 同 `domain` 均 `source_of_truth=true` | **报告冲突**，不自动二选一 |
| `registry` 与文档 Front Matter 漂移 | **报告 DRIFT**，`registry` 优先，不自动覆盖 |
| `archive` | 默认**仅逻辑归档**（标记 + 移出活跃集 + 保留索引），不移动/删除文件 |
| 派生摘要缺 provenance 行 | **视为生成失败**，必须补回 |

> 原则：宁可多问，不要把未确认的文档状态固化。状态晋升不能仅因 Agent 声称「已完成」。

## 概念模型

三件事必须分开，不可混用：

- **逻辑文档身份 `doc_id`**：文件改多少次都不变（如 `DOC-SYSTEM-DESIGN`）。
- **修订版本 `revision`**：同一逻辑文档的第 N 次受管理修订。版本号增加 ≠ 状态变化。
- **生命周期状态 `status`**：`DRAFT / REVIEWING / ACTIVE / FROZEN / SUPERSEDED / ARCHIVED`。

**权威元数据源 = `.doc-steward/registry.yaml`**，唯一。文档内的 Front Matter 仅作可选镜像/人工提示，非权威；两者不一致报 DRIFT，registry 优先。默认扫描 `docs/`，可由项目配置 `document_roots` / `exclude` 覆盖。

## 七种操作
## 核心操作

确定性操作由 `scripts/` 下的脚本完成；LLM 负责摘要、变化解释、依赖识别与风险提示。

当确定性后端不可用时，系统进入 **READ_ONLY_ADVISORY** 模式：只能执行 INSPECT 和 PLAN，不得修改 registry。

### 1. `register` — 纳入新文档
- 判断文档类型、分配稳定 `doc_id`、初始化元数据、生成 L0/L1 摘要、登记到 registry。
- 初始状态**恒为 `DRAFT`**（不变量 I2）。
- 注册时必须立即保存 r1 快照，确保后续可重建版本。

### 2. `sync` — 刷新状态（最常用）
- 找新增/修改文档 → 比对上一修订生成变化摘要 → 检查引用关系与状态是否过期 → 更新 Dashboard。
- 支持 `--dry-run`（仅检测）和 `--apply`（接受变更）。
- 若内容 hash 变但 `revision` 未增、`status` 未变 → 标记 `content_drift=true`（仓库观察），归入「需要关注」。

### 3. `focus` — 生成最小阅读集
- 输出三类：必须阅读（doc + 原因 + 章节）/ 只需了解变化 / 本轮无需阅读。
- 这是控制注意力分散的关键，而非简单总结。

### 4. `transition` — 状态迁移
- `DRAFT→REVIEWING`、`REVIEWING→ACTIVE` 需用户确认。
- `ACTIVE→FROZEN`、`FROZEN→ACTIVE` **需用户明确批准（Tier2）**。
- 每次迁移写入 `decision: { by: user, at: <ISO>, reason: <str> }`。

### 5. `supersede` — 声明替代
- 旧文档被新文档替代时**原子完成**：旧 `SUPERSEDED` + 设 `superseded_by`、新 `supersedes` 含旧、旧移出活跃集、保留历史引用、检查依赖文档是否过期。
- **需用户明确批准（Tier2）**。详见 `spec-frozen.md` §2.3。

### 6. `archive` — 逻辑归档
- 生成归档记录（`archive_reason` / `archived_at` / `last_status`），移出活跃阅读集，保留索引与引用。
- **默认不移动/删除文件**；物理移动为显式 opt-in 操作。

### 7. `query` — 自然语言查询
- 支持：「当前有效系统设计是哪份？」「哪些文档仍依赖旧 PRD？」「上次改实施计划改了什么？」「哪些已超过两周未同步？」「我现在只需读哪三份？」
- 基于 registry 元数据回答，不依赖文件 mtime。

## 生命周期与状态迁移

六种状态定义见 `spec-frozen.md` §1（权威）。行为铁律：**禁止跳级晋升**、**禁止复活已失效文档**（`SUPERSEDED`/`ARCHIVED→DRAFT` 不允许）、`FROZEN` 不可直接改（须先 `FROZEN→ACTIVE` 并记录解冻原因）、有效性**绝不**依据文件 mtime / git commit time。完整 Transition Matrix 与不变量（I1–I6）以 spec 为准。

## 事实源与冲突

`registry.yaml` 唯一权威。每份文档可声明 `source_of_truth` 与 `domain`；若同一 `domain` 出现 ≥2 个 `ACTIVE`/`FROZEN` 且 `source_of_truth=true` 的文档 → **必须报告冲突、不得自行二选一**。`supersede` 是消解同 domain 冲突的正当途径（替代后新文档成为该 domain 事实源，需用户批准）。派生文档（`summaries/`、`diffs/`、`DOCS_DASHBOARD.md`）**永不为事实源**，必须含 provenance 行：「派生阅读物，事实以 `<doc_id>@r<N>` 为准」。完整规则见 spec §2。

## 输出与注意力分级

分层阅读 L0 状态卡 / L1 执行摘要（300–500 字）/ L2 变化摘要 / L3 原始全文（格式见 spec §3）。注意力分级（确定性）：`needs_attention=true` 当且仅当 `status==REVIEWING`、本轮状态或修订变化、`attention.level==high`、存在被替代的依赖（`stale_dependency`）、或 `sync` 标 `stale`。**默认输出先呈现「需要关注」集**，完整差异仅按需展开，不得默认倾倒长分析。

## 工作流闭环

```
AI Agent 生成/修改文档
  → doc-steward 检测变化
  → 识别 doc_id 与类型
  → 生成快照与版本差异
  → 生成 L0/L1/L2
  → 检查依赖、冲突与失效关系
  → 更新 Dashboard
  → 展示最小关注集
  → 用户确认状态变化
  → 正式归档或冻结
```

## 脚本入口（MVP 后端，规划中）

确定性操作建议落到以下脚本，Skill 负责判断何时执行、展示什么、何时要求确认：

- `scripts/scan_docs.py` — 扫描 `document_roots`，识别新增/修改文档
- `scripts/update_registry.py` — 维护 `registry.yaml`（doc_id / revision / status / 依赖）
- `scripts/snapshot_doc.py` — 保存上一修订快照（覆盖前的安全网）
- `scripts/generate_diff.py` — 生成 revision 间变化摘要
- `scripts/validate_links.py` — 校验依赖与替代关系、发现冲突/漂移

脚本就绪前，可按 `spec-frozen.md` 的契约手动执行等效步骤；**禁止以「脚本未实现」为由放宽本文件的停止/批准规则**。

## 禁止事项

- 静默覆盖受管文档（覆盖前必须可恢复）
- 自认文档已冻结/已批准（Agent 只建议，用户决策）
- 自动选择冲突的事实源
- 把摘要/派生文档当事实源，或省略 provenance
- 归档时默认移动/删除用户文件
- 跳级晋升或复活已失效文档
- 用文件修改时间判断文档是否有效

## 参考

- [docs/spec-frozen.md](docs/spec-frozen.md) — 冻结设计规格（生命周期 / 事实源 / 输出格式，权威契约）
- [references/registry-schema.md](references/registry-schema.md) — `registry.yaml` 字段契约（Schema 权威说明，映射 spec 条款）
- [schema/registry.schema.json](schema/registry.schema.json) — 机器可读 JSON Schema（供脚本校验）
- [examples/registry.example.yaml](examples/registry.example.yaml) — 覆盖各状态的完整示例
- [docs/design.md](docs/design.md) — 设计背景与定位
- [evals/evals.json](evals/evals.json) — 行为评测用例
