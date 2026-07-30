---
created: 2026-07-30T14:35
updated: 2026-07-30T14:36
---

## InkOS 使用指南（使用者视角）

> 面向"我想用它把故事写出来"的人。按"先准备 → 选入口 → 跑任务 → 排错"的顺序组织，不是按代码模块。
> 参考版本：InkOS 1.7.x（AGPL-3.0，pnpm monorepo）。

---

### 一、它是什么，能做什么

InkOS 是一个**故事创作 AI Agent 系统**，把创意、设定、角色、记忆、审稿、修订、封面、互动和翻译统一在一个工作台里管。

能做的创作类型：

| 类型                | 说明                                                              |
| ------------------- | ----------------------------------------------------------------- |
| 长篇小说            | 从简报建书，按"规划 → 写作 → 审计 → 修订 → 状态结算"逐章推进      |
| 短篇小说            | 一条指令产出完整短篇（正文 + 简介卖点 + 封面提示词 + 可选封面图） |
| 剧本 / 分镜         | Studio 内的剧本与分镜工作台                                       |
| 同人 / 番外         | 正典延续、架空、性格重塑、CP 向四种模式                           |
| 续写                | 导入已有章节，自动重建状态后继续写                                |
| 互动影游 / 开放世界 | 分支剧情、变量旗标、角色关系、多结局，系统维护世界状态            |
| 多语言翻译          | EPUB / PDF / TXT / Markdown 按章节翻译，维护术语表与对照审校报告  |

三种交互入口共享同一套执行内核：**Studio（Web）**、**CLI（命令行）**、**TUI（终端全屏）**，外加可被其他 Agent（如 OpenClaw）调用的 `inkos interact` 入口。

---

### 二、安装

#### 方式一：作为 CLI 工具（推荐普通使用者）

```bash
npm i -g @actalk/inkos
```

装好后直接有 `inkos` 命令。

#### 方式二：从源码开发 / 二次开发

```bash
git clone <repo> && cd inkos
pnpm install
pnpm build      # cli 会自动先 build core
```

#### 环境要求

- Node **>= 20**，推荐 **22+**（22+ 才会启用 SQLite 长期记忆库）
- pnpm **>= 9**

---

### 三、配置 LLM（动手写之前必须先做）

InkOS 不自带模型，需要接一个 OpenAI 兼容的 LLM 服务。两条互不污染的配置路径：

#### 方式一：Studio 可视化配置（推荐本地写作）

```bash
inkos init my-novel      # 在当前目录初始化项目
cd my-novel
inkos                   # 启动 Studio（默认端口 4567）
```

打开 Studio → 「模型配置」：

1. 选服务商（Google Gemini / Moonshot / MiniMax / 智谱 / 百炼 / OpenRouter / kkaiapi / 自定义端点等）
2. 粘贴 API Key，点「测试连接」
3. 选可用模型，保存

> 关键点：Studio 运行时**只**用 Studio 配置 + 项目内 `.inkos/secrets.json`，不会用环境变量覆盖服务/模型/Key。API Key 写在 `.inkos/secrets.json`，**不进** `inkos.json`。

#### 方式二：CLI / 守护进程 / 部署环境的 env 配置

适合批处理、服务器、CI、Docker。

全局写 env：

```bash
inkos config set-global \
  --provider <openai|anthropic|custom> \
  --base-url <API 地址> \
  --api-key <你的 API Key> \
  --model <模型名>
```

或手动写 `~/.inkos/.env` / 项目 `.env`：

```bash
INKOS_LLM_PROVIDER=custom
INKOS_LLM_BASE_URL=https://api.moonshot.cn/v1
INKOS_LLM_API_KEY=sk-...
INKOS_LLM_MODEL=kimi-k2.5
# 可选
INKOS_LLM_SERVICE=moonshot        # 推荐写，便于从 baseUrl 反推服务商
INKOS_LLM_TEMPERATURE=0.7
INKOS_DEFAULT_LANGUAGE=zh
```

CLI 合成顺序（后者覆盖前者）：

```
Studio/project 配置 → .inkos/secrets.json → 全局 ~/.inkos/.env → 项目 .env → 进程环境变量 → CLI 参数
```

#### 多模型路由（可选，平衡质量与成本）

