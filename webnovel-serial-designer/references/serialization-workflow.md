# 连载设计 11 阶段详细流程

本文档是 `webnovel-serial-designer` 的工作流程权威参考。
每个阶段包含：输入、活动、输出、质量检查、决策级别。

---

## 阶段 0：连载定界（00-serialization-brief.md）

| 项目 | 内容 |
|------|------|
| **输入** | `source/synopsis.md`、`source/synopsis-contract.yaml` |
| **活动** | 从上游提取目标平台、章数、字数、读者画像、核心连载体验、节奏偏好；与上游 `target_hints` 对齐 |
| **输出** | `design/00-serialization-brief.md` |
| **质量检查** | 6 项字段（platform, target_chapters, chapter_words, reader_profile, core_experience, pacing）全部填写且与上游不矛盾 |
| **决策级别** | L1（自主，记录） |

---

## 阶段 1：连载承诺（01-serial-promise.md）

| 项目 | 内容 |
|------|------|
| **输入** | `00-serialization-brief.md`、上游核心梗概 |
| **活动** | 设计四层承诺：点击钩子、前三章承诺、前三十章承诺、长期追读承诺；确保每层递进而非重复 |
| **输出** | `design/01-serial-promise.md` |
| **质量检查** | 四层承诺逻辑递进（点击→留下→追读→追完）；每层可独立向读者解释；不剧透上游真相 |
| **决策级别** | L1（自主，记录） |

---

## 阶段 2：故事发动机（02-story-engine.md）⚡ Gate A

| 项目 | 内容 |
|------|------|
| **输入** | `00`、`01`、上游冲突与规则 |
| **活动** | 设计可重复运行的剧情循环（≥4 步）、可变输入（≥10 种触发条件）、累计状态（不可逆）、升级轴、反重复规则；执行五项发动机测试（见 `story-engine-design.md`） |
| **输出** | `design/02-story-engine.md` |
| **质量检查** | 五项测试全部通过；循环可运行 50+ 次不重复；升级轴单调递增；反重复规则覆盖 ≥3 种重复模式 |
| **决策级别** | **L2（Gate A 确认）** |

---

## 阶段 3：人物连载化（03-character-serialization.md）

| 项目 | 内容 |
|------|------|
| **输入** | `02`、上游角色设定 |
| **活动** | 为主角设计跨卷弧光检查点（每卷一个 forced_choice + cost）；配角分配连载功能；设计阶段性对手；制定禁止漂移规则 |
| **输出** | `design/03-character-serialization.md` |
| **质量检查** | 主角弧光节点覆盖所有卷；配角无"万能工具人"；对手有独立时间线；漂移规则可执行 |
| **决策级别** | L1（Gate A 后自主） |

---

## 阶段 4：世界压力系统（04-world-pressure-system.md）

| 项目 | 内容 |
|------|------|
| **输入** | `02`、`03`、上游世界规则 |
| **活动** | 识别 ≥3 个持久压力源；设计每个压力源的升级路径（≥3 级）；映射压力到故事产出类型；标记世界状态不可逆变化 |
| **输出** | `design/04-world-pressure-system.md` |
| **质量检查** | 压力源覆盖全部卷（无空卷）；升级路径与发动机升级轴对齐；不可逆变化与上游 `frozen_facts` 不矛盾 |
| **决策级别** | L1（Gate A 后自主） |

---

## 阶段 5：分卷架构（05-volume-architecture.md）⚡ Gate A

| 项目 | 内容 |
|------|------|
| **输入** | `00`-`04` 全部 |
| **活动** | 确定总卷数和每卷章数范围；为每卷设计：核心目标、冲突、揭示、高潮、不可逆状态变化、卷末钩子；确保卷间升级关系 |
| **输出** | `design/05-volume-architecture.md` |
| **质量检查** | 章数总和在目标 ±10% 内；每卷高潮递进；卷间无重复冲突类型；每卷有明确不可逆变化；卷末钩子驱动下一卷 |
| **决策级别** | **L2（Gate A 确认）** |

---

## 阶段 6：爽点与节奏（06-payoff-and-rhythm.md）

| 项目 | 内容 |
|------|------|
| **输入** | `05`、`01`（追读承诺） |
| **活动** | 分类爽点类型（mystery_reveal / authority_reversal / capability / relationship / resource）；设计小/中/大兑现密度；为每卷分配爽点轮换；设计压抑→兑现→代价节奏 |
| **输出** | `design/06-payoff-and-rhythm.md` |
| **质量检查** | 前 10 章有 ≥2 个明确兑现；正常连载期最小爽点间隔 ≤ 目标值；每卷至少 1 个大兑现；无"无代价爽点" |
| **决策级别** | L1（Gate A 后自主） |

---

## 阶段 7：伏笔与信息释放（07-mystery-and-information.md）

| 项目 | 内容 |
|------|------|
| **输入** | `05`、上游真相（`synopsis-contract.yaml` 中 truth 相关字段） |
| **活动** | 为每个核心真相设计线索时间表（哪卷埋、哪卷强化、哪卷揭示）；设计读者/主角/对手三层知识不对称；设计 ≥2 个错误解释（fair-play）；确定回收条件和位置 |
| **输出** | `design/07-mystery-and-information.md` |
| **质量检查** | 每个真相有 ≥3 条公平线索；错误解释有逻辑基础；揭示位置与分卷高潮对齐；无"凭空揭示"（所有揭示有前置线索） |
| **决策级别** | L1（Gate A 后自主） |

---

## 阶段 8：开局计划（08-launch-plan.md）

