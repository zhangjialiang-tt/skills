# Review Annotations

This report renders reviewer annotations attached to Review Studio gates and source/report paths.

- Annotations: `2`
- Open: `2`
- Resolved: `0`
- Deferred: `0`
- Open blockers: `2`
- Open warnings: `0`

## Annotation Ledger

| ID | Gate | Severity | Status | Target | Reviewer | Note |
| --- | --- | --- | --- | --- | --- | --- |
| governed-file-write-approval-missing | permission-gates | blocker | open | security/permission_policy.md | automated-governance-check | Governed promotion is blocked because file_write has no real human approval, expiry, evidence, or target enforcement record; this is missing evidence, not an approved permission. |
| governed-blind-review-missing | output-lab | blocker | open | reports/output_review_kit.md | automated-governance-check | Governed promotion is blocked because all six blind A/B decisions and reviewer metadata remain missing evidence; recorded_fixture results are not human adjudication. |

## Review Rule

- Use annotations for reviewer comments tied to a gate or source line.
- Use waivers only for explicit acceptance of warning-level release risk.
- Open blocker annotations should block a release decision until resolved or deferred with rationale.
