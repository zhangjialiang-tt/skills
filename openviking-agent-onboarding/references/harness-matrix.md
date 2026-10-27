# 宿主接入矩阵（本机实测，2026-09）

> 标注约定：**[实测]** = 本机配置/服务端可验证；**[推断]** = 依据结构合理推断，未验证；
> **[待确认]** = 已知有该能力但注册点未定位，以 `ov-agent-probe.mjs` 输出为准。
>
> ⚠️ 本表是**起点不是答案**。给出某个宿主的具体路径前，先用探测脚本确认该路径在当前机器上真实存在。

## A. 官方支持清单（install.sh 校验通过）

| harness | 宿主 | hook 注册位置 | MCP 注册位置 | 会话前缀 |
|---|---|---|---|---|
| `claude` | Claude Code | `~/.claude/settings.json` → `hooks` | `~/.claude.json` / plugin `.mcp.json` | `cc-` |
| `codex` | Codex CLI / App | `~/.codex/config.toml` → `[plugins."openviking-memory@openviking"]` + `[features] plugin_hooks=true` | `~/.codex/config.toml` → `[mcp_servers.*]` 或插件 `.mcp.json` | `cx-` |
| `cursor` | Cursor | `~/.cursor/hooks.json` | `~/.cursor/mcp.json` | — |
| `trae` | TRAE | `~/.trae/hooks.json` | `~/.trae/mcp.json`（macOS 在 `~/Library/Application Support/Trae/User/mcp.json`） | — |
| `trae-cn` | TRAE CN | `~/.trae-cn/hooks.json` | `~/.trae-cn/mcp.json`（macOS 同理） | — |
| `trae-cli` | TraeCode CLI 2.0 | 归一化为 `codex`（旧文件 `~/.trae/cli/hooks.json`、`~/.trae/traecli.toml`） | 同 codex | — |
| `zcode` | ZCode | `~/.zcode/cli/config.json` → `hooks.events`（**用户级 hook 源唯一**，易被 provider 工具抹掉；注意同目录树的 `~/.zcode/v2/config.json` 是同一工具的**另一个改写目标**，两份都要核）；workspace 级可放 `<项目>/zcode.json` 或 `<项目>/.zcode/config.json`（向上找、以 `.git` 为界） | 同文件 `mcp.servers` → stdio 指向 `servers/mcp-proxy.mjs` | `zc-` |
| `opencode` | OpenCode | 宿主 SDK 插件（非配置式） | `opencode.json` → `plugin` 数组（npm 包） | `oc-` |
| `pi` | pi coding agent | 扩展目录自动发现：`~/.pi/agent/extensions/openviking/` | 扩展内置（同一目录） | `pi-` |
| `dsh` | DeepSeek Harness | `dsh plugin --profile <profile> add @openviking/dsh-memory-plugin` | 同上（npm 包） | — |

**install.sh 关键环境变量**（改路径/镜像时用）：

| 变量 | 默认 |
|---|---|
| `OPENVIKING_HOME` / `OV_HOME` | `~/.openviking` |
| `OPENVIKING_REPO_URL` | `https://github.com/volcengine/OpenViking.git` |
| `OPENVIKING_REPO_REF` | `main` |
| `OPENVIKING_TOS_BASE` | `https://ovrelease.tos-cn-beijing.volces.com` |
| `CODEX_CONFIG_FILE` | `~/.codex/config.toml` |
| `TRAE_HOME` / `TRAECLI_HOME` | `~/.trae` / `~/.trae/cli` |
| `OPENVIKING_DSH_PROFILE` | `web` |

## B. 官方未覆盖 · 本机已自建

| 宿主 | 现有形态 | 注册点 | 会话前缀 | 分层状态 |
|---|---|---|---|---|
| **Qoder CN** | 装配 `agent-integrations/qoder/`（**Claude Code 插件派生包**） | `~/.qoder-cn/settings.json` → `hooks` + `mcpServers` | **`qd-`**（2026-09-22 从借用的 `cc-` 分出，见 §D-1） | **两层都通** |
| **Antigravity** | `agent-integrations/antigravity/`（薄适配器 + `PreInvocation`/`Stop`） | MCP：`~/.gemini/settings.json`；hooks：`~/.gemini/config/hooks.json` | `ag-` | **两层都通** |
| **omp**（oh-my-pi 系） | `~/.omp/agent/extensions/openviking/`（**从 pi 扩展派生，但前缀已正确改为 `omp-`**） | 扩展目录自动发现 | `omp-` | **两层都通** |

