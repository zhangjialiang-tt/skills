# Skill IR — ai-plat-bridge

> Skill IR 是分离平台打包的持久能力契约层。

## 基本信息

| 字段 | 值 |
|------|-----|
| name | ai-plat-bridge |
| version | 2.0.0 |
| owner | zhangjl |
| maturity | production |
| review_cadence | per-major-change |
| target_platforms | WorkBuddy |

## 能力契约

### 本 Skill 负责

- 当 AI 当前工作目录不在 AI-Plat vault 时，响应对工作台的读写请求
- 读取工作台状态、项目文件、今日日志、活跃任务、项目记忆
- AI 完成实质性工程工作后，将进展同步到工作台（追加日志、更新项目文件、创建/归档任务卡片）

### 本 Skill 不负责

- 替代 AGENTS.md 在 vault 内直接操作
- 为无工程动作的信息查询触发
- 写入未经验证的结论
- 覆盖已有内容

## 触发描述

AI 工作台跨路径桥接。当 AI 当前工作目录不在 AI-Plat vault 时，响应对工作台的读写请求。读取不要求工程变化；写入仅在状态变化、动作完成、结论形成、决策确定、阻塞点改变或任务推进时触发。

## 触发条件

### 应该触发

- 用户明确要求：记录到工作台、查工作台、查项目状态、查今日日志、工作台同步、更新项目文件、写工作日志、更新项目记忆、看今天干了什么
- AI 完成实质性工程工作后主动判断需同步

### 不应该触发

- 当前工作目录已在 AI-Plat vault 内
- 纯聊天、日常问候
- 信息查询（查文档、查语法、查 API）没有工程动作
- 未落地的方案讨论、头脑风暴
- 简单代码阅读、浏览文件
- 仅格式或注释修改
- 临时尝试、没有形成工程状态变化的实验

## 近邻边界

详见 [references/near-neighbor-routing.md](references/near-neighbor-routing.md)

## 工作流步骤

1. 判断操作模式（只读 / 写入）
2. 如为写入，选择同步级别（轻量 / 标准 / 深度）
3. 确认目标项目文件
4. 读取目标文件现有内容
5. 执行写入（章节级、局部修改）
6. 写后验证（重新读取确认落盘）

## 决策点

| 决策 | 条件 | 动作 |
|------|------|------|
| 是否触发 | 当前在 vault 内 | 不触发，直接按 AGENTS.md 操作 |
| 是否触发 | 信息查询无工程动作 | 不触发 |
| 同步级别 | 小参数调整/局部修复 | 轻量同步 |
| 同步级别 | 状态/目标/阻塞点变化 | 标准同步 |
| 同步级别 | 独立任务/里程碑/架构决策 | 深度同步 |
| 是否写入 | 无实质内容 | 说明"无可记录内容" |

## 失败模式

详见 [references/output-risks.md](references/output-risks.md)

## 资源与脚本

| 资源 | 路径 | 用途 |
|------|------|------|
| 近邻路由表 | references/near-neighbor-routing.md | 防误触发 |
| 同步级别决策 | references/sync-level-decision.md | 选择最轻量同步流程 |
| 输出风险防御 | references/output-risks.md | P0~P3 防御规则 |
| 触发评估 | references/trigger-eval.md | 路由判断 |
| 输出风险矩阵 | reports/output-risk-profile.md | 风险防御（reports/ 版） |
| 触发评测 | scripts/trigger_eval.py | 路由回归测试 |
| 评测用例 | evals/evals.json | 10 个用例 |
| Agent 接口 | agents/interface.yaml | 接口契约 |

## 评测计划

### Trigger Eval

- 文件：`evals/evals.json`（10 个用例）
- 运行：`python3 scripts/trigger_eval.py`
- 覆盖：应该触发 6 个、不应该触发 4 个
- 目标：准确率 ≥ 90%

### Output Eval

- 待建立：验证写入质量（章节级修改、无覆盖、写后验证等）
- 断言：
  - 写入前已读取目标文件
  - 仅做章节级修改
  - 新信息与已有记录冲突时保留旧记录
  - 写后重新读取确认落盘

## 信任边界

- 本 Skill 不访问外部服务
- 不修改 vault 外的文件
- 不写入密钥/密码/Token
- 所有写入基于用户提供的信息和 Agent 的推理
