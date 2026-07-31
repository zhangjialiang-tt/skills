---
created: 2026-07-30T16:34
updated: 2026-07-30T17:33
---

## InkOS 建书目录结构参考

> 基于 `packages/core/src` 源码核实（`project-tools.ts` 建书入口 → `pipeline.initBook` → `architect.writeFoundationFiles` + `StateManager.ensureControlDocuments` + `state-bootstrap` + `memory-db`）。
> 本文描述 `inkos init` / `/new` 建书后**磁盘上实际生成的文件与目录**。

### 1. 顶层位置

`inkos init <project>` 后，每本书位于：

```
<projectRoot>/books/<bookId>/
```

项目级还有 `.inkos/`（全局配置/会话/资料，非单书专属，见第 5 节）。

### 2. 单本书目录树

```
books/<bookId>/
├── 🟡 book.json              # 书录配置（黄区：InkOS 读且写 saveBookConfig，改动可能被冲）
├── 🔴 .write.lock            # 写锁（红区：禁止修改）
├── chapters/                 # 章节点（懒创建）
│   ├── 🔴 index.json         # 章节索引（红区：禁止修改）
│   └── 🟡 001_章节名.md      # 每章正文（黄区：外部修改后须 write sync）
└── story/                    # 控制面核心目录（建书即生成）
    ├── 🟢 author_intent.md   # 作者意图（绿区：可改）
    ├── 🟢 current_focus.md   # 当前焦点（绿区：可改）
    ├── 🟢 style_guide.md     # 风格指南（绿区：init/append-only，不被流水线覆盖）
    ├── 🟢 book_rules.md      # 书籍规则（绿区：可改）
    ├── 🟡 current_state.md   # 当前状态（黄区：JSON 优先）
    ├── 🟡 pending_hooks.md   # 待回收伏笔（黄区：JSON 优先）
    ├── 🟡 emotional_arcs.md  # 情感弧线表（黄区：writer 每章全量覆盖 updatedEmotionalArcs）
    ├── 🔴 story_bible.md     # 兼容指针文（红区：InkOS 建书时写一次，废弃勿改）
    ├── 🔴 character_matrix.md # 兼容指针文（红区：writer 每章可能覆盖，改用 roles/）
    ├── 🟢 outline/           # 架构大纲（绿区）
    │   ├── 🟢 story_frame.md # 故事框架（绿区：可改）
    │   ├── 🟢 volume_map.md  # 卷地图（绿区：可改）
    │   └── 🟢 节奏原则.md     # 可选（绿区）
    ├── 🟢 roles/             # 角色卡（绿区）
    │   ├── 🟢 主要角色/<角色名>.md
    │   └── 🟢 次要角色/<角色名>.md
    ├── 🔴 runtime/           # 运行时产物（红区：禁止修改）
    │   └── narrative-forecasts/   # 剧情推演产物（红区）
    ├── 🟡 state/             # 结构化状态（黄区为主，manifest 属红区）
    │   ├── 🔴 manifest.json  # 状态清单（红区：禁止修改）
    │   ├── 🟡 current_state.json
    │   ├── 🟡 hooks.json
    │   └── 🟡 chapter_summaries.json
    └── 🔴 memory.db           # SQLite 记忆库（红区：禁止修改）
```

> **编辑分区图例**（基于 Codex↔InkOS 编辑契约，经源码核实）
>
> - 🟢 **绿区**：Codex 可直接维护。InkOS 规划/写作时从磁盘重读，且流水线**不会覆盖**用户内容（`writeIfMissing`/append-only 语义）。含 `author_intent.md`、`current_focus.md`、`book_rules.md`、`outline/*`、`roles/**`、`style_guide.md`。
> - 🟡 **黄区**：InkOS **读且写**这些文件——要么存在同名权威 `.json`（JSON 优先于 MD），要么被 writer 在每章流水线里**全量覆盖** Markdown。Codex 改动会被冲掉或失效，须走 InkOS 流程更新。含 `current_state.md`、`pending_hooks.md`、`chapters/*.md`（改后须 `write sync`）、`emotional_arcs.md`（writer 每章覆盖 `updatedEmotionalArcs`）、`book.json`（pipeline 调 `saveBookConfig` 改写）。
> - 🔴 **红区**：运行时数据、索引、快照、锁、记忆库，以及 InkOS **拥有/回写、不应手改**的遗留文件。Codex 禁止写入（可读做诊断）。含 `.write.lock`、`chapters/index.json`、`runtime/**`、`state/manifest.json`、`memory.db`，以及废弃兼容指针文 `story_bible.md`（建书时写一次）、`character_matrix.md`（writer 每章可能覆盖 `updatedCharacterMatrix`，改用 `roles/`）。
>
> 补充：源码中另有 `story/brief.md`（🟢 绿区：规划阶段由 `--context` 落盘，planner 会读，但再次用 `--context` 跑 `plan` 会覆盖它）与 `story/snapshots/<章号>/`（🔴 红区：rewrite/回滚恢复机制核心），本树未列入，使用时同样适用对应分区。

### 3. 文件/目录按职责说明

#### 书录与锁