> **omp 是「派生包正确换前缀」的正面样板**：`sync.ts` 里变量名仍叫 `piSessionId`，
> 但派生语句已写成 `deriveHarnessSessionId("omp-", piSessionId)`，harness 报 `omp`、
> UA 报 `openviking-memory-omp/<版本>` —— 派生自 pi 却没有与 pi 混库。
> 对照 Qoder 从 Claude Code 派生时忘改前缀（借用了 `cc-`，见 §D-1）。
| **MiMo Code**（小米） | **仅 MCP** | `~/.config/mimocode/mimocode.jsonc` → `mcp` | 无 | ⚠️ **mcp-only** |
| **WorkBuddy** | 自建 hook 适配层 + 启动器 | `~/.workbuddy/settings.json` → `hooks` → `hooks/ov/run-ov-hook.sh` | `wb-` | **两层都通**（命令里不含 openviking 字样，需追溯脚本才能认出） |

### 本机实测快照（2026-09-22，服务端 v0.4.17）

| 宿主 | 客户端探测 | 服务端会话 | 最近活动 | 判读 |
|---|---|---|---|---|
| pi | integrated | 87（**本机 24** + 他机 63） | 当日 | 活跃。⚠️ 这个 `87` 是**未做主机分离**的原始数，曾被误读为"本机成绩"；分离后本机 24 条全部正常。会话目录 `~/.pi/agent/sessions` |
| codex | integrated | 63 | 当日 | 活跃 |
| omp | integrated | 24（**本机 16** + 他机 8） | 7 天前 | ✅ 2026-09-22 验证通过。扩展落地（08-29）**前** 156 条会话 0 上传（正常，当时未接入）；落地**后** 20 条上传 16 条 = **80%**。未上传 4 条：2 条超短（4KB/8KB，阈值未触发）、1 条安装期（落地后 4 分钟）、1 条被 `session_exit reason=sighup` 中断。`pending/` 为空 → **无上传失败积压** |
| zcode | integrated（**已恢复 + 破坏源彻底清除**） | 14 | 5 天前 | 2026-09-20 10:43 注册被 provider 工具（EasyCLIProxyAPI / `cpa-gui`）抹掉 → 09-22 从工具自带的自动备份**完整还原 `v2`/`cli` 两份配置**（补回 8 个 provider + `plugins` + 自有 provider）；同日弃用该工具，**彻底清除**其 `cpa-gui` provider（两份 config + `v2/provider_config.json` 的 1 条 providerRule / 9 条 modelRule）、状态文件与开机自启项。**待重启 ZCode 验证落库** |
| claude | integrated | **0** | — | ⚠️ 插件 0.6.0 已注册但本机 3 个会话均未上传，待查。`cc-` 现为 claude-code **独占**（Qoder 已迁出） |
| antigravity | **integrated** | 6 | 当日 | ✅ 2026-09-24 补齐 hooks 注册（`~/.gemini/config/hooks.json`），`ag-` 前缀恢复落库 |
| workbuddy | integrated | 4 | 当日 | 活跃 |
| opencode | integrated | 2 | 近一月前 | 配置在，近期未用 |
| mimocode | **mcp-only** | 0 | — | ⚠️ 需补 hooks |
| qoder | integrated | **6**（`qd-`） | 当日 | ✅ 2026-09-21 15:40 接入；接入后 4/4 会话 100% 上传。2026-09-22 前缀由 `cc-` 改为 `qd-` 并迁移 6 条历史 → 与 claude 彻底分离 |

**这张表说明什么**：客户端探测"通过"不代表链路还在跑。**zcode 的例子最典型** ——
集成包完好、配置目录在，但宿主配置被覆盖后注册消失，只有把服务端的最近活动时间
和 `~/.openviking/logs/*-hooks.log` 的 mtime 一起看才能发现。

**Antigravity 的两个配置面（容易混淆）**：

