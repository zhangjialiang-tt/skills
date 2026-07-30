# doc-steward MVP 闭包计划

> 本文档定义 doc-steward 从当前状态到可用 MVP 的实施路径。
> 目标不是继续扩展状态机，而是先把现有后端连接成纵向闭环：
> **发现变化 → 保存修订 → 解释变化 → 只展示必要关注。**

---

## 0. 范围边界

### 本计划包含

| 里程碑 | 名称 | 核心交付 |
|--------|------|----------|
| A | 可靠内核 | 正式测试套件、Schema 校验、路径安全、统一 CLI、dry-run |
| B | 修订闭环 | register 自动保存 r1、content drift 检测、snapshot-based diff、revision history |
| C | 注意力闭环 | L0 状态卡、确定性 attention、focus 输出、Dashboard、provenance |

### 本计划明确排除

| 能力 | 排除原因 |
|------|----------|
| `restore` | 定义不清，MVP 中 ARCHIVED/SUPERSEDED 不原地复活 |
| Front Matter drift 检测 | 非核心痛点，可延期 |
| 自动 Hook | 需要 IDE/Agent 集成，非 MVP 前置 |
| 多 Agent 强并发 | 单用户本地场景不需要 |
| 密码学审批 | 会话授权 + 审计足够 |
| 物理归档 | 默认仅逻辑归档 |
| 自然语言 query 后端 | Agent 可直接读 registry |
| 外部审批系统 | 本地手动调用场景不需要 |

---

## 1. Milestone A：可靠内核

### 1.1 目标

> 所有治理写入都可以先预览、后执行，非法 registry 永远不会被落盘。

### 1.2 修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `scripts/doc_steward.py` | **新增** | 统一 CLI 入口 |
| `scripts/_core.py` | 修改 | 增加 Schema 校验、路径安全、change set 结构 |
| `scripts/update_registry.py` | 修改 | 接入统一入口，支持 dry-run |
| `scripts/scan_docs.py` | 修改 | 接入统一入口 |
| `scripts/snapshot_doc.py` | 修改 | 接入统一入口 |
| `scripts/generate_diff.py` | 修改 | 接入统一入口 |
| `scripts/validate_links.py` | 修改 | 接入统一入口 |
| `tests/__init__.py` | **新增** | 测试包 |
| `tests/conftest.py` | **新增** | 共享夹具 |
| `tests/test_registry_schema.py` | **新增** | Schema 校验测试 |
| `tests/test_scan.py` | **新增** | 扫描行为测试 |
| `tests/test_revision.py` | **新增** | revision 模型测试 |
| `tests/test_snapshot.py` | **新增** | 快照行为测试 |
| `tests/test_transition.py` | **新增** | 状态迁移测试 |
| `tests/test_supersede.py` | **新增** | 替代语义测试 |
| `tests/test_path_safety.py` | **新增** | 路径安全测试 |
| `tests/test_attention.py` | **新增** | 注意力计算测试 |
| `tests/test_end_to_end.py` | **新增** | 端到端流程测试 |

### 1.3 行为契约

#### 统一执行流程

所有操作必须经过：

