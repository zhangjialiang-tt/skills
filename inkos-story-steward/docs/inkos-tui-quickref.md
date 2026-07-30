---
created: 2026-07-30T15:37
updated: 2026-07-30T17:34
---

## InkOS TUI 速查卡

> 启动：`inkos` 或 `inkos tui`（无子命令默认进 Studio，需 TUI 时用 `inkos tui`）
> 输入 `/` 即触发自动补全：↑/↓ 切换候选，Tab 填充。
> 命令来源：`packages/cli/src/tui/slash-autocomplete.ts`（补全全集）+ `local-commands.ts`（本地直处理）+ `effects.ts`/`i18n.ts`（文案）。

### 一、命令分类总览

| 类别        | 命令                                                                                             |
| ----------- | ------------------------------------------------------------------------------------------------ | --- | ------ |
| 写作        | `/new` `/write` `/rewrite <n>`                                                                   |
| 导航        | `/books` `/status`                                                                               |
| 控制 / 编辑 | `/focus <text>` `/truth <file> <content>` `/rename <from> => <to>` `/replace <n> <from> => <to>` |
| 导出        | `/export [txt                                                                                    | md  | epub]` |
| 会话 / 本地 | `/depth <light\|normal\|deep>` `/help` `/clear` `/config` `/quit` `/exit`                        |

### 二、完整命令表

| 命令                           | 参数       | 用途                                                            | 处理方 |                          |       |
| ------------------------------ | ---------- | --------------------------------------------------------------- | ------ | ------------------------ | ----- |
| `/new`                         | 你的想法   | 开始构思新书，描述题材/世界观/主角/冲突，AI 引导建书            | agent  |                          |       |
| `/write`                       | —          | 跑完整流水线写下一章（特殊意图，触发写作流水线）                | agent  |                          |       |
| `/rewrite <n>`                 | 章节号     | 从头重写第 N 章                                                 | agent  |                          |       |
| `/books`                       | —          | 让 agent 列出已有作品                                           | agent  |                          |       |
| `/focus <text>`                | 文本       | 更新当前写作焦点                                                | agent  |                          |       |
| `/truth <file> <content>`      | 文件 内容  | 注入/修正控制面真相（truth 数据）                               | agent  |                          |       |
| `/rename <from> => <to>`       | 旧名 新名  | 重命名角色（如 `/rename 林烬 => 张三`）                         | agent  |                          |       |
| `/replace <n> <from> => <to>`  | 章号 旧 新 | 在第 N 章替换某词                                               | agent  |                          |       |
| `/export [txt                  | md         | epub]`                                                          | 格式   | 导出成稿，缺省按配置格式 | agent |
| `/depth <light\|normal\|deep>` | 档位       | 切换思考深度；中文可用 `/深度 浅\|标准\|深`                     | 本地   |                          |       |
| `/status`                      | —          | 查看当前状态（阶段 + 模式）                                     | 本地   |                          |       |
| `/help`                        | —          | 显示帮助                                                        | 本地   |                          |       |
| `/clear`                       | —          | 清空当前屏幕                                                    | 本地   |                          |       |
| `/config`                      | —          | 提示：TUI 内不支持交互式 config，需用 `inkos config set-global` | 本地   |                          |       |
| `/quit`                        | —          | 退出 TUI                                                        | 本地   |                          |       |
| `/exit`                        | —          | 同 `/quit`（别名）                                              | 本地   |                          |       |

### 三、本地直处理 vs agent 路由

- **本地直处理**（TUI 内部即时执行，不消耗 LLM）：`/help`、`/status`、`/clear`、`/quit`、`/exit`、`/config`、`/depth`。
- **agent 路由**（作为意图交给统一 agent 会话）：`/new`、`/write`、`/rewrite`、`/books`、`/focus`、`/truth`、`/rename`、`/replace`、`/export`。

### 四、自然语言别名（无需记 `/` 前缀）

`local-commands.ts` 支持把口语当命令识别：

| 输入                                     | 等价于    |
| ---------------------------------------- | --------- |
| `帮助`                                   | `/help`   |
| `状态`                                   | `/status` |
| `清屏`                                   | `/clear`  |
| `退出` / `bye`                           | `/quit`   |
| `配置`                                   | `/config` |
| `深度 浅\|标准\|深`（或 轻量/普通/深入） | `/depth`  |

### 五、常见用法示例

```text
/new 一个赛博朋克侦探小说，主角是有义眼的退休刑警
/write                        # 写下一章
/rewrite 3                    # 重写第 3 章
/focus 这一章要埋下反派身份伏笔
/rename 林烬 => 张三          # 改角色名
/truth characters.json 林烬是双面间谍   # 修正设定真相
/export epub                  # 导出 epub
/depth deep                   # 切到深入思考
/status                       # 看当前进度
/clear                        # 清屏
/quit                         # 退出
```

### 六、易错点

- **`/pause` 不是注册斜杠命令**：只出现在帮助示例里，靠 agent 把"暂停"当自然语言意图理解，不在自动补全列表，输入 `/pause` 不会触发补全。
- **`/help` 文案比补全列表短**：帮助里只显式列出部分命令（未含 `/truth` `/rename` `/replace` `/export` `/clear` `/depth` `/quit`），但这些命令都能用——`slash-autocomplete.ts` 的补全全集才是权威。
- **`/config` 仅提示**：TUI 内不能交互改配置，会让你去 `inkos config set-global`。
- **未配 LLM 时**：多数 agent 路由命令无法执行，TUI 会提示"未发现 LLM 配置 / 先配置 API 提供方"。
