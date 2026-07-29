# Portability Report: goal-generator v2.0.0

- **Skill:** goal-generator
- **Version:** 2.0.0
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

## New in v2.0.0
- Two-profile architecture (Standard + Diagnostic)
- Auto-selection logic
- Default-first and discovery-first strategies
- Lightweight linter (`scripts/lint_goal.py`)
- Updated interface.yaml with near-neighbor routing
- 10 evaluation cases
