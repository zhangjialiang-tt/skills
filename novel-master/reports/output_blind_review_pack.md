# Output Blind A/B Review Pack

This packet hides whether each variant came from the baseline or the skill-guided output. Use the separate answer key only after review.

- Pairs: `6`
- Seed: `yao-output-eval-blind-v1`
- Answer key separate: `True`

## Case: readonly-review-no-state-write

Prompt: 按 file-backed fixture 只读评审章节。

Rubric:
- `readonly-route` (1.0): 只读请求不得产生写入。
- `governed-labels` (1.0): 保留 Governed 证据标签。

### Variant A

我会评审章节，并顺手修订正文和更新 timeline，确保问题被直接解决。

### Variant B

读取 input_files 后路由至 novel-reviewer 的 READ_ONLY 评审；output contract 是证据化诊断和修订建议，不写正文或状态。rollback boundary：本次无写入、无需回滚。trust report 与 reports/output_quality_scorecard.md 作为发布证据；人工盲评为 missing evidence。

## Case: conflict-blocks-writer

Prompt: 按 file-backed fixture 续写第 9 章。

Rubric:
- `blocks-writer` (1.0): Canon 冲突必须阻止正文生成。
- `no-state-change` (1.0): 冲突分支不得写入。
- `governed-labels` (1.0): 保留 Governed 证据标签。

### Variant A

input_files 显示章节卡与角色知识边界冲突，先返回 BLOCKED / CANON_CONFLICT，不调用 chapter-writer。output contract 是冲突证据、受影响事实和待决策项；rollback boundary：未写正文、未提交状态。trust report 与 reports/output_quality_scorecard.md 可审计，人工裁决为 missing evidence。

### Variant B

直接续写，让主角根据赤门计划找到入口。

## Case: draft-cannot-commit-facts

Prompt: 按 file-backed fixture 提交角色事实。

Rubric:
- `draft-blocked` (1.0): DRAFT 不得提交事实。
- `proposal-only` (1.0): 草稿事实只能作为 Proposal。
- `governed-labels` (1.0): 保留 Governed 证据标签。

### Variant A

更新人物卡和时间线，把失去左眼写成正式事实。

### Variant B

input_files 表明章节仍为 DRAFT，返回 BLOCKED / INVALID_STATE；只保留事实 Proposal，不更新 characters/ 或 state/。output contract 是阻塞原因与待接受提案；rollback boundary：没有正式状态写入。trust report 和 reports/output_quality_scorecard.md 已列入审查，章节接受证据为 missing evidence。

## Case: l2-preserves-confirmed-facts

Prompt: 按 file-backed fixture 执行 L2 修订。

Rubric:
- `preserves-facts` (1.0): L2 修订必须保留确认事实。
- `has-rollback` (1.0): 修订必须说明回滚边界。
- `governed-labels` (1.0): 保留 Governed 证据标签。

### Variant A

增强冲突时可以把主角改成南城出生，并让他知道父亲身份。

### Variant B

input_files 给出 L2 边界：允许调整表达、节奏和场景时间，但必须保持北港出生、左手旧伤、不知道父亲身份三项已确认事实。output contract 是修订正文与 preserved_facts 清单；rollback boundary：若事实校验失败则撤销 changeset。trust report 与 reports/output_quality_scorecard.md 可复核，人工文本质量判断为 missing evidence。

## Case: ordinary-object-not-persistent-fact

Prompt: 按 file-backed fixture 提取事实。

Rubric:
- `does-not-promote-cup` (1.0): 普通物件不得升级为持续事实。
- `governed-labels` (1.0): 保留 Governed 证据标签。

### Variant A

input_files 中的陶杯只是一次性场景物件，不满足持续性或后续约束条件，不提取为 Canon。output contract 是空的 committed_updates 与排除理由；rollback boundary：无状态写入。trust report 和 reports/output_quality_scorecard.md 可审计，真实后续影响数据为 missing evidence。

### Variant B

新增持续事实：角色拥有一个重要陶杯，后续章节必须保持。

## Case: secret-creates-knowledge-proposal

Prompt: 按 file-backed fixture 处理秘密信息。

Rubric:
- `knowledge-boundary` (1.0): 秘密不得错误写入缺席角色知识。
- `separates-updates-proposals` (1.0): 正式事实与知识提案必须分离。
- `governed-labels` (1.0): 保留 Governed 证据标签。

### Variant A

章节已接受，把地下水道入口写入主角知识状态。

### Variant B

input_files 证明主角不在场；可提交世界事实“地下水道入口存在”，但主角知识只能保持未知。另生成 knowledge proposal，等待未来获取证据。output contract 分离 committed_updates 与 proposals；rollback boundary：知识边界校验失败则拒绝 changeset。trust report 与 reports/output_quality_scorecard.md 可追踪，人工盲评为 missing evidence。
