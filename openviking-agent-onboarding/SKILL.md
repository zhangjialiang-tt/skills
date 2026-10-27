---
name: openviking-agent-onboarding
description: 把任意 coding agent 接入 OpenViking 长期记忆。含官方一键安装器的 harness 清单、各宿主配置位置矩阵、自建适配器方法论（复用 memory-plugin-shared/agent-hook-runtime.mjs）、只读探测与落库审计脚本，以及"官方未覆盖 Agent"的接入记录模板。触发：给某 Agent 接 OpenViking / 加长期记忆、新装的 Agent 想接 OV、判断某 Agent 是否已接入 OV、Agent 之间记忆不互通、OV 能 search 但会话不落库、openviking-memory 插件安装。
agent_created: true
triggers:
  include:
    - "把 X 接入 OpenViking / 给 X 加长期记忆"
    - "新装的 Agent 想接 OpenViking（含官方未覆盖的）"
    - "判断某 Agent 是否已接入 OpenViking"
    - "某 Agent 的会话没进 OpenViking / 记忆不互通"
    - "OV 能 search 但新对话不落库"
    - "openviking-memory 插件 / install.sh --harness"
  exclude:
    - "OV 服务端运维、换模型、reindex、迁移（见 openviking-server-ops）"
    - "WorkBuddy hook 细节与深度排障 SOP（见 workbuddy-hook-ops）"
    - "OV 记忆内容的检索/写入用法（属 MCP 工具用法）"
---

# 给 Agent 接入 OpenViking

## 铁律：接入分两层，先分层再动手

| 层 | 载体 | 能力 | 判据 |
|---|---|---|---|
| **只读层（MCP）** | 宿主的 MCP 配置 | 模型能 `search` / `read` / `find` OV | MCP 握手通、工具进了索引 |
| **同步层（Hooks）** | 宿主的生命周期 hook 配置 | 会话被写入 OV，跨 Agent 记忆互通 | 服务端出现该 Agent 前缀的会话 |

**只做 MCP ≠ 接入。** 最常见的半成品：MCP 挂上了、hooks 没挂 —— 模型能查历史，新对话却永不入库。
向用户汇报时必须分层说，不要让"能 search"被理解成"已同步"。

## 第一步：先探测，再选路径（只读，零副作用）

```bash
node <SKILL>/scripts/ov-agent-probe.mjs <agent>      # 单查：客户端配置面 + 分层判定
node <SKILL>/scripts/ov-agent-probe.mjs --all        # 扫全部已知宿主
node <SKILL>/scripts/ov-agent-probe.mjs --scan ~/.foo  # 官方未收录的宿主：扫它的配置目录
node <SKILL>/scripts/ov-session-audit.mjs            # 服务端：各前缀落库量与最近活动
```

探测脚本输出：配置目录是否存在、MCP/hook 各自命中点（含追溯到的实际脚本）、
hook 日志的最近更新时间、官方是否支持、分层判定结论。

**判读要点**：

- 结论 `[MH]` = 两层都命中；`[M-]` = 只有只读层；`[--]` = 文件在但无 OV 痕迹
- 带 `← 经 <脚本>` = 配置本身不含 "openviking" 字样，是追溯它指向的脚本才认出来的
  （WorkBuddy 就是这种形态，光搜关键词会漏判）
- `⏸ 日志 N 天未更新` 或 `pkg 已就位但宿主配置里没注册` = **典型静默失效**：
  集成包完好、配置目录在，但注册被覆盖或从未生效

⚠️ 客户端探测是**基于文本的启发式**，只能说明"配置看起来对不对"。
**链路是否真的在跑，必须用服务端审计确认**（会话数 + 最近活动时间）。两者结论不一致时，以服务端为准。

**最危险的一种状态**：客户端显示 integrated、集成包也完好，但服务端该前缀最近活动是很久以前 —— 注册已被覆盖。

## 第二步：按探测结果选路径

| 现象 | 路径 |
|---|---|
| 宿主在官方 harness 清单内 | **A 官方一键安装** |
| 宿主兼容 Claude Code / Codex 插件格式 | **B 装配官方插件包** |
| 有 hook/extension 机制但官方未覆盖 | **C 自建适配器** |
| 只有 MCP，无生命周期事件 | **D MCP-only** |

