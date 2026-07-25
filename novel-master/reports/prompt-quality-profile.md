# Prompt Quality Profile

Skill: `novel-master`
Relevance: `prompt-aware`
Overall quality score: `84.0/100`

## Primary Task Family

**Analytical reasoning**
- Matched keywords: decision, 分析, 决策

## Complexity

- Band: `complex`
- Score: `6`
- Reason: multiple inputs, constraints, or task families require tradeoff handling

## Need Model

- Explicit Need: 编排长篇网文项目的初始化、设定与人物/情节设计、章节规划与正文创作/续写/修订、文本评审、连续性维护、状态提交和恢复；负责意图识别、最小子 Skill 路由、权限风险与接受闸门，不直接替代子 Skill 生成内容。用户要求创建或持续维护网文项目、跨阶段协调或治理事实状态时使用；普通文本润色、第三方作品分析、阅读推荐、诗歌/一次性短篇灵感及非小说任务不使用。
- Implicit Need: The reusable skill needs a stable role, task, and output contract rather than a one-off prompt.
- Scenario: not yet explicit
- User Level: infer from examples and standards; ask only if it changes output depth
- Success Standard: usable output with clear validation cues

## RTF To Skill Mapping

- Role: Use an analyst role that separates evidence, inference, uncertainty, and recommendation.
- Task: State assumptions, compare alternatives, and make the decision path inspectable.
- Format: Return findings, evidence, tradeoffs, recommendation, and residual risks.

## Quality Matrix

### Completeness — 80/100
- Matched signals: example, 输入, 输出, 标准
- Repair: Name missing inputs, outputs, constraints, or success standards before deepening the package.

### Clarity — 80/100
- Matched signals: none
- Repair: Replace broad verbs with observable actions and define what done means.

### Consistency — 90/100
- Matched signals: boundary, 边界
- Repair: Check that role, task, format, exclusions, and examples do not contradict each other.

### Practicality — 95/100
- Matched signals: use, workflow, 执行, 使用
- Repair: Add runnable steps, examples, or verification cues instead of abstract advice.

### Specificity — 75/100
- Matched signals: 用户
- Repair: Anchor wording in the user's audience, domain nouns, and target outcome.

## Matched Task Families

### Analytical reasoning
- Score: `3`
- Keywords: decision, 分析, 决策
- Role: Use an analyst role that separates evidence, inference, uncertainty, and recommendation.
- Task: State assumptions, compare alternatives, and make the decision path inspectable.
- Format: Return findings, evidence, tradeoffs, recommendation, and residual risks.

### Execution operation
- Score: `3`
- Keywords: workflow, 操作, 执行
- Role: Use an operator role with explicit boundaries, inputs, outputs, and failure handling.
- Task: Convert the job into ordered steps with validation checks and stop conditions.
- Format: Return a runbook-like handoff with commands, checks, owners, and next actions when relevant.

### Creative generation
- Score: `1`
- Keywords: 内容
- Role: Use a taste-aware creator role with clear audience, tone, and originality boundaries.
- Task: Generate variants, explain selection logic, and preserve the user's distinctive constraints.
- Format: Return options with rationale, selection criteria, and refinement paths.

### Dialogue interaction
- Score: `1`
- Keywords: 对话
- Role: Use a conversational role that asks only high-leverage questions and remembers the user's goal.
- Task: Clarify intent, resolve uncertainty, and converge toward a recommendation instead of a long option list.
- Format: Return concise prompts, decision points, and reviewer-visible assumptions.

## Self-Repair Checks

- Check explicit need, implicit need, scenario, user level, and success standard before deepening.
- Map Role, Task, and Format into skill behavior, not decorative prompt labels.
- Ask one focused clarification only when missing information changes the package boundary.
- Add tests or examples for prompt-heavy behavior before treating it as reusable.
- Keep prompt methodology in references and reports instead of bloating SKILL.md.

## Reviewer Note

Use this profile when the package depends on prompt behavior, role design, output contracts, or conversation quality.