```
PRECHECK      → 检查 registry 存在、Schema 合法、项目根目录有效
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

#### 约束

- `INSPECT` 和 `PLAN` 永远只读。
- 没有确定性后端时只能执行到 `PLAN`（READ_ONLY_ADVISORY 模式）。
- Tier2 没有用户批准时不能进入 `APPLY`。
- `APPLY` 后必须重新读取 registry 和文件进行 `VERIFY`。

#### 路径安全规则

```python
# 所有受管路径必须经过此检查
candidate = (project_root / relative_path).resolve()
candidate.relative_to(project_root.resolve())  # 失败则拒绝
```

- registry 只保存项目内相对路径。
- 拒绝绝对路径。
- 拒绝 `../` 逃逸。
- 默认不跟随指向项目外部的 symlink。
- `SKILL_ROOT` 与 `PROJECT_ROOT` 显式分离。

#### Schema 校验时机

```
读取 registry
→ Schema 校验（jsonschema）
→ 业务不变量校验
→ 执行内存变更
→ 再次 Schema 和不变量校验
→ 原子写入（write-then-rename）
```

#### 删除 `delete` 公开入口

- `update_registry.py delete` 子命令移除。
- 仅保留内部 repair 能力（需 `--maintenance-mode`）。
- MVP 阶段直接移除入口。

### 1.4 前置条件

- Python 3.9+
- `pyyaml` 依赖
- `jsonschema` 新增依赖（用于运行时 Schema 校验）
- `pytest` 测试框架

### 1.5 测试用例

#### test_registry_schema.py

| 测试 | 说明 |
|------|------|
| `test_valid_registry_loads` | 合法 registry 正常加载 |
| `test_missing_required_field_rejected` | 缺少必填字段被拒绝 |
| `test_invalid_status_rejected` | 非法 status 被拒绝 |
| `test_invalid_doc_id_pattern_rejected` | doc_id 格式非法被拒绝 |
| `test_superseded_without_superseded_by_rejected` | SUPERSEDED 缺 superseded_by 被拒绝 |
| `test_archived_without_archive_rejected` | ARCHIVED 缺 archive 三元组被拒绝 |
| `test_duplicate_doc_id_rejected` | 重复 doc_id 被拒绝 |
| `test_duplicate_path_rejected` | 重复 path 被拒绝 |

#### test_path_safety.py

| 测试 | 说明 |
|------|------|
| `test_relative_path_accepted` | 相对路径正常接受 |
| `test_absolute_path_rejected` | 绝对路径被拒绝 |
| `test_dotdot_escape_rejected` | `../` 逃逸被拒绝 |
| `test_symlink_to_outside_rejected` | 指向项目外的 symlink 被拒绝 |
| `test_path_inside_project_root` | 解析后的路径在项目根内 |

#### test_transition.py

| 测试 | 说明 |
|------|------|
| `test_draft_to_reviewing` | DRAFT→REVIEWING 允许 |
| `test_reviewing_to_active` | REVIEWING→ACTIVE 允许 |
| `test_active_to_frozen_requires_user` | ACTIVE→FROZEN 需 user 批准 |
| `test_frozen_to_active_requires_user` | FROZEN→ACTIVE 需 user 批准 |
| `test_skip_level_rejected` | 跳级晋升被拒绝 |
| `test_resurrection_rejected` | SUPERSEDED/ARCHIVED→DRAFT 被拒绝 |
| `test_illegal_rejected` | 非法迁移被拒绝 |

### 1.6 拒绝条件

| 条件 | 行为 |
|------|------|
| Schema 校验失败 | 拒绝读写，报告具体字段 |
| 路径逃逸 | 拒绝操作，报告非法路径 |
| Tier2 无批准 | 拒绝 APPLY，仅输出 PLAN |
| 不变量冲突 | 拒绝写入，报告冲突详情 |
| 并发写冲突（未来） | 拒绝第二个写入者 |

### 1.7 完成证据

- [ ] `pytest tests/ -v` 全部通过
- [ ] 所有写操作支持 `--dry-run`
- [ ] 路径安全测试全部通过
- [ ] Schema 校验在每次读写时执行
- [ ] `delete` 公开入口已移除

---

## 2. Milestone B：修订闭环

### 2.1 目标

> 任意受管文档的当前版本、上一版本和变化都可以被准确还原。

### 2.2 修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `scripts/_core.py` | 修改 | 增加 revision 事件模型 |
| `scripts/update_registry.py` | 修改 | register 自动保存 r1；增加 `accept-revision` 子命令 |
| `scripts/snapshot_doc.py` | 修改 | 支持按 revision 命名快照 |
| `scripts/generate_diff.py` | 修改 | 支持任意两 revision 间 diff |
| `scripts/doc_steward.py` | 修改 | 增加 `sync --apply` 编排 |

### 2.3 行为契约

#### 三类状态分离

```yaml
# 治理生命周期（权威）
status: ACTIVE

# 仓库观察（派生）
observations:
  content_drift: true      # live hash != registry hash
  missing: false           # 文件不存在
  path_changed: false      # 文件路径改变
  stale_dependency: false  # 依赖被替代

# 输出层（派生）
derived:
  needs_attention: true