### A. 官方一键安装（优先走这条）

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/volcengine/OpenViking/main/examples/memory-plugin-shared/install.sh) --harness <name>
```

官方 install.sh 校验清单（全部取值）：
`claude` `codex` `cursor` `trae` `trae-cn` `trae-cli` `zcode` `opencode` `pi` `dsh`

- `trae-cli` 正常安装时归一化为 `codex`（走 Codex 兼容插件格式），仅在 `--uninstall` 时独立存在
- GitHub 不可达时加 `--dist tos` 走 TOS 镜像
- 脚本做的事：写 `~/.openviking/ovcli.conf` → 注册 marketplace/插件 → 开 `features.plugin_hooks` → 校验 stdio MCP → 清理旧 wrapper
- **一键安装与 marketplace 安装不要混用** —— 两条路径暴露同一个插件，同时启用会让 hooks 跑两遍、记忆重复

### B. 装配官方插件包（宿主兼容 Claude/Codex 格式）

官方插件包已成型，宿主只要兼容格式就不必从零写：

- **Claude Code 格式**：`${CLAUDE_PLUGIN_ROOT}` 模板变量、`settings.json` 的 `hooks`、`mcpServers`
- **Codex 格式**：`.codex-plugin/plugin.json` + `hooks/hooks.json` + `.mcp.json`

做法：以 `~/.openviking/agent-integrations/<host>/` 为插件根，安装时把 hook 命令里的模板变量替换成绝对路径，MCP 指向 `servers/mcp-proxy.mjs`。

本机实例：Qoder CN（Claude 格式，注册在 `~/.qoder-cn/settings.json`）。

⚠️ **派生包必须把前缀改成自己的**（并改 `harness`，否则日志名与统计标识继续冒充原宿主），
否则与原宿主混进同一命名空间 —— 改法、四项连带耦合核查清单与历史会话迁移见
`references/harness-matrix.md` §D-1，工具 `scripts/ov-session-reprefix.mjs`。

### C. 自建适配器（官方未覆盖）

**权威依据是官方开发标准，不是推断**：
`docs/zh/agent-integrations/18-plugin-development.md`（仓库 `volcengine/OpenViking`）

核心原则：**复用共享运行时 `memory-plugin-shared/lib/agent-hook-runtime.mjs`，只写宿主差异。**
不要复制一份 client/recall/doctor 改名 —— 那是官方明确禁止的做法。

实现步骤、API 清单与陷阱见 `references/adapter-authoring.md`。

### D. MCP-only

```jsonc
// 远程 streamable HTTP
{ "url": "http://<ov-host>:1933/mcp", "headers": { "Authorization": "Bearer <key>" } }

// stdio 代理（推荐）
{ "command": "node", "args": ["<ov>/agent-integrations/<host>/servers/mcp-proxy.mjs"] }
```

⚠️ **优先用 stdio 代理**：它运行时读 `ovcli.conf` / `OPENVIKING_*`，凭据不落进 agent 配置。
把 API key 明文抄进 `config.toml` / `settings.json` / `*.jsonc` 是常见错误 —— 那些文件会被同步、备份、贴进 issue。

MCP-only 的用户预期要讲清：只有显式搜索，**没有自动 recall 注入、没有会话归档**。

## 第三步：核实宿主契约（不可跳过）

**绝不套用另一款 Agent 的行为。** 十项必查清单与可直接填写的接入记录模板见 `references/host-contract.md`。

最低限度必须确认：

1. 有哪些生命周期事件（启动 / 提交 / 轮次结束 / 压缩前 / 会话结束）
2. stdin payload 里有什么（session id / cwd / transcript / 消息正文）
3. 输出格式（注入用哪个字段；未知字段会不会让整份输出被丢弃）
4. 超时单位（秒 or 毫秒）与超时后是否杀整个进程组
5. 会话身份的可靠来源（payload 字段，还是 rollout/transcript 文件）

**没有"会话结束"事件的宿主，必须显式选择替代提交点**（如 ZCode 在 `Stop` 提交），
不能注册一个永不触发的 `SessionEnd` 假装完整。

## 第四步：验证四级，别停在第三级

| 级 | 做什么 | 判据 |
|---|---|---|
| 1 | 语法 / 离线自检 | `bash -n`、伪造 payload 跑通全部事件 |
| 2 | dry-run 端到端 | 独立 state 目录，不联网、不污染生产状态 |
| 3 | live 写入并读回 | 服务端 `message_count` 增长 |
| 4 | **注册后跑真实事件，回服务端确认落库** | 出现该 Agent 前缀的会话 |

⚠️ 已实际踩过：第 3 级通过就以为接好了，但注册的仍是探针，真实会话一条没上传，隔天才发现。
**测试通过 ≠ 生产启用**，只有第 4 级能证明链路在跑。

## 第五步：落库审计（只读，验证第 4 级）

```bash
node <SKILL>/scripts/ov-session-audit.mjs              # 全部前缀统计 + 最近活动
node <SKILL>/scripts/ov-session-audit.mjs --agent pi   # 某宿主：commit/记忆深度统计 + 自动判据
node <SKILL>/scripts/ov-session-audit.mjs --agent pi --local-sessions ~/.pi/agent/sessions
                                                       # ★多机场景必用★ 分离「本机 / 其它主机」
                                                       # 已登记目录见脚本 LOCAL_SESSION_DIR
                                                       # （pi / omp / claude-code / qoder）