给不同 Agent 配不同模型，例如写手用好模型、审计用便宜模型：

```bash
inkos config set-model writer <model> --provider <provider> --base-url <url> --api-key-env <ENV>
inkos config set-model auditor <model> --provider <provider>
inkos config show-models        # 查看当前路由
```

#### 诊断配置

```bash
inkos doctor
```

会显示当前生效配置模式（`studio-project` / `cli-project` / `legacy-env`）、Key 来源、API 连通性和服务商兼容提示。

---

### 四、选哪种入口

| 入口               | 适合谁                        | 怎么进                                      | 特点                                     |
| ------------------ | ----------------------------- | ------------------------------------------- | ---------------------------------------- |
| **Studio（Web）**  | 大多数使用者、本地写作        | `inkos` 或 `inkos studio`（默认 4567 端口） | 可视化、确认卡、生成物预览、多语言界面   |
| **CLI**            | 脚本、批处理、外部 Agent 调用 | 终端敲 `inkos …` 命令                       | 原子命令可组合，支持 `--json` 结构化输出 |
| **TUI**            | 键盘流终端用户                | `inkos tui`                                 | 终端全屏仪表盘                           |
| **OpenClaw Skill** | 其他 Agent 调用 InkOS         | `inkos interact --json --message "…"`       | 走与 TUI 相同的执行内核，结构化返回      |

> 建议：第一次用先从 **Studio** 走一遍建书 → 写作 → 导出，熟悉后再用 CLI 做批处理或自动化。

---

### 五、常见任务分步

#### A. 写第一本长篇（最常见路径）

```bash
inkos book create --title "吞天魔帝" --genre xuanhuan   # 建书（--genre 指定题材）
inkos write next 吞天魔帝        # 写下一章：草稿 → 审计 → 按配置自动修订
inkos status                     # 查看状态
inkos review list 吞天魔帝        # 审阅草稿
inkos review approve-all 吞天魔帝 # 批量通过
inkos export 吞天魔帝            # 导出全书
inkos export 吞天魔帝 --format epub   # 导出 EPUB（手机/Kindle 阅读）
```

> 项目只有一本书时，命令里的 `[id]` 可省略，自动检测。

#### B. 写完整短篇

对话里直接说：

```
写一篇 12 章短篇，方向是：都市婚姻反转，女主拿到账本证据后反杀。
```

或走 CLI：

```bash
inkos short run \
  --direction "都市短篇 婚姻反转 女主证据反杀" \
  --chapters 12 \
  --chars 1000
```

产物落在 `shorts/<故事名>/final/`：`full.md`、`sales-package.md`、`cover-prompt.md`，配置封面服务后还有 `cover.png`。

#### C. 单独做封面

对话里说「给《标题》生成一张短篇封面，偏 XX 风格」。产物：`covers/<标题>/cover-prompt.md` 和 `covers/<标题>/cover.png`。配置封面服务在 Studio「模型配置」里。生成后可继续改封面提示词，只重生成封面、不重跑正文。

#### D. 互动影游 / 开放世界

Studio Chat 选「开放世界」或「分支互动」，用自然语言描述世界：

```
做一个魔兽风格的边境哨塔开放世界。时间不是固定回合，巡逻是一小时，练功可以跨几天。装备有稀有度，但不要数值面板。
```

系统生成世界、角色、物品、证据、关系、场景和可选动作；配置图片服务后角色/物品/场景可自动配图。

#### E. 多语言翻译

```bash
inkos translate init     # 初始化翻译工程
inkos translate run       # 按章节/语义段翻译
inkos translate export    # 导出 TXT / Markdown / EPUB
```

支持 EPUB、文本型 PDF、TXT、Markdown 输入；维护术语表，生成对照审校报告。Studio / Chat 共用同一能力。

#### F. 导入旧稿续写

```bash
inkos import chapters 吞天魔帝 --from /path/to/old-novel.txt
```

自动重建结构化状态、章节摘要、伏笔、角色关系和可读 Markdown 投影。支持 `第X章` 与自定义分割、`--resume-from` 断点续导。导入后 `inkos write next` 继续创作。

#### G. 同人创作

```bash
inkos fanfic init --from source.txt --mode canon   # canon/au/ooc/cp
```

