# 仓库指南

novel-master v1.1.0 — 工业级长篇网文多 Agent 编排 Skill。将用户意图路由到最小必要子 Skill 集合，执行文件所有权隔离，通过可审计的事务协议治理 Canon/状态。纯 Python，仅 pip 管理，无异步，无类抽象。

## 项目概述

`novel-master` 是一个**编排器 Skill** — 本身不生成内容。它负责识别用户意图、路由到最小必要子 Skill 集合、执行权限边界检查、在高风险操作前插入审批闸门，最终返回 `MasterResult` 汇总变更内容与待确认提案。

管理的六个子 Skill：

| Skill | 职责 | 可写区域 |
|---|---|---|
| `novel-brief` | 项目定位、卖点、读者画像 | `project_brief.md` |
| `story-architect` | 故事/人物/世界/情节架构 | `architecture/`、`characters/`、`world/`、`outline/` |
| `chapter-planner` | 章节规划、节拍、目标 | `chapters/plans/` |
| `chapter-writer` | 正文创作、续写、修订 | `chapters/drafts/` |
| `novel-reviewer` | 一致性、节奏、风格评审 | `reviews/` |
| `continuity-keeper` | Canon 核对、状态提交与恢复 | `state/` |

## 架构与数据流

```
用户请求
  → novel-master（编排器）
    1. 意图识别 + 项目定位
    2. 风险评估 + 审批闸门（高风险时）
    3. 构建 TaskEnvelope → 派发到最小必要子 Skill
    4. 子 Skill 返回 SkillResult（交付物 + 状态变更提案）
    5. 接受闸门（章节创作后）
    6. 状态提交（仅 ACCEPTED/PUBLISHED 内容）
    7. 汇总 → MasterResult 返回用户
```

**三层架构**：编排器（路由/审批/治理）→ 子 Skill（领域工作）+ references/schemas（共享契约与脚本）。

**13 条系统不变量**已冻结在 `docs/novel-master-architecture-v1.0.1-frozen.md`。编排器是唯一可写入 `project.yaml`、`workflow/route_log.md`、`workflow/pending_decisions.md`、`workflow/change_log.md` 的组件。

关键设计决策：
- **单一 Canon 写入者** — 仅 `continuity-keeper` 可写入 `state/`
- **chapter-writer 不可修改 Canon** — 草稿输出为 Proposal，接受后方可升格
- **评审/修订分离** — 评审者标记问题，作者执行修复
- **最小上下文包** — 发送给子 Skill 的上下文 ≤2000 实质字符 / ≤4000 tokens
- **多项目隔离** — 跨项目读写一律 `BLOCKED`

## 关键目录

```
novel-master/
├── SKILL.md                        # 编排器入口（路由逻辑、I/O 契约）
├── manifest.json                   # v1.1.0 包清单
├── agents/                         # Agent 接口配置（interface.yaml、openai.yaml）
├── references/                     # 8 份共享规则文档（路由、所有权、生命周期等）
├── schemas/                        # 7 个 JSON Schema Draft 2020-12 定义
├── scripts/                        # 7 个确定性 Python 校验脚本
├── templates/novel-project/        # 新项目模板（11 个分区目录 + 3 个启动文件）
├── tests/                          # 7 个 pytest 测试文件
├── evals/                          # 10 个回归用例（NM-REG-001..010）+ fixtures
├── docs/                           # 冻结架构、契约、实施指南
├── novel-brief/                    # 子 Skill：项目简报
├── chapter-planner/                # 子 Skill：章节规划
├── chapter-writer/                 # 子 Skill：正文创作
├── novel-reviewer/                 # 子 Skill：文本评审
├── continuity-keeper/              # 子 Skill：Canon 与状态治理
├── registry/                       # 包注册表（schema 2.0、校验和）
├── security/                       # 网络拒绝所有 + 权限策略
├── dist/                           # 构建产物（清单、zip、平台适配器）
├── reports/                        # 审计报告（漂移、一致性等）
└── examples/                       # 有效/无效 schema 示例
```

## 开发命令

```bash
# 运行时依赖（宽松版本）
pip install -r requirements.txt

# CI 依赖（锁定版本）
pip install -r requirements-ci.txt

# 运行完整测试套件
pytest tests/

# 运行单个测试文件
pytest tests/test_changeset.py

# 运行 prompt 回归
python scripts/prompt_regression_validator.py --report
```

无 `pyproject.toml`、无 `setup.py`、无 `Makefile`。测试直接通过 `pytest` 运行。

## 代码规范与常见模式

### Python 风格
- **纯过程式** — 无类、无 async、无装饰器
- **CLI 入口点** — 脚本使用 `argparse` + `if __name__ == "__main__"` 守卫
- **校验工具复用** — 跨模块导入共享（`validate_contract`、`validate_approval`、`validate_paths`）
- **错误处理** — 异常在 CLI 边界捕获；退出码映射到 `references/error-codes.md`

### JSON Schema 规范
- 全部 7 个 schema 使用 **Draft 2020-12**
- 每个 schema 对象**必须声明 `additionalProperties: false`**
- **严格校验** — 不允许隐式字段追加；所有属性必须预先声明
- schema 文件位于 `schemas/`，验证示例位于 `examples/valid/` 和 `examples/invalid/`

### 标识与版本
- **`revision`** = 单调递增整数，以**字符串**形式存储（如 `"1"`、`"42"`）
- **`content_hash`** = 文件内容的 SHA-256 十六进制摘要
- **过期上下文检测** — TaskEnvelope 中的 `base_revision` 必须与当前文件版本一致

### 文件所有权
每个子 Skill 在 `references/file-ownership.md` 中定义了明确的可写区域。越权写入 = `OWNERSHIP_VIOLATION` → `BLOCKED`。路径校验规则：
- 所有路径相对于项目根目录
- `..` 穿越一律拒绝
- 绝对路径一律拒绝
- 跨项目路径一律拒绝

