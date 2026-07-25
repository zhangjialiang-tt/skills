# novel-master V1 实施已知问题

> 记录实施过程中发现的与冻结文档的冲突、歧义或待决策项。
> 不修改冻结文档，仅在此记录。

## 当前状态

本次冻结升版（v1.0.1 → v1.1.0）修复以下三项冻结契约留白。

### ISSUE-001: style_guide.md 在冻结契约中是孤儿文件

- 发现日期：2026-07-25
- 相关冻结文档章节：契约 §3.1（目录清单有 style_guide.md）、§3.3（无所有权行）、§2.2（无产出 skill）、§10（无路由）、§7.2（approval_scope 无 style_guide）；架构 §4.2（子 Skill 表无 style 归属）
- 问题描述：`style_guide.md` 仅作为 §3.1 标准目录树成员出现，无所有权行、无路由、无产出方、无消费者引用；但 `chapter-writer` 和 `novel-reviewer` 的 SKILL.md 已把它当作必需只读输入，下游依赖悬空。
- 影响范围：新书初始化无法产出可用 style_guide，导致 chapter-writer 写作时风格约束缺失、novel-reviewer 评审无风格维度证据。
- 当前采用的临时方案：本次冻结升版新增子 skill `novel-style`，正式纳入架构 §4.2 和契约 §2.2/§3.3/§7.2/§10，把 style_guide.md 所有权归属 novel-style。
- 待决策：无（已决策：立即启动冻结升版补齐）。

### ISSUE-002: routing-table 引用了 novel-master 未定义的 INITIALIZATION_REVIEW 模式

- 发现日期：2026-07-25
- 相关冻结文档章节：契约 §10.4（完整新书初始化路由含 INITIALIZATION_REVIEW 步骤）；novel-master/SKILL.md「激活模式」只声明 DEFAULT
- 问题描述：路由表把 `novel-master / INITIALIZATION_REVIEW` 作为初始化收尾步骤，但 novel-master 的 SKILL.md 只声明 `DEFAULT`（唯一模式），INITIALIZATION_REVIEW 模式未定义。
- 影响范围：初始化收尾步骤的语义模糊——Agent 不知道 INITIALIZATION_REVIEW 是独立模式还是 DEFAULT 下的子流程。
- 当前采用的临时方案：本次升版在 novel-master/SKILL.md 明确 INITIALIZATION_REVIEW 是 DEFAULT 模式下的初始化收尾子流程（不是独立激活模式），并补其职责与输出要求。
- 待决策：无（已决策）。

### ISSUE-003: 两份 style_guide 模板结构不一致

- 发现日期：2026-07-25
- 相关冻结文档章节：非冻结文件，但影响 novel-style 的标准产出
- 问题描述：`references/style-guide-template.md`（权威模板）使用 12 个编号章节 + `{{占位符}}`；`templates/novel-project/style_guide.md`（新项目起始文件）使用 11 个命名章节 + `<!-- TODO -->`，且缺失「题材特殊规则」章节，章节顺序与权威模板不一致。
- 影响范围：novel-style 基于模板填写时，两份模板结构不对齐，可能产出遗漏章节或顺序错乱的 style_guide。
- 当前采用的临时方案：本次升版把 `templates/novel-project/style_guide.md` 对齐权威模板的 12 章节结构与顺序（保留 `<!-- TODO -->` 占位风格）。
- 待决策：无（已决策）。

## 记录格式

```markdown
### ISSUE-XXX: 标题

- 发现日期：YYYY-MM-DD
- 相关冻结文档章节：
- 问题描述：
- 影响范围：
- 当前采用的临时方案：
- 待决策：
```
