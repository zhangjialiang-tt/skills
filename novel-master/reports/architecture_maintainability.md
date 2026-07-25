# Architecture Maintainability

Generated at: `2026-07-25T00:00:00Z`

## Summary

- decision: `watch-maintainability-hotspots`
- python files: `14`
- scripts: `0`
- tests: `0`
- internal modules: `0`
- CLI scripts: `7`
- Yao CLI command handlers: `0`
- entrypoint command handlers: `0`
- command modules: `0`
- largest file lines: `1042`
- early watch threshold lines: `600`
- early watchlist: `0`
- watch threshold lines: `720`
- watchlist: `0`
- hotspots: `2`
- blockers: `0`

This report keeps maintainability risk visible before the Meta Skill grows more gates, renderers, and CLI commands.

## Hotspots

| File | Lines | Kind | Severity | Recommended action |
| --- | ---: | --- | --- | --- |
| `tests\test_changeset.py` | `1042` | `test` | `warn` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `scripts\commit_changeset.py` | `906` | `cli-script` | `warn` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |

## Watchlist

No near-threshold files found.

## Early Watchlist

No early watch files found.

## Largest Files

| File | Lines | Kind | Severity |
| --- | ---: | --- | --- |
| `tests\test_changeset.py` | `1042` | `test` | `warn` |
| `scripts\commit_changeset.py` | `906` | `cli-script` | `warn` |
| `scripts\check_prompt_regressions.py` | `350` | `cli-script` | `pass` |
| `tests\test_schemas.py` | `335` | `test` | `pass` |
| `scripts\validate_approval.py` | `261` | `cli-script` | `pass` |
| `scripts\project_lock.py` | `253` | `cli-script` | `pass` |
| `scripts\validate_paths.py` | `185` | `cli-script` | `pass` |
| `scripts\validate_contract.py` | `165` | `cli-script` | `pass` |
| `scripts\compute_revision.py` | `151` | `cli-script` | `pass` |
| `tests\test_approval.py` | `147` | `test` | `pass` |
| `tests\test_paths.py` | `132` | `test` | `pass` |
| `tests\test_prompt_regressions.py` | `122` | `test` | `pass` |

## Release Rule

- `block` hotspots should be split before governed release.
- `warn` hotspots can ship only when Review Studio keeps them visible and a reviewer accepts the modularization plan.
- Do not split a file only for line count; split when a stable responsibility boundary is clear.