- **`book.json`** — 书录元数据，决定语言、类型、目标章数、单章字数、发布平台等。
- **`.write.lock`** — 运行时写锁。并发写入冲突时返回 `BOOK_BUSY`，不是建书即时产物，而是首次写入时建立。

#### 章节区 `chapters/`（懒创建）

- **`chapters/index.json`** — 章节索引，记录每章编号、标题、相对路径。
- **`<序号>_<标题>.md`** — 成稿正文，命名规则 `<NNN>_<title>.md`。

#### 控制面 `story/`（建书即生成骨架）

- **作者意图类**：`author_intent.md`（建书由 `/new` 写入）、`current_focus.md`（当前焦点）。
- **规则/风格类（权威）**：`book_rules.md`（书籍规则，所有读者经此解析）、`style_guide.md`（风格指南，含"写作方法论"段）。
- **状态/连续性类**：`current_state.md`（每章后由 consolidator 追加）、`pending_hooks.md`（待回收伏笔）、`emotional_arcs.md`（情感弧线表）。
- **兼容指针文（已废弃）**：`story_bible.md`、`character_matrix.md` 仅作指针，分别指向 `outline/story_frame.md` 与 `roles/` 下角色卡。

#### 架构大纲 `story/outline/`（Phase 5 新布局）

- `story_frame.md` — 故事框架，世界观/设定权威源。
- `volume_map.md` — 卷/分卷地图，含节奏原则段。
- `节奏原则.md` — 可选，仅当架构师单独产出时写。

#### 角色卡 `story/roles/`（Phase 5 新布局）

- `主要角色/<角色名>.md`、`次要角色/<角色名>.md` — 一人一卡。`rules-reader` 优先读新布局并回退旧文件。

#### 运行时 `story/runtime/`

- `narrative-forecasts/` — 剧情推演（forecast 命令）产物目录，建书即建空目录。

#### 结构化状态 `story/state/`（首次 bootstrap 时生成，懒）

- `manifest.json` — 状态清单，含 `schemaVersion=2`、`lastAppliedChapter` 等。
- `current_state.json`、`hooks.json`、`chapter_summaries.json` — 结构化状态片段，供 reducer 应用 delta。

#### 时序记忆 `story/memory.db`（首次访问时建，懒）

- Node 22+ 内置 `node:sqlite` 时序记忆库，用于跨章节检索。

### 4. 关键机制

1. **两套布局并存**：旧布局（Phase 4）把 `story_bible.md`/`volume_outline.md`/`character_matrix.md` 平铺在 `story/`；新布局（Phase 5）拆到 `outline/` + `roles/`，`story/` 只留兼容指针文。`rules-reader` 优先读新布局、回退旧文件。建书时按架构师输出决定走哪套。
2. **懒创建**：建书阶段先建 `story/` 文档与目录骨架；`chapters/`（首章落盘）、`state/*.json`（首次结构化引导）、`memory.db`（首次记忆访问）在后续运行中按需生成。
3. **控制文档幂等**：`ensureControlDocuments` 使用 `writeIfMissing`，只在文件缺失时写，不会覆盖你手动改过的 `author_intent.md` / `current_focus.md` / `style_guide.md`。

### 5. 项目级 `.inkos/`（非单书，运行 inkos 时建）

与单书无关，是项目级运行时目录：

- `secrets.json` — LLM 密钥
- `sessions/` — 会话记录
- `materials/` — 归档资料卡
- `research/` — 研究报告
- `uploads/` — 上传文件

### 6. 数据来源（核实路径）

- 建书入口：`packages/core/src/interaction/project-tools.ts`
- 流水线初始化：`packages/core/src/pipeline/` 的 `initBook`
- 架构文件：`packages/core/src/agents/architect.ts`（`writeFoundationFiles`）
- 控制文档：`packages/core/src/state/manager.ts`（`ensureControlDocumentsAt`，`writeIfMissing` 幂等）
- 状态引导：`packages/core/src/state/state-bootstrap.ts`
- 记忆库：`packages/core/src/state/memory-db.ts`（`node:sqlite`）


### 7. Steward 设计包目录（非 InkOS 原生）

`inkos-story-steward` Skill 在项目根管理一个独立的创意设计区域：

```
<project-root>/story-design/<design-id>/
├── manifest.yaml          # 设计包元数据与 bookId 绑定
├── design/                # 作者可读设计源构件（00-10）
└── compile/inkos/         # InkOS 机器编译包（--brief 输入）
```

**此目录不属于 InkOS book tree。** InkOS 不读取、不管理、不覆盖 `story-design/`。

- 建书前：Steward 在此区域完成创意研发和编译，不写 `books/`。
- 建书时：`inkos book create --brief story-design/<id>/compile/inkos/book-brief.md`。InkOS 在 `books/.tmp-book-create-*` 构建 staging 目录，原子重命名为 `books/<book-id>`。
- 建书后：Steward 通过 `manifest.yaml` 中的 `book_id` 绑定定位设计包，进入正式书目录维护。

`books/.tmp-book-create-* → books/<book-id>` 的 EPERM 是 InkOS staging 提交阶段或 Windows 文件占用问题，不是 `--brief` 路径问题。