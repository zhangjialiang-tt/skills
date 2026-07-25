# Permission Approval Requirement

Status: `missing evidence`

`novel-master` contains deterministic scripts with local `file_write` capability.
No `security/permission_policy.json` is created until a real reviewer supplies
an approval decision, identity, expiry, evidence, and target enforcement notes.

## Requested scope

- Write only below a validated novel project root and the owned zones defined by
  `references/file-ownership.md`.
- Write reports only to an explicit `--report` destination.
- Limit workflow writes to changesets, approvals, locks, revisions, backups, and
  the paths permitted by the frozen contracts.
- Do not grant network, subprocess, or interactive capabilities.

## Required approval evidence

The reviewer must create `security/permission_policy.json` with
`decision: approved`, reviewer, scope, reason, expiry, evidence, and enforcement
notes for both OpenAI and Generic targets. Until then, the Governed release gate
must remain blocked and this document is the permission `missing evidence`.
