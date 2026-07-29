# Trust Report: goal-generator skill v2.0.0

- **Skill:** goal-generator
- **Version:** 2.0.0
- **Date:** 2026-07-29
- **Trust tier:** local (no remote code execution, no network I/O)

## Capability contract

**What the skill owns:**
- Transforms raw task descriptions into structured `/goal` contracts
- Supports two profiles: Standard (product/feature/docs) and Diagnostic (bug/performance/hardware/root-cause)
- Auto-selects profile based on task characteristics
- Applies quality gates before outputting a goal
- Generates a quality scorecard alongside the goal (optional)
- Includes lightweight structural linter (`scripts/lint_goal.py`)

**What the skill does NOT own:**
- Executing the goal (agent's job)
- Modifying any system state (text-only output)
- Making decisions about task feasibility (human decides)
- Semantic judgment (linter is structural only)

## Side effects
- Produces goal contract as inline text output
- No network I/O, no shell execution, no file deletion
- Linter script is read-only

## Resource boundaries
- SKILL.md: ~8.8 KB
- agents/interface.yaml: ~3.7 KB
- manifest.json: ~1 KB
- references/: ~10 KB total
- scripts/lint_goal.py: ~12.7 KB
- No external dependencies (Python standard library only)

## Trust assertions
- No remote inline execution
- No code generation
- No system mutation
- Deterministic text transformation
- Linter is read-only structural checker

## Missing evidence
- No trigger eval run yet (holdout set pending)
- No blind A/B review pack yet
- No adversarial holdout test yet

## Recommendation
Safe for local use. Promotion to library/governed tier requires:
1. Trigger eval with holdout set
2. Blind A/B review on 3+ evals
3. Route confusion check with adjacent skills (requirement-alignment, plan-mode, brainstorming)
