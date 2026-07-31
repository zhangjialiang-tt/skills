# 绿区维护操作（ACTIVE_MAINTENANCE 模式）

> 本文件在 ACTIVE_MAINTENANCE 模式下加载。定义绿区文件的维护操作。

---

## 绿区文件清单与语义

| 文件                     | 语义                         | 修改注意事项                         |
| ------------------------ | ---------------------------- | ------------------------------------ |
| `author_intent.md`       | 作者意图，建书时写入         | 表达创作方向和不可违背的意图         |
| `current_focus.md`       | 当前写作焦点                 | 指导接下来几章的方向，随时可更新     |
| `style_guide.md`         | 风格指南                     | 普通章节流水线不覆盖；style import 或仿写初始化时可能重建 |
| `book_rules.md`          | 书籍规则（世界观可执行规则） | 所有 reader 经此解析，修改影响全局   |
| `outline/story_frame.md` | 故事框架，世界观/设定权威源  | 修改需同步检查角色卡和卷地图         |
| `outline/volume_map.md`  | 卷地图，含节奏原则           | 修改需检查当前进度是否已超越修改范围 |
| `outline/节奏原则.md`    | 可选节奏指导                 | —                                    |
| `roles/主要角色/<名>.md` | 主角角色卡                   | 修改需检查关系网络                   |
| `roles/次要角色/<名>.md` | 配角角色卡                   | —                                    |

---

## 操作 1：`review-foundation`（只读故事诊断）

**目的**：结合 InkOS 已保存的设计、状态和最近正文，判断故事为什么失速或偏离。诊断本身只读，
不修改文件、不执行 InkOS 命令；用户要求修复后，必须重新进入变更影响分析和写入安全流程。

**评审维度**：

- 世界观自洽性
- 人物动机与关系
- 主线推进力
- 分卷结构合理性
- 爽点分布
- 伏笔回收进度
- 中期重复风险
- 结局兑现可行性

**固定诊断七项**：

1. 作品承诺是否被近期正文持续兑现；
2. 主角是否连续多个关键节点被动响应，没有主动选择；
3. 爽点类型、兑现方式或见证反应是否重复；
4. 伏笔是否超过计划回收窗口、缺少推进或公平线索；
5. 重要角色是否长期没有独立目标和下一步行动；
6. 下一卷是否只更换场景，没有冲突、代价和状态层级升级；
7. 卡文根因属于信息不足、冲突不足还是选择不足。

**修改前必须读取的文件**：

```
story/author_intent.md
story/current_focus.md
story/book_rules.md
story/outline/story_frame.md
story/outline/volume_map.md
story/roles/**
story/pending_hooks.md            # 只读
story/state/current_state.json    # 只读（存在时）
story/state/hooks.json            # 只读（存在时）
chapters/（最近 5-10 章，了解当前进度和重复模式）
```

**产物**：只读诊断报告。每条发现必须包含：

```yaml
dimension: promise_drift | protagonist_agency | payoff_repetition | hook_decay | inactive_character | next_volume_escalation | stuck_cause
severity: blocking | major | minor
evidence:
  - <本地构件或正文路径 + 可定位事实>
problem: <为什么会伤害作品承诺或后续生产>
recommended_zone: green | yellow | chapter | none
coach_needed: true | false
runtime_action:
  plan: true | false
  compose: true | false
  sync: true | false
  rewrite: true | false
recommendation: <最小可执行修正方向>
```

卡文诊断必须在 `information_missing`、`conflict_missing`、`choice_missing` 中选择一个主因；证据不足
时写明无法判断，不得用泛化建议替代证据。

只有核心目标、核心冲突、结局、整卷结构发生重大变化，Steward 无法定位卡文原因，或用户明确
要求质量对抗时，才以 `postbuild_diagnosis` 委托 Coach。Coach 不能替代变更影响分析、区域分类
或 InkOS 命令判断。

---

## 操作 2：`revise-world`

**目的**：修改世界观/设定。

**目标文件**：

```
story/outline/story_frame.md    # 主要修改对象
story/book_rules.md             # 可执行规则同步
story/roles/<相关角色>.md       # 受影响的色卡
story/outline/volume_map.md     # 必要时同步
```

**修改规则**：

1. 先输出变更影响分析（见 `change-impact-analysis.md`）
2. 修改 `story_frame.md` 中的世界观描述
3. 同步更新 `book_rules.md` 中的可执行规则
4. 检查受影响的角色卡是否需要调整
5. 如果世界观变化影响分卷规划，更新 `volume_map.md`

**注意事项**：

- 世界观规则修改可能影响已写正文的连续性
- 如果与已发布正文矛盾，需要评估是否需要 chapter sync/rewrite
- `book_rules.md` 中的规则必须是可执行的（不是百科描述）
- 普通绿区规则补充不调用 Coach；只有改变核心冲突或作品承诺时才考虑质量复核

---

## 操作 3：`revise-character`

**目的**：修改角色设定。

**目标文件**：

```
story/roles/<角色>.md           # 主要修改对象
story/roles/<关系角色>.md       # 关系网络中的其他角色
story/current_focus.md          # 必要时更新焦点
```

**修改规则**：

1. 先输出变更影响分析
2. 修改目标角色卡
3. 检查关系网络：哪些角色与此角色有冲突/债务/秘密关系
4. 同步更新受影响的关系角色卡
5. 如果角色变化影响近期写作方向，更新 `current_focus.md`

**注意事项**：

- 角色弧光修改需要检查是否与前文行为矛盾
- 删除角色需要评估对主线的影响
- 角色关系变化可能影响伏笔设计

---

## 操作 4：`revise-plot`

**目的**：修改剧情规划/分卷结构。

**目标文件**：

```
story/outline/volume_map.md     # 主要修改对象
story/current_focus.md          # 当前焦点同步
story/pending_hooks.md          # 仅设计提案（不直接改黄区）
```

**修改规则**：

1. 先输出变更影响分析
2. 修改 `volume_map.md` 中的分卷规划
3. 更新 `current_focus.md` 反映新的近期方向
4. 如果涉及伏笔调整，输出伏笔变更提案（写入 `current_focus.md` 的近期推进要求）
5. 不要直接修改 `pending_hooks.md`（黄区）

**注意事项**：

- 修改未来卷的规划风险较低
- 修改当前卷或已写部分的规划需要评估正文影响
- 伏笔回收位置变化需要检查线索是否已埋下

---

## 操作 5：`prepare-next-arc`

**目的**：根据当前正文和状态，规划接下来一个小阶段。

**目标文件**：

```
story/current_focus.md          # 主要落点
story/outline/volume_map.md     # 必要时细化
```

**规划内容**：

- 未来 5～15 章目标
- 主要冲突
- 爽点分布
- 线索推进
- 角色变化
- 不得提前揭示的内容

**修改前必须读取的文件**：

```
story/current_focus.md          # 当前焦点（避免重复/矛盾）
story/outline/volume_map.md     # 所在卷的规划
chapters/（最近 5-10 章）        # 当前进度和状态
story/pending_hooks.md          # 待回收伏笔（只读）
story/state/current_state.json  # 结构化状态（只读，如果存在）
```

**注意事项**：

- 规划必须与当前正文状态一致
- 不能规划揭示读者不应知道的信息
- 爽点节奏需要与前面章节衔接
