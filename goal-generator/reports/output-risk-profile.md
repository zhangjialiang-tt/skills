# Output Risk Profile: goal-generator v2.0.3

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
| Missing provenance for a numeric target | Medium | Skill Rule 3: confirmed targets enter verification; baselines stay facts; proposed targets need a derivation (SLO/baseline/industry) or measure-first. Provenance is a manual gate (not regex) |
| Over-specifying implementation path | Low | Skill failure mode #6 + "优先使用行为标准" guidance |
| Profile misselection (Standard vs Diagnostic) | Medium | Skill has automatic selection rules; default to Standard with explicit assumption |
| All tasks default to "local MVP" | Low (after fix) | Skill explicitly forbids this; default strategy varies by task type |
| Mechanical generation of meaningless blocking conditions | Low (after fix) | Standard Goal only needs completion + key pause; Diagnostic needs full blocked report |
| Baseline silently converted to target | Medium (addressed v2.0.1+) | Skill Rule 3 forbids it; linter W06 coercion REMOVED so a baseline-only goal passes `--strict` instead of being forced to fabricate a threshold |
| Trigger too broad (weak signals) | Medium (new in v2.0.1) | Skill separates strong vs weak triggers; failure mode #12 added |
| Multi-goal mixing | Medium (new in v2.0.1) | Skill Rule 6: single main result per Goal; failure mode #13 added |
| Cross-domain example contamination | Low (new in v2.0.1) | Failure mode #11 added; examples audited for contamination |
| Missing or empty Outcome | High (without skill) | Linter E07 requires a non-empty Outcome for both profiles; never inferred from Current Facts |
| Thin Diagnostic blocked report ("stop when there's a problem") | Medium | Linter W10 requires >=3 blocking conditions or report fields |

## Quality gates (automated + manual)

| # | Gate | Automated |
|---|------|-----------|
| 1 | `/goal` command present (not `/目标`) | ✅ lint_goal.py E01/E02/E03 |
| 2 | All required markers for selected profile present | ✅ lint_goal.py E03 |
| 3 | No unresolved placeholders (TBD, TODO, [XXX]) | ✅ lint_goal.py W01 |
| 4 | No dangerous vague instructions | ✅ lint_goal.py W02 |
| 5 | Verification contains concrete evidence | ✅ lint_goal.py W04 |
| 6 | No over-wide boundaries | ✅ lint_goal.py W05 |
| 7 | Baseline not forced to a fabricated target | ✅ lint_goal.py (W06 coercion removed; baseline-only passes `--strict`) |
| 8 | Anti-gaming constraints present (gameable goals only) | ✅ lint_goal.py W09 (scoped to outcome/verification/facts) |
| 9 | Stop condition not "continue until done" | ✅ lint_goal.py E04 |
| 10 | Stop condition present (separate from Pause) | ✅ lint_goal.py E05 |
| 11 | Pause condition present | ✅ lint_goal.py E06 |
| 12 | Facts vs hypotheses separated (Diagnostic) | ⚠️ lint_goal.py W07 (heuristic) |
| 13 | Experiment strategy starts with reproduction (Diagnostic) | ⚠️ lint_goal.py W08 (heuristic) |
| 14 | Outcome describes observable state | ❌ Manual check only |
| 15 | Anti-gaming constraints are domain-specific | ❌ Manual check only |
| 16 | Default strategy appropriate for task type | ❌ Manual check only |
| 17 | Baseline not silently converted to target | ❌ Manual check only |
| 18 | Single main result per Goal | ❌ Manual check only |
| 19 | Canonical SKILL templates pass linter `--strict` | ✅ scripts/run_lint_tests.py |
| 20 | Section fields do not bleed into one another | ✅ scripts/run_lint_tests.py |
| 21 | All formal files declare one version | ✅ scripts/run_lint_tests.py |
| 22 | Outcome present and non-empty (both profiles) | ✅ lint_goal.py E07 |
| 23 | Diagnostic blocked report has real structure | ✅ lint_goal.py W10 |
| 24 | Standard Stop and Pause are distinct labels | ✅ lint_goal.py E05/E06 |

## Linter modes

| Mode | Command | Behavior |
|------|---------|----------|
| Default | `python3 scripts/lint_goal.py goal.txt` | Warnings don't fail |
| Strict | `python3 scripts/lint_goal.py --strict goal.txt` | Warnings (Wxx) become errors; infos (Ixx) never promoted |

## Reviewer notes
The generated goal.md is a contract document. Reviewers should check whether it would actually guide an agent to stop when blocked, detect speculation, and verify completion objectively. The goal should be executable without further clarification.

The linter (`scripts/lint_goal.py`) is a structural checker, not a semantic judge. Warnings (W-) are advisory; errors (E-) are structural failures. Manual review is still required for Outcome quality, domain specificity, and default strategy appropriateness.
