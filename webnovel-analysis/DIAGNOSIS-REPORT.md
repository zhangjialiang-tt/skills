# webnovel-analysis Skill 库系统性诊断报告

> 历史诊断快照（2026-08-01）：其中关于多 Skill 入口、S6 报告职责和测试状态的结论已被 Milestone 1 冻结替代。当前规范见 `SKILL.md` 与 `docs/architecture-freeze-m1.md`。

> 诊断时间：2026-08-01 | 诊断人：AI Agent（小龙） | 目标：评估 Skill 库能否稳定发挥"对网文进行拆书分析"的预期作用

---

# 1. 执行摘要

## 当前 Skill 能否达到预期目标

**基本能够达成，但存在需要修复的阻塞问题。** 以《悟空传》为测试案例，全链路（O0→S9+Q0）跑通并产生了结构化输出：21 章中央表、情绪/爽点数据、人物关系、商业卡点、质量审计、题材配方、章节模板。测试输出质量较高，S1 识别出双时间线非线性结构，Q0 发现了 7 项 P1 待复核（含反向释放与商业爽点的口径冲突），S8 产出了可迁移的题材配方。

## 总体成熟度

**中高（75/100）**
- 架构设计成熟：三层分离（控制/分析/聚合）+ 中央表契约 + 批次处理 + Q0 审计
- 实现完整度较高：12 个模块的 SKILL.md + prompt-template + enums 齐全
- 测试覆盖中等：单 Skill eval 存在，但缺少端到端流水线测试和异常路径测试
- 文档一致性中等：design 文档与 SKILL.md 存在迭代漂移

## 最严重的三个问题

1. **【阻塞】S6 报告生成功能未测试** — `analysis_report.md` 是交付物⑤，模板存在但测试目录中无任何输出，无法验证人类可读报告能否正确生成。
2. **【阻塞】O0 prompt-template.md 与 design-2.md 输入格式不一致** — O0 的参考模板简化了设计文档中的完整输入结构，可能导致信息收集不全。
3. **【阻塞】S1 consolidation 测试数据违反规范** — 测试使用 consolidation 模式处理全书，但 consolidation 应在所有批次完成后运行，而非单批内。

## 建议

**局部优化后继续使用。** 核心架构合理，主要问题是文档一致性和测试覆盖。无需重新设计，但需要修复 4 项阻塞问题和 4 项高优先级问题。

---

# 2. 当前实现全景

## 仓库和文件结构

```
webnovel-analysis/
├── docs/
│   ├── design-1.md          # 架构总览、中央数据表、批次策略
│   ├── design-2.md          # O0-S4 标准化定义
│   └── design-3.md          # S5-Q0 标准化定义 + 共享枚举
├── schemas/
│   ├── enums.yaml           # 共享枚举（17 个枚举域）
│   └── output-envelope.schema.json  # 通用输出信封
├── O0-orchestrator/         # 编排器
├── S0-text-preprocess/      # 文本预处理
├── S1-narrative-structure/  # 叙事结构
├── S2-emotion-rhythm/       # 情绪节奏
├── S3-character-network/    # 人物关系
├── S4-payoff-engineering/   # 爽点工程
├── S5-commercial-hooks/     # 商业卡点
├── S6-data-aggregation/     # 数据聚合（含报告生成）
├── S7-visualization/        # 可视化
├── S8-genre-formula/        # 题材配方
├── S9-chapter-template/     # 章节模板
├── Q0-quality-audit/        # 质量审计
└── test/analysis/wukongzhuan/  # 《悟空传》测试案例（完整输出）
```

## 完整执行链

```
原始文本
    │
    ▼
O0 ──→ task_manifest.yaml + execution-plan.yaml + file-manifest.yaml + review-policy.yaml
    │
    ▼
S0 ──→ standardized_chapters.md + chapter_index.csv + batch_manifest.yaml + preprocessing_issues.csv
    │
    ├──→ S1 ──→ 结构字段 + story_unit_updates + volume_updates + open_loops
    ├──→ S2 ──→ 情绪/压力/释放评分 + 批次统计
    ├──→ S3 ──→ character_registry_updates + relationship_events + faction_updates
    └──→ S4 ──→ 章节爽点字段 + payoff_events + batch_statistics
    │
    ▼
S5 ──→ 章节商业字段 + commercial_pattern_summary
    │
    ▼
S6 ──→ chapter_analysis_master.csv/xlsx + volume_analysis.csv + payoff_events.csv
    │    + relationship_events.csv + analysis_report.md  ← 未生成
    │
    ▼
Q0 ──→ issues(P0/P1/P2) + minimal_review_queue + distribution_checks
    │
    ├──→ S7 ──→ 工作表设计 + 条件格式 + chart_specs + [Python脚本]
    ├──→ S8 ──→ genre_formula.yaml（题材配方）
    └──→ S9 ──→ field_dictionary.json + blank_template.csv + manual_review_view.csv
```

