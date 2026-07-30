---
created: 2026-07-30T15:19
updated: 2026-07-30T15:21
---

## InkOS CLI 指令用法参考

> 整理自 `packages/cli/src/program.ts` 与 `packages/cli/src/commands/*.ts`（v1.7.2）。
> 约定：`[book-id]` 可省略——当项目里只有一本书时系统自动识别；`<…>` 为必填，`[…]` 为可选。

### 0. 全局说明

- **运行入口**：`inkos <verb> [args] [options]`。全局二进制名 `inkos`（`packages/cli` 的 `bin`）。
- **无动词行为**：单独运行 `inkos`（不带任何动词）会启动 **InkOS Studio**（Web 工作台，默认端口 `4567`）。
- **全局选项（每个命令都可用）**：`--service <svc>`、`--model <model>`、`--api-key-env <envVar>`、`--base-url <url>`、`--api-format <chat|responses>`、`--stream` / `--no-stream`。这些会临时覆盖 LLM 配置。
- **自然语言不是动词**：`inkos hello` 这类自由文本会被视为未知命令并报错；要用自然语言请走 `inkos agent "<text>"` 或 `inkos interact "<text>"`。
- **前置依赖**：
  - 全局类（不需已有书）：`init`、`config *`、`doctor`、`update`、`studio`、`tui`、`translate *`、`short *`、`genre *`、`radar`、`up`/`down`。
  - 需先 `init` 或 `book create` 建书：`write`、`auto`、`draft`、`plan`、`compose`、`agent`、`forecast`、`review`、`audit`、`revise`、`detect`、`eval`、`status`、`analytics`、`consolidate`、`chapter`、`export`、`style import`、`fanfic *`、`book *`、`import *`。
  - 需 LLM 配置（`INKOS_LLM_*` 或 `config set-global`）：上述"需建书"里真正调用模型的部分（write/auto/draft/audit/revise/detect/plan/compose/import/agent/interact/radar/forecast/fanfic/style import/translate/short/consolidate）；纯状态操作（review/chapter/book/status/eval/export/analytics/config）只读取 `inkos.json`，不调用模型。

---

### A. 项目初始化与建书

| 命令                                       | 用途                           | 关键选项                                                                                                                                                                |
| ------------------------------------------ | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `inkos init [name]`                        | 初始化项目（当前目录或子目录） | `--lang <zh\|en>`（默认 `zh`）                                                                                                                                          |
| `inkos book create`                        | 创建书并生成 AI 世界观基底     | `--title`（必填）、`--genre`（默认 xuanhuan）、`--platform`（默认 tomato）、`--target-chapters`（200）、`--chapter-words`（3000）、`--brief <path>`、`--lang`、`--json` |
| `inkos book update [book-id]`              | 更新书籍设置                   | `--chapter-words`、`--target-chapters`、`--status <outlining\|active\|paused\|completed>`、`--lang`、`--json`                                                           |
| `inkos book list`                          | 列出全部书                     | `--json`                                                                                                                                                                |
| `inkos book delete <book-id>`              | 删除书                         | `--force`、`--json`                                                                                                                                                     |
| `inkos book backup <book-id>`              | 快照到 `.inkos/backups/`       | `--list`、`--json`                                                                                                                                                      |
| `inkos book restore <book-id> <backup-id>` | 从快照恢复                     | `--json`                                                                                                                                                                |

---

### B. 写作流水线（需建书 + LLM）

| 命令                                                        | 用途                                 | 关键选项                                                                                              |
| ----------------------------------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| `inkos write next [book-id]`                                | 写下一章（规划→撰写→审计→修订→定稿） | `--count`(1)、`--words`、`--context`、`--context-file`、`--json`、`-q/--quiet`、`--notify`            |
| `inkos write rewrite [book-id] <chapter>`                   | 重写指定章节                         | `--force`、`--words`、`--brief`、`--json`、`--notify`                                                 |
| `inkos write sync [book-id] <chapter>`                      | 根据已编辑正文重建 truth/SQLite      | `--brief`、`--json`                                                                                   |
| `inkos write repair-state [book-id] <chapter>`              | 重建 truth 不重写正文                | `--json`                                                                                              |
| `inkos auto [book-id] <target-chapter>`                     | 无人值守批量写到目标章               | `--words`、`--json`、`-q`、`--notify`                                                                 |
| `inkos draft [book-id]`                                     | 仅写草稿（跳过审计/修订）            | `--words`、`--context`、`--context-file`、`--json`、`-q`                                              |
| `inkos plan chapter [book-id]`                              | 生成章节意图                         | `--context`、`--context-file`、`--json`、`-q`                                                         |
| `inkos compose chapter [book-id]`                           | 生成运行期产物                       | 同上                                                                                                  |
| `inkos agent <instruction>`                                 | 自然语言 Agent 模式                  | `--book <id>`、`--session <id>`、`--context`、`--context-file`、`--json`、`--quiet`                   |
| `inkos forecast create [book-id]`                           | 分支剧情推演                         | `--divergence <text>`（必填）、`--branches`(3)、`--horizon`(5)、`--model`、`--llm-base-url`、`--json` |
| `inkos forecast show [book-id] <forecast-id>`               | 查看推演                             | `--json`                                                                                              |
| `inkos forecast select [book-id] <forecast-id> <branch-id>` | 选用某分支                           | `--json`                                                                                              |

