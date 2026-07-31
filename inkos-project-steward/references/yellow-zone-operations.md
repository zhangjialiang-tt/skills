# 黄区操作矩阵（YELLOW_ZONE_OPERATION 模式）

> 本文件在 YELLOW_ZONE_OPERATION 模式下加载。定义黄区文件的受控操作流程。
> 核心原则：黄区修改必须通过对应的 InkOS 状态同步机制（不变量 3）。

---

## 黄区文件清单与生命周期

| 文件                           | 生命周期                                      | 谁在写                  |
| ------------------------------ | --------------------------------------------- | ----------------------- |
| `book.json`                    | 建书时创建，pipeline 调 `saveBookConfig` 改写 | InkOS pipeline          |
| `chapters/*.md`                | 每章写作时生成                                | InkOS writer / 外部编辑 |
| `pending_hooks.md`             | 建书时生成，每章结算时更新                    | InkOS consolidator      |
| `current_state.md`             | 每章后由 consolidator 追加                    | InkOS consolidator      |
| `emotional_arcs.md`            | writer 每章全量覆盖 `updatedEmotionalArcs`    | InkOS writer            |
| `state/current_state.json`     | reducer 应用 delta                            | InkOS reducer           |
| `state/hooks.json`             | 结构化伏笔状态                                | InkOS consolidator      |
| `state/chapter_summaries.json` | 章节摘要                                      | InkOS consolidator      |

---

## 操作矩阵

| 目标              | Skill 操作                                      | 禁止行为                          |
| ----------------- | ----------------------------------------------- | --------------------------------- |
| 修改目标章数/字数 | 调用 `inkos book update`                        | 直接写 `book.json`                |
| 修改最新章措辞    | 编辑正文 + 建议 `inkos audit`                   | 修改 `index.json`                 |
| 修改最新章事实    | 编辑正文 + `inkos write sync <chapter>`         | 只改正文不结算                    |
| 修改历史因果      | `inkos write rewrite <chapter>`                 | 手改历史章并保留后续              |
| 新增长期伏笔      | 写入 `volume_map`/`current_focus`，通过剧情落地 | 活跃连载时只改 `pending_hooks.md` |
| 修改当前状态      | 通过正文变化 + `write sync`                     | 直接改 `state/current_state.json` |
| 修改情感方向      | 修改角色卡和焦点                                | 把 `emotional_arcs.md` 当权威     |
| 修复状态异常      | `inkos write repair-state <chapter>`            | 手改 `manifest.json`              |

---

## 操作详解

### 1. `book.json` — 通过 CLI 更新

**不要直接写文件。**

通过命令更新：

```bash
inkos book update [book-id] \
  --chapter-words 2500 \
  --target-chapters 300 \
  --status active
```

可用选项：`--chapter-words`、`--target-chapters`、`--status <outlining|active|paused|completed>`、`--lang`。

Skill 可以生成并建议用户执行此命令。

---

### 2. `chapters/*.md` — 三种修改类型判断

外部可编辑正文，但必须判断修改类型：

#### 类型 A：纯文风修改

示例：删除重复描述、调整句子、修改错别字、不改变事实和行为结果。

**操作**：

1. 直接编辑正文
2. 建议运行 `inkos audit [chapter]` 确认无连续性问题

**不需要** `write sync`（但运行一次审查是好习惯）。

#### 类型 B：改变本章事实

示例：谁拿到了物品、谁知道了秘密、人物关系变化、伏笔被提前揭示、角色受伤情况改变。

**操作**：

1. 编辑正文
2. 必须执行：

```bash
inkos write sync [book-id] <chapter>
```

3. `write sync` 会根据编辑后的正文重建 truth 文件和 SQLite 索引

**风险提示**：如果后续章节依赖被修改的事实，可能需要 rewrite 后续章节。

#### 类型 C：修改历史因果

示例：修改第 10 章，而后面已经写到第 30 章，且修改会影响后续剧情。

**操作**：

```bash
inkos write rewrite [book-id] <chapter>
```

**重要**：InkOS 会恢复到前一章快照，并**删除目标章及后续章节**后重新生成。

**必须**：

1. 向用户明确说明会删除后续章节
2. 获得用户确认
3. 建议先 `inkos book backup` 备份

---

### 3. `pending_hooks.md` — 区分生命周期

#### 尚未开始写第一章

如果 `story/state/hooks.json` 尚不存在，可以把设计出的初始伏笔写入 `pending_hooks.md`。

#### 已进入正式连载

结构化 `hooks.json` 已经是优先读取源，不能只修改 Markdown。

**正确路径**：

1. 输出伏笔变更提案
2. 将近期推进要求写入 `current_focus.md`（绿区）
3. 通过下一章正文完成推进
4. 让 InkOS 正常结算
5. 或修改正文后执行 `write sync`

**v0.1 不建议直接改 `hooks.json`。**

---

### 4. `current_state.md` — 不直接维护

连载后不直接维护。`state/current_state.json` 存在时会优先使用结构化状态。

**正确路径**：

路径 A：

```
修改正文事实 → write sync
```

路径 B：

```
让下一章发生预期变化 → InkOS 自动结算
```

---

### 5. `emotional_arcs.md` — 间接影响

不应直接作为长期人工维护面，因为 Writer 每章可能全量覆盖。

**正确路径**：修改绿区文件来间接影响情感走向：

```
story/roles/**           # 角色关系和性格
story/outline/volume_map.md  # 剧情节奏
story/current_focus.md       # 近期情感方向
```

定义人物关系和情绪方向，然后让 InkOS 在章节结算时更新情感状态。

---

### 6. 状态异常修复

当检测到状态不一致时：

```bash
inkos write repair-state [book-id] <chapter>
```

此命令重建 truth 但不重写正文。

**禁止**：手改 `state/manifest.json`（红区）。

---

## 确认要求

以下操作在执行前必须获得用户明确确认：

1. `write rewrite`（会删除后续章节）
2. 改变已发布正文中的事实
3. 任何可能导致数据丢失的操作

确认时应说明：

- 将要执行什么
- 会影响哪些内容
- 不可逆的后果是什么
- 建议先备份


---

## 执行—验证闭环

黄区操作必须形成闭环，不能把"建议执行"写成"已完成修改"。

### 非破坏性命令（book update、audit、status）

有终端权限时：
1. 执行命令
2. 检查退出码（非 0 = 失败）
3. 解析输出确认预期变化
4. 运行 `inkos status` 验证状态正常

无终端权限时：
1. 输出完整命令
2. 明确标记 **"未执行，需用户手动运行"**
3. 不得声称修改已完成

### 破坏性命令（write sync、write rewrite）

1. 输出变更影响分析
2. 建议备份（`inkos book backup`）
3. 获得作者明确确认
4. 执行命令
5. 检查退出码
6. 运行 `inkos status` + `inkos audit` 验证
7. 向用户报告验证结果

### 命令失败处理

命令执行失败时：
- **不得声称操作已完成**
- 报告错误信息
- 分析可能原因（锁冲突？版本不对？参数错误？）
- 给出下一步建议
- 如果是 `.write.lock` 冲突，等待后重试

### 验证检查清单

每次黄区操作完成后，确认：

- [ ] 命令退出码为 0
- [ ] `inkos status` 显示预期状态
- [ ] 无新的 audit 错误
- [ ] 未误写红区（可用 `scripts/verify_diff.py` 验证）
- [ ] 向用户报告了实际结果（不是计划）