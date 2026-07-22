# Skill IR — requirement-alignment

> Skill IR 是分离平台打包的持久能力契约层。

## 基本信息

| 字段 | 值 |
|------|-----|
| name | requirement-alignment |
| version | 2.0.0 |
| owner | zhangjl |
| maturity | production |
| review_cadence | per-major-change |
| target_platforms | WorkBuddy |

## 能力契约

### 本 Skill 负责

- 识别复杂任务请求中的高影响歧义
- 通过最少量关键澄清与用户对齐需求
- 输出「需求对齐摘要」作为 Plan/执行阶段的输入

### 本 Skill 不负责

- 输出完整技术方案或 Plan
- 修改任何文件
- 替代 Plan 模式的详细任务分解
- 为显示严谨而发起冗长访谈

## 触发描述

复杂编程/工程任务进入 Plan、设计或实现前，识别请求中可能导致方向性返工的高影响歧义，通过最少量的关键澄清与用户对齐真实目标、范围、约束和验收标准，产出「需求对齐摘要」。

## 触发条件

### 应该触发

- 请求存在歧义或多种合理理解
- 优化/重构/支持 X，但 X 的具体对象不明
- 用户同时提多个目标且优先级不明
- 大范围删除/迁移/不可逆操作
- 用户说"先确认需求""先不要写代码""帮我梳理问题"

### 不应该触发

- 单一、明确、低风险的修改
- 用户已给出目标、范围、约束和验收标准
- 纯知识问答、命令查询、语法解释
- 已生成并确认过需求对齐摘要
- 当前正在执行已批准的 Plan

### 近邻边界

详见 [references/near-neighbor-routing.md](references/near-neighbor-routing.md)

## 工作流步骤

1. 读取已有上下文（不重复询问）
2. 拆分请求（事实/目标/手段/约束/验收/假设）
3. 判断歧义影响（只保留高影响歧义）
4. 必要时有限只读探索（仅消除歧义）
5. 提出关键问题（≤3 个，通常一轮）
6. 处理"按你理解做"的情况
7. 输出需求对齐摘要

## 决策点

| 决策 | 条件 | 动作 |
|------|------|------|
| 是否触发 | 请求清楚无歧义 | L0 直接通过 |
| 对齐级别 | 歧义数量和风险 | L1/L2/L3 |
| 是否继续访谈 | 用户回答后仍有歧义 | 非阻塞→假设继续；阻塞→再问 1 个 |
| 是否写操作 | 任何级别 | 禁止，只输出摘要 |

## 失败模式

详见 [references/failure-modes.md](references/failure-modes.md)

## 资源与脚本

| 资源 | 路径 | 用途 |
|------|------|------|
| 近邻路由表 | references/near-neighbor-routing.md | 防误触发 |
| 失败模式清单 | references/failure-modes.md | 自检 |
| 示例 | references/examples.md | 对齐示例 |
| 触发评估 | references/trigger-eval.md | 路由判断 |
| 工件设计 | reports/artifact-design-profile.md | 摘要规范 |
| 输出风险 | reports/output-risk-profile.md | 风险防御 |
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

- 待建立：验证摘要质量（区分确认与假设、验收可验证性、未输出 Plan 等）
- 断言：
  - 摘要包含"真实目标""范围""验收标准"章节
  - 区分"已确认决策"和"Agent 假设"
  - 未输出完整技术方案或文件修改
  - 验收标准可观察、可验证

## 输出风险

详见 [reports/output-risk-profile.md](reports/output-risk-profile.md)

## 信任边界

- 本 Skill 不访问外部服务
- 不修改任何文件
- 不执行任何命令
- 所有输出基于用户提供的信息和 Agent 的推理
