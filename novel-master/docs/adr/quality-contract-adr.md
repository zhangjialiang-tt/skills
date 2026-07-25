# ADR：章节生产与质量契约

> 文档类型：架构决策记录
> 关联：NM-ARCH §6.6、NM-CONTRACT §17–§20
> 版本：v1.2.0-rc1
> 时间：2026-07-25

---

## 背景

v1.1.0 冻结架构完成了长篇网文创作系统的治理骨架：

- 1+7 Skill 编排。
- Canon 单一写入者。
- 章节接受闸门。
- 文件所有权隔离。
- ChangeSet 事务。
- ApprovalRef 授权。
- 最小上下文包。

v1.1.0 的 133（实际 108）条治理测试证明系统在**正确性维度**上可靠：不会越权写文件、不会跨项目读取、不会跳过接受闸门、不会把 Proposal 静默提交为 Canon。

但阶段 0 的质量基线评估（10 份 v1.1 样本，均分 23.9/30）暴露了**质量维度的系统性不足**：

1. **Planner 输出缺乏结构化的读者体验目标**。`chapter_function` 是单一自然语言字符串，无法被 Writer 逐项执行或 Reviewer 逐项验证。"本章推进主线"和"本章向读者兑现了师徒关系的真相"承载的是完全不同的执行要求，但在 v1.1 中没有区分度。

2. **Writer 无法报告质量的执行情况**。`chapter_report` 仅跟踪事实变化（character_state_changes、foreshadowing_changes），不跟踪质量目标的达成情况。一章可以事实正确但阅读体验平平。

3. **Reviewer 诊断缺乏维度化和证据绑定**。v1.1 使用通用 `overall_assessment` + `confirmed_issues`。10 份基线样本中，D6（证据充分性）均分为 3.0/5——最低的两项之一。Reviewer 容易输出"节奏可以更紧凑"的非执行性意见。

4. **Style Guide 没有场景弹性**。v1.1 的 style_guide.md 对所有场景使用同一套固定参数。然而网文创作中，战斗章和情感章对句长、描写密度、对话占比的要求完全不同。

---

## 决策

**引入章节生产与质量契约**，将 v1.2.0 的质量生产链定义为：

```text
novel-style（定义场景调制规则 + protected_fields）
 → continuity-keeper / EXTRACT_CONTEXT（通过 ContextPack 传递 style_profile）
 → chapter-planner（输出 reader_experience + scene style_modulation_ref）
 → chapter-writer（逐项报告目标执行：target_execution + evidence_ref）
 → novel-reviewer（按维度独立验证 + guardrail 安全扫描）
 → novel-master（显式传入 review_scope）
```

核心设计原则：
- 不新增 Skill（复用 1+7 架构）。
- 不引入正式质量状态机（延后到 v1.3+）。
- 质量是**契约**——Planner 定义、Writer 执行、Reviewer 验证——不是附属备注。

---

## 替代方案评估

### 方案 A：隐式质量约束（仅靠提示词）

在 Planner、Writer、Reviewer 的 SKILL.md 中增加质量相关的提示词约束，不增加任何字段。

- **评估**：实施成本最低，但完全不可测试、不可验证、不可回归。10 份基线样本已经证明当前 v1.1 的提示词约束不足以稳定产出高质量章节。

### 方案 B：独立质量评分器 Skill

新增一个独立的 "quality-scorer" Skill，对每个章节输出质量评分。

- **评估**：在已有 Reviewer 的情况下增加第二重质量评估，造成职责重叠、决策困惑。而且独立的评分器无法从 Planner 获得目标定义——它只能"凭感觉"评分。

### 方案 C：正式质量状态机

增加 UNASSESSED / NEEDS_REVISION / PASS_INTERNAL / READY_TO_PUBLISH 等正式质量状态，将其与章节生命周期并行管理。

- **评估**：方向正确但过早。质量状态机的设计需要基于真实运行数据（哪种质量目标最有效、哪些 Reviewer 维度最关键），而这些数据只有在 P1 的质量契约闭环运行后才能收集。现在引入可能产生一个设计错误的状态机。

### 方案 D（采用）：以现有生产链为载体，增加质量字段

在 Planner → Writer → Reviewer 链中增加 reader_experience、target_execution、dimension_results 等结构。不新增 Skill，不引入正式状态机。

- **优势**：
  - 最低架构变更（仅增加字段，不改变 1+7 架构）
  - 可测试：reader_experience 的存在性、合法性、模式条件均可程序断言
  - 可 A/B 对比：同任务 v1.1 vs v1.2 可精确比较
  - 渐进式：v1.2 积累数据后可基于实际运行结果设计 v1.3 的质量状态机
- **风险**：
  - 结构化字段可能抑制创作弹性（通过增加场景调制和 Writer 只报执行不评分的约束来降低这个风险）
  - 需要所有 4 个 Skill 同时更新（通过阶段化纵向闭环实现来降低协调风险）

---

## 影响

### 修改的子系统

| 子系统 | 变更性质 | 影响 |
| --- | --- | --- |
| 冻结架构 | 新增 ADR 6.6、6.7；扩展不变量 16–20 | RC 阶段不覆盖 v1.1 frozen |
| 冻结契约 | 新增 §17–§23；扩展 §4.3、§9、§12 | RC 阶段不覆盖 v1.1 frozen |
| chapter-planner | SKILL.md 新增 reader_experience 和 style_modulation_ref | 向后兼容 v1.1 章节卡 |
| chapter-writer | SKILL.md 新增 target_execution 和 evidence_ref | Writer 不自我评分 |
| novel-reviewer | SKILL.md 新增 dimension_results 和 guardrail_results | review_scope 改为枚举列表 |
| novel-style | SKILL.md 新增 scene_modulations 和 override_policy | 非破坏性扩展 |
| continuity-keeper | EXTRACT_CONTEXT 新增 style_profile | ContextPack 向后兼容 |
| novel-master | SKILL.md 路由增加 review_scope 显式传入 | 非破坏性扩展 |
| Schemas | 新增 chapter-plan/report/review-request/report/style-guide/context-pack 更新 | 纯增量 |
| 校验脚本 | 新增 validate_quality_contract.py | 纯增量 |
| 测试 | 新增 19 条确定性契约测试 + 10 条语义 Eval | 纯增量 |

### 不修改的子系统

- skill-result.schema.json（仅管理通用信封）
- commit_changeset.py（事务协议不变）
- project_lock.py、validate_approval.py、validate_paths.py、compute_revision.py
- state/ 的所有权结构

---

## 验收

章节生产与质量契约生效的条件：
1. 原 108 条治理测试全部通过。
2. 新增确定性契约测试 19 条全部通过。
3. A/B 盲测中，v1.2 WIN+TIE ≥ 70%，WIN ≥ 40%，LOSS ≤ 30%。
4. 关键静态类型各至少有一个 WIN 或 TIE 样本：SETUP、TRANSITION、PAYOFF、CLIMAX。
5. holdout 任务（3 个）中，"自然度"和"模板化程度"未出现系统性下降。
6. 至少 2 个 holdout 任务由人工复核，确认 Judge 判定与真实阅读体验一致。

---

## 版本

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 1.0 | 2026-07-25 | 初始版本 |
