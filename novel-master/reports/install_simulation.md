# Install Simulation

- OK: `False`
- Package directory: `C:\100-Working\105-Working-improvement\github_lib\zhangjl-skills\novel-master\dist`
- Archive extracted: `True`
- Entrypoint loaded: `True`
- Manifest loaded: `True`
- Interface loaded: `True`
- Adapters readable: `2`
- Installer permissions enforced: `0`
- Installer permission failures: `5`
- Failures: `5`
- Warnings: `0`

## Checks

| Check | Status | Detail |
| --- | --- | --- |
| `archive-present` | `pass` | Package archive exists: C:\100-Working\105-Working-improvement\github_lib\zhangjl-skills\novel-master\dist\novel-master.zip |
| `archive-safe-paths` | `pass` | Archive has no absolute or parent-traversal entries |
| `single-top-level` | `pass` | Archive top-level directory is novel-master |
| `entrypoint-load` | `pass` | Installed SKILL.md frontmatter is readable |
| `entrypoint-name` | `pass` | Installed SKILL.md name matches package directory |
| `entrypoint-description` | `pass` | Installed SKILL.md description is present |
| `manifest-load` | `pass` | Installed manifest.json is readable |
| `manifest-name` | `pass` | Installed manifest name matches package manifest |
| `manifest-version` | `pass` | Installed manifest version matches package manifest |
| `interface-load` | `pass` | Installed agents/interface.yaml is readable |
| `overview-report` | `pass` | Installed overview report is present |
| `review-studio-report` | `pass` | Installed Review Studio report is present |
| `adapter-generic` | `pass` | generic adapter is readable after package install simulation |
| `adapter-generic-name` | `pass` | generic adapter name matches package manifest |
| `adapter-openai` | `pass` | openai adapter is readable after package install simulation |
| `adapter-openai-name` | `pass` | openai adapter name matches package manifest |
| `permission-policy-load` | `fail` | Installed permission policy is readable |
| `permission-generic-contract` | `pass` | generic adapter exposes target permission contract for installer enforcement |
| `permission-generic-file_write-approved` | `fail` | generic capability file_write has active reviewer approval |
| `permission-generic-file_write-target-enforcement` | `fail` | generic capability file_write has target enforcement note |
| `permission-openai-contract` | `pass` | openai adapter exposes target permission contract for installer enforcement |
| `permission-openai-file_write-approved` | `fail` | openai capability file_write has active reviewer approval |
| `permission-openai-file_write-target-enforcement` | `fail` | openai capability file_write has target enforcement note |

## Failures

- Installed permission policy is readable
- generic capability file_write has active reviewer approval
- generic capability file_write has target enforcement note
- openai capability file_write has active reviewer approval
- openai capability file_write has target enforcement note

## Warnings

- None
