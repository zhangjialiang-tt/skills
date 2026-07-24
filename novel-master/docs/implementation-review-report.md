# novel-master V1 实施层 Prompt 执行结果检查报告

> 检查对象：`novel-master/docs/prompt.md`（V1 实施层补充与最小骨架建设 Prompt）
> 检查范围：`novel-master/` 全部新增产物
> 检查时间：2026-07-24
> 检查方式：逐项对照 prompt 17 节完成标准 + 第 4 节严格边界 + 第 13 节测试要求，并实际运行 pytest 验证
> 检查基准：冻结文档 `novel-master-architecture-v1.0.1-frozen.md`、`novel-master-contracts-v1.0.1-frozen.md`

---

## 0. 总体结论

**整体评价：骨架完整度 high，但存在 1 项 critical 偏离、5 项 major 偏离、若干 minor 偏离。**

- 目录骨架、Schema、references、SKILL.md、templates、单元测试基本到位，82 个测试用例在隔离 venv 中全部 PASSED。
- 但 **prompt 第 13.4 节明确要求的 10 条 Skill 回归样例完全缺失**，是本次执行的最大盲区。
- `commit_changeset.py` 未集成 ApprovalRef 校验，违反 prompt 第 4.3 节"必须由脚本承担"的硬性要求。
- 6 个 schema 根级别未设置 `additionalProperties: false`，无法拒绝额外字段。
- `progress.md` 自称"运行测试 DONE"过于乐观，未记录运行环境前提（系统 Python 下 pytestqt 插件冲突会导致 pytest 直接崩溃）。

| 维度 | 状态 |
| --- | --- |
| 冻结文档未被修改 | ✅ 通过 |
| 目录骨架完整 | ⚠️ references 缺 1 个文件 |
| 实施说明文档章节 | ✅ 通过（7.1-7.8 全覆盖） |
| references 内容质量 | ✅ 通过（覆盖度好） |
| Schema 必填字段与枚举 | ✅ 通过（22 个枚举全对齐） |
| Schema additionalProperties | ❌ 6/7 缺失（major） |
| Schema 条件校验 | ⚠️ 部分（缺 expires_after_use、COMMIT_CHAPTER_STATE 来源限制等） |
| 辅助脚本功能 | ⚠️ 部分实现（commit_changeset 缺 ApprovalRef + Schema 校验） |
| 1+6 SKILL.md 骨架 | ✅ 通过（13 字段全覆盖） |
| 项目模板 | ✅ 通过 |
| 合法/非法样例 | ⚠️ 部分（invalid 缺 4 个场景文件，但单测覆盖） |
| Schema 单元测试 | ✅ 10/10 场景覆盖 |
| 生命周期测试 | ✅ 全覆盖 |
| ChangeSet 事务测试 | ⚠️ 4/8 场景覆盖 |
| Skill 回归样例 | ❌ 0/10（critical） |
| 测试运行 | ✅ 隔离 venv 82 passed；⚠️ 系统 Python 环境崩溃 |
| 边界遵守 | ⚠️ 未扩展架构、未修改冻结；但 4.3 ApprovalRef 强制校验未落地 |

---

## 1. 完成标准对照（prompt 第 16 节）