## 依赖关系

| 模块 | 强依赖 | 弱依赖 |
|------|--------|--------|
| S0 | O0 task_manifest | — |
| S1 | S0 chapter_index | 前批 summary |
| S2 | S0 chapters | S1 turning_points |
| S3 | S0 chapters | S1 structure |
| S4 | S0 chapters | S2 emotion_records, S1 story_units |
| S5 | S0 chapters | S1 structure, S2 emotion, S4 payoff |
| S6 | S0-S5 全部 | — |
| Q0 | S6 master_table | S4 payoff_events, S3 relationship_events |
| S7 | S6 master_table | — |
| S8 | S6 master_table + S1 volume + S4 payoff + S3 char | Q0 audit_summary |
| S9 | S6 central_schema | S8 genre_formula |

## 输入、输出和状态流

**核心状态：**
- `task_manifest.yaml` — 任务身份，贯穿全链路
- `chapter_index.csv` — S0 输出，所有分析 Skill 的定位基础
- `batch_manifest.yaml` — 批次划分，支持断点恢复
- `character_states` — S3 滚动更新，跨批次传递
- `open_loops` — S1 滚动更新，跨批次传递
- `recent_major_payoffs` — S4 滚动更新

## 已实现能力与声明能力的差异

| 声明能力 | 实现状态 | 差异说明 |
|---------|---------|---------|
| 自动切章 | ✅ 已实现 | S0 有完整 prompt-template |
| 章节功能识别 | ✅ 已实现 | S1 枚举完整 |
| 情绪评分 | ✅ 已实现 | 1-10 分锚点明确 |
| 人物关系网络 | ✅ 已实现 | S3 含 registry + events |
| 爽点工程 | ✅ 已实现 | S4 含 payoff_nature 扩展 |
| 商业卡点 | ✅ 已实现 | S5 含 hook_fairness |
| 数据聚合 | ✅ 已实现 | S6 含合并规则 |
| 质量审计 | ✅ 已实现 | Q0 含 P0/P1/P2 |
| 可视化 | ⚠️ 部分实现 | S7 有设计模板但无 Python 脚本测试 |
| 题材配方 | ✅ 已实现 | S8 含参数化配方 |
| 章节模板 | ✅ 已实现 | S9 含 field_dictionary |
| 人类可读报告 | ❌ 未测试 | S6 report-template.md 存在但无输出 |
| 反向释放标记 | ✅ 已实现 | 迭代添加的 payoff_nature |

---

# 3. 场景推演结果

## 标准场景：100 章商业网文拆解

**路径：** 用户提供 txt → O0 规划 10 批 → S0 切章 → S1-S4 并行 → S5 → S6 → Q0 → S7/S8/S9

**结果：可行。** 以《悟空传》（21 章、非线性结构、悲剧基调）为案例，全链路跑通。Q0 正确识别了反向释放与商业爽点的冲突，S8 产出了可迁移配方并标注了"单书警告"。

**但存在风险：** 100 章需 10 批次，每批次 S1-S5 的上下文窗口压力较大；批次摘要包 1500 字限制在角色众多的作品中可能不够。

## 输入信息不足场景：只说"帮我分析这本书"

**路径：** 用户未提供文本或书籍信息

**结果：O0 会尝试按模板生成计划，但因为缺少 `source_files` 和 `book_title`，生成的 task_manifest 内容不完整。** O0 SKILL.md 中没有明确要求用户必须提供文本，也没有定义"信息不足时如何优雅退出"的策略。

**风险：** 可能生成一份空壳计划并要求调用 S0，但 S0 没有文本输入会失败。

## 排除场景：用户提供的是非网文（如学术论文、新闻）