node <SKILL>/scripts/ov-session-audit.mjs --detail cx-  # 抽样读 message_count / commit_count
node <SKILL>/scripts/ov-session-audit.mjs --json        # 供其它脚本消费
```

判据（四级递进，别只看第一级）：

1. 该前缀**有会话** → 至少写入过一次
2. **最近活动时间是近期** → 链路现在还在跑（很久以前 = 已断）
3. `--detail` 抽样**有 `message_count > 0`** → 内容真的送达了
4. `--agent` 的深度统计里**有 commit 的会话数 == 有记忆提取的会话数，且 > 0**
   → 「commit → 提取」这段也通了。**两者为 0 不等于失效**，多半是 commit 阈值未触发

⚠️ 实测要留意的五种假象：

- **会话存在 ≠ 有内容**（`messages=0` 但 `commits=7` 的空会话是存在的）
- **前缀可能被不同宿主共用**：从官方插件包派生的自建集成默认继承原宿主的 `harness` 与前缀，
  两个不同的 agent 写进同一命名空间，**服务端没有字段能区分** —— 实测 Qoder CN 与 Claude Code
  都用 `cc-`，于是 `--agent claude-code` 会把 Qoder 的会话算作 Claude Code 的成绩。
  **前缀数与本地会话记录对不上时，先怀疑这一点**，用 `--local-sessions` 反向定归属
  （`references/pitfalls.md` 第十四节）。
  ⚠️ 但这**不是**派生包的宿命：前缀就是派生包里的一个字符串字面量，可改，历史会话也可迁移
  —— 判据与工具见 `references/harness-matrix.md` §D-1
- **同一前缀可能来自多台主机**（服务端不记主机标识）。同一个 agent 装在多台机器上时，
  不先分离主机就统计，会把别的机器当成自己 —— 本机 pi 只有 24 条会话，而云端 `pi-`
  有 87 条，其中 63 条属于另一台。必须用 `--local-sessions` 分离后再下结论
  （详见 `references/pitfalls.md` 第十三节）
- **非 UUID 命名的会话不参与归属比对**（如手工探测会话 `qd-qoder-probe-0001`），
  脚本会单列为「无法判定归属」，不要当成"其它主机"
- **「云端会话数远少于本机会话数」多半不是故障** —— 宿主的历史会话在**接入之前**就已存在，
  永远不可能被上传，所以**不能拿总量作比**。本机 omp 实测：176 个会话、云端本机只 16 条，
  直觉是 9%（像是坏了），实际按集成落地时刻分界后是 **80%**（健康）。
  正确做法：用落地时刻（扩展/插件目录的 mtime）切分，只算落地后那组的上传率；
  再确认 `~/.openviking/pending/` 为空（空 = 从未发起上传，而非失败积压）
  （详见 `references/pitfalls.md` 第十五节）

已知前缀对照（2026-09-22 本机实测，**已无共用前缀**）：`cc-` claude-code · `cx-` codex ·
`pi-` pi · `omp-` omp · `zc-` zcode · `oc-` opencode · `ag-` antigravity · `wb-` WorkBuddy ·
`qd-` Qoder CN。`cron_*` 为定时任务会话，无前缀。

新增宿主时挑一个**未占用**的前缀，并记回 `references/harness-matrix.md` 与本脚本的
`AGENT_ALIAS` / `PREFIX_MAP`。**派生包还要按 §D-1 把前缀改成自己的**，并把历史会话迁过来
（`scripts/ov-session-reprefix.mjs`）。

## 第六步：注册守卫（宿主配置会被第三方整体重写时必做）

**通病，不是某一款 Agent 的特例**：宿主把「接入配置」和「业务配置」放在同一个文件里，
再由某个 GUI / 同步工具管理它 —— 那个工具整体重写文件而非增量合并，
只保留它认识的键，hooks / mcp 就被一起抹掉。

识别信号（满足任一就要警惕）：

- 同一文件既有 hook/MCP 注册，又有模型 / 供应商 / 账户等业务设置
- 存在第三方 GUI（provider 管理器、配置同步器）会写这个文件
- 服务端审计显示：配置看着对，但落库在某个日期**戛然而止**
- 宿主日志里 `hookCount` / `mcpServerCount` 出现**台阶式下降**

已确认实例：**ZCode**。

- 用户级 hook 源**唯一** = `~/.zcode/cli/config.json`
  （源码依据：`userConfigPath ?? join(home, ".zcode", "cli", "config.json")`；
  workspace 级另有 `<项目>/zcode.json` 与 `<项目>/.zcode/config.json`，向上一级级找、**以 `.git` 为边界**）
- provider 管理工具（EasyCLIProxyAPI / cpa-gui）会**成对重写** `cli/config.json` + `v2/config.json`，
  只写 model / provider 两段
- 实测：2026-09-20 10:43 被重写 → 10:44 起 `hookCount` 归零、`zc-` 会话停止落库
  （日志时间戳是 UTC，换算本地时间再与文件 mtime 比对才能对上号）
- 该工具**已于 2026-09-22 彻底清除**（含它的二级注册表 `~/.zcode/v2/provider_config.json`、
  状态文件与开机自启项）。**彻底清除的完整清单见 `references/pitfalls.md` 第十一节末 —— 只删主配置会留下复发路径**

**判据**：`~/.zcode/cli/log/zcode-YYYY-MM-DD.jsonl` 里 `ZCode plugins resolved` 事件的
`hookCount`。**归零 = 注册丢了**；非 0 就只能说明「有注册」——别把它的数值等同于事件数
（本机实测 4 个事件注册时该值是 2，口径未确证，不要据此推断）。

对策是**写幂等守卫脚本，而不是手改一次文件**：

1. 守卫脚本先剔除「本集成归属的 group」再追加 → 重复运行不产生重复 hook
2. 保留文件里其它键（模型 / 供应商 / 其它 MCP）
3. JSON 解析失败时**拒绝写入**，绝不覆盖损坏文件
4. 每次动过宿主设置后跑一次；修完靠宿主日志的 hookCount 与服务端落库共同确认

本机现成工具：

```bash
node <SKILL>/scripts/ov-zcode-guard.mjs          # 只检查（默认）
node <SKILL>/scripts/ov-zcode-guard.mjs --fix    # 缺失则修复，修复前自动备份
node <SKILL>/scripts/ov-zcode-guard.mjs --json   # 机器可读
```

它顺带体检：集成包必需文件齐否、共享运行时可加载否、凭据可读否、`node` 可由 PATH 解析否。

⚠️ `node` 可解析性这一项测的是**脚本自己的 PATH**，与宿主 GUI 进程未必一致，只作参考。
hook 命令写的是 `command: "node"`，若宿主进程 PATH 里没有 node，
hook 会**静默失效**（不报错、不落库）—— 这类宿主值得改用绝对路径 Node。

### 冒烟测试选哪个脚本

验证 hook 链路时，**优先挑不写库的那个事件**（ZCode 是 `PreToolUse` 的 `uri-guard.mjs`：
纯函数判断，不联网、不写库）。它能一次性证明「Node 能启动脚本 → 共享模块能加载 →
stdin 能读 → 输出符合宿主协议」，且不产生任何脏数据。
用写库事件（recall / capture）做冒烟会污染服务端，别这么干。

```bash
# 放行用例：预期无输出
printf '%s' '{"tool_name":"Read","tool_input":{"file_path":"C:/temp/plain.txt"}}' | node <集成包>/scripts/uri-guard.mjs
# 拦截用例：预期输出 deny 决策
printf '%s' '{"tool_name":"Read","tool_input":{"file_path":"viking://memory/notes"}}' | node <集成包>/scripts/uri-guard.mjs
```

## 参考资料

- `references/harness-matrix.md` —— 各宿主配置位置 / 事件 / 输出格式矩阵（本机实测）；§D-0 宿主会话目录（UUID 归属反查）、§D-1 派生包改前缀
- `references/host-contract.md` —— 接入前必查清单 + 接入记录模板（对应官方 §2）
- `references/adapter-authoring.md` —— 自建适配器：共享运行时 API、实现步骤、事件映射
- `references/pitfalls.md` —— 头号坑、配置层级、凭据与 peer 策略；§十三/十四 归属误判、§十五 上传率判读

## 脚本

| 脚本 | 用途 | 读写 |
|---|---|---|
| `scripts/ov-agent-probe.mjs` | 客户端配置面探测 + 分层判定 | 只读 |
| `scripts/ov-session-audit.mjs` | 服务端落库审计、多机/多宿主归属分离 | 只读 |
| `scripts/ov-zcode-guard.mjs` | ZCode 注册幂等守卫 | 默认只读，`--fix` 才写 |
| `scripts/ov-session-reprefix.mjs` | 会话批量改前缀（派生包分化命名空间） | 默认预演，`--apply` 才写，`--undo` 回滚 |

## 相关技能

- 服务端侧（换模型 / reindex / 迁移 / 健康）：`openviking-server-ops`
- WorkBuddy hook 细节与深度排障 SOP：`workbuddy-hook-ops`
- 拉取 OV 记录回填工作日志：`openviking-worklog-sync`