| 完成标准项 | 实际状态 | 证据 |
| --- | --- | --- |
| 未修改两份冻结文档 | ✅ | `git status` 显示冻结文档不在 untracked/modified 列表，已在 commit `f00195c` |
| 创建实施说明 | ✅ | `docs/novel-master-implementation-guide-v1.md` 存在，覆盖 §0-§9 |
| 创建目标目录骨架 | ⚠️ | `references/` 缺 `lifecycle-and-approval.md`，仅 7/8 文件 |
| 创建所有要求的 reference 文件 | ❌ | 同上，缺 `lifecycle-and-approval.md` |
| 创建七类 Schema | ✅ | 7 个 schema 文件全部存在 |
| 创建合法和非法样例 | ⚠️ | valid 5 个、invalid 6 个；invalid 缺场景 6/8/9/10 的独立文件（但单测覆盖） |
| 创建辅助脚本骨架或实现 | ⚠️ | 6 个脚本全部存在；`commit_changeset.py` 缺 ApprovalRef + Schema 校验 |
| 创建 1+6 Skill.md 骨架 | ✅ | novel-master + 6 子 Skill 全部存在，13 字段全覆盖 |
| 创建小说项目模板 | ✅ | `templates/novel-project/` 下全部目录和文件齐全 |
| 创建最小单章闭环说明 | ⚠️ | 实施说明 §1.2 路由表覆盖闭环路由；但缺少独立的"最小闭环说明"文档 |
| 创建并运行基础测试 | ⚠️ | 5 个测试文件存在；隔离 venv 82 passed；系统 Python 环境下 pytest 崩溃 |
| 真实报告测试 PASS/FAIL | ❌ | `progress.md` 仅写"运行测试 DONE"，未记录 PASS 数、环境前提、已知崩溃 |
| 未完成项明确列出 | ❌ | `progress.md` 未列出任何未完成项；`implementation-known-issues.md` 自称"无已知冲突" |
| 没有声称实现未验证能力 | ⚠️ | 脚本无违规声明；但 `progress.md` 把"运行测试"标 DONE 而不提环境问题，属于过度乐观 |

---

## 2. 偏离项清单

### 2.1 Critical 偏离（必须修复）

#### C1. Skill 回归样例完全缺失

- **prompt 要求**：第 13.4 节"至少创建以下 prompt regression 样例"，明确列出 10 条：
  1. 用户要求"只分析"，不得修改源文件和状态
  2. 用户要求"不要修改任何东西"，不得保存评审报告
  3. Writer 不得把 DRAFT 直接提交状态
  4. Writer 发现大纲与 Canon 冲突时返回 NEEDS_DECISION
  5. Reviewer 只诊断，不重写正文
  6. Story Architect 未声明模式时拒绝
  7. Story Architect 声明多个模式时拒绝
  8. L2 润色不得改变事实
  9. 章节中出现普通杯子，不应默认提取为状态候选
  10. 人物得知关键秘密，应提取为 knowledge state 变化
- **实际状态**：项目中无任何 prompt regression 样例文件或目录（`find` 搜索 `*regression*`、`*prompt-sample*` 均无结果）。
- **影响**：prompt 第 13.4 节是"至少创建"的硬性要求，完全缺失意味着 Skill 行为约束无法回归验证。这恰是 V1 骨架最需要保护的设计意图（防止 Skill 越权、防止把 DRAFT 提交为 Canon、防止 Reviewer 重写正文等）。
- **修正建议**：
  - 在 `tests/regression/` 或 `examples/prompt_regression/` 下创建 10 个 markdown 样例文件，每个包含：用户 prompt、期望 Skill 行为、禁止行为、验收点。
  - 样例可参考 `references/common-rules.md`、`references/fact-extraction-rules.md` 中的禁止条款编写。
  - 至少把第 3、4、6、7 条做成可执行断言（结合 schema 校验脚本）。

---

### 2.2 Major 偏离（应修复）

#### M1. `commit_changeset.py` 未集成 ApprovalRef 校验

- **prompt 要求**：第 10.6 节"先校验 Schema、路径、锁、revision 和 ApprovalRef"；第 4.3 节将 ApprovalRef 有效性校验列为"必须由脚本或校验逻辑承担，不得仅依赖 Skill 自我约束"。
- **实际状态**：`commit_changeset.py` 的 `main` 函数（L386-417）只调用 `verify_lock` 和 `validate_changeset`，**全程未调用 `validate_approval.py` 或其逻辑**。ChangeSet 可在无有效 ApprovalRef 的情况下提交。
- **影响**：违反 prompt 第 4.3 节硬性要求；`COMMIT_CANON` / `RETCON` / `EDIT_L3` / `EDIT_L4` 等高风险操作的事务入口失去脚本层防护。
- **修正建议**：
  - 在 `commit_changeset.py` 的 `validate_changeset` 之后、Phase 1 备份之前，新增 ApprovalRef 校验步骤。
  - 校验逻辑：加载 ChangeSet 中引用的 `approval_ref`，调用 `validate_approval.validate()`，校验 status=ACTIVE、operation 匹配、scope 覆盖 target_updates、revision 匹配、一次性授权未使用。
  - 校验失败返回 `BLOCKED / INVALID_APPROVAL`，不进入事务流程。
  - 同时在脚本头补 TODO 标注 ApprovalRef 集成为"V1.1 待实现"，避免静默。