内置正典导入器、同人专属审计维度、信息边界管控，确保设定不矛盾。

#### H. 剧情多线推演（forecast）

写下一章前，基于当前正史生成 2–5 条彼此隔离的候选未来：

```bash
inkos forecast create     # 生成候选分支
inkos forecast show       # 横向比较章节节拍、人物决定、风险、作者意图匹配度
inkos forecast select     # 只保存候选计划，不修改正史
```

> 采用分支只保存 `selected-branch-plan.md` 候选计划，不会提前改正文/大纲/正史；正史变化后旧推演会标记过期。

#### I. 守护进程自动写章

```bash
inkos up      # 启动后台循环自动写章
inkos down    # 停止
```

管线自动推进可处理的问题；需人工判断的会暂停并留可审结果。通知支持 Telegram / 飞书 / 企业微信 / Webhook（HMAC-SHA256）。日志写 `inkos.log`（JSON Lines），`-q` 静默。

---

### 六、命令速查（按场景）

#### 初始化与项目

| 命令                     | 说明                                                                                  |
| ------------------------ | ------------------------------------------------------------------------------------- |
| `inkos init [name]`      | 初始化项目（省略 name 则在当前目录）                                                  |
| `inkos book create`      | 建书（`--genre`/`--platform`/`--chapter-words`/`--target-chapters`/`--brief <file>`） |
| `inkos book update [id]` | 改书设置                                                                              |
| `inkos book list`        | 列出所有书                                                                            |
| `inkos book delete <id>` | 删书及全部数据（`--force` 跳过确认）                                                  |

#### 长篇写作（规划 → 写作 → 审计 → 修订）

| 命令                           | 说明                                                                                       |
| ------------------------------ | ------------------------------------------------------------------------------------------ |
| `inkos plan chapter [id]`      | 生成下一章 `intent.md`（`--context` 传指令）                                               |
| `inkos compose chapter [id]`   | 生成 `context.json` / `rule-stack.yaml` / `trace.json`（**不需在线 LLM**，可先查输入治理） |
| `inkos write next [id]`        | 完整管线写下一章（`--words` 覆盖字数，`--count` 连写，`-q` 静默）                          |
| `inkos write rewrite [id] <n>` | 重写第 N 章（回滚状态快照，`--force` 跳过确认）                                            |
| `inkos draft [id]`             | 只写草稿                                                                                   |
| `inkos audit [id] [n]`         | 审计指定章节                                                                               |
| `inkos revise [id] [n]`        | 修订指定章节                                                                               |

#### 短篇 / 封面 / 风格

| 命令                             | 说明                             |
| -------------------------------- | -------------------------------- |
| `inkos short run`                | 生成独立短篇包                   |
| `inkos style analyze <file>`     | 分析参考文本提取文风指纹         |
| `inkos style import <file> [id]` | 导入文风指纹到指定书             |
| `inkos detect [id] [n]`          | AIGC 检测（`--all` / `--stats`） |

#### 互动 / 世界 / 推演

| 命令                                      | 说明                                  |
| ----------------------------------------- | ------------------------------------- |
| `inkos import canon [id] --from <parent>` | 导入正传正典到番外书                  |
| `inkos forecast create/show/select`       | 非正史分支生成 / 核验 / 选择          |
| `inkos play …`                            | 开放世界 / 分支互动（见 Studio 入口） |

#### 状态 / 审阅 / 导出 / 分析

| 命令                                                | 说明                                                          |
| --------------------------------------------------- | ------------------------------------------------------------- |
| `inkos status [id]`                                 | 项目状态                                                      |
| `inkos review list [id]` / `approve-all [id]`       | 审阅草稿 / 批量通过                                           |
| `inkos export [id]`                                 | 导出（`--format txt/md/epub`、`--approved-only`、`--output`） |
| `inkos consolidate [id]`                            | 归并长篇章节摘要，降上下文压力                                |
| `inkos eval [id]` / `analytics [id]` / `stats [id]` | 质量评估 / 数据分析                                           |
| `inkos radar scan`                                  | 扫描平台趋势                                                  |

#### 配置与诊断