```

#### register 流程

```
读取 live 文档
→ 计算 content_hash
→ revision = 1
→ 保存 snapshots/<doc_id>/r1.md
→ registry 记录 r1 hash + 快照路径
→ 追加 history 事件：REGISTERED
```

**关键**：注册时必须立即保存 r1，否则文件后续被修改后，无法可靠重建上一版本。

#### 检测修改（sync --dry-run）

```
扫描 document_roots
→ 计算 live hash
→ 与 registry.content_hash 比较
→ 不同则标记 observations.content_drift=true
→ 使用 snapshot rN 与 live 文件生成 diff
→ 不修改 registry
→ 输出 change set
```

#### 接受新修订（sync --apply）

```
检查当前 status
→ 如果 FROZEN：
   → 拒绝接受
   → 报告 content_drift
   → 建议先 unfreeze
→ 如果 ACTIVE/REVIEWING/DRAFT：
   → 展示 change set
   → 用户确认
   → 保存 live 内容为 snapshot rN+1
   → revision = N+1
   → 更新 registry.content_hash
   → 追加 history 事件：REVISION_ACCEPTED
   → 校验并原子写入
```

#### revision 事件模型

```yaml
history:
  - event_id: EVT-20260729-001
    event_type: REGISTERED
    revision: 1
    content_hash: "aa" * 64
    at: "2026-07-29"
    actor: user
    reason: "初始登记"
  - event_id: EVT-20260729-002
    event_type: REVISION_ACCEPTED
    from_revision: 1
    to_revision: 2
    content_hash: "bb" * 64
    at: "2026-07-29"
    actor: user
    reason: "补充了错误码定义"
```

- `history` 是 append-only 数组。
- 本地项目规模较小时，放在 registry 中即可。
- 未来可迁移到外部事件存储。

#### FROZEN 语义

```
外部修改 FROZEN 文件
→ 检测到 content_drift
→ 标记 observations.content_drift=true
→ 阻止 sync --apply
→ 要求用户批准 unfreeze（FROZEN→ACTIVE）
→ 不自动改变 registry hash/revision
```

**关键**：doc-steward 不阻止外部文件修改，但拒绝静默接受、登记或把它视为有效修订。

### 2.4 前置条件

- Milestone A 完成
- 快照目录 `.doc-steward/snapshots/` 已存在

### 2.5 测试用例

#### test_revision.py

| 测试 | 说明 |
|------|------|
| `test_register_creates_r1_snapshot` | 注册后存在 r1 快照 |
| `test_register_records_r1_hash` | registry 记录 r1 hash |
| `test_content_drift_detected` | 修改文件后 content_drift=true |
| `test_revision_not_auto_incremented` | sync 不自动增加 revision |
| `test_accept_revision_creates_r2` | 接受后生成 r2 快照 |
| `test_revision_increments_to_2` | revision 增加为 2 |
| `test_sync_idempotent` | 重复 sync 不重复增加 revision |
| `test_frozen_drift_blocks_apply` | FROZEN 文档修改后只报告 drift，不能 apply |
| `test_failure_preserves_consistency` | 操作失败时 registry 与 snapshot 不出现不一致 |
| `test_history_appended_not_overwritten` | history 是追加而非覆盖 |

#### test_snapshot.py

| 测试 | 说明 |
|------|------|
| `test_snapshot_saved_with_revision` | 快照按 revision 命名 |
| `test_snapshot_content_matches_revision` | 快照内容匹配对应 revision |
| `test_snapshot_not_overwritten` | 已存在快照不被覆盖 |
| `test_meta_file_written` | meta.yaml 正确写入 |

### 2.6 拒绝条件

| 条件 | 行为 |
|------|------|
| FROZEN + content_drift | 拒绝 apply，要求先 unfreeze |
| revision 倒退 | 拒绝写入 |
| snapshot 已存在 | 不覆盖，报告冲突 |
| hash 不匹配 | 拒绝写入，报告预期 vs 实际 |

### 2.7 完成证据

- [ ] register 自动保存 r1 快照
- [ ] content drift 检测正确
- [ ] revision 接受流程完整
- [ ] history 是 append-only
- [ ] FROZEN drift 阻塞 apply
- [ ] 所有 revision 测试通过

---

## 3. Milestone C：注意力闭环

### 3.1 目标

> 用户只运行一次命令，就能知道现在该看什么，而不需要理解五个后端脚本。

### 3.2 修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `scripts/doc_steward.py` | 修改 | 增加 `inspect`、`focus`、`dashboard` 子命令 |
| `scripts/_core.py` | 修改 | 增加 `compute_attention()` 确定性算法 |
| `templates/dashboard.md.j2` | **新增** | Dashboard Jinja2 模板 |
| `templates/focus.md.j2` | **新增** | focus 输出模板 |
| `templates/l0_card.md.j2` | **新增** | L0 状态卡模板 |

### 3.3 行为契约

#### 注意力计算（确定性）

```python
def compute_attention(doc: dict, observations: dict) -> dict:
    """计算文档的注意力分级。
    
    返回：
    - blocked: bool      # 是否阻塞（冲突/非法/缺文件）
    - needs_attention: bool  # 是否需要关注
    - priority: "must_read" | "change_only" | "no_need"
    """