#### M2. 6 个 Schema 根级别未设置 `additionalProperties: false`

- **prompt 要求**：第 9 节第 4 条"设置 `additionalProperties` 策略"。
- **实际状态**：仅 `task-envelope.schema.json` 根级别设置了 `additionalProperties: false`；其余 6 个 schema（`skill-result`、`approval-ref`、`changeset`、`context-pack`、`master-result`、`recovery-report`）根级别均未设置。
- **影响**：这 6 个 schema 不会拒绝额外字段，无法捕获拼写错误或未授权字段，违反"严格契约"定位。
- **修正建议**：
  - 为 6 个 schema 根级别补 `additionalProperties: false`。
  - 对 task-envelope 的嵌套对象（project/task/authority/context/constraints/output/semantic_impact/file_ref）也补 `additionalProperties: false`（或显式声明 `true` 并说明理由）。
  - 补一个 invalid 样例 `additional-property-rejected.json` 并加单测。

#### M3. `approval-ref.schema.json` 缺 `expires_after_use` 条件校验

- **prompt 要求**：第 9 节第 5 条"对条件权限使用 `if/then/else` 或等价机制"；冻结契约 §7"L4 和 RETCON 必须使用 `expires_after_use: true` 的一次性授权"。
- **实际状态**：schema 中无任何 `if/then` 机制强制 `operation ∈ {EDIT_L4, RETCON}` 时 `expires_after_use: true`。
- **影响**：L4/RETCON 操作可能使用永久授权，违反契约不变量。
- **修正建议**：在 `approval-ref.schema.json` 中添加：
  ```json
  {
    "if": { "properties": { "operation": { "enum": ["EDIT_L4", "RETCON"] } }, "required": ["operation"] },
    "then": { "properties": { "expires_after_use": { "const": true } }, "required": ["expires_after_use"] }
  }
  ```

#### M4. `COMMIT_CHAPTER_STATE` 来源状态限制未在 schema 层建模

- **prompt 要求**：第 9 节第 8 条"对 `COMMIT_CHAPTER_STATE` 的来源状态限制为 `ACCEPTED | PUBLISHED`"。
- **实际状态**：7 个 schema 中无任何字段承载 `commit_input.source_deliverable.chapter_lifecycle_status`，无法通过 schema 校验来源章节是否为 ACCEPTED/PUBLISHED。
- **影响**：DRAFT/REVIEWED 章节可能通过 schema 校验进入状态提交流程；当前仅靠 `continuity-keeper` 的 SKILL.md 文字约束和 `commit_changeset.py` 的 TODO 注释阻止。
- **修正建议**：
  - 在 `changeset.schema.json` 中扩展 `source_ref` 为对象，包含 `deliverable_id`、`chapter_lifecycle_status` 字段。
  - 添加 `if/then`：当 `target_updates` 涉及 `state/` 且 operation=MODIFY 时，强制 `source_ref.chapter_lifecycle_status ∈ {ACCEPTED, PUBLISHED}`。
  - 或新增 `commit-input.schema.json` 子 schema 并在 changeset 中 `$ref` 引用。

#### M5. `progress.md` 未真实报告测试结果与环境前提

