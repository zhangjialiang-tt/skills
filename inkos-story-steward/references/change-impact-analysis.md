# 变更影响分析格式

> 本文件在建书后执行任何修改前加载。定义变更影响分析的标准格式和流程。

---

## 分析前必须回答的 7 个问题

每次建书后修改前，必须先回答：

1. **这是未来设计变更，还是追溯修改？**
   - 未来设计变更：只影响尚未写的章节
   - 追溯修改：与已写正文产生矛盾

2. **是否与已经发布的正文矛盾？**
   - 检查已写章节中是否有与被修改内容直接矛盾的描述

3. **会影响哪些角色？**
   - 列出直接和间接受影响的角色

4. **会影响哪些伏笔？**
   - 检查 `pending_hooks.md` / `state/hooks.json` 中相关的伏笔

5. **会影响哪些卷？**
   - 当前卷？后续卷？

6. **需要修改正文吗？**
   - 如果与已写正文矛盾，是否需要编辑章节

7. **需要 sync 还是 rewrite？**
   - 只改本章事实 → sync
   - 影响后续因果 → rewrite
   - 不影响正文 → 都不需要

---

## YAML 输出格式

```yaml
change_id: CHANGE-<YYYYMMDD>-<NNN>
change_type: future_design | retroactive_fix
target:
  - <被修改的文件路径>

affected_chapters:
  written: none | <章节范围>
  future: none | <章节范围>

affected_characters:
  - <角色名>

affected_hooks:
  - <伏笔编号>

runtime_action:
  plan_required: true | false
  compose_required: true | false
  sync_required: true | false
  rewrite_required: true | false

risk:
  level: low | medium | high | critical
  reason: <一句话说明风险原因>
```

---

## 字段说明

| 字段                        | 说明                                                          |
| --------------------------- | ------------------------------------------------------------- |
| `change_id`                 | 变更编号，格式 `CHANGE-<YYYYMMDD>-<NNN>`（日期+当日序号），跨会话不重复 |
| `change_type`               | `future_design`（只影响未来）或 `retroactive_fix`（追溯修改） |
| `target`                    | 本次修改直接涉及的文件                                        |
| `affected_chapters.written` | 已写章节中受影响的范围                                        |
| `affected_chapters.future`  | 未来章节中受影响的范围                                        |
| `affected_characters`       | 受影响的角色列表                                              |
| `affected_hooks`            | 受影响的伏笔编号                                              |
| `runtime_action`            | 是否需要运行 InkOS 命令                                       |
| `risk.level`                | 风险等级                                                      |
| `risk.reason`               | 风险原因                                                      |

---

## 风险等级定义

| 等级       | 含义                                       | 示例                                 |
| ---------- | ------------------------------------------ | ------------------------------------ |
| `low`      | 只影响未来设计，不与已写内容矛盾           | 修改第三卷的规划                     |
| `medium`   | 影响当前卷规划或角色关系，但未在正文中揭示 | 改变第二卷对手身份（尚未揭示）       |
| `high`     | 与已写正文存在矛盾，需要 sync              | 修改角色能力设定（前文已展示）       |
| `critical` | 影响多章因果链，需要 rewrite               | 改变关键角色存活状态（后续多章依赖） |

---

## 示例

### 示例 1：低风险未来设计变更

```yaml
change_id: CHANGE-20260730-001
change_type: future_design
target:
  - story/outline/volume_map.md
  - story/current_focus.md

affected_chapters:
  written: none
  future: 42-58

affected_characters:
  - 林远
  - 何卫国

affected_hooks:
  - H007
  - H012

runtime_action:
  plan_required: true
  compose_required: true
  sync_required: false
  rewrite_required: false

risk:
  level: medium
  reason: 改变第二卷对手身份，但尚未在正文中揭示
```

### 示例 2：高风险追溯修改

```yaml
change_id: CHANGE-20260730-002
change_type: retroactive_fix
target:
  - chapters/010_基地危机.md

affected_chapters:
  written: 10-15
  future: 16-30

affected_characters:
  - 陈工
  - 李队长

affected_hooks:
  - H003

runtime_action:
  plan_required: false
  compose_required: false
  sync_required: false
  rewrite_required: true

risk:
  level: critical
  reason: 改变第10章角色存活状态，后续5章直接依赖此事实
```

---

## 简化规则

以下情况可以输出简化版分析（只需回答 7 个问题，不需要完整 YAML）：

- 纯文风修改（类型 A 章节编辑）
- 只修改 `current_focus.md` 的近期方向
- `review-foundation`（只评审不修改）

以下情况必须输出完整 YAML：

- 修改 `story_frame.md` / `book_rules.md`
- 修改角色卡
- 修改 `volume_map.md`
- 任何涉及正文事实的修改
- 任何需要 sync/rewrite 的操作