---

### C. 审阅与质量（需建书）

| 命令                                        | 用途                                | 关键选项                                                                                                      |
| ------------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `inkos review list [book-id]`               | 列出审阅状态                        | `--json`                                                                                                      |
| `inkos review approve [book-id] <chapter>`  | 通过章节                            | `--json`                                                                                                      |
| `inkos review approve-all [book-id]`        | 全部通过                            | `--json`                                                                                                      |
| `inkos review reject [book-id] <chapter>`   | 驳回章节                            | `--reason`、`--keep-subsequent`、`--json`                                                                     |
| `inkos audit [book-id] [chapter]`           | 连续性审计（缺省最新章）            | `--json`、`--notify`                                                                                          |
| `inkos revise [book-id] [chapter]`          | 按审计问题修订                      | `--mode <spot-fix\|polish\|rewrite\|rework\|anti-detect>`（默认 `spot-fix`）、`--brief`、`--json`、`--notify` |
| `inkos detect [book-id] [chapter]`          | AIGC 检测（需 `detection.enabled`） | `--all`、`--stats`、`--json`                                                                                  |
| `inkos eval [book-id]`                      | 质量报告                            | `--json`、`--chapters <range>`                                                                                |
| `inkos status [book-id]`                    | 项目/书状态                         | `--chapters`、`--json`                                                                                        |
| `inkos analytics [book-id]`（别名 `stats`） | Token/统计                          | `--json`                                                                                                      |
| `inkos consolidate [book-id]`               | 卷级总结整合                        | `--json`                                                                                                      |
| `inkos chapter sync [book-id]`              | 同步章节数据                        | `--json`                                                                                                      |
| `inkos chapter delete <book-id>`            | 删除章节                            | `--chapter <n>`、`--force`、`--json`                                                                          |

---

### D. 短篇 / 同人（全局，需 LLM）

| 命令                             | 用途       | 关键选项                                                                                                                                                                                                                                                                                  |
| -------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `inkos short run`                | 短篇生成链 | `--direction <text>`（必填）、`--reference`、`--story-id`、`--out-dir`(shorts)、`--lang`(zh)、`--chapters`(12-18)、`--chars`、各阶段模型覆盖（`--planner-model` 等）、封面选项（`--cover-base-url/--cover-endpoint/--cover-model/--cover-size/--cover-api-key-env/--no-cover`）、`--json` |
| `inkos fanfic init`              | 创建同人书 | `--title`、`--from <path>`（必填）、`--mode <canon\|au\|ooc\|cp>`(canon)、`--genre`、`--platform`、`--target-chapters`(100)、`--chapter-words`(3000)、`--lang`、`--json`                                                                                                                  |
| `inkos fanfic show [book-id]`    | 查看同人书 | `--json`                                                                                                                                                                                                                                                                                  |
| `inkos fanfic refresh [book-id]` | 刷新同人书 | `--from`（必填）、`--json`                                                                                                                                                                                                                                                                |

---

### E. 互动 / Play / TUI

| 命令                               | 用途                                | 关键选项                                                      |
| ---------------------------------- | ----------------------------------- | ------------------------------------------------------------- |
| `inkos interact [message…]`        | 对项目发自然语言指令                | `--message <text>`、`--book <id>`、`--session <id>`、`--json` |
| `inkos tui`                        | 打开项目 TUI（终端界面）            | —                                                             |
| `inkos studio [-p, --port <port>]` | 启动 Studio Web 工作台（默认 4567） | `-p/--port`（默认 `4567`）                                    |

---

### F. 状态导出与翻译

