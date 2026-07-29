# Output Risk Profile: goal-generator v2.0.0

## Artifact family
Text-only Markdown contract (the `/goal`). No visual artifact; the deliverable is a structured goal document that feeds into agent execution.

## Top risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Outcome describes action ("optimize X") instead of observable state | High (without skill) | Skill explicitly requires "完成后系统是什么样" check; failure mode examples included; linter warns if outcome is too short |
| Verification surface uses vague terms ("tests pass", "looks correct") | High | Skill mandates: every verification item names a concrete command/condition; linter warns if verification lacks evidence patterns |
| Hypothesis presented as confirmed fact (e.g., "root cause is X") | Medium | Skill has dedicated Rule 1 (fact/hypothesis separation) + failure mode #1; linter warns if facts block contains hypothesis language |
| Missing anti-speculation constraints | High (without skill) | Skill makes this a mandatory part of Constraints section + failure mode #3; linter warns if constraints lack anti-gaming language |
| Missing blocked stop conditions | Medium | Skill failure mode #5; Diagnostic Goal requires ≥3 blocking conditions + report content |
| Missing business-metric threshold when user provides one | Medium | Skill Rule 3: if user mentions a metric, verification must include a target threshold; linter warns if metrics exist but no threshold |
| Over-specifying implementation path | Low | Skill failure mode #6 + "优先使用行为标准" guidance |
| Profile misselection (Standard vs Diagnostic) | Medium | Skill has automatic selection rules; default to Standard with explicit assumption |
| All tasks default to "local MVP" | Low (after fix) | Skill explicitly forbids this; default strategy varies by task type |
| Mechanical generation of meaningless blocking conditions | Low (after fix) | Standard Goal only needs completion + key pause conditions; Diagnostic needs full blocked report |

## Quality gates (automated + manual)

| # | Gate | Automated |
|---|------|-----------|
| 1 | `/goal` command present (not `/目标`) | ✅ lint_goal.py E01/E02 |
| 2 | All required markers for selected profile present | ✅ lint_goal.py E03 |
| 3 | No unresolved placeholders (TBD, TODO, [XXX]) | ✅ lint_goal.py W01 |
| 4 | No dangerous vague instructions | ✅ lint_goal.py W02 |
| 5 | Verification contains concrete evidence | ✅ lint_goal.py W04 |
| 6 | No over-wide boundaries | ✅ lint_goal.py W05 |
| 7 | User metrics → thresholds | ✅ lint_goal.py W06 |
| 8 | Anti-gaming constraints present | ✅ lint_goal.py W09 |
| 9 | Stop condition not "continue until done" | ✅ lint_goal.py E04 |
| 10 | Facts vs hypotheses separated (Diagnostic) | ⚠️ lint_goal.py W07 (heuristic) |
| 11 | Experiment strategy starts with reproduction (Diagnostic) | ⚠️ lint_goal.py W08 (heuristic) |
| 12 | Outcome describes observable state | ❌ Manual check only |
| 13 | Anti-gaming constraints are domain-specific | ❌ Manual check only |
| 14 | Default strategy appropriate for task type | ❌ Manual check only |

## Reviewer notes
The generated goal.md is a contract document. Reviewers should check whether it would actually guide an agent to stop when blocked, detect speculation, and verify completion objectively. The goal should be executable without further clarification.

The linter (`scripts/lint_goal.py`) is a structural checker, not a semantic judge. Warnings (W-) are advisory; errors (E-) are structural failures. Manual review is still required for Outcome quality, domain specificity, and default strategy appropriateness.