**路径：** 用户给了一段非叙事性文本

**结果：没有显式排除机制。** 触发条件（"分析这本书"、"拆解网文"）是用户意图判断，Skill 本身不验证输入是否为叙事文本。S0 会尝试切章（可能按段落），S1 会尝试识别"章节功能"（可能强行套用网文分析框架）。

**风险：** 对非网文输出无意义的分析，浪费用户时间。

## 执行中途失败场景：S3 人物合并冲突

**路径：** S3 将两个同名角色错误合并，后续批次发现矛盾

**结果：** S3 有 `conflicts` 输出字段，Q0 有 `cross_batch_checks` 机制。但 **错误合并的字符 registry 已经进入下一批次的输入**，后续批次会基于错误前提继续分析。Q0 能检测到"角色状态倒退且没有剧情原因"，但 **无法自动修复**，只能标记 P1 让人工处理。

**风险：** 错误在批次间传播，修复成本高。

## 多轮、长上下文场景：1000 章超长篇

**路径：** 超长篇需 100+ 批次

**结果：** 系统设计上支持断点恢复（checkpoint_policy），但存在以下问题：
- S1 consolidation 需要读全部章节，1000 章可能超出上下文窗口
- 角色状态表和开放悬念包会随批次增长而膨胀
- Q0 全书审计需遍历全部 master_table

**风险：** 长上下文下 S1 consolidation 可能无法一次性完成。

## 与其他 Skill 可能冲突的场景：webnovel-serial-designer

**路径：** 用户同时安装 webnovel-analysis 和 webnovel-serial-designer

**结果：** 两个 Skill 目标不同（分析 vs 创作设计），但触发词可能重叠（如"帮我设计一本类似《悟空传》的书"）。O0 的触发描述中没有排除"为创作而分析"的场景。

**风险：** 用户意图是"创作"但触发了"分析"流程，反之亦然。

---

# 4. 问题清单

## 阻塞问题（P0）

### B1. S6 报告生成未测试
- **文件：** `S6-data-aggregation/SKILL.md`、`S6-data-aggregation/references/report-template.md`
- **证据：** `report-template.md` 定义了完整的九节报告结构，但 `test/analysis/wukongzhuan/` 目录下不存在 `analysis_report.md`。Glob 搜索全项目无任何 `.md` 报告输出。
- **真实影响：** 交付物⑤"人类可读汇总报告"缺失，作者无法获得分析结论的自然语言总结。
- **触发场景：** 用户完成全部分析后期望获得一份报告。
- **建议修改：** 在测试目录中补充报告生成 eval，验证 S6 能否根据 S1-S5+Q0 数据生成完整报告。
- **是否涉及产品决策：** 否。
- **是否建议本轮实施：** 是。

### B2. O0 prompt-template.md 与 design-2.md 输入格式不一致
- **文件：** `O0-orchestrator/references/prompt-template.md` vs `docs/design-2.md`
- **证据：** design-2.md 定义了完整的 `project_request` 结构（含 `source_files[].format`、`desired_outputs[]`、`preferred_batch_size`、`available_tools`、`constraints`），但 prompt-template.md 简化为 `project_request` 包装，缺少 `available_tools` 和 `constraints` 的详细字段。
- **真实影响：** 用户可能不提供工具限制或约束条件，导致 O0 生成的执行计划与实际环境不匹配。
- **触发场景：** 用户使用非标准工具链（如只有 ChatGPT 没有 Excel）。
- **建议修改：** 统一 prompt-template.md 与 design-2.md 的输入结构。
- **是否涉及产品决策：** 否。
- **是否建议本轮实施：** 是。

### B3. S1 consolidation 测试数据违反规范
- **文件：** `test/analysis/wukongzhuan/s1/S1_narrative_structure.json`
- **证据：** JSON 中 `"mode": "consolidation"`，`design-2.md` 明确规定 consolidation 模式"根据全部章节重新划分故事单元和卷"，但测试数据似乎是单批处理全书 21 章（无渐进批次）。
- **真实影响：** 测试数据模式与规范不一致，无法验证 incremental→consolidation 的正确转换。
- **触发场景：** 用户先逐批分析再 consolidation。
- **建议修改：** 测试数据应改为 incremental 模式输出，或补充 consolidation 的独立调用证据。
- **是否涉及产品决策：** 否。
- **建议本轮实施：** 是。

