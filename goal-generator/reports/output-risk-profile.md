# Output Risk Profile: goal-generator

## Artifact family
Text-only Markdown contract (the `/goal`). No visual artifact; the deliverable is a structured goal document that feeds into agent execution.

## Top risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Outcome describes action ("optimize X") instead of observable state | High (without skill) | Skill explicitly requires "完成后系统是什么样" check; failure mode examples included |
| Verification surface uses vague terms ("tests pass", "looks correct") | High | Skill mandates: every verification item names a concrete command/condition AND a numeric threshold |
| Hypothesis presented as confirmed fact (e.g., "root cause is X") | Medium | Skill has dedicated Step 2 (fact/hypothesis separation) + failure mode #1 |
| Missing anti-speculation constraints | High (without skill) | Skill makes this a mandatory part of Constraints section + failure mode #2 |
| Missing blocked stop conditions | Medium | Skill failure mode #4 + mandatory 3+ blocking conditions |
| Missing business-metric threshold when user provides one | Medium | Skill now requires: if user mentions a metric (e.g., "每周 3-5 例"), verification must include a target threshold |
| Over-specifying implementation path | Low | Skill failure mode #5 + "优先使用行为标准" guidance |

## Quality gates
1. Six sections present (Outcome, Verification, Constraints, Boundaries, Iteration, Blocked)
2. Outcome contains no action verbs (分析/研究/尝试/优化/实现/改造)
3. Every verification item has: concrete command/condition + numeric threshold
4. Constraints include at least one anti-speculation prohibition
5. Blocked section lists ≥3 specific blocking conditions
6. Hypothesis section exists and is non-empty (when user provides unverified claims)
7. If user mentions a metric, verification includes a target threshold for it

## Reviewer notes
The generated goal.md is a contract document. Reviewers should check whether it would actually guide an agent to stop when blocked, detect speculation, and verify completion objectively. The goal should be executable without further clarification.