| 命令                                  | 用途           | 关键选项                                                                               |
| ------------------------------------- | -------------- | -------------------------------------------------------------------------------------- |
| `inkos export [book-id]`              | 导出章节       | `--format <txt\|md\|epub>`(txt)、`--output <path>`、`--approved-only`、`--json`        |
| `inkos translate init`                | 初始化翻译任务 | `--from`、`--source`、`--target`（均必填）、`--title`、`--segment-max-chars`、`--json` |
| `inkos translate run <project-id>`    | 执行翻译       | `--batch-size`、`--max-tokens`、`--json`                                               |
| `inkos translate export <project-id>` | 导出翻译       | `--format`(md)、`--output`、`--json`                                                   |
| `inkos style analyze <file>`          | 分析文风       | `--name`、`--json`                                                                     |
| `inkos style import <file> [book-id]` | 导入文风       | `--name`、`--stats-only`、`--json`                                                     |

---

### G. 市场情报

| 命令               | 用途                             | 关键选项 |
| ------------------ | -------------------------------- | -------- |
| `inkos radar scan` | 市场扫描，存 `radar/scan-*.json` | `--json` |

---

### H. 守护进程

| 命令         | 用途             | 关键选项 |
| ------------ | ---------------- | -------- |
| `inkos up`   | 启动自主守护进程 | `-q`     |
| `inkos down` | 停止守护进程     | —        |

---

### I. 配置与诊断（全局）

| 命令                                                           | 用途                                 | 关键选项                                                                                                                                            |
| -------------------------------------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `inkos config set <key> <value>`                               | 设置项目级配置项                     | —                                                                                                                                                   |
| `inkos config set-global`                                      | 设置全局 LLM（写入 `~/.inkos/.env`） | `--provider`、`--base-url`、`--api-key`、`--model`（必填）；`--temperature`、`--max-tokens`、`--thinking-budget`、`--api-format`、`--lang`          |
| `inkos config show-global`                                     | 查看全局配置                         | —                                                                                                                                                   |
| `inkos config show`                                            | 查看当前项目配置                     | —                                                                                                                                                   |
| `inkos config set-model <agent> <model>`                       | 给某 Agent 单独设模型                | agents：`writer`/`auditor`/`reviser`/`architect`/`radar`/`chapter-analyzer`；`--base-url`、`--provider`、`--api-key-env`、`--stream`、`--no-stream` |
| `inkos config remove-model <agent>`                            | 移除某 Agent 的专属模型              | —                                                                                                                                                   |
| `inkos config show-models`                                     | 查看模型路由                         | `--json`                                                                                                                                            |
| `inkos config list-models <service>`                           | 列出某服务可用模型                   | `--api-key`、`--base-url`、`--json`                                                                                                                 |
| `inkos genre list` / `show <id>` / `create <id>` / `copy <id>` | 题材库管理                           | `create` 选项：`--name`、`--numerical`、`--power`、`--era`、`--lang`                                                                                |
| `inkos import canon [target-book-id]`                          | 导入父 canonical 书                  | `--from <parent-book-id>`（必填）、`--json`                                                                                                         |
| `inkos import chapters [book-id]`                              | 导入已有章节续写                     | `--from <path>`（必填）、`--split <regex>`、`--resume-from <n>`、`--series`、`--json`                                                               |
| `inkos doctor`                                                 | 环境/项目健康与 API 连通性检查       | `--repair-node-runtime`                                                                                                                             |
| `inkos update`                                                 | 通过 npm 更新 InkOS                  | —                                                                                                                                                   |

---

### 常用示例

```bash
# 1. 初始化并打开 Studio
inkos init my-novel
cd my-novel
inkos                      # 启动 Studio（端口 4567）

# 2. 命令行写下一章
inkos write next

# 3. 用 Token Plan（custom provider）临时覆盖写一章
inkos write next --provider custom \
  --base-url https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1 \
  --api-key sk-sp-xxxx --model qwen3.6-plus

# 4. 先规划、再审校、再修订
inkos plan chapter
inkos audit
inkos revise --mode anti-detect

# 5. 导出 epub
inkos export --format epub --approved-only --output book.epub

# 6. 守护进程（无人值守连续写）
inkos up -q
# ... 一段时间后
inkos down

# 7. 配置与自检
inkos config set-global --provider custom \
  --base-url https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1 \
  --api-key sk-sp-xxxx --model qwen3.6-plus
inkos doctor
```

### 备注

- 全局选项（`--provider/--model/--api-key-env/--base-url/--api-format/--stream`）可临时覆盖配置，等价于对每个命令做一次性 LLM 路由切换，不写入配置文件。
- `config set-global` 写入 `~/.inkos/.env`；项目根 `.env`（若由 `init` 创建）亦可被 dotenv 加载——二者二选一，避免来源混淆。
- 真实命令细节以 `packages/cli/src/commands/` 下源码为准；本表为命令骨架与用途概览。