### B4. payoff_nature literary 判定中 S2 依赖矛盾
- **文件：** `S4-payoff-engineering/references/prompt-template.md`
- **证据：** `literary` 判定条件为"非反向但 S2 release_score ≤ 2"，但 S4 的 `emotion_records` 输入标记为"可为空"。若 S2 未运行，S4 无法获取 release_score。
- **真实影响：** S4 在独立运行（无 S2 输入）时无法正确分类 payoff_nature。
- **触发场景：** 用户只运行 S4 不运行 S2。
- **建议修改：** 将 `emotion_records` 从可选改为必需，或调整 literary 判定逻辑（不依赖 S2）。
- **是否涉及产品决策：** 否。
- **建议本轮实施：** 是。

## 高优先级问题（P1）

### H1. Q0 反向释放冲突排除规则与实现不一致
- **文件：** `Q0-quality-audit/SKILL.md`、`Q0-quality-audit/references/prompt-template.md`
- **证据：** SKILL.md 写"reverse 类除外"，但 prompt-template.md 写"S4 payoff_nature != reverse"。测试数据中 CH18/19/20 触发了 P1 冲突（reverse 事件），但按规则应被排除。
- **真实影响：** Q0 对反向释放事件产生了误报，增加了不必要的人工复核负担。
- **触发场景：** 作品含悲剧/死亡等反向释放事件。
- **建议修改：** 统一 Q0 的冲突排除规则，确保 reverse 类事件不触发 P1。
- **是否涉及产品决策：** 否。
- **建议本轮实施：** 是。

### H2. S6 合并时对 S3 角色数据消费不完整
- **文件：** `S6-data-aggregation/SKILL.md`
- **证据：** S6 输入只列了 `s1_records, s2_records, s3_records, s4_records, s5_records`，但 S3 输出包含 `character_registry_updates`、`faction_updates` 和 `relationship_events`，S6 的合并逻辑未明确说明如何处理角色注册表和阵营数据。
- **真实影响：** 角色配方和阵营结构无法进入中央表，S8 配方的角色功能组合部分数据来源不明确。
- **触发场景：** 需要角色网络数据的聚合。
- **建议修改：** 在 S6 输入和合并规则中明确 S3 角色数据的消费方式。
- **是否涉及产品决策：** 否。
- **建议本轮实施：** 是。

### H3. S9 模板生成缺乏验证数据
- **文件：** `test/analysis/wukongzhuan/s9/`
- **证据：** `S9_chapter_template.json` 和 `field_dictionary.json` 存在，但 `blank_template.csv` 仅含表头（1行），`manual_review_view.csv` 无数据行。
- **真实影响：** S9 输出质量未经验证，无法确认生成的模板能否直接用于新书分析。
- **触发场景：** 用户基于模板开始新书分析。
- **建议修改：** 补充 S9 的测试数据验证，确保 blank_template.csv 包含完整表头。
- **是否涉及产品决策：** 否。
- **建议本轮实施：** 是。

### H4. 没有端到端流水线测试
- **文件：** 无
- **证据：** 只有单 Skill eval（S0 和 S1），没有从 O0 到 S9 的完整流水线测试。
- **真实影响：** 模块间接口不匹配、数据传递断裂等问题无法在测试中发现。
- **触发场景：** 模块版本升级或字段变更后。
- **建议修改：** 补充至少一个端到端流水线 eval（从 O0 输入到 S9 输出）。
- **是否涉及产品决策：** 否。
- **建议本轮实施：** 否（工作量大，建议后续迭代）。

## 中优先级问题（P2）

### M1. 批次摘要包 1500 字限制可能不够
- **文件：** `docs/design-1.md` 第 7.3 节
- **证据：** 10 章批次可能包含多个角色状态、多条开放悬念，1500 字在高角色密度作品中可能不足。
- **真实影响：** 跨批次上下文丢失，后续批次忘记前文关键信息。
- **触发场景：** 角色众多、悬念复杂的超长篇。
- **建议修改：** 将 1500 字限制改为弹性限制（如"不超过批次章节总字数的 5%"）。
- **是否涉及产品决策：** 否。
- **建议本轮实施：** 否。

