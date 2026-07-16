---
name: smart-commit
description:
  分析 git 暂存区（git diff --cached）变更，生成符合规范的 commit message（type + 可选 scope + emoji + 祈使 summary）。
  默认【只生成提交信息、不执行提交】；仅当用户明确说"执行提交 / commit it / yes commit / 提交吧"时才运行 git commit。
  触发词：commit、提交、/commit、生成 commit message、写提交信息。
  主动检查：仓库状态、当前分支、敏感信息、超大/二进制 diff、不相关变更需拆分。
  排除：amend/rebase/squash/CHANGELOG/未暂存变更/签名/自动提交。
---

# Smart Commit - 智能提交（安全优先）

分析暂存区变更，生成规范提交信息。**默认只生成、不提交**；仅在用户明确授权时才执行 `git commit`。设计目标是避免在 agent 环境下误提交。

## 执行契约速查（停止 / 只提醒 / 可执行）

核心运行契约，优先级高于下方所有步骤：

| 情况 | 动作 |
|------|------|
| 不在 Git 仓库内 | **停止**：提示进入仓库或 `git init` |
| 暂存区为空 | **停止**：展示 `git status`，提示先 `git add` |
| 命中疑似敏感信息 | **停止提交**（仍生成 message），提醒用户确认/移除 |
| 当前分支为保护分支（main/master/production/release） | **只提醒 + 额外明确授权** 才提交 |
| staged 文件 > 20 或 diff 过大 | **只提醒**：建议拆分，列出拟拆分 message |
| 多类不相关变更 | **只提醒**：建议拆分，不生成单一 message |
| 用户仅要 message | **只展示**，不执行 git commit |
| 用户明确"执行提交 / commit it / yes commit / 提交吧" | **执行** `git commit` |

> 原则：宁可多问，不要替用户提交。生成 message 永远安全；执行 `git commit` 必须明确授权。

## 工作流程

### 1. 运行确定性分析（推荐）
在仓库根目录执行 `scripts/analyze_staged.py`。它一次性完成：
- 仓库状态 / 当前分支 / 是否保护分支
- 暂存清单（空则停止）
- 分层 diff（`--stat` / `--name-status` / `--numstat`）
- 二进制文件识别（numstat 两列为 `-`）
- 敏感信息扫描（规则见 [references/sensitive-scan.md](references/sensitive-scan.md)）
- 拆分信号检测（规则见 [references/split-criteria.md](references/split-criteria.md)）

若脚本不可用，按 [references/diff-analysis.md](references/diff-analysis.md) 手动执行等效 git 命令。

### 2. 读取分析结论并决策
- `repo_valid=false` 或 `staging_empty=true` → 按契约停止。
- `protected_branch=true` → 展示时高亮；若用户最终要求提交，需**额外明确授权**（不只是"提交"，最好复述分支名）。
- `sensitive_hits` 非空 → **停止提交**，提醒用户处理（仍生成 message）。
- `split_signals` 非空 → 按 [references/split-criteria.md](references/split-criteria.md) 分组，各组生成 message，默认不提交。

### 3. 生成提交信息
依据 diff 分类与模块，按 [references/commit-format.md](references/commit-format.md) 生成：
`<type>(<scope>?): <emoji> <imperative summary>`，可选 body（默认中文）。
大 diff / 二进制 / lock 文件的处理见 [references/diff-analysis.md](references/diff-analysis.md)。

### 4. 审查与执行（默认只生成）
展示：仓库状态、暂存概览、敏感扫描结果、拆分建议、完整 message。
**默认只展示，不执行 git commit。** 仅当用户明确说"执行提交 / commit it / yes commit / 提交吧"才运行：

```bash
git commit -m "<header>" -m "<body>"
```

捕获退出码：成功显示哈希；失败（如 pre-commit hook 阻断）展示 stderr，不假装成功。

## 禁止事项

- 暂存区为空 / 不在仓库内执行 `git commit`
- 保护分支未获额外授权即提交
- 敏感信息命中时仍执行 `git commit`
- 推测未暂存的变更内容
- 自创 type/emoji 组合
- 过度解读 lock / 生成 / 二进制文件的内容
- 为不相关变更生成单一 message
- **默认执行 `git commit`**（必须拿到明确授权）
- 把"要 message"误判为"要提交"

## 最终自检

| 检查项 | 判定 |
|--------|------|
| 仓库有效 | `repo_valid=true` |
| 分支已知 | 已显示；保护分支需额外授权 |
| 暂存非空 | `staging` 非空 |
| 大 diff 分层 | >20 文件或 >2000 行用 `--stat` / `--name-status` |
| 敏感通过 | 无命中，或已拦截提醒 |
| 拆分已判 | 多类变更已建议拆分 |
| 格式合规 | `<type>(<scope>?): <emoji> <summary>` |
| 长度合规 | summary ≤ 50，header ≤ 72 |
| 语言统一 | header 默认英文 / body 默认中文 |
| 默认不提交 | 仅展示，未自动 commit |
| 执行需授权 | 仅用户明确说"执行提交"才运行 |

## 参考

- [references/commit-format.md](references/commit-format.md) — type/emoji 映射、scope、语言策略、示例
- [references/diff-analysis.md](references/diff-analysis.md) — 分层 diff、二进制/lock 处理
- [references/sensitive-scan.md](references/sensitive-scan.md) — 敏感信息模式与流程
- [references/split-criteria.md](references/split-criteria.md) — 拆分判定标准
- [agents/interface.yaml](agents/interface.yaml) — 输入输出契约
- [evals/evals.json](evals/evals.json) — 行为评测用例
- [reports/output-risk-profile.md](reports/output-risk-profile.md) — 输出风险矩阵