| 用途 | 路径 | 格式 |
|---|---|---|
| MCP servers | `~/.gemini/settings.json` | `mcpServers` ← **实测只有这里有 OV** |
| lifecycle hooks | `~/.gemini/config/hooks.json` | 按 group 名分组，事件含 `PreInvocation` / `PostInvocation` / `Stop` / `PostToolUse` |

注意 `~/.gemini/config/` 下还有 `mcp_config.json`、`config.json` —— 实测这两个**不含** openviking。
**别只看文件名猜**，且 `~/.gemini/settings.json` 是 JSONC（含注释与尾逗号），
用 `JSON.parse` 会抛错，判定时按文本正则匹配更稳。

## C. 宿主事件与输出格式差异（决定适配层怎么写）

| 宿主 | 事件集 | payload 特点 | 输出注入字段 |
|---|---|---|---|
| Claude Code | `SessionStart` `UserPromptSubmit` `PreToolUse` `PostToolUse` `PreCompact` `Stop` `SessionEnd` `SubagentStart/Stop` | 标准 | `hookSpecificOutput.additionalContext` |
| Codex | 同 Claude 系（无 Subagent 两事件） | `Stop` 为**轮次结束非会话结束** | 同上 |
| ZCode | **仅 7 个**：`SessionStart` `UserPromptSubmit` `PreToolUse` `PermissionRequest` `PostToolUse` `PostToolUseFailure` `Stop` | stdin **无 user 内容**，须读 rollout `~/.zcode/cli/rollout/model-io-<sid>.jsonl`；`Stop` 暴露 `responseText`/`responsePreview` | 严格 JSON schema，**多一个键整份输出被丢弃**；只用 `hookSpecificOutput` |
| Qoder CN | 同 Claude 系 5 事件 [实测] | 配置用 `command` + `args[]` 数组形态（非 shell 字符串） | 同 Claude |
| Antigravity | `PreInvocation` `PostInvocation` `Stop` `PostToolUse` | 适配层用 env `OPENVIKING_HOOK_EVENT` 分发 | 见 `agent-integrations/antigravity/scripts/` |
| WorkBuddy | `SessionStart` `UserPromptSubmit` `Stop` `PreCompact` `SessionEnd` | `Stop` 带 `last_assistant_message`；`UserPromptSubmit` 带 `prompt` | `SessionStart`/`UserPromptSubmit` 的 stdout 注入上下文 |

**两条衍生结论**：

1. **不支持的宿主事件宁可少注册** —— ZCode 注册 `PreCompact`/`SessionEnd` 会被静默丢弃，
   提交责任必须落到 `Stop`。
2. **先确认 payload 有什么，再决定要不要解析 transcript** —— ZCode 必须读 rollout；
   WorkBuddy/Claude/Codex 的 payload 自带正文，纯 payload + 跨事件状态就够。

## D. 会话前缀命名约定

适配层自选前缀，用于在服务端区分来源。
已用：`cc-` claude-code · `cx-` codex · `pi-` pi · `omp-` omp · `zc-` zcode · `oc-` opencode ·
`ag-` antigravity · `wb-` WorkBuddy · `qd-` Qoder CN。
新增宿主时挑一个未占用的两字母前缀，并记回本表。

### D-0. 宿主会话位置（UUID 归属反查用）

判断某条云端会话是否来自**本机**，唯一可靠办法是拿它的 UUID 去该宿主的本地会话库里查
（服务端不记主机标识）。已实测可用的目录：

| 宿主 | 本机会话目录 | 文件命名 | 备注 |
|---|---|---|---|
| pi | `~/.pi/agent/sessions` | `<ISO>_<uuid>.jsonl` | |
| omp | `~/.omp/agent/sessions` | `<ISO>_<uuid>.jsonl` | 另有 `<proj>/<uuid>/<name>.jsonl` **子文件**层，同一 uuid 多次出现 → **必须按 uuid 去重**（实测 341 个 jsonl = 176 主文件 + 165 子文件） |
| claude-code | `~/.claude/projects` | `<uuid>.jsonl` | |
| qoder | `~/.qoder-cn/projects` | `<uuid>.jsonl` | |

```bash
node <SKILL>/scripts/ov-session-audit.mjs --agent omp --local-sessions ~/.omp/agent/sessions
```