### M2. S2 calibration 模式未在测试中覆盖
- **文件：** `S2-emotion-rhythm/SKILL.md`
- **证据：** SKILL.md 提到 `calibration` 模式用于全书校准，但无测试数据。
- **真实影响：** 校准后评分分布是否合理未知。
- **触发场景：** 全书完成后需要统一校准评分。
- **建议修改：** 补充 calibration 模式 eval。
- **是否涉及产品决策：** 否。
- **建议本轮实施：** 否。

### M3. S7 Python 增强路径未测试
- **文件：** `test/analysis/wukongzhuan/s7/`
- **证据：** `S7_visualization.json` 只有工作表设计，无可运行 Python 脚本。
- **真实影响：** Python 可视化增强功能是否可用未知。
- **触发场景：** 用户选择 Python 模式生成图表。
- **建议修改：** 补充 Python 脚本生成测试。
- **是否涉及产品决策：** 否。
- **建议本轮实施：** 否。

### M4. O0 next_action 固定为 "调用S0"
- **文件：** `O0-orchestrator/references/prompt-template.md`
- **证据：** 模板中 `next_action` 固定为 "调用S0处理原始文本"，无论输入是否充分。
- **真实影响：** 缺少动态决策，无法处理"输入不足"等异常情况。
- **触发场景：** 用户只提供书名未提供文本。
- **建议修改：** 增加条件判断：若文本缺失，next_action 改为 "向用户索取原始文本"。
- **是否涉及产品决策：** 否。
- **建议本轮实施：** 是（小改动）。

### M5. evals.json 中 expected_output 为非结构化描述
- **文件：** `S0-text-preprocess/evals/evals.json`、`S1-narrative-structure/evals/evals.json`
- **证据：** 期望输出为"应识别出..."的自然语言描述，而非字段级精确断言。
- **真实影响：** 无法自动化验证 eval 结果。
- **触发场景：** CI/CD 自动化测试。
- **建议修改：** 将 expected_output 改为结构化断言（如 JSON Path 匹配）。
- **是否涉及产品决策：** 否。
- **建议本轮实施：** 否。

### M6. design-1.md 中 templates/ 目录未使用
- **文件：** `docs/design-1.md`
- **证据：** design-1.md 推荐 `templates/` 目录存放模板文件，但实际目录结构中没有 `templates/`。
- **真实影响：** 文档漂移，用户按设计文档寻找模板文件会找不到。
- **触发场景：** 新用户按文档操作。
- **建议修改：** 删除 design-1.md 中 templates/ 目录建议，或创建该目录。
- **是否涉及产品决策：** 否。
- **建议本轮实施：** 是（删除无用引用）。

## 低优先级问题（P3）

### L1. S0 preprocessing_issues.csv 格式未定义
- **文件：** `S0-text-preprocess/SKILL.md`
- **证据：** SKILL.md 提到输出 `preprocessing_issues.csv`，但没有定义 CSV 列结构。
- **真实影响：** 下游 Q0 消费 issues 时字段不明确。
- **建议修改：** 在 S0 prompt-template.md 中定义 issues 列。
- **建议本轮实施：** 否。

### L2. enums.yaml 中 character_narrative_function 在 design-3.md 中未列出
- **文件：** `schemas/enums.yaml`
- **证据：** enums.yaml 有 `character_narrative_function` 枚举，但 design-3.md 的共享枚举规范中未列出。
- **真实影响：** 文档与实现轻微不一致。
- **建议修改：** 在 design-3.md 中补充该枚举。
- **建议本轮实施：** 否。

---

# 5. 根因分析

不要只描述表面症状，说明问题来自哪里。

| 问题 | 根因类型 | 具体原因 |
|------|---------|---------|
| B1 报告生成未测试 | **实现缺陷** | S6 SKILL.md 第5步要求生成报告，但开发时优先完成结构化输出，报告生成被遗漏 |
| B2 O0 模板不一致 | **文档漂移** | design-2.md 是设计规范，prompt-template.md 是实际 Skill 参考，两者在迭代中未同步 |
| B3 S1 consolidation 违规 | **测试不足** | 测试数据生成时未严格区分 incremental/consolidation 模式 |
| B4 literary 判定矛盾 | **契约缺失** | payoff_nature 是迭代添加的功能，修改时未检查 S4 对 S2 的隐式依赖 |
| H1 Q0 reverse 排除规则矛盾 | **文档漂移** | SKILL.md 与 prompt-template.md 由不同步骤更新，未交叉验证 |
| H2 S3 数据消费不完整 | **契约缺失** | S6 合并逻辑设计时未明确角色注册表和阵营数据的处理路径 |
| H3 S9 缺乏验证数据 | **测试不足** | S9 是最后一个模块，测试时优先验证了核心分析模块 |
| H4 无端到端测试 | **测试不足** | 单 Skill eval 容易编写，端到端测试需要完整流水线，工作量大 |
| M1 摘要包字数限制 | **流程设计** | 1500 字是经验值，未考虑高角色密度场景 |
| M4 O0 next_action 固定 | **流程设计** | O0 定位为"编排器"，但未定义异常路径的决策逻辑 |

