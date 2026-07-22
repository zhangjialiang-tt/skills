---
name: ai-plat-bridge
version: "2.0"
description: >
  AI 工作台跨路径桥接。当 AI 当前工作目录不在 AI-Plat vault 时，响应对工作台的读写请求。
  读取不要求工程变化；写入仅在状态变化、动作完成、结论形成、决策确定、阻塞点改变或任务推进时触发。
  触发词：记录到工作台、查工作台、查项目状态、查今日日志、工作台同步、更新项目文件、写工作日志、更新项目记忆、看今天干了什么。
  排除：当前工作目录已在 vault 内、纯聊天、信息查询无工程动作、未落地方案讨论、简单浏览、仅格式修改。
output_contract:
  artifacts:
    - "工作台写入操作（章节级、局部修改）"
    - "需求对齐摘要（仅读取时）"
  format: "markdown"
  constraints:
    - "写入前必须先读取目标文件"
    - "仅做章节级、局部修改"
    - "写后必须重新读取确认落盘"
    - "不写入密钥/密码/Token"
triggers:
  include:
    - "记录到工作台 / 查工作台 / 查项目状态"
    - "查今日日志 / 工作台同步 / 更新项目文件"
    - "写工作日志 / 更新项目记忆 / 看今天干了什么"
    - "AI 完成实质性工程工作后主动判断需同步"
  exclude:
    - "当前工作目录已在 vault 内（直接按 AGENTS.md 操作）"
    - "纯聊天、日常问候"
    - "信息查询（查文档、查语法、查 API）没有工程动作"
    - "未落地的方案讨论、头脑风暴"
    - "简单代码阅读、浏览文件"
    - "仅格式或注释修改"
---

# AI-Plat Bridge — 跨路径工作台桥接

当 WorkBuddy 当前工作目录不在 AI-Plat vault 时，通过本 skill 对工作台进行读写。

## 常量

```text
VAULT = C:\Users\zhangjl\Documents\obsidian-syncthing\AI-Plat\AI-Plat
```

本 skill 中所有路径均相对于 VAULT 根目录。目录结构见 [vault-structure.md](references/vault-structure.md)。

## 操作模式

| 模式 | 触发条件 |
|---|---|
| **只读** | 用户要求查询工作台、项目状态、今日日志、任务或记忆 |
| **写入** | 用户明确要求记录/同步，或 AI 完成实质性工程工作后主动判断 |

## 工作流程

### 1. 判断是否触发

- 当前工作目录在 vault 内 → **不触发**，直接按 AGENTS.md 操作
- 信息查询无工程动作 → **不触发**
- 用户显式要求读写 → **触发**
- AI 完成实质性工程工作 → 根据 [trigger-eval.md](references/trigger-eval.md) 判断

详见 [near-neighbor-routing.md](references/near-neighbor-routing.md)。

### 2. 选择同步级别（写入时）

按信息价值和工程影响选择最轻量流程。决策树见 [sync-level-decision.md](references/sync-level-decision.md)。

| 级别 | 适用场景 | 操作 |
|---|---|---|
| **轻量** | 小参数调整、局部修复、单次验证通过 | 追加今日日志 + 按需更新项目文件 |
| **标准** | 状态/目标/阻塞点/关键结论变化 | 读取项目文件 → 更新相关章节 + 追加日志 |
| **深度** | 独立任务、里程碑、架构决策、长期约定 | 更新项目文件 + 创建/归档任务卡片 + 追加日志 + 判断是否更新 MEMORY.md |

### 3. 确认目标项目文件

定位顺序：
1. 根据当前仓库名、路径和项目上下文匹配 `30-Projects/`
2. 优先使用项目文件中的工程入口路径确认
3. 无法唯一匹配时，列出候选项目并说明无法安全写入

### 4. 读取目标文件

**写入前必须先读取目标文件现有内容。** 不假设文件为空或内容已知。

### 5. 执行写入

- 仅做章节级、局部修改
- 新信息与已有记录冲突时，保留旧记录并追加变更标注
- 不写入密钥、密码、Token、客户数据

### 6. 写后验证

完成写入后，必须：
1. 重新读取被修改的目标章节，确认内容已正确落盘
2. 检查是否出现重复标题、重复条目或格式破坏
3. 确认未修改无关章节
4. 只有验证成功后才能向用户报告"已同步"

## 读取操作速查

| 操作 | 路径 |
|---|---|
| 查工作台整体状态 | 读取 `30-Projects/` 下所有 `.md` 的 frontmatter |
| 查具体项目 | 读取 `30-Projects/<project>.md` |
| 查今日日志 | 读取 `10-Daily/YYYY-MM-DD.md` |
| 查活跃任务 | 列出 `20-Tasks/active/` |
| 查项目记忆 | 读取 `.workbuddy/memory/MEMORY.md` |
| 查每日记忆 | 读取 `.workbuddy/memory/YYYY-MM-DD.md` |

## 写入操作速查

| 操作 | 路径 | 模板 |
|---|---|---|
| 追加今日日志 | `10-Daily/YYYY-MM-DD.md` | 见 [templates.md](references/templates.md) |
| 更新项目文件 | `30-Projects/<project>.md` | 仅更新需要变更的节 |
| 创建任务卡片 | `20-Tasks/active/<date>-<slug>.md` | 见 [templates.md](references/templates.md) |
| 归档任务卡片 | 状态改 `resolved` 或移 `20-Tasks/done/` | 追加 `## 最终结果` |
| 更新项目记忆 | `.workbuddy/memory/MEMORY.md` | 仅追加长期稳定信息 |
| 追加每日记忆 | `.workbuddy/memory/YYYY-MM-DD.md` | 格式：`- <项目>：<动作/结论>` |

## 输出风险防御

完整规则见 [output-risks.md](references/output-risks.md)。核心要点：
- **写入前必须先读取目标文件**，仅做章节级、局部修改
- 只有经过验证的结果才能进入 `已验证结论` 和 MEMORY.md
- 新信息与已有记录冲突时，保留旧记录并追加变更标注
- 不写入密钥、密码、Token、客户数据

## 参考

- [vault-structure.md](references/vault-structure.md) — 目录结构与基础约定
- [templates.md](references/templates.md) — 日志/任务卡片模板
- [output-risks.md](references/output-risks.md) — P0~P3 防御规则
- [near-neighbor-routing.md](references/near-neighbor-routing.md) — 近邻路由表
- [sync-level-decision.md](references/sync-level-decision.md) — 同步级别决策树
- [trigger-eval.md](references/trigger-eval.md) — 触发评估
- [agents/interface.yaml](agents/interface.yaml) — 输入输出契约
- [evals/evals.json](evals/evals.json) — 行为评测用例
- [reports/output-risk-profile.md](reports/output-risk-profile.md) — 输出风险矩阵