⚠️ **Windows 下传路径要当心**：Git Bash 会把 `~/.omp/...` 展开成 `/c/Users/...`，
Node 不认这种盘符写法，早期脚本会静默吞掉 `readdirSync` 的错误并报
「没找到任何带 UUID 的会话文件」—— **把路径格式问题误报成目录填错**（实测踩过）。
脚本现已内置归一化（`/c/...` → `C:/...`，并兜住引号包裹导致 shell 未展开的字面量 `~/`），
命中时输出会标注「路径已自动归一化」；目录真的不存在与目录里没有 UUID 文件也会分开报。

### D-1. 派生包必须换掉前缀（否则与原宿主混库）

从官方插件包**派生**出的自建集成（B 路径），默认会继承原宿主的 `harness` 与会话前缀，
于是它写进服务端后与原宿主**完全混在一起**，而服务端没有任何字段能区分来源。

派生时必须改**两处**：

| 位置 | 改什么 | 只改这个会怎样 |
|---|---|---|
| `scripts/lib/ov-session.mjs` | `deriveHarnessSessionId("<prefix>-", …)` 的前缀 | —— |
| `scripts/config.mjs` | `harness: "<host>"`、`buildUserAgent("<host>", …)` | 只影响日志名 / 服务端统计标识，**不影响归属**，但留着会误导排障 |

**前缀是单点可改的**（实测 Qoder 2026-09-22）：全部 hook 都经由 `deriveOvSessionId()`
这一个函数派生会话 id，且整个包**没有任何反向解析前缀的代码**
（无 `startsWith("cc-")`、无 `replace(/^cc-/)`）→ 改一个字符串字面量即可，不存在解析错位。

改前缀前先核实**没有任何连带耦合**，四项都要查：

| 疑点 | 怎么查 | Qoder 实测结论 |
|---|---|---|
| `harness` 是否参与配置分节 | 看 `loadPluginSettings()` 的实参 | 实参是 `HARNESS_KEYS.claudeCode` = `claude_code`（**下划线**），与 `harness` 标签（连字符）是两条线 → 无关 |
| `harness` 是否参与 peer 身份 | 看默认 `peer.source` 模板含不含 `{harness}` | 默认 `git` → `{git_remote}`/`{git_root}`，不含 → 无关 |
| 本地队列 / 状态有无旧前缀残留 | `grep -r "<prefix>-" ~/.openviking/pending ~/.openviking/hook-state` | 无 |
| 已落库会话归属 | UUID 到各宿主本地会话目录反查 | 6 条全属 Qoder → 可安全迁移 |

**历史会话要一并迁移**，否则旧前缀下仍留着你的数据、审计照样分不清：

```bash
node <SKILL>/scripts/ov-session-reprefix.mjs --from cc- --to qd-            # 预演（只读）
node <SKILL>/scripts/ov-session-reprefix.mjs --from cc- --to qd- --apply    # 执行，写映射文件
node <SKILL>/scripts/ov-session-reprefix.mjs --undo <映射文件>               # 回滚
```

原理：服务端会话就是普通目录（`messages.jsonl` + `history/archive_*` + `tool-results/`），
`GET /api/v1/sessions` 的列表由目录扫描派生，且存在 `POST /api/v1/fs/mv`
→ **改目录名即改会话 id**，消息与归档原样保留（实测 76266B 字节数不变）。
脚本会逐条比对 `messages.jsonl` 字节数，不一致即告警。

迁移后确认**旧前缀已归零、新前缀等于迁移条数**：

```bash
node <SKILL>/scripts/ov-session-audit.mjs            # 例：cc- 应为 0 条，qd- 为 6 条
```

⚠️ 前缀一改，**同一个宿主会话就派生出不同的 OV 会话 id**（id = 前缀 + 宿主 session_id）。
所以历史不迁移的话，重新打开旧会话会命中一个空的 OV 会话、旧归档成为孤儿 —— 迁移要一次做完。

## E. 探测脚本会输出的判定

`ov-agent-probe.mjs` 对每个宿主给出四选一：

- `not-found` —— 宿主未安装或配置目录不在已知位置
- `not-integrated` —— 宿主在，无任何 openviking 痕迹
- `mcp-only` —— 有 MCP 注册，无 hooks → **半成品，建议补 hooks**
- `integrated` —— 两层都有痕迹