- **prompt 要求**：第 17.3 节"提供实际执行命令和真实结果 PASS/FAIL/SKIPPED。禁止只写'测试应该通过'"；第 14 节"不生成伪造测试结果"。
- **实际状态**：
  - `progress.md` 仅写"运行测试 | DONE"，无 PASS 数、无执行命令、无环境前提。
  - 实测：当前 shell `python -m pytest`（系统 Python 3.13 + 全局 site-packages 的 pytestqt 插件）会因 `ModuleNotFoundError: No module named 'typing_extensions'` 在 plugin 加载阶段崩溃，无法收集测试。
  - 在隔离 venv（`C:/Users/zhangjl/.workbuddy/binaries/python/envs/default`，已安装 pyyaml/jsonschema/pytest）中运行：**82 passed in 1.61s**。
- **影响**：用户按 progress.md 的"DONE"判断会误以为任意环境都能跑通；实际依赖未声明，初次克隆者无法复现。
- **修正建议**：
  - 在 `progress.md` 中补：
    - 执行命令：`python -m pytest tests/ -v`
    - 真实结果：`82 passed`
    - 依赖前提：`pip install pyyaml jsonschema pytest`（或新增 `requirements.txt`）
    - 已知环境问题：系统全局 Python 若装了 pytestqt 但缺 typing_extensions，pytest 会在插件加载阶段崩溃；建议使用隔离 venv。
  - 在项目根新增 `requirements.txt`：`pyyaml>=6.0\njsonschema>=4.20\npytest>=9.0`。

---

### 2.3 Minor 偏离（建议修复）

#### m1. `references/lifecycle-and-approval.md` 缺失

- **prompt 要求**：第 6 节目标目录结构中 `references/` 列出 8 个文件，包含 `lifecycle-and-approval.md`。
- **实际状态**：`references/` 目录只有 7 个文件，缺 `lifecycle-and-approval.md`。`progress.md` 自称"共享 references（7 文件）DONE"，与 prompt 要求的 8 个不一致。
- **影响**：章节生命周期和接受闸门规则散落在 `routing-table.md` 末尾和 `common-rules.md` 中，缺乏独立可引用的单一来源。
- **修正建议**：新增 `references/lifecycle-and-approval.md`，集中定义：
  - 7 个生命周期状态（PLANNED/DRAFT/REVIEWED/ACCEPTED/SUPERSEDED/DEPRECATED/PUBLISHED）。
  - 允许的转换矩阵（与 `tests/test_lifecycle.py` 一致）。
  - 接受闸门规则（ACCEPT_CHAPTER 触发条件、ApprovalRef 绑定、revision 锁定）。
  - 然后从 `routing-table.md` 末尾的"接受闸门规则"小节移除冗余内容，改为引用。

#### m2. 子 SKILL.md 未引用 `references/` 共享规则

- **prompt 要求**：第 8 节"不要复制整份冻结契约"；第 11.2 节"不要把完整冻结文档复制进去。通过 references 引用共享规则"。
- **实际状态**：6 个子 SKILL.md 的"相关 references"部分只引用了 `docs/novel-master-contracts-v1.0.1-frozen.md` 和 `docs/novel-master-architecture-v1.0.1-frozen.md` 的章节号，**没有引用 `references/` 下的任何共享规则文件**。
- 而 `references/` 文件本身的头部注释声称"引用方式：每个子 Skill 的 SKILL.md 中 `include: references/common-rules.md`"，实际并未落地。
- **影响**：共享规则与子 Skill 的耦合关系不明确；子 Skill 执行时可能漏读关键约束（如 `common-rules.md` 的"不得伪造缺失上下文"、`fact-extraction-rules.md` 的"普通杯子不提取"）。
- **修正建议**：在每个子 SKILL.md 的"相关 references"部分追加具体的共享规则文件列表，例如：
  - `novel-brief`：`references/common-rules.md`、`references/file-ownership.md`、`references/error-codes.md`、`references/style-guide-template.md`
  - `chapter-writer`：增加 `references/fact-extraction-rules.md`、`references/context-retrieval-rules.md`、`references/style-guide-template.md`
  - `continuity-keeper`：增加 `references/fact-extraction-rules.md`、`references/context-retrieval-rules.md`

#### m3. `validate_approval.py` 缺 hash 校验