---

# 6. 优化方案

## 6.1 必须修改（不修改就无法可靠使用）

### F1. 补充 S6 报告生成测试
- **目标：** 验证 `analysis_report.md` 能根据 S1-S5+Q0 数据正确生成
- **涉及文件：** `S6-data-aggregation/SKILL.md`、`S6-data-aggregation/references/report-template.md`
- **预期行为变化：** S6 输出新增 `analysis_report.md`
- **风险：** 报告生成依赖 S1-S5 全部数据，若某 Skill 输出缺失，报告应有降级处理
- **验证方法：** 在测试目录中新增 eval，输入 S1-S5+Q0 mock 数据，验证报告九节结构完整且无占位符残留
- **向后兼容：** 是，新增输出文件不影响现有字段

### F2. 统一 O0 prompt-template.md 与 design-2.md
- **目标：** O0 输入结构与设计规范完全一致
- **涉及文件：** `O0-orchestrator/references/prompt-template.md`
- **预期行为变化：** O0 能收集 `available_tools` 和 `constraints`
- **风险：** 输入字段增多可能增加用户填写负担
- **验证方法：** 对比两份文件的字段列表，确保 100% 对齐
- **向后兼容：** 是，新增可选字段

### F3. 修复 S1 consolidation 测试数据
- **目标：** 测试数据模式与规范一致
- **涉及文件：** `test/analysis/wukongzhuan/s1/S1_narrative_structure.json`
- **预期行为变化：** 测试使用 incremental 模式，或补充 consolidation 独立调用证据
- **风险：** 无
- **验证方法：** 检查 JSON 中 mode 字段与 design-2.md 规范一致
- **向后兼容：** 是，仅修改测试数据

### F4. 修复 payoff_nature literary 判定矛盾
- **目标：** S4 在 S2 未运行时仍能正确分类 payoff_nature
- **涉及文件：** `S4-payoff-engineering/references/prompt-template.md`、`S4-payoff-engineering/SKILL.md`
- **预期行为变化：** `emotion_records` 标记为必需，或 literary 判定改为不依赖 S2
- **风险：** 强制要求 S2 可能增加用户运行成本
- **验证方法：** 检查 literary 判定逻辑是否自包含
- **向后兼容：** 是，仅调整判定条件

## 6.2 建议修改（明显提升稳定性，但不阻塞核心使用）

### R1. 统一 Q0 反向释放冲突排除规则
- **目标：** SKILL.md 与 prompt-template.md 中的排除规则完全一致
- **涉及文件：** `Q0-quality-audit/SKILL.md`、`Q0-quality-audit/references/prompt-template.md`
- **预期行为变化：** reverse 类事件不再触发 P1 冲突
- **风险：** 无
- **验证方法：** 对测试数据中的 reverse 事件运行 Q0，确认无 P1 冲突
- **向后兼容：** 是

### R2. 明确 S6 对 S3 角色数据的消费方式
- **目标：** S6 合并逻辑包含角色注册表和阵营数据
- **涉及文件：** `S6-data-aggregation/SKILL.md`、`S6-data-aggregation/references/prompt-template.md`
- **预期行为变化：** 角色配方数据可传递到 S8
- **风险：** 增加 S6 合并复杂度
- **验证方法：** 检查 S6 输出是否包含角色相关派生字段
- **向后兼容：** 是

### R3. 补充 S9 测试数据验证
- **目标：** S9 输出质量得到验证
- **涉及文件：** `test/analysis/wukongzhuan/s9/`
- **预期行为变化：** blank_template.csv 包含完整表头，manual_review_view.csv 包含数据行
- **风险：** 无
- **验证方法：** 检查 S9 输出文件
- **向后兼容：** 是