```

**阻塞项**（`blocked=true`）：
- registry 无效（Schema 校验失败）
- source-of-truth 冲突
- FROZEN content drift
- 缺少受管文件
- 非法状态关系
- 等待 Tier2 批准

**阅读优先级**：
- `must_read`：status==REVISIONING、本轮 status/revision 变化、attention.level==high
- `change_only`：revision 增加但无行为/接口变化
- `no_need`：稳定文档

#### L0 状态卡（确定性生成）

```markdown
## DOC-SYSTEM-DESIGN

- 状态：ACTIVE
- Revision：r4
- 仓库观察：内容已修改，尚未接受
- 上游依赖：1 项可能过期
- 是否阻塞：否
- 是否需要关注：是
```

**不包含 LLM 摘要**，仅输出结构化字段。

#### Focus 输出

```markdown
## 文档治理结果

### 阻塞问题
- DOC-X：source-of-truth 冲突，参与方：[...]

### 等待你的批准
- DOC-Y：FROZEN 内容漂移，建议先 unfreeze

### 必须阅读
- DOC-Z：REVIEWING 状态，等待评审

### 只需了解变化
- DOC-A：r3 → r4，新增错误码定义

### 无需关注
- DOC-B：ACTIVE，无变化

### 已检测但未执行的变更
- DOC-C：内容已修改，未接受新 revision

### 建议下一步
1. 批准 DOC-Y 的 unfreeze
2. 接受 DOC-C 的新 revision
```

#### Dashboard 结构

```markdown
# 文档治理 Dashboard

> 生成时间：2026-07-29 09:00
> Registry 哈希：a1b2c3...
> 受管文档总数：12

## 项目状态
- 阻塞问题：2
- 等待批准：1
- 需要阅读：3

## 当前事实源
| Domain | 文档 | Revision |
|--------|------|----------|
| architecture | DOC-SYSTEM-DESIGN | r4 |

## 最近修订
- DOC-SYSTEM-DESIGN：r3 → r4（2026-07-29）

## 等待批准
- DOC-RELEASE-PLAN：FROZEN 内容漂移

## 可能过期文档
- DOC-IMPLEMENTATION-PLAN：依赖 DOC-API-SPEC（已 SUPERSEDED）

## 活跃文档索引
| 文档 | 状态 | Revision | 需要关注 |
|------|------|----------|----------|
| DOC-SYSTEM-DESIGN | ACTIVE | r4 | 是 |

## 历史与归档
- DOC-SYSTEM-DESIGN-OLD：SUPERSEDED by DOC-SYSTEM-DESIGN@r4
- DOC-LEGACY-NOTES：ARCHIVED

---
> 本文件为派生阅读物。
> Registry 哈希：a1b2c3...
> 生成时间：2026-07-29 09:00
> 数据源：
>   - DOC-SYSTEM-DESIGN@r4 (hash: ...)
>   - DOC-API-SPEC@r2 (hash: ...)
```

#### Provenance 规则

每个派生产物必须包含：

```yaml
generated:
  registry_hash: "a1b2c3..."
  generated_at: "2026-07-29T09:00:00"
  generator: "doc-steward v0.2.0"
  sources:
    - doc_id: DOC-SYSTEM-DESIGN
      revision: 4
      content_hash: "..."