| 命令                                     | 说明                            |
| ---------------------------------------- | ------------------------------- |
| `inkos config set-global …`              | 全局 LLM env（`~/.inkos/.env`） |
| `inkos config show-global`               | 查看全局配置                    |
| `inkos config set/show`                  | 项目配置查看 / 更新             |
| `inkos config set-model <agent> <model>` | Agent 模型覆盖                  |
| `inkos config remove-model <agent>`      | 移除覆盖（回退默认）            |
| `inkos config show-models`               | 查看模型路由                    |
| `inkos doctor`                           | 诊断配置与连通性                |
| `inkos update`                           | 更新到最新版本                  |

#### 入口与守护

| 命令                                  | 说明                             |
| ------------------------------------- | -------------------------------- |
| `inkos` / `inkos studio`              | 启动 Web 工作台（`-p` 指定端口） |
| `inkos tui`                           | 终端全屏 TUI                     |
| `inkos agent "<指令>"`                | 自然语言 Agent 模式              |
| `inkos interact --json --message "…"` | 外部 Agent 结构化入口            |
| `inkos up` / `inkos down`             | 守护进程启停                     |

> 所有命令支持 `--json` 输出结构化数据。一次性 LLM 覆盖参数：`--service`、`--model`、`--api-key-env`、`--base-url`、`--api-format <chat|responses>`、`--stream` / `--no-stream`。

---

### 七、关键概念（避免踩坑）

- **控制面两文档**：每本书有 `story/author_intent.md`（长期想成为什么）和 `story/current_focus.md`（近期 1–3 章关注点）。写前先调它们，比临时 prompt 更稳。
- **长期记忆三层**：`story/state/*.json`（权威结构化状态，Zod 校验）+ `story/*.md`（人类可读投影）+ `story/memory.db`（Node 22+ 的 SQLite 时序检索）。坏数据会被 Zod 拒绝，不会滚雪球。
- **去 AI 味与审计**：连续性审计员从 37 个维度查每章（角色记忆、物资连续、伏笔回收、节奏、情感弧线等），含 AI 痕迹检测。默认最多自动修订 1 次，可用 `inkos config set writing.reviewRetries 3` 调高。
- **字数治理**：`--words` 是目标字数，系统推导允许区间；中文按 `zh_chars`、英文按 `en_words`；超出 hard range 最多单 pass 归一化，不硬截断。
- **并发与写锁**：异常写锁可恢复，冲突写入返回 `BOOK_BUSY`，完成态只来自真实工具结果和落盘文件，不从模型口头声明推断。
- **输入治理模式**：`write next` 默认走 `v2`（plan→compose→write）；`inkos.json` 设 `inputGovernanceMode: "legacy"` 可回退旧 prompt 拼装路径。
- **原子命令可组合**：`plan`/`compose`/`draft`/`audit`/`revise` 各自独立，适合脚本和外部 Agent 通过 `exec` 调用。

---

### 八、排错速查

| 现象                          | 排查                                                                                            |
| ----------------------------- | ----------------------------------------------------------------------------------------------- |
| 服务测试失败                  | 先查服务商/模型/协议是否匹配；`inkos doctor` 看 effective config mode 与 Key 来源               |
| 模型错配报错                  | `--service google --model kimi-k2.5` 这类会被直接拒绝；`--model` 必须属于最终 service           |
| 写章卡住 / 并发冲突           | 看是否返回 `BOOK_BUSY`；异常写锁可恢复，无需手动删锁                                            |
| 升级失败 / `workspace:*` 泄漏 | 多为 npm 发布包问题，已修复；本地开发用 `pnpm build` 即可                                       |
| 本地记忆不生效                | 确认 Node >= 22（`node:sqlite` 才启用）；旧书首次运行会从 legacy Markdown 自动迁移到结构化 JSON |

---

### 九、快速上手最小步骤

```bash
npm i -g @actalk/inkos
inkos init my-novel && cd my-novel
inkos                       # 打开 Studio，在「模型配置」粘贴 Key 并测试
# 回到终端或 Studio 对话：
inkos book create --title "我的第一本书" --genre xuanhuan
inkos write next            # 写第一章
inkos export --format epub  # 导出
```

需要更细的某个模块（如 Studio 界面操作、Play 世界契约写法、forecast 推演比较、CLI 批量脚本）再单独深入。