### R4. 修复 O0 next_action 动态决策
- **目标：** O0 根据输入充分性动态决定 next_action
- **涉及文件：** `O0-orchestrator/references/prompt-template.md`
- **预期行为变化：** 输入不足时 next_action 为 "向用户索取原始文本"
- **风险：** 无
- **验证方法：** 构造输入不足场景，检查 next_action 输出
- **向后兼容：** 是

## 6.3 暂不修改（有价值，但会扩大范围或需要更多证据）

### D1. 端到端流水线测试
- **理由：** 工作量大，需要完整运行一次 O0→S9 并验证每个中间产物
- **建议后续迭代时补充**

### D2. S2 calibration 模式测试
- **理由：** calibration 是可选增强功能，非核心路径
- **建议后续迭代时补充**

### D3. S7 Python 脚本生成测试
- **理由：** Python 是可选增强路径，Excel/WPS 条件格式是主要方案
- **建议后续迭代时补充**

### D4. evals.json 结构化断言改造
- **理由：** 当前自然语言描述足够人工验证，自动化验证需额外框架
- **建议后续迭代时补充**

## 6.4 明确不做

### N1. 不引入数据库
- **理由：** design-1.md 明确"不设计复杂数据库"，CSV/XLSX 对单人创作者更友好

### N2. 不重构流水线架构
- **理由：** 当前三层分离架构合理，问题在于实现细节而非架构

### N3. 不增加新的分析维度
- **理由：** 当前 12 个模块已覆盖主要分析需求，增加新模块会扩大复杂度

---

# 7. 实施记录

（待用户确认后实施）

---

# 8. 验证结果

（待实施后执行）

---

# 9. 待用户决策项

## 决策 1：payoff_nature literary 判定是否应依赖 S2？

**问题：** S4 的 `literary` 判定需要 S2 的 release_score，但 S4 输入中 S2 是可选的。

**推荐选择：** 将 S2 标记为 S4 的**必需输入**。理由：S4 的爽点强度评估本质上需要情绪数据作为参照，单独运行 S4 会导致 literary 判定缺失。

**备选选择：** 调整 literary 判定逻辑，改为不依赖 S2。理由：降低模块间耦合，允许 S4 独立运行。但需定义替代判定标准（如"释放方式为部分释放且无明确获得型奖励"）。

**不决策时的安全默认值：** S2 标记为必需，S4 在未获取 S2 数据时拒绝运行并提示用户先运行 S2。

---

## 决策 2：批次摘要包字数限制是否调整为弹性值？

**问题：** 当前 1500 字固定限制在高角色密度作品中可能不够。

**推荐选择：** 调整为弹性限制："不超过批次章节总字数的 5%，且不超过 3000 字"。理由：兼顾短批次和超长批次。

**备选选择：** 保持 1500 字不变。理由：简洁明确，用户容易理解。超出限制时截断并标记"摘要已截断"。

**不决策时的安全默认值：** 保持 1500 字不变。

---

# 10. 最终判定

## 结论：小幅修改后可用

## 理由

1. **核心架构合理**：三层分离（控制/分析/聚合）+ 中央表契约 + 批次处理 + Q0 审计的设计模式成熟，模块职责清晰。

2. **实现完整度较高**：12 个模块的 SKILL.md + prompt-template + enums 齐全，测试案例《悟空传》验证了全链路可行性。

3. **问题可控**：4 个阻塞问题均为文档一致性和测试覆盖问题，不涉及架构缺陷；修复工作量小。

4. **产品定位清晰**："AI 负责结构化分析，人工负责争议判断与最终确认"的分工明确，未越权替代用户决策。

5. **向后兼容**：所有建议修改均为新增字段或测试补充，不改变现有接口。

## 后续建议

- **短期（本轮）**：修复 4 个阻塞问题 + 4 个高优先级问题
- **中期（1-2 周）**：补充端到端流水线测试、S2 calibration 测试
- **长期（1-3 月）**：积累多书分析数据，横向比较提炼题材公式，验证"可迁移性"声明

---

*诊断完成。以上报告基于对全部 12 个 SKILL.md、10 个 prompt-template、schema、enums、evals 和《悟空传》测试数据的逐文件分析。*
