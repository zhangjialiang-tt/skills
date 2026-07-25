# novel-master

> 工业级长篇网文多 Agent 编排 Skill — 将创作意图转化为最小、可追踪、可验证的专业工作流。

`novel-master` 是一个编排器 Skill，负责识别用户创作意图、路由到最合适的子 Skill、管控权限与风险、维护跨章节一致性，并通过持久化项目状态实现可追溯、可审计、可恢复的长篇创作治理。

---

## 核心特性

- **意图驱动路由** — 自动识别用户请求类型，选择最小必要子 Skill 集合，不做多余调用
- **权限隔离** — 严格的文件所有权体系，每个 Skill 只能写入自己负责的区域
- **事实分离** — 严格区分已确认事实（Canon）、未确认建议（Proposal）和废弃内容（Deprecated）
- **状态治理** — 所有正式状态变更可追溯、可审计、可恢复
- **风险闸门** — 高风险操作（如改变主线、结局、核心规则）必须经过作者确认
- **冻结契约** — 架构和契约冻结基线，变更有记录、有回归、有版本

---

## 架构总览

```
novel-master (编排器)
├── novel-brief        — 项目简报：一本书的定位、卖点、读者画像
├── story-architect    — 故事架构：背景 / 人物 / 世界 / 情节
├── chapter-planner    — 章节规划：章纲、节拍、目标
├── chapter-writer     — 正文创作：草稿、续写、修订
├── novel-reviewer     — 文本评审：一致性、节奏、风格
└── continuity-keeper  — 连续性维护：Canon 核对、状态提交与恢复
```

---

## 标准工作流

```
1. 初始化项目
   novel-brief → story-architect (STORY/CHARACTER/WORLD/PLOT) → INITIALIZATION_REVIEW

2. 章节创作
   chapter-planner → chapter-writer → ACCEPTANCE_GATE → continuity-keeper (可选)

3. 文本评审
   novel-reviewer → 生成评审报告 → 作者决策

4. 状态提交
   continuity-keeper → 将 ACCEPTED/PUBLISHED 内容写入 state/
```

---

## 项目结构

```
novel-master/
├── SKILL.md                        # 编排器主文件
├── manifest.json                   # 包清单 (v1.1.0)
├── agents/                         # Agent 接口配置
├── references/                     # 公共规则、路由表、错误码等参考文档
│   ├── common-rules.md
│   ├── routing-table.md
│   ├── file-ownership.md
│   ├── error-codes.md
│   └── ...
├── docs/                           # 冻结架构与契约文档
│   ├── novel-master-architecture-v1.0.1-frozen.md
│   ├── novel-master-contracts-v1.0.1-frozen.md
│   └── ...
├── schemas/                        # JSON Schema 定义 (7 个)
├── scripts/                        # 确定性校验脚本
├── templates/novel-project/        # 新项目模板
├── tests/                          # 测试套件
├── evals/                          # 评测用例
├── examples/                       # 有效/无效示例
├── reports/                        # 审计报告
├── registry/                       # 包注册表
└── security/                       # 权限策略
```

---

## 子 Skill 一览

| Skill               | 职责                            | 可写区域                                             |
| ------------------- | ------------------------------- | ---------------------------------------------------- |
| `novel-brief`       | 项目简报、定位、卖点            | `project_brief.md`                                   |
| `story-architect`   | 故事架构（背景/人物/世界/情节） | `architecture/`、`characters/`、`world/`、`outline/` |
| `chapter-planner`   | 章节规划、章纲                  | `chapters/plans/`                                    |
| `chapter-writer`    | 正文创作、续写、修订            | `chapters/drafts/`                                   |
| `novel-reviewer`    | 文本评审、一致性检查            | `reviews/`                                           |
| `continuity-keeper` | Canon 核对、状态提交与恢复      | `state/`                                             |

---

## 快速开始

### 环境要求

- Python >= 3.10
- PyYAML >= 6.0
- jsonschema >= 4.20
- pytest >= 9.0（开发/测试）

### 安装依赖

```bash
pip install -r requirements.txt
# 或锁定版本
pip install -r requirements-ci.txt
```

### 运行测试

```bash
pytest tests/
```

### 创建新项目

使用 `templates/novel-project/` 模板初始化一个新的网文项目：

```bash
cp -r templates/novel-project/ my-novel-project/
```

模板包含完整目录结构：

```
my-novel-project/
├── project.yaml           # 项目元数据
├── project_brief.md       # 项目简报
├── architecture/          # 故事架构
├── characters/            # 角色档案
├── world/                 # 世界观设定
├── outline/               # 大纲
├── chapters/
│   ├── drafts/            # 草稿
│   └── plans/             # 章纲
├── reviews/               # 评审报告
├── state/                 # 正式状态
│   └── archives/          # 归档
├── workflow/              # 工作流日志
│   ├── approvals/
│   ├── backups/
│   ├── changesets/
│   └── runs/
└── style_guide.md         # 风格指南
```

---

## 关键设计原则

1. **最小路由** — 只调用完成任务所需的最小子 Skill 集合
2. **事实与提案分离** — AI 输出标记为 Proposal，必须经作者确认才成为 Canon
3. **文件所有权隔离** — 每个 Skill 只能写入自己负责的区域，防止越权
4. **状态变更可追溯** — 所有 Canon 变更通过 changeset 提交，可审计、可回滚
5. **高风险操作需确认** — 改变主题、主线、结局等操作必须经过 Approval Gate
6. **不伪造前文** — 上下文不完整时暴露未知项，不补造 Canon

---

## 文档

| 文档                                                            | 说明                                       |
| --------------------------------------------------------------- | ------------------------------------------ |
| [架构冻结基线](docs/novel-master-architecture-v1.0.1-frozen.md) | 系统目标、术语、总体架构、设计决策         |
| [契约冻结手册](docs/novel-master-contracts-v1.0.1-frozen.md)    | 字段级契约、路由、文件所有权、输入输出规范 |
| [实施指南](docs/novel-master-implementation-guide-v1.md)        | 实施顺序、验收方法                         |
| [路由表](references/routing-table.md)                           | 路由决策的可测试规则                       |
| [文件所有权](references/file-ownership.md)                      | 每个 Skill 的文件读写权限边界              |
| [公共规则](references/common-rules.md)                          | 所有 Skill 共享的规则                      |
| [错误码](references/error-codes.md)                             | 阻塞、失败、降级结果的错误码定义           |

---

## 版本与状态

- **当前版本**: 1.1.0
- **生命周期**: Production
- **架构冻结**: v1.0.1 (2026-07-24)
- **兼容性目标**: OpenAI / Generic

---

## 许可证

Proprietary — All Rights Reserved

Copyright (c) 2026 zhangjl.

本 Skill 包仅在所有者明确授权的环境中使用和分发，不授予任何开源许可。

---

## 更新日志

参见 [docs/novel-master-architecture-v1.0.1-frozen.md §16](docs/novel-master-architecture-v1.0.1-frozen.md) 变更记录章节。
