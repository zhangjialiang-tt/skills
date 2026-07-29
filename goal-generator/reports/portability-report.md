# Portability Report: goal-generator v2.0.2

- **Skill:** goal-generator
- **Version:** 2.0.2
- **Date:** 2026-07-29

## Canonical format
- Primary: `SKILL.md` (Markdown + YAML frontmatter)
- Supplementary: `agents/interface.yaml`, `references/`, `reports/`, `scripts/`

## Adapter targets

| Target | Format | Status |
|--------|--------|--------|
| Claude | Markdown + YAML frontmatter | Native |
| Codex | Markdown + YAML frontmatter | Native |
| Oh-My-Pi (OMP) | Markdown + YAML frontmatter | Native |
| OpenAI | frontmatter only | Partial (body consumed as instructions) |
| Generic | Markdown | Degrades to description-only |

## Degradation strategy
If only `description` is available (e.g., OpenAI), the trigger still routes correctly but the body is not loaded. Users should receive a shortened prompt-based version.

## Platform-specific notes
- **Claude Code:** Full skill loads via `skill://goal-generator`
- **Codex:** Routes by frontmatter `description`
- **OMP:** Routes by `available_skills` listing
- **OpenAI:** Frontmatter-only; body must be copy-pasted or summarized

## Version history

### v2.0.0
- Two-profile architecture (Standard + Diagnostic)
- Auto-selection logic
- Default-first and discovery-first strategies
- Lightweight linter (`scripts/lint_goal.py`)
- Updated interface.yaml with near-neighbor routing

### v2.0.1
- Strong-trigger vs weak-signal separation (weak signals no longer trigger on their own)
- Three-axis judgment (task type × information state × risk level)
- baseline / confirmed-target / proposed-target separation
- Single-main-result gate; multi-goal tasks split
- Maturity downgraded from governed to local

### v2.0.2 (consistency convergence)
- Linter rebuilt around one canonical label grammar (accepts `验证：`, `Verification（验证）：`, `【验收证据】`)
- Section parser no longer bleeds one field into the next
- Removed W06 baseline→threshold coercion; baseline-only goals pass `--strict`
- `--strict` now promotes W07/W08; `--help` exits 0
- Anti-gaming required only for gameable goals; distinguished from plain invariants
- Evals rewritten (12 cases, inputs distinct from references; weak-signal-only negatives)
- Contract-consistency test runner `scripts/run_lint_tests.py`