| 项目 | 内容 |
|------|------|
| **输入** | `01`、`02`、`05`、`06` |
| **活动** | 设计黄金三章（每章核心事件 + 章尾钩子）；规划前十章节奏；确定前三十章方向；写出第一个发动机完整循环 |
| **输出** | `design/08-launch-plan.md` |
| **质量检查** | 黄金三章兑现了 `01` 的"前三章承诺"；第 3 章包含不可逆选择；前十章完成至少 1 个完整发动机循环；前三十章方向与 VOL-01 目标一致 |
| **决策级别** | L1（Gate A 后自主） |

---

## 阶段 9：终局收束（09-endgame-convergence.md）

| 项目 | 内容 |
|------|------|
| **输入** | `05`、`07`、上游结局 |
| **活动** | 定义收束条件（什么状态满足后进入终局）；设计上游结局的忠实实现路径；列出禁止的终局改变；规划最后 10-20 章方向 |
| **输出** | `design/09-endgame-convergence.md` |
| **质量检查** | 收束条件可验证（非模糊状态描述）；结局与上游冻结结局一致；伏笔回收位置在终局前完成；禁止改变列表覆盖上游 `prohibited_directions` |
| **决策级别** | L1（Gate A 后自主） |

---

## 阶段 10：Readiness Review（10-readiness-review.md）

| 项目 | 内容 |
|------|------|
| **输入** | `00`-`09` 全部 + `source/synopsis-contract.yaml` |
| **活动** | 执行 9 维度自检（见 `references/readiness-checklist.md`）；自动修复可修复项；生成 `reviews/readiness-review.yaml`；产出 verdict |
| **输出** | `design/10-readiness-review.md` + `reviews/readiness-review.yaml` |
| **质量检查** | 9 维度全部有明确 pass/fail/fixable 判定；blocking 项为 0 或已标注作者接受风险 |
| **决策级别** | 自动生成（非作者 Gate），结果呈现给 Gate B |

---

## Gate A 触发与容差

### 触发时机

阶段 0-5 的草稿全部完成后，进入 `AWAITING_GATE_A`。
作者确认 4 项内容：
1. 故事发动机（`02`）
2. 宏观分卷架构（`05`：卷数、每卷目标、高潮）
3. 主角跨卷弧光节点（`03` 中的 arc_checkpoints）
4. 核心真相的宏观释放位置（`07` 中的 reveal_volume）

### 容差规则

Gate A 冻结后，以下修改**不需要**重新打开 Gate A：
- 章数调整 ±15%（如 300 章 → 255-345 均可）
- 局部事件替换（不改变卷目标和弧光节点）
- 配角增减（不影响主角弧光）
- 爽点类型微调

以下修改**必须**重新打开 Gate A：
- 增加或删除整卷
- 改变主角弧光节点
- 替换故事发动机核心循环
- 改变核心真相揭示卷

---

## Gate B 触发

阶段 10 完成后，进入 `AWAITING_GATE_B`。
作者确认：
1. Readiness Review 结果（verdict + 风险清单）
2. 上游忠实度（preserved_synopsis_facts 完整性）
3. 剩余风险（accepted_risks）
4. SerialDesignPackage 最终冻结

决策选项：`approve_and_freeze` / `revise` / `reopen_gate_a` / `return_to_synopsis`

---

## 五级升级触发

以下情况暂停当前工作并请求作者决策：

| # | 触发条件 | 动作 |
|---|----------|------|
| 1 | 需要修改上游冻结事实 | 生成 SynopsisRevisionProposal，退回 story-synopsis |
| 2 | 目标体量无法成立（发动机无法支撑目标章数） | 提供三选项：降低篇幅 / 扩大世界边界 / 修改上游 |
| 3 | 存在体验显著不同的宏观架构 | Gate A 时提供 2-3 个方案供选择 |
| 4 | 需要改变已确认 Gate A | 重新打开 Gate A（检查容差规则） |
| 5 | 阻塞性质量风险无法自动修复 | 请求作者风险接受决策 |

---

## Assertion 生成规则

`serial-contract.yaml` 中的 assertions 在 Gate B 冻结时自动生成：

1. **来源**：每个设计文件（`00`-`09`）中的**已确认设计结论**
2. **筛选标准**：只记录**跨构件约束**（如"发动机升级轴与分卷高潮对齐"），不记录文件内部细节
3. **规模**：300 章长篇约 30-60 条
4. **字段填充**：
   - `id`: `ASSERT-<TYPE>-<NNN>`（TYPE 取 ENGINE/VOLUME/ARC/PAYOFF/TRUTH/LAUNCH/ENDGAME）
   - `status`: Gate B 后全部为 `confirmed`
   - `importance`: 影响终局或发动机为 `critical`；影响单卷为 `major`；其余 `supporting`
   - `source_ref`: 指向源设计文件和段落
   - `invariants`: 从该结论推导出的语义不变量（编译时不可违反）

---

## serial-contract.yaml 组装流程

Gate B `approve_and_freeze` 后执行：

1. 从 `00` 提取 `serialization_target`
2. 从上游复制 `upstream_integrity`（frozen_facts + prohibited_directions）
3. 从 `01` 提取 `serial_promise`
4. 从 `02` 提取 `story_engine`
5. 从 `05` 提取 `volumes`
6. 从 `03` 提取 `serial_characters`
7. 从 `04` 提取 `world_pressure`
8. 从 `06` 提取 `payoff_system`
9. 从 `07` 提取 `information_design`
10. 从 `08` 提取 `launch_plan`
11. 从 `09` 提取 `endgame_convergence`
12. 从全部文件生成 `assertions`
13. 设置 `status.serial_design_status: frozen`、`handoff_ready: true`
14. 填入 `compilation_policy`（固定，见模板）

生命周期进入 `READY_FOR_COMPILATION`。