```

当 registry hash 变化时，Dashboard 自动判定需要重新生成。

### 3.4 前置条件

- Milestone A 完成
- Milestone B 完成
- Jinja2 模板引擎（可用 `string.Template` 替代，减少依赖）

### 3.5 测试用例

#### test_attention.py

| 测试 | 说明 |
|------|------|
| `test_conflict_blocked` | source-of-truth 冲突标记为 blocked |
| `test_frozen_drift_blocked` | FROZEN content drift 标记为 blocked |
| `test_reviewing_needs_attention` | REVIEWING 状态需要关注 |
| `test_change_needs_attention` | 本轮 revision 变化需要关注 |
| `test_high_attention_needs_attention` | attention.level==high 需要关注 |
| `test_stable_no_need` | 稳定文档无需关注 |
| `test_must_read_priority` | 必须阅读优先级正确 |
| `test_change_only_priority` | 只需了解变化优先级正确 |

#### test_end_to_end.py

| 测试 | 说明 |
|------|------|
| `test_register_sync_focus_flow` | 完整流程：register → sync → focus |
| `test_supersede_updates_focus` | supersede 后 focus 输出正确 |
| `test_archive_removes_from_active` | archive 后从活跃集移除 |
| `test_dashboard_includes_provenance` | Dashboard 包含 provenance |
| `test_dry_run_no_changes` | dry-run 不修改任何文件 |

### 3.6 拒绝条件

| 条件 | 行为 |
|------|------|
| registry hash 与 Dashboard 不匹配 | 标记 Dashboard 过期 |
| 缺少 provenance | 视为生成失败 |
| 模板渲染失败 | 报告错误，不输出不完整 Dashboard |

### 3.7 完成证据

- [ ] `doc_steward inspect` 输出完整状态
- [ ] `doc_steward focus` 输出最小阅读集
- [ ] `doc_steward dashboard` 生成 Dashboard
- [ ] 所有派生产物包含 provenance
- [ ] 注意力计算测试全部通过
- [ ] 端到端测试全部通过

---

## 4. 统一 CLI 设计

### 4.1 命令结构

```bash
doc_steward <command> [options]

Commands:
  inspect     只读扫描，输出当前状态
  focus       输出最小阅读集
    --output FILE   写入文件而非 stdout
  sync        同步文档状态
    --dry-run       仅检测，不修改
    --apply         接受检测到的变更
  transition  状态迁移
    --to STATUS     目标状态
    --reason TEXT   迁移原因
  supersede   声明替代
    --old DOC_ID    旧文档
    --new DOC_ID    新文档
    --reason TEXT   替代原因
  archive     逻辑归档
    --reason TEXT   归档原因
  validate    校验 registry 不变量
  dashboard   生成 Dashboard
    --output FILE   写入文件
```

### 4.2 统一选项

| 选项 | 说明 |
|------|------|
| `--root PATH` | 项目根目录 |
| `--registry PATH` | registry 路径（覆盖自动检测） |
| `--format FORMAT` | 输出格式：text/json/yaml |
| `--no-color` | 禁用颜色输出 |

### 4.3 返回码

| 返回码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 一般错误 |
| 2 | 校验失败（Schema/不变量） |
| 3 | 路径安全问题 |
| 4 | 用户批准缺失 |

---

## 5. 不在本计划范围内的能力

| 能力 | 原因 |
|------|------|
| `restore` | 定义不清，MVP 中不原地复活 |
| Front Matter drift | 非核心痛点 |
| 自动 Hook | 需要外部集成 |
| 多 Agent 并发 | 单用户场景不需要 |
| 密码学审批 | 会话授权足够 |
| 物理归档 | 默认仅逻辑归档 |
| 自然语言 query | Agent 可直接读 registry |
| 外部审批系统 | 本地手动调用 |
| 数据库事务 | 单文件 write-then-rename 足够 |
| 分布式锁 | 单用户场景不需要 |

---

## 6. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 用户不接受 revision 模型 | 闭环无法形成 | 早期用户测试 |
| 路径安全规则过严 | 合法操作被拒绝 | 提供 `--force` 覆盖 |
| Dashboard 模板维护成本 | 变更困难 | 保持模板简单 |
| 快照目录膨胀 | 磁盘占用 | 未来可添加清理策略 |

---

## 7. 验收标准总结

| 里程碑 | 验收条件 |
|--------|----------|
| A | `pytest tests/ -v` 全部通过；所有写操作支持 `--dry-run`；路径安全测试通过 |
| B | register 自动保存 r1；content drift 检测正确；revision 接受流程完整；FROZEN drift 阻塞 apply |
| C | `doc_steward focus` 输出最小阅读集；Dashboard 包含 provenance；端到端测试通过 |

---

**文档结束。**
