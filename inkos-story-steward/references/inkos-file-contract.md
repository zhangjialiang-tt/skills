# InkOS 建书目录结构与红黄绿分区

> 本文件定义 InkOS 建书后的文件契约。建书后任何模式下需要判断文件分区时参考。
> 数据来源：InkOS v1.7.x 源码核实（`packages/core/src`）。

---

## 顶层位置

`inkos init <project>` 后，每本书位于：

```
<projectRoot>/books/<bookId>/
```

项目级还有 `.inkos/`（全局配置/会话/资料，非单书专属）。

---

## 单本书目录树（带区域标记）

```
books/<bookId>/
├── 🟡 book.json              # 书录配置（黄区）
├── 🔴 .write.lock            # 写锁（红区）
├── chapters/                 # 章节区（懒创建）
│   ├── 🔴 index.json         # 章节索引（红区）
│   └── 🟡 001_章节名.md      # 每章正文（黄区）
└── story/                    # 控制面核心目录（建书即生成）
    ├── 🟢 author_intent.md   # 作者意图（绿区）
    ├── 🟢 current_focus.md   # 当前焦点（绿区）
    ├── 🟢 style_guide.md     # 风格指南（绿区，append-only）
    ├── 🟢 book_rules.md      # 书籍规则（绿区）
    ├── 🟡 current_state.md   # 当前状态（黄区，JSON 优先）
    ├── 🟡 pending_hooks.md   # 待回收伏笔（黄区，JSON 优先）
    ├── 🟡 emotional_arcs.md  # 情感弧线表（黄区，writer 每章覆盖）
    ├── 🔴 story_bible.md     # 兼容指针文（红区，废弃）
    ├── 🔴 character_matrix.md # 兼容指针文（红区，writer 覆盖）
    ├── 🟢 outline/           # 架构大纲（绿区）
    │   ├── 🟢 story_frame.md # 故事框架
    │   ├── 🟢 volume_map.md  # 卷地图
    │   └── 🟢 节奏原则.md     # 可选
    ├── 🟢 roles/             # 角色卡（绿区）
    │   ├── 🟢 主要角色/<角色名>.md
    │   └── 🟢 次要角色/<角色名>.md
    ├── 🔴 runtime/           # 运行时产物（红区）
    │   └── narrative-forecasts/
    ├── 🟡 state/             # 结构化状态
    │   ├── 🔴 manifest.json  # 状态清单（红区）
    │   ├── 🟡 current_state.json
    │   ├── 🟡 hooks.json
    │   └── 🟡 chapter_summaries.json
    └── 🔴 memory.db           # SQLite 记忆库（红区）
```

补充：源码中另有 `story/brief.md`（🟢 绿区）与 `story/snapshots/<章号>/`（🔴 红区）。

---

## 编辑分区规则

### 🟢 绿区语义

Codex/Skill 可直接维护。InkOS 规划/写作时从磁盘重读，且流水线**不会覆盖**用户内容。

语义：`writeIfMissing` / append-only。

包含：`author_intent.md`、`current_focus.md`、`book_rules.md`、`outline/*`、`roles/**`、`style_guide.md`、`brief.md`。

### 🟡 黄区语义

InkOS **读且写**这些文件。存在同名权威 `.json`（JSON 优先于 MD），或被 writer 在每章流水线里全量覆盖。

Skill 改动会被冲掉或失效，须走 InkOS 流程更新。

包含：`current_state.md`、`pending_hooks.md`、`chapters/*.md`（改后须 `write sync`）、`emotional_arcs.md`、`book.json`、`state/*.json`（manifest 除外）。

### 🔴 红区语义

运行时数据、索引、快照、锁、记忆库，以及 InkOS 拥有/回写的遗留文件。

Skill **禁止写入**（可读做诊断）。

包含：`.write.lock`、`chapters/index.json`、`runtime/**`、`state/manifest.json`、`memory.db`、`story_bible.md`、`character_matrix.md`、`snapshots/**`。

---

## 文件/目录职责说明

### 书录与锁

- **`book.json`** — 书录元数据（语言、类型、目标章数、单章字数、发布平台等）。
- **`.write.lock`** — 运行时写锁。并发写入冲突时返回 `BOOK_BUSY`。

### 章节区 `chapters/`（懒创建）

- **`index.json`** — 章节索引（编号、标题、相对路径）。
- **`<NNN>_<title>.md`** — 成稿正文。

### 控制面 `story/`

- **作者意图类**：`author_intent.md`、`current_focus.md`。
- **规则/风格类**：`book_rules.md`、`style_guide.md`。
- **状态/连续性类**：`current_state.md`、`pending_hooks.md`、`emotional_arcs.md`。
- **兼容指针文（废弃）**：`story_bible.md`、`character_matrix.md`。

### 架构大纲 `story/outline/`

- `story_frame.md` — 世界观/设定权威源。
- `volume_map.md` — 卷/分卷地图，含节奏原则段。
- `节奏原则.md` — 可选。

### 角色卡 `story/roles/`

- `主要角色/<角色名>.md`、`次要角色/<角色名>.md` — 一人一卡。

### 运行时 `story/runtime/`

- `narrative-forecasts/` — 剧情推演产物目录。

### 结构化状态 `story/state/`（懒创建）

- `manifest.json` — 状态清单（`schemaVersion=2`、`lastAppliedChapter`）。
- `current_state.json`、`hooks.json`、`chapter_summaries.json` — 结构化状态片段。

### 时序记忆 `story/memory.db`（懒创建）

- Node 22+ 内置 `node:sqlite` 时序记忆库。

---

## 关键机制

1. **两套布局并存**：旧布局（Phase 4）把 `story_bible.md`/`volume_outline.md`/`character_matrix.md` 平铺在 `story/`；新布局（Phase 5）拆到 `outline/` + `roles/`。`rules-reader` 优先读新布局、回退旧文件。
2. **懒创建**：建书阶段先建 `story/` 骨架；`chapters/`（首章落盘）、`state/*.json`（首次引导）、`memory.db`（首次访问）按需生成。
3. **控制文档幂等**：`ensureControlDocuments` 使用 `writeIfMissing`，只在文件缺失时写，不覆盖用户修改。

---

## 项目级 `.inkos/`

与单书无关，是项目级运行时目录：

- `secrets.json` — LLM 密钥
- `sessions/` — 会话记录
- `materials/` — 归档资料卡
- `research/` — 研究报告
- `uploads/` — 上传文件
