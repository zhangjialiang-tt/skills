# 建书对齐流程（FOUNDATION_ALIGNMENT 模式）

> 本文件在 FOUNDATION_ALIGNMENT 模式下加载。定义建书后对齐检查的完整流程。
> 触发条件：存在 `books/<bookId>/` 目录，但 `chapters/` 为空或不存在。

---

## 为什么需要对齐

建书时 InkOS 架构师会对 `--brief` 进行二次转换，生成 `story_frame.md`、`volume_map.md`、`roles/`、`book_rules.md`、`pending_hooks.md` 等文件。

**不能直接信任这个二次转换结果。** 常见问题：

- 世界观复杂度被降级（架构师简化了规则系统）
- 角色关系被简化（多人冲突网络变成单线对立）
- 伏笔被丢弃（brief 中的谜题线索未映射到 hooks）
- 分卷规划被压缩（多卷结构变成笼统概述）
- 风格要求被忽略

---

## 对齐步骤

### 步骤 1：收集比对材料

**设计包侧**（如果存在 `story-design/` 目录）：

```
story-design/09-story-outline.md
story-design/inkos/book-brief.md
story-design/02-world-system.md
story-design/03-character-system.md
story-design/07-foreshadowing-and-mystery.md
story-design/08-volume-outline.md
```

**InkOS 侧**（建书生成）：

```
books/<bookId>/story/outline/story_frame.md
books/<bookId>/story/outline/volume_map.md
books/<bookId>/story/roles/**
books/<bookId>/story/book_rules.md
books/<bookId>/story/pending_hooks.md
books/<bookId>/story/author_intent.md
books/<bookId>/story/current_focus.md
books/<bookId>/book.json
```

如果没有 `story-design/` 目录，则基于用户口述的设计意图进行对齐。

### 步骤 2：逐项比对

比对维度：

| 设计包内容 | 对应 InkOS 文件                    | 检查点                     |
| ---------- | ---------------------------------- | -------------------------- |
| 世界观规则 | `story_frame.md` + `book_rules.md` | 规则是否完整、是否可执行   |
| 角色设定   | `roles/**`                         | 角色是否齐全、属性是否完整 |
| 角色关系   | `roles/**` 中的关系描述            | 冲突网络是否保留           |
| 分卷规划   | `volume_map.md`                    | 卷数、节奏、转折是否一致   |
| 伏笔设计   | `pending_hooks.md`                 | 初始伏笔是否映射           |
| 作品承诺   | `author_intent.md`                 | 核心意图是否准确           |
| 目标参数   | `book.json`                        | 章数、字数、平台是否正确   |

### 步骤 3：识别问题

对每个比对项，判断：

- **遗漏**：设计包中有但 InkOS 文件中缺失
- **曲解**：InkOS 文件中的表述改变了原意
- **降级**：InkOS 文件简化了设计包中的复杂度

### 步骤 4：修正绿区

对识别出的问题，直接修正绿区文件：

- 世界观遗漏/曲解 → 修正 `story_frame.md` + `book_rules.md`
- 角色缺失/简化 → 补充/修正 `roles/<角色>.md`
- 分卷压缩 → 修正 `volume_map.md`
- 意图偏差 → 修正 `author_intent.md`
- 焦点不准 → 修正 `current_focus.md`

**注意**：

- `pending_hooks.md` 是黄区。如果伏笔被丢弃，将伏笔设计写入 `current_focus.md` 的近期推进要求，或通过 `author_intent.md` 补充。
- `book.json` 是黄区。参数不对时建议用户执行 `inkos book update`。

### 步骤 5：输出对齐报告

使用模板：`templates/alignment-report.md`

---

## 对齐报告格式

```markdown
# 建书对齐报告

## 比对摘要

- 设计包来源：story-design/ | 用户口述
- 比对时间：
- 总体评估：通过 | 需修正 | 严重偏差

## 比对结果

### 世界观（story_frame.md + book_rules.md）

- 状态：✅ 一致 | ⚠️ 需修正 | ❌ 严重偏差
- 问题：
- 修正动作：

### 角色（roles/\*\*）

- 状态：
- 问题：
- 修正动作：

### 分卷规划（volume_map.md）

- 状态：
- 问题：
- 修正动作：

### 伏笔（pending_hooks.md）

- 状态：
- 问题：
- 替代方案（绿区写入）：

### 作者意图（author_intent.md）

- 状态：
- 问题：
- 修正动作：

### 书录参数（book.json）

- 状态：
- 问题：
- 建议命令：

## 已执行修正

- [ ] 修正 1
- [ ] 修正 2

## 验证清单

- [ ] 所有绿区文件已更新
- [ ] 无红区写入
- [ ] 黄区问题已通过替代路径处理
- [ ] 建议用户执行 `inkos plan chapter` 验证输入
```

---

## 对齐后建议

对齐完成后，建议用户：

1. 运行 `inkos plan chapter` 验证规划阶段能正确读取修正后的绿区
2. 运行 `inkos compose chapter` 检查运行期产物是否正确
3. 确认无误后再开始写第一章
