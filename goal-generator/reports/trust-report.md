# Trust Report: goal-generator skill v2.0.1

- **Skill:** goal-generator
- **Version:** 2.0.2
- **Date:** 2026-07-29
- **Trust tier:** local (no remote code execution, no network I/O)

## Capability contract

**What the skill owns:**
- Transforms raw task descriptions into structured `/goal` contracts
- Supports two profiles: Standard (product/feature/docs) and Diagnostic (bug/performance/hardware/root-cause)
- Auto-selects profile based on task characteristics
- Separates strong triggers (explicit request) from weak signals (profile hints only)
- Applies quality gates before outputting a goal
- Generates a quality scorecard alongside the goal (optional)
- Includes lightweight structural linter (`scripts/lint_goal.py`) with `--strict` mode
- Contract-consistency test runner (`scripts/run_lint_tests.py`) verifies canonical templates pass `--strict`, fixtures behave, sections don't bleed, and all versions match
- Forbids baseline-to-target silent conversion
- Enforces single-main-result-per-Goal rule

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
- SKILL.md: ~10.1 KB
- agents/interface.yaml: ~4.2 KB
- manifest.json: ~1 KB
- references/~10 KB total
- scripts/lint_goal.py: ~14 KB
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
- No route confusion check with adjacent skills (requirement-alignment, plan-mode)

## Recommendation
Safe for local use (candidate-local tier). Contract consistency — canonical templates passing `--strict`, baseline-only not coerced, section isolation, and version agreement — is machine-checked by `scripts/run_lint_tests.py`. Promotion to library/governed tier still requires:
1. Trigger eval with holdout set (independent from reference examples)
2. Blind A/B review on 3+ evals (v1 vs v2 vs qiaomu vs no-skill)
3. Route confusion check with adjacent skills
4. Adversarial eval (baseline-as-target, multi-goal mixing, cross-domain contamination)