- **prompt 要求**：第 10.4 节"校验 revision/hash"。
- **实际状态**：`validate_approval.py` L115-129 只校验 `based_on_revision`，**未对比 `content_hash`**。
- **影响**：revision 未变但内容被篡改的场景无法发现。
- **修正建议**：在 `validate_approval.py` 中新增 hash 比对逻辑，并在文件头补 TODO 标注当前仅校验 revision。

#### m4. `validate_paths.py` 跨项目检测为死代码

- **prompt 要求**：第 10.2 节"检测跨项目访问"。
- **实际状态**：`detect_cross_project` (L97-107) 仅查 `../`/`..\`，而该模式已在 `normalize_path` (L38-40) 拦截，函数实际无法发现任何新攻击面。
- **影响**：跨项目访问检测名义存在但实际无效。
- **修正建议**：要么删除 `detect_cross_project` 并在 `normalize_path` 注释中说明已覆盖；要么实现真正的跨项目检测（例如校验 `root_path` 是否属于已注册的 project_id 集合）。同时补 TODO 标注当前实现局限。

#### m5. PyYAML 依赖未记录安装方式

- **prompt 要求**：第 14 节"YAML 依赖如有必要应记录安装方式"。
- **实际状态**：4 个脚本（`validate_approval.py`、`project_lock.py`、`commit_changeset.py`、`validate_contract.py`）`import yaml`，但项目无 `requirements.txt`/`pyproject.toml`；`implementation-guide-v1.md` 只记录了 `jsonschema 4.24.0 + pytest 9.1.1`，未记录 PyYAML。
- **修正建议**：新增 `requirements.txt` 记录 `pyyaml`、`jsonschema`、`pytest`，并在 `implementation-guide-v1.md` §0 平台能力调查表中补 PyYAML 版本。

#### m6. `commit_changeset.py` CREATE 操作回滚不完整

- **实际状态**：`replaced_files` 仅记录 MODIFY/DELETE 的备份，rollback 仅 `shutil.copy2(backup, target)`；CREATE 操作失败后新创建的文件未被删除，可能残留。
- **修正建议**：在 `replaced_files` 中区分 operation 类型，rollback 时对 CREATE 执行 `unlink`，对 MODIFY/DELETE 执行 `copy2`。

#### m7. `commit_changeset.py` Phase 5 revision 一律 +1

- **实际状态**：Phase 5 (L274-281) 对 MODIFY/CREATE 一律 `old_rev + 1`，未调用 `compute_revision.py` 的"内容未变化不递增"逻辑。
- **影响**：对未实际变化的文件可能递增 revision，破坏"内容未变化时不递增"不变量。
- **修正建议**：Phase 5 调用 `compute_revision.compute_or_update` 比较新旧 hash，决定是否递增。

#### m8. `examples/invalid/` 缺 4 个场景的独立样例文件

- **prompt 要求**：第 9 节"至少提供 examples/valid/ 和 examples/invalid/，合法和非法样例"。
- **实际状态**：invalid 目录有 6 个文件，覆盖 prompt 13.1 的场景 2/3/4/5/7 + Canon DELETE。但场景 6（非 ACCEPTED 章节提交状态）、8（路径越界）、9（所有权违规）、10（Proposal 进 committed_updates）无独立 invalid 文件。
- 注：这 4 个场景在 `test_schemas.py::TestContractRules` 中有代码级断言覆盖，所以契约层面已验证，只是缺独立样例文件。
- **修正建议**：补 4 个 invalid json 文件，便于人工查阅和回归。

#### m9. `examples/valid/task-envelope-valid.json` 中 hash 格式不规范

- **实际状态**：`hash` 字段值为 `"sha256:a1b2c3d4e5f6"`，不是合法的 SHA-256 hex（应 64 个 hex 字符）。
- **影响**：schema 未对 hash 格式做约束，样例能通过校验，但作为"合法样例"会误导使用者。
- **修正建议**：把 hash 改为真实的 64 字符 hex（可用 `python -c "import hashlib; print(hashlib.sha256(b'test').hexdigest())"` 生成）；或在 schema 中对 hash 加 `pattern: "^[a-f0-9]{64}$"` 约束。

#### m10. `project_lock.py` / `commit_changeset.py` 未捕获 `YAMLError`

- **实际状态**：`load_lock` (project_lock.py L29-34) 和 `verify_lock` (commit_changeset.py L108-118) 用 `yaml.safe_load` 但未捕获 `YAMLError`，锁文件损坏会抛未处理异常。
- **修正建议**：补 `try/except yaml.YAMLError`，返回明确的 `BLOCKED / SCHEMA_INVALID` 错误。

#### m11. `templates/novel-project/project.yaml` 内容过简

- **实际状态**：仅 9 行（schema_version/project_id/title/language/root_path/current_volume/current_chapter/created_at/updated_at）。
- **影响**：缺少 style_guide 路径、状态文件清单、approval_policy 等运行时元信息。
- **修正建议**：补 `style_guide_path`、`state_files`（canon/timeline/character_state/knowledge_state/open_loops/foreshadowing 等默认路径）、`auto_accept.enabled: false`、`lifecycle_policy` 等字段。

#### m12. `docs/inbox/` 含 prompt 未要求的额外文件

- **实际状态**：`docs/inbox/` 下有 `craft-1.md`、`craft-2.md`、`craft-3.md`，不在 prompt 要求范围内。
- **影响**：无害，但属于任务范围外的产物。
- **修正建议**：确认这些文件是否为先前笔记；若是，可保留但在 `progress.md` 中说明"非本次任务产物"。

---

## 3. 边界遵守情况（prompt 第 4 节）

| 边界项 | 遵守情况 | 证据 |
| --- | --- | --- |
| 4.1 未修改冻结文档 | ✅ | git status 显示冻结文档未变 |
| 4.1 未直接创建新冻结版本 | ✅ | 无 `*-frozen.md` 新文件 |
| 4.1 问题记录到 known-issues | ⚠️ | `implementation-known-issues.md` 存在但自称"无已知冲突"，未记录本次检查发现的偏离 |
| 4.2 未新增子 Skill | ✅ | 仍是 1+6 架构 |
| 4.2 未改变 1+6 架构 | ✅ | 路由表与冻结契约一致 |
| 4.2 未拆分 story-architect | ✅ | story-architect 仍为单一 Skill，4 模式互斥 |
| 4.2 未拆分 chapter-writer/EDIT | ✅ | chapter-writer 含 WRITE/CONTINUE/EDIT 三模式 |
| 4.2 未增加市场/封面/漫剧/发布 | ✅ | 无相关 Skill 或文件 |
| 4.2 未引入跨项目共享世界观 | ✅ | 无相关文件 |
| 4.2 未修改 Canon 单一写入者 | ✅ | `file-ownership.md` 明确 continuity-keeper 是 state/ 唯一写入者 |
| 4.2 未绕过章节接受闸门 | ✅ | `routing-table.md` 接受闸门规则齐全 |
| 4.2 未绕过 ApprovalRef/ChangeSet | ⚠️ | 路由表要求 ApprovalRef，但 `commit_changeset.py` 未强制校验（见 M1） |
| 4.3 JSON Schema 校验由脚本承担 | ✅ | `validate_contract.py` 实现 |
| 4.3 路径越界校验由脚本承担 | ✅ | `validate_paths.py` 实现（部分死代码，见 m4） |
| 4.3 文件所有权校验由脚本承担 | ✅ | `validate_paths.py` 的 `check_ownership` 实现 |
| 4.3 revision 和 hash 计算由脚本承担 | ✅ | `compute_revision.py` 实现 |
| 4.3 stale context 校验由脚本承担 | ✅ | `commit_changeset.py` L170-187 实现 |
| 4.3 ApprovalRef 有效性校验由脚本承担 | ⚠️ | `validate_approval.py` 实现但未集成进 `commit_changeset.py`（见 M1） |
| 4.3 ChangeSet 提交流程由脚本承担 | ✅ | `commit_changeset.py` 实现（缺 ApprovalRef + Schema 校验） |
| 4.3 Canon 删除拦截由脚本承担 | ✅ | `commit_changeset.py` L157-161 + `changeset.schema.json` L53-70 双重拦截 |
| 4.3 多文件状态写入回滚由脚本承担 | ⚠️ | `commit_changeset.py` L306-352 实现，但 CREATE 回滚不完整（见 m6） |
| 4.3 单项目写锁由脚本承担 | ✅ | `project_lock.py` 实现 |
| 4.3 未声称具备完整事务能力 | ✅ | `commit_changeset.py` L9-10 明确否认 DB 级保证 |

---

## 4. 测试运行真实结果

### 4.1 执行命令

```bash
cd novel-master
# 使用隔离 venv（避免系统 Python 的 pytestqt 插件冲突）
C:/Users/zhangjl/.workbuddy/binaries/python/envs/default/Scripts/python.exe -m pytest tests/ -v
```

### 4.2 真实结果

```
============================= 82 passed in 1.61s ==============================
```

### 4.3 测试覆盖度对照

| prompt 要求 | 覆盖情况 |
| --- | --- |
| 13.1 Schema 测试 10 场景 | ✅ 10/10（`test_schemas.py` 中 `TestContractRules` 全覆盖） |
| 13.2 生命周期测试 8 转换 + 非法拒绝 | ✅ 全覆盖（`test_lifecycle.py` 38 个用例） |
| 13.3 ChangeSet 测试 8 场景 | ⚠️ 4/8（缺：临时文件校验失败、第二文件替换失败恢复、change_log 更新失败回滚、Canon DELETE 拒绝已有但仅单测） |
| 13.4 Skill 回归样例 10 条 | ❌ 0/10（见 C1） |

### 4.4 已知环境问题

- **系统 Python 3.13 + 全局 site-packages 的 pytest** 会因 pytestqt 插件缺失 typing_extensions 在插件加载阶段崩溃，无法收集测试。
- **隔离 venv** 需手动安装 `pyyaml jsonschema pytest`，项目无 `requirements.txt`。
- 建议在 `progress.md` 或 `README` 中记录运行前提。

---

## 5. 修正建议优先级排序

### P0（critical，必须立即修复）

1. **C1**：创建 10 条 Skill 回归样例（`tests/regression/` 或 `examples/prompt_regression/`）。

### P1（major，本轮内修复）

2. **M1**：`commit_changeset.py` 集成 ApprovalRef 校验。
3. **M2**：6 个 schema 根级别补 `additionalProperties: false`。
4. **M3**：`approval-ref.schema.json` 补 `expires_after_use` 条件校验。
5. **M4**：`changeset.schema.json` 建模 `source_deliverable.chapter_lifecycle_status` 并加条件校验。
6. **M5**：`progress.md` 补真实测试结果与环境前提；新增 `requirements.txt`。

### P2（minor，下轮迭代修复）

7. **m1**：补 `references/lifecycle-and-approval.md`。
8. **m2**：子 SKILL.md 引用 `references/` 共享规则文件。
9. **m3**：`validate_approval.py` 补 hash 校验。
10. **m4**：`validate_paths.py` 跨项目检测死代码处理。
11. **m5**：PyYAML 依赖记录（与 M5 合并）。
12. **m6**：`commit_changeset.py` CREATE 回滚补 unlink。
13. **m7**：`commit_changeset.py` Phase 5 调用 compute_revision 决定是否递增。
14. **m8**：补 4 个 invalid 样例文件。
15. **m9**：修正 `task-envelope-valid.json` 的 hash 格式。
16. **m10**：补 `YAMLError` 捕获。
17. **m11**：扩展 `project.yaml` 模板字段。
18. **m12**：确认 `docs/inbox/` 文件归属。

---

## 6. 文件清单核对

### 6.1 新增文件（与 prompt 第 6 节目录结构对照）

| 路径 | 状态 |
| --- | --- |
| `novel-master/SKILL.md` | ✅ |
| `novel-master/references/common-rules.md` | ✅ |
| `novel-master/references/routing-table.md` | ✅ |
| `novel-master/references/file-ownership.md` | ✅ |
| `novel-master/references/fact-extraction-rules.md` | ✅ |
| `novel-master/references/error-codes.md` | ✅ |
| `novel-master/references/style-guide-template.md` | ✅ |
| `novel-master/references/context-retrieval-rules.md` | ✅ |
| **`novel-master/references/lifecycle-and-approval.md`** | ❌ 缺失 |
| `novel-master/schemas/task-envelope.schema.json` | ✅ |
| `novel-master/schemas/skill-result.schema.json` | ✅ |
| `novel-master/schemas/approval-ref.schema.json` | ✅ |
| `novel-master/schemas/changeset.schema.json` | ✅ |
| `novel-master/schemas/context-pack.schema.json` | ✅ |
| `novel-master/schemas/master-result.schema.json` | ✅ |
| `novel-master/schemas/recovery-report.schema.json` | ✅ |
| `novel-master/scripts/validate_contract.py` | ✅ |
| `novel-master/scripts/validate_paths.py` | ✅ |
| `novel-master/scripts/compute_revision.py` | ✅ |
| `novel-master/scripts/validate_approval.py` | ✅ |
| `novel-master/scripts/project_lock.py` | ✅ |
| `novel-master/scripts/commit_changeset.py` | ✅ |
| `novel-master/templates/novel-project/project.yaml` | ✅ |
| `novel-master/templates/novel-project/project_brief.md` | ✅ |
| `novel-master/templates/novel-project/style_guide.md` | ✅ |
| `novel-master/templates/novel-project/{architecture,characters,world,outline,reviews,state,state/archives,chapters/plans,chapters/drafts}/.gitkeep` | ✅ |
| `novel-master/templates/novel-project/workflow/{runs,approvals,changesets,backups}/.gitkeep` | ✅ |
| `novel-master/templates/novel-project/workflow/{route_log,pending_decisions,change_log}.md` | ✅ |
| `novel-master/examples/valid/*.json` | ✅ 5 个 |
| `novel-master/examples/invalid/*.json` | ⚠️ 6 个（缺 4 个场景） |
| `novel-master/tests/test_{schemas,paths,approval,lifecycle,changeset}.py` | ✅ 5 个 |
| **`novel-master/tests/regression/` 或 `examples/prompt_regression/`** | ❌ 缺失（C1） |
| `novel-master/novel-brief/SKILL.md` | ✅ |
| `novel-master/story-architect/SKILL.md` | ✅ |
| `novel-master/chapter-planner/SKILL.md` | ✅ |
| `novel-master/chapter-writer/SKILL.md` | ✅ |
| `novel-master/novel-reviewer/SKILL.md` | ✅ |
| `novel-master/continuity-keeper/SKILL.md` | ✅ |
| `novel-master/docs/novel-master-implementation-guide-v1.md` | ✅ |
| `novel-master/docs/implementation-known-issues.md` | ✅ |
| `novel-master/docs/implementation-progress.md` | ✅ |
| **`novel-master/requirements.txt`** | ❌ 缺失（M5） |

### 6.2 未修改的冻结文件

- `novel-master/docs/novel-master-architecture-v1.0.1-frozen.md` ✅
- `novel-master/docs/novel-master-contracts-v1.0.1-frozen.md` ✅

### 6.3 任务范围外的额外文件（需确认）

- `novel-master/docs/inbox/craft-{1,2,3}.md`（非 prompt 要求，疑似先前笔记）

---

## 7. 下一步建议（单一最自然下一步）

> **修复 C1 + M1 + M5，补齐 prompt 第 13.4 节的 10 条 Skill 回归样例，并在 `commit_changeset.py` 中集成 ApprovalRef 校验，同时把 `progress.md` 的测试结果改为真实记录（82 passed + 隔离 venv 前提 + requirements.txt）。**

完成这三项后，V1 骨架才真正满足 prompt 第 16 节"完成标准"中的"未完成项明确列出"和"没有声称实现未验证能力"两条。
