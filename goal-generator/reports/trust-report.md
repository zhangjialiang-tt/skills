# Trust Report: goal-generator skill

- **Skill:** goal-generator
- **Version:** 1.0.0
- **Date:** 2026-07-26
- **Trust tier:** local (no remote code execution, no network I/O)

## Capability contract

**What the skill owns:**
- Transforms raw task descriptions into structured `/goal` contracts
- Applies 7 quality gates before outputting a goal
- Generates a quality scorecard alongside the goal

**What the skill does NOT own:**
- Executing the goal (agent's job)
- Modifying any system state (text-only output)
- Making decisions about task feasibility (human decides)

## Side effects
- Produces goal.md, transcript.md, metrics.json in workspace
- No network I/O, no shell execution, no file deletion

## Resource boundaries
- SKILL.md: ~3.3 KB
- references/failure-modes.md: ~1.5 KB
- No scripts; no external dependencies

## Trust assertions
- No remote inline execution
- No code generation
- No system mutation
- Deterministic text transformation

## Missing evidence
- No trigger eval run yet
- No blind A/B review pack yet
- No adversarial holdout test yet

## Recommendation
Safe for local use. Promotion to library/governed tier requires:
1. Trigger eval with holdout set
2. Blind A/B review on 3+ evals
3. Route confusion check with adjacent skills (plan-mode, brainstorming)
