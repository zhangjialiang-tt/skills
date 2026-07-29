# Goal Generator

把原始任务转换为适合 Coding Agent 持续执行的高质量 `/goal` 完成契约。

## Goal 与普通 Prompt、Plan 的区别

| 模式 | 回答的问题 | 适合场景 |
|------|-----------|---------|
| **普通 Prompt** | "现在做什么？" | 一次性问答、简单修改、即时执行 |
| **Plan Mode** | "修改哪些文件？什么技术方案？什么顺序？" | 需要探索代码、形成实施路线的任务 |
| **Goal** | "最终必须达到什么状态？用什么证据证明？哪些不能破坏？走不通时如何诚实停止？" | 终点明确但路径未知、需要持续执行和证据验证的任务 |

## 两种 Profile

本 Skill 支持两种 Goal Profile，根据任务特征自动选择：

### Standard Goal（产品/功能/文档/UI）

适用于：创建新东西、实现明确功能、文档交付、UI 修改、常规重构。

逻辑字段：Outcome / Verification / Constraints / Boundaries / Iteration / Stop & Pause

### Diagnostic Goal（Bug/性能/硬件/根因调查）

适用于：已有失败现象、未验证的根因猜测、性能优化、硬件/板级问题、数据一致性。

逻辑字段：Outcome / Current Facts / Hypotheses / Verification Evidence / Invariants & Anti-gaming / Work Boundaries / Experiment Strategy / Stop / Blocked Report

### 自动选择规则

- 用户描述了失败现象 → Diagnostic
- 用户提出未验证猜测 → Diagnostic
- 任务涉及硬件/板级/时序 → Diagnostic
- 任务目标是创建新东西 → Standard
- 无法判断时默认 Standard 并显式声明假设

## 什么时候使用

**适合 → 生成 Goal：**
- 完成条件相对明确
- 实现路径需要根据调查或实验动态决定
- 存在可检查的测试、日志、benchmark、生成物或其他证据

**不适合 → 建议其他模式：**
- 一次性修改、纯探索 → 普通 Prompt 或 Plan Mode
- 任务模糊到无法定义任何完成条件 → 先 Plan
- 简单翻译、一行 shell 输出、纯头脑风暴 → 直接回答

## 核心能力

### 事实与假设分离（Diagnostic）

已确认的现象写入【当前事实】，线索/猜测写入【待验证假设】。禁止把未验证的猜测写成既定根因。

### 可执行验收证据

每项验收证据包含：具体检查动作（命令/脚本/测试）+ 通过阈值（数值或可观察条件）。

### 用户指标转化为验收阈值

如果用户提到了具体数字（如"每周 3-5 例"、"P95 太高"），验收证据必须包含该指标的目标阈值，且必须基于用户数字推导。

### 领域相关反投机约束

禁止泛泛的"不通过删除测试来虚假达标"。按领域写出具体的投机手段：

- 支付/金融：不通过拒绝所有重复请求达成"零重复扣款"
- 性能优化：不通过减少返回结果数量、关闭核心功能虚标性能
- 硬件/嵌入式：不通过降频、关闭校验模块通过可靠性测试

### 复现优先（Diagnostic）

迭代策略第一步必须包含可执行的复现操作，而非"先分析"。

### Default-First 策略

低风险不确定性由 Skill 选择保守默认值，不拦用户填表。只有当决策会实质改变产品方向、成本、风险、所有权时才追问。

### Discovery-First 策略

陌生专业领域（医疗、金融、合规）不编造领域规则，要求 Agent 先读取工作区权威信息再实现。

## 使用方式

```text
帮我生成 Goal：<你的任务描述>
写一个 goal：<你的任务描述>
把下面任务变成 goal：<你的任务描述>
```

## 轻量校验工具

```bash
python3 scripts/lint_goal.py <goal-file> [<goal-file> ...]
```

校验覆盖：
- 是否存在 `/goal` 命令（而非 `/目标`）
- 所选 Profile 的必需字段是否完整
- 是否遗留 TODO/TBD/占位符
- 是否存在无限授权（"随便改""一直尝试"）
- 是否存在过宽的修改边界
- Verification 是否包含具体检查动作或证据
- Diagnostic Goal 是否正确区分事实与假设
- 用户提供指标时是否进入验收条件
- 是否有明确 Stop 条件
- 是否有必要的 Pause/Blocked 条件

**注意：** linter 是结构检查器，不是语义判断器。WARNING 是建议性的，ERROR 是结构性失败。

## 示例

参见：
- `references/standard-goal-examples.md` — Standard Goal 示例
- `references/diagnostic-goal-examples.md` — Diagnostic Goal 示例

## 安装

本 Skill 为仓库内本地 Skill，通过 `skill://goal-generator` 调用。

## 已知限制

- 不能替代人工判断 Goal 是否合理
- 不能保证生成的 Goal 在所有 Agent 环境下都能完美执行
- 静态 linter 无法可靠判断 Outcome 是否真正描述了可观察状态（仅做长度和关键词提示）
- 不熟悉的领域可能生成 discovery-first Goal，需要用户提供权威信息

## License

MIT