### 状态与生命周期
四种信息状态及其允许转换：

```
UNKNOWN → PROPOSAL → CANON
                   → DEPRECATED
```

章节生命周期（仅允许正向转换）：

```
PLANNED → DRAFT → REVIEWED → ACCEPTED → PUBLISHED
                                 → SUPERSEDED
                                 → DEPRECATED
```

仅 `ACCEPTED` 或 `PUBLISHED` 状态的章节有资格执行 Canon 状态提交（`COMMIT_CHAPTER_STATE`）。

### ChangeSet 事务协议
所有 Canon/状态变更通过 ChangeSet 进行，支持回滚：

```
PREPARE → VALIDATE → APPLY → VERIFY → COMMIT
                                     → ROLLBACK（失败时）
```

实现方式：备份文件 + 临时文件 + `os.replace`（非数据库原子性）。Canon `DELETE` 在 schema 层通过 `not:allOf` 模式**永久禁止**。

## 重要文件

| 文件 | 用途 |
|---|---|
| `SKILL.md` | 编排器路由契约、激活规则、I/O 规格 |
| `agents/interface.yaml` | 通用 Agent 接口（显示名、提示、兼容性、信任层级） |
| `references/routing-table.md` | 13 条路由规则（步骤、审批闸门、状态提交） |
| `references/file-ownership.md` | 按 Skill 划分的文件区域矩阵（读/写/禁止） |
| `references/common-rules.md` | 8 条核心规则（信息状态、作用域、禁止伪造、所有权） |
| `references/error-codes.md` | 12 个统一错误码（BLOCKED / NEEDS_DECISION / FAILED） |
| `references/lifecycle-and-approval.md` | 章节生命周期、ApprovalRef schema、有效性校验 |
| `references/context-retrieval-rules.md` | continuity-keeper 的 10 维度上下文提取策略 |
| `references/fact-extraction-rules.md` | 什么内容进入 state_change_proposals，什么不进入 |
| `schemas/task-envelope.schema.json` | 派发信封（项目、任务类型/作用域/模式/风险、权限、上下文） |
| `schemas/skill-result.schema.json` | 子 Skill 返回（交付物、提案、问题、交接） |
| `schemas/changeset.schema.json` | 状态事务契约 |
| `schemas/approvalref.schema.json` | 审批令牌（作用域、版本绑定、一次性过期） |
| `schemas/context-pack.schema.json` | 发送给子 Skill 的受限上下文（≤2000 字符 / ≤4000 tokens） |
| `schemas/master-result.schema.json` | 编排器最终输出给用户 |
| `docs/novel-master-architecture-v1.0.1-frozen.md` | 冻结架构基线（610 行、13 条不变量） |
| `docs/novel-master-contracts-v1.0.1-frozen.md` | 冻结字段级契约（1577 行，唯一真相源） |
| `docs/novel-master-implementation-guide-v1.md` | 实施顺序、已知限制（未冻结） |

## 运行时与工具偏好

- **运行时**：Python >= 3.10（依赖最低要求 3.8+，但项目目标为 3.10+）
- **包管理器**：仅 `pip` — 无 Poetry、无 Conda、无 npm
- **必需库**：`PyYAML>=6.0`、`jsonschema>=4.20`、`pytest>=9.0`
- **CI 锁定版本**：`PyYAML==6.0.3`、`jsonschema==4.26.0`、`pytest==9.1.1`
- **无构建步骤** — Skill 为 markdown + YAML + JSON，由 Agent 平台直接消费
- **目标平台**：`openai`、`generic`（平台适配器位于 `dist/targets/`）
- **网络策略**：拒绝所有（`security/network_policy.json`）
- **发布闸门**：在 `security/permission_policy.md` 获得审阅者证据之前被阻塞

## 测试与质量保障

- **框架**：pytest 9.1.1
- **测试运行器**：`pytest tests/`（无 `conftest.py`；测试使用 `tmp_path`、`monkeypatch`）
- **7 个测试文件**：治理、prompt 回归、schema、changeset、审批、生命周期、路径
- **10 个回归用例**：`evals/evals.json`（NM-REG-001..010），文件支持的 fixtures 在 `evals/output/fixtures/`
- **校验方式**：所有 schema 测试使用 `jsonschema.Draft202012Validator`
- **基线**：127+ pytest 测试通过（截至 2026-07-25）
- **回归测试**：`scripts/prompt_regression_validator.py` 支持 sample + report 两种模式
- **覆盖重点**：契约合规、生命周期转换、所有权执行、Canon 保护

## 在本仓库工作：AI 助手注意事项

- **最小路由优先**：永远不要调用超过用户请求所需数量的子 Skill
- **Proposal 与 Canon 区分**：子 Skill 输出永远是 Proposal；仅 ACCEPTED/PUBLISHED 内容经 continuity-keeper 升格后成为 Canon
- **禁止伪造**：上下文不完整时，暴露为 `UNKNOWN` — 永远不要凭猜测补全 Canon
- **文件区域执行**：任何写入前，对照 `references/file-ownership.md` 确认当前 Skill 的可写区域
- **冻结意识**：架构（`§4,§5,§7,§8`）和契约（`§2,§5,§10,§11,§14`）已冻结 — 变更需附带文档化修订和回归测试
- **平台适配器**：`dist/targets/openai/adapter.json` 和 `dist/targets/generic/adapter.json` 是编译后的 IR — 通过 `yao-skill-ir-compiler` 重新生成，不要手动编辑
- **安全约束**：不要引入网络调用、子进程或交互式输入；`permission_policy.md` 在发布前必须经过审阅
