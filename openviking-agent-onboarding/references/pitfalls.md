# 接入陷阱与配置模型

## 一、头号坑：解释器路径静默失效

**现象**：hook 昨天正常，宿主重启/升级后**彻底不触发** —— 不报错、不提示、日志无痕。

**根因**：hook 配置里写死了带版本号的解释器绝对路径。宿主的运行时目录带版本号并在升级时轮换
（如 WorkBuddy 的 `binaries/node/versions/22.22.2-3`，重启会换目录名并删除旧目录）。
路径失效 → 命令执行失败 → **静默失效**。

**本机已存在的同类风险实例**：Qoder CN 的 hooks 配置里写死了 `C:\Software\nodejs\node.exe`。
能跑，但用户升级系统 Node 就会断，且不会有任何提示。

**对策 —— 稳定启动器模式**：配置里只写一个不带版本号的启动器脚本，由它动态解析解释器：

```bash
# run-hook.sh —— hook 的唯一入口
set -u
BASE="${OV_HOOK_ROOT:-C:/Users/zhangjl/.workbuddy}"   # 换成宿主的实际根
NODE=""
# ① 优先读"当前版本"指针文件
v="$(tr -d '\r\n' < "$BASE/binaries/node/versions/current" 2>/dev/null || true)"
[ -n "${v:-}" ] && [ -f "$BASE/binaries/node/versions/$v/node.exe" ] \
  && NODE="$BASE/binaries/node/versions/$v/node.exe"
# ② 兜底：版本目录取最新
[ -z "$NODE" ] && NODE="$(ls -d "$BASE"/binaries/node/versions/*/node.exe 2>/dev/null | tail -1)"
# ③ 兜底：PATH
if [ -z "$NODE" ] || [ ! -f "$NODE" ]; then
  p="$(command -v node 2>/dev/null || true)"; [ -n "$p" ] && NODE="$p"
fi
[ -n "$NODE" ] && [ -f "$NODE" ] || exit 0     # fail-open：绝不阻塞宿主
exec "$NODE" "$BASE/hooks/your-hook.mjs" "${1:-unknown}"
```

**排查动作**：任何 hook 突然不触发，先查配置里解释器路径是否仍存在，再查日志 mtime。
探针/日志文件的 mtime 与当前时间接近 = 活着；长时间不更新 = 已失效。

## 二、fail-open 是硬要求

hook 里任何异常都应 `exit 0`，并设硬超时：

```js
setTimeout(() => process.exit(0), 5000).unref();
```

状态类 hook 永远不该卡死宿主主流程。一个卡住的 recall 会让用户每次提问都多等十几秒。

## 三、stdout 语义按宿主/事件不同

- Claude/Codex/WorkBuddy 的 `SessionStart` / `UserPromptSubmit` stdout **会注入上下文**
- ZCode 用严格 JSON schema，**多一个键整份输出被丢弃**（头号静默失败模式）
- Cursor 用 `additional_context`，Claude 系用 `hookSpecificOutput.additionalContext`，**不能混用**
- `decision: "approve"` 是 Claude Code 专有写法，不是通用格式

**纯采集类 hook 必须保持 stdout 为空。** 日志一律写文件或 stderr。

## 四、配置与凭据的层级（官方统一模型）

优先级从高到低：

```
OPENVIKING_* 环境变量
→ ~/.openviking/workspaces/<slot>.json         (机器级)
→ <repo>/.openviking/config.local.json         (私有，gitignore)
→ <repo>/.openviking/config.json               (团队共享，进 git)
→ ovcli.conf 的 plugin.<harness>               (按宿主覆盖)
→ ovcli.conf 的 plugin                          (全部宿主共用)
→ ov.conf 中按 harness 命名的段                  (旧版)
→ 内置默认
```

要点：

- **一处配置全部 harness**：`ovcli.conf` 的 `plugin` 段对所有宿主生效；`plugin.<harness>` 做单宿主覆盖
  - 宿主名两种拼写都认：`claude_code` / `claude-code`、`trae_cn` / `trae-cn`
- **workspace 文件拒绝连接与凭据键**（`url` / `api_key` / `account` / `user` / `extra_headers` …），
  且**不展开 `${VAR}`** —— 所以凭据不能靠它下发，只能走 env 或 `ovcli.conf`
- workspace 文件是**免确认信任**的（hook 是非交互的，审批门会退化成每个工作区一次命令）
- `.gitignore` 不能把整个 `.openviking/` 忽略掉，否则 `config.json` 永远进不了 git；
  应收窄到 `.openviking/media/`、`.openviking/downloads/`

## 五、凭据：不要写进 agent 配置

**正确做法**：`~/.openviking/ovcli.conf`（权限 0600）或 `OPENVIKING_*` 环境变量，
由 `mcp-proxy.mjs` / `credentials.mjs` 在**运行时**读取。

**错误做法**（本机实际存在）：把 `Authorization: Bearer <key>` 明文写进
`~/.codex/config.toml`、`~/.config/mimocode/mimocode.jsonc`、`~/.gemini/settings.json` 的 `mcpServers`。

这些文件会被同步、备份、贴进 issue、进 dotfiles 仓库。发现时应提醒用户改用 stdio 代理或环境变量。

**parity 要求**：hook 与 MCP proxy 必须解析到**同一份**凭据与同一个 actor peer
（官方有 `mcp-hook-parity.test.mjs` 专门守这一条）。两者分叉会出现"MCP 能搜到、hook 却写不进"或反之。

## 六、peer 打碎记忆库

默认 `peer.source: git`：有 git 仓库 → `github.com-org-repo`，跨机器/子目录/worktree 收敛；
**非 git 目录不发 peer** → 记忆落到用户级空间。

| 宿主 cwd 语义 | 后果 |
|---|---|
| cwd = 项目目录 | 正常，可与其它宿主交叉检索 |
| cwd = 每次会话的临时目录 | ⚠️ **每个会话一个新 peer，记忆库被打碎** |

旧行为是"cwd 路径把非字母数字换成 `-`"，克隆到别的路径 / 改目录名 / 用 worktree / 从子目录启动
各会造出一个独立空命名空间。迁移不需要动作：旧 id 总能本地重算，`peer_scope: "all"` 的默认召回
已覆盖它们；要退回旧行为设 `peer.source: "cwd"`。

## 七、pending 队列的饥饿特性

`~/.openviking/pending/` 是所有 agent **共用**的待发队列。`replayPending` 只在 SessionStart 触发，
三个必须知道的特性：

- 首条 `addMessage` 遇到**可重试失败**（status ∈ {0, 408, 429, ≥500}）即 `deferred += 剩余全部; break`
  → **首条不通 = 整队永不被尝试**
- 首条 `retries >= OPENVIKING_PENDING_MAX_RETRIES`（默认 3）会被**永久丢弃**
  → 每次 SessionStart 消耗 1 次，连续 4 次会话启动就丢消息
- 只有 `commitSession` 记录失败详情，`addMessage` 的失败状态码**无处可查**（可观测性盲区）

```bash
ls ~/.openviking/pending/*.json | wc -l        # 积压条数
ls ~/.openviking/pending/                       # 后缀 _<n> 即 retries，_1 = 已失败 1 次
ls ~/.openviking/pending/ | grep -v '\.json$'   # .processing 残留 = claim 未释放
```

**处置顺序**：先恢复链路，**再**让它 replay（否则白耗 retries、加速丢弃）。
操作前必备份 `pending/`。

## 八、Windows 上的写入路径不可靠

宿主退出后，detached 子进程**无法存活** → 异步写入路径在 Windows 上等于不写入。

- 特征：hook 确实触发了（宿主日志有 spawn 记录），但服务端零落库、状态文件缺关键字段
- 判据：同步模式下**父进程返回时日志文件已存在**；异步模式下返回时必定不存在
- 对策：接入时把写入路径默认设为**同步**（`OPENVIKING_WRITE_PATH_ASYNC=0`），
  并设 `OPENVIKING_TIMEOUT_MS` 限制最坏阻塞（同步 Stop 实测 ~1.4s）

⚠️ **手工复现会给出假阳性**：在宿主进程之外跑同一条 detach 路径，worker 能存活并成功写入。
所以"手工 live test 通过"不能证明生产可用，必须做真实事件验证。
（完整案例见 `workbuddy-hook-ops`「头号坑」与坑 6。）

## 九、网络链路的误判

- **`curl` 可能连不上 OV 而 node `fetch` 正常**（Mihomo/TUN 会干扰 curl 的 socket 处理，
  典型报错 `curl: (52) Empty reply from server`）。**别据此判断服务端挂了**，一律改用
  `node -e "fetch(...)"` 验证。
- 排查链路 vs 服务端：**多个不相干目标同时超时 ⇒ 本机链路问题**；只有 OV 超时 ⇒ 服务端。
  判据在 Mihomo service 日志的失败计数（5 min 滚动），不要只靠一次性探测下结论 ——
  该故障是间歇的，密集短探测可能全落进成功窗口而"看起来正常"。
- Git Bash 下 `netstat` 查不到监听端口（进程可能监听在 IPv6 通配 `::`），
  用 PowerShell `Get-NetTCPConnection -State Listen` 才可见。

## 十、其他易漏项

1. **`--harness` 拼错会被显式拒绝**（install.sh 有白名单校验），不会静默降级 —— 这是好事
2. **一键安装与 marketplace 安装不能混用**，否则同一个插件跑两遍、记忆重复
3. **改了共享源码要跑 `node examples/memory-plugin-shared/sync.mjs`**，
   vendor 副本不会自动同步；生成的副本**不要手改**（升级会覆盖），改权威源
4. **`.d.mts` 类型声明与 `.mjs` 同目录、一起生成**，不要在产物目录手写
5. **不要在普通模块 import 时读 stdin / 起子进程 / 联网 / 退出进程** —— 会污染调用方
6. **启动器里用 `${VAR:-default}` 而不是 `export VAR=1`** —— 硬赋值会让外部无法覆盖，
   排障时切不了 dry-run / 同步模式

## 十一、注册被第三方工具整体覆盖（配置写入方不唯一）

**坑**：宿主把「接入配置」和「业务配置」放进同一个文件，而那个文件还有别的写入方
（provider 管理器、配置同步 GUI、宿主自己的设置界面）。它们**整体重写**文件、
只保留自己认识的键 —— hooks / mcp 就被顺带抹掉，且**不会报任何错**。

已确认实例（ZCode）：

| 项 | 内容 |
|---|---|
| 唯一用户级 hook 源 | `~/.zcode/cli/config.json` 的 `hooks.events` |
| 覆盖者 | provider 管理工具（EasyCLIProxyAPI / cpa-gui），**成对重写** `cli/config.json` + `v2/config.json` |
| 覆盖内容 | 只留 `model` / `provider`，抹掉 `hooks` / `mcp` / **`plugins`**（三键全丢，2026-09-22 核实） |
| 额外损害 | `v2/config.json` 侧另丢 **8 个 provider**（含百炼TokenPlan），只剩 `cpa-gui` 一个 |
| 首次发现 | 2026-09-20 10:43 被写 → 10:44 起 `hookCount` 归零、服务端 `zc-` 停止落库 |
| **触发方式** | **不是手动操作** —— CPA 自动更新（`autoUpdate`）后约 **1.5 分钟**自动重新接入，会反复发生 |
| 自启 | 注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\EasyCLIProxyAPI`；另 `config.toml` 有 `run-on-startup = true` |

**为什么难发现**：集成包完好、配置目录在、脚本语法没问题，客户端探测也"看着对"。
只有把三样东西放在一起看才会暴露 —— **宿主日志的 `hookCount`**、
**服务端该前缀的最近活动时间**、**关键文件的 mtime**。

### 恢复的唯一依据：它写前会自动备份

这类工具**改写前会把原文逐字节存下来**（算是不幸中的万幸）。以 CPA 为例：

```
<CPA安装目录>/backups/agents/<client>/<sha256>/<本地时间戳>-<pid>-<n>.json
```

结构是 `{ payload: { version, id, client, createdAt, files[], mappings }, checksum }`，
每个 `files[]` 条目含 `{ path, bytes[], hash }` —— **`bytes` 是原文的字节数组，`hash` 是 sha256**。
所以恢复流程是纯机械的：

1. 按 `client` 找到备份目录，取最新（或指定时刻）的快照
2. `JSON.parse` 后对每个 `files[]`：`Buffer.from(bytes).toString("utf8")` 还原原文
3. **用 `hash` 校验**（`sha256(原文) === f.hash`）—— 校验不过就别用这份备份
4. 对比原文与当前文件，列出被丢弃的键
5. 按决策合并写回（**注意下面的陷阱**）

⚠️ **陷阱：不能把备份原文直接照搬回 `model`**。备份是"工具介入之前"的状态，但
工具可能**更早就已经改过一次 `model`**（本例中 8-27/9-07 两份备份的 `model` 是
`builtin:bigmodel-coding-plan/glm-5.1`，而 9-20 破坏前它已变成 `cpa-gui/gpt-5.6-luna`）。
照搬会得到一个**指向即将被删除的 provider 的悬空引用**。
正确做法是从**更早的备份**里取回原始 `model` 值，或按用户意图重新指定。

**顺带一个判据**：`~/.zcode/v2/config.json.cpa-gui.state.json` 是工具自己的跟踪文件
（记录 `configurationRevision` 与 `backupFiles`），它的 `updatedAtUnix` 能精确告出
**工具介入过几次、每次都备份了哪些文件** —— 是重建时间线的最快入口。


**时间对不上的坑**：ZCode 日志的 `timestamp` 是 **UTC**。文件 mtime 是本地时间。
北京 10:43 的文件改动，在日志里显示为 `02:43Z` —— 不换算就会得出"时间顺序矛盾"的错误结论，
进而误判根因。

**对策**：写**幂等守卫脚本**，而不是手改一次文件。

- 先剔除「本集成归属的 group」再追加 → 重复跑不会产生重复 hook
- 只增不删，保留文件里其它键
- JSON 解析失败时**拒绝写入**（绝不覆盖损坏文件）
- 本机工具：`node <SKILL>/scripts/ov-zcode-guard.mjs [--fix]`

⚠️ **守卫只是缓解，不是根治**：它能在你手动跑时把配置修回来，但**阻止不了工具改写**。
根治只有两条路 —— 不用那个工具（本例用户的选择），或把接入从「宿主全局配置」
迁到**工作区级配置**（ZCode 有 workspace 级 `zcode.json`，不受这类工具影响）。

**同一工具对不同宿主可以差很多，别一概而论**：

| | 对 ZCode（破坏性） | 对 pi（追加式） |
|---|---|---|
| 改法 | 白名单整体重写全局 `config.json` | 走官方 npm 插件，独立文件 + 宿主设置里**追加**一项 |
| 落点 | **抹掉**别人的键 | `~/.pi/agent/cliproxyapi.json`、`cliproxyapi-models.json`、`npm/node_modules/@router-for-me/...` |
| 碰宿主设置吗 | 是，且**删除** `hooks`/`mcp`/`plugins` | 是，但只在 `settings.json` 的 `packages[]` **追加**一项，**不删任何既有配置** |
| 净损失 | OV 接入全失效 + 8 个 provider | 无（`defaultModel`/`defaultProvider`/`auth.json`/`models.json` 均未变） |

⚠️ **「温和」不等于「没碰宿主设置」**（2026-09-22 更正）：先前据 `~/.pi/agent/settings.json`
"看起来没提到 CPA" 就下了「settings.json 不动」的结论，**是错的**。
事实：CPA 在 2026-09-20 11:44 写入了 `settings.json`，在 `packages[]` 里追加了
`"npm:@router-for-me/pi-cliproxyapi-provider"` —— 这正是扩展的**加载入口**，只删包体不删这一项，
pi 下次启动仍会尝试加载。**教训：判断某工具是否碰过某文件，要按 mtime + 内容双向核对，
不能只 grep 关键词**（该文件用 `npm:` 前缀引用包名，关键词命中的是 `cliproxyapi`，换个写法就漏了）。

排查时先看「它改的是哪个文件、是替换还是追加」，再定严重程度。

**推论**：接入前先问一句「这个配置文件还有谁会写？」。
若答案是「有」，那这次接入就必须配守卫，否则注定在某次无关操作后静默失效。

### 彻底清除一个改写方的清单（2026-09-22 实操验证）

用户弃用那个工具后要做的不只是"把 provider 删掉"。**只删显眼的那个文件会留下复发路径。**

| # | 目标 | 为什么必须一起清 |
|---|---|---|
| 1 | 宿主主配置里的条目 | 显眼项（如 `provider["cpa-gui"]`）。**注意可能有多份**：ZCode 有 `cli/config.json` + `v2/config.json` 两份，只修一份会漏 |
| 2 | ⚠️ **工具的二级注册表** | `~/.zcode/v2/provider_config.json` 里另有 1 条 `providerRule` + 9 条 `providerModelRule`。**这是宿主设置界面的存储，不清它，界面可能把 provider 再生回来** —— 本清单里最容易漏、后果最隐蔽的一项 |
| 3 | 工具自己的状态文件 | 如 `config.json.cpa-gui.state.json`，记录 `configurationRevision` 与它备份过哪些文件 |
| 4 | 开机自启 | 注册表 `HKCU\...\Run\<工具名>`（**先 `reg export` 备份整键再删**）。不改它，工具再启动就再改一遍 |
| 5 | 工具在**其它宿主**留下的东西 | 本例是 pi：`settings.json` 的 `packages[]` 条目 + npm 依赖 + `node_modules` 包体 + lockfile + `cliproxyapi*.json` + Temp 缓存。**同一个工具对不同宿主的落点完全不同，必须逐个宿主单独扫** |

**方法要点**（比清单本身更重要）：

- **按"配置面"扫，不按文件名猜**：遍历 `~/.<host>` 下所有 `json/jsonc/toml/yaml`，匹配工具特征串
  （provider id、包名、监听端口如 `127.0.0.1:8317`），排除运行态目录（`sessions`/`logs`/`db`/`artifacts`/`rollout`）
  与备份（`.bak`/`pre-*`）。**历史会话里有旧工具名是正常的，别当残留删**。
- **二进制里的文案要用正确编码提**：Tauri/Rust 打包的 exe 里中文界面串是 UTF-8，直接 grep 会显示成 GBK 乱码，
  看起来"没有相关文案"而误判工具没这功能。
- **删包体但漏了宿主设置里的引用 → 下次启动报错**：必须"引用（`packages[]`/`dependencies`）"与
  "包体（`node_modules`）"同步处理，lockfile 也要摘条目，否则下次 `npm install` 又装回来。
- **lockfile 先确认无连带依赖再外科式摘除**：本例 CPA 包 `dependencies` 为空（只有 peerDependencies），
  所以只需删 `packages["node_modules/..."]` + 根条目里的 `dependencies[...]` 两处，
  不必重跑 `npm install`（重跑会顺带改动其它包的解析结果，风险更大）。
- **写脚本而不是手改**：默认预演、`--apply` 才落盘、保留原缩进与末位换行、**写后逐项断言**。
  断言要**同时**验「该删的没了」和「不该删的还在」——后者才是防误删的关键。
  本机留档：`cpa-purge.mjs` + `cpa-purge-files.mjs`（在 WorkBuddy 工作区）。
- **删除用「移入隔离区」而非 `rm`**：`renameSync` 到一个备份目录，全程可回滚。
- **宿主在运行时改配置要留后手**：改完立刻复查（比对 mtime + 内容）确认没被运行态写回；
  脚本做成幂等，万一复活可原地重跑。ZCode 本次未出现复活（它不在退出时回写全量 provider 列表）。

## 十二、「有消息但没记忆」多半是正常机制，不是接入失效

**坑**：审计时看到某前缀会话数不少、`message_count` 在涨，但 `commit_count` 和
`memories_extracted.total` 大量为 `0` → 容易误判成"hook 半死"。

**真相**：**消息同步**（每轮写）与 **commit + 记忆提取**（阈值触发）是两条独立路径。
没 commit 只说明没跨过触发条件，不代表链路断了。

**决定性判据** —— 先统计两个集合而不是看单条：

```
有记忆提取的会话数  ==  有 commit 的会话数     （严格一一对应）
```

两者数量**完全相等**且都 > 0，就证明「commit → 提取」这段是通的，
剩下没记忆的会话属于**未触发**，不是**失败**。（本机 pi：19 = 19，即此形态。）

**触发条件因宿主而异，接入前要读宿主扩展的代码确认**。两种常见形态：

| 形态 | 触发点 | 备注 |
|---|---|---|
| 直接提交 | `session_shutdown`（会话结束）、`session_before_compact`（上下文压缩）、手动命令 | 最直白 |
| 阈值驱动（takeover 类） | 累积 token ≥ 阈值 **且** 用户轮次 > 保留轮数 | **启用 takeover 后，shutdown 分支往往不再直接 commit** |

已确认实例（pi，本机实测 2026-09-22）：

- 配置 `~/.pi/agent/extensions/openviking/config.json`：`takeover.enabled=true`、
  `commitTokenThreshold=20000`、`takeover.tokenThreshold=30000`、`takeover.keepRecentTurns=3`
- 触发链：`turn_end` 每轮同步 → 累积 `pendingTokens`；达 `takeoverTokenThreshold` **且**
  `lastSeenUserTurns > keepRecentTurns` 才 `commitAndAdvance()`
- 因此 `index.ts` 里 `session_shutdown` 走的是 `takeover.shutdown()`；
  **只有** `takeover.enabled=false` 时那条分支才调 `sync.commit()`
- 结果：短会话天然零 commit。本机数据 `09-17` 单日 15 commit / 39 条记忆，
  而 `09-19~09-20` 连续零 commit（同期 600+ 条消息仍在正常写入）——**符合设计，非故障**

**排查顺序**（务必按此序，别一上来就查配置）：

1. 统计两个集合是否相等且 > 0 → 相等即链路通，可收工
2. 若 `commit` 数也为 0 且服务端最后活动时间是**很久以前** → 才怀疑链路
3. 确实要立刻落库时，用宿主的手动命令兜底（pi 是 `/viking commit`）

**相关误判**（同一个坑的两种表现）：

- **调试日志缺失 ≠ 失效**。多数实现的 `debugLogPath` 未配置时直接返回 `noop`
  （pi 的 `shared/debug-log.mjs`、ZCode 的 `zcode-hooks.log` 都是如此），
  日志文件不存在或长期为 0 字节属正常。
- **长会话零 commit** 仍可能出现（本机有一条 439 条消息、`commit=0` 的会话）。
  这属于长尾，不影响整体判据；在意就用手动命令补一次。

## 十三、同一前缀可能来自多台主机（多机混库）

**坑**：同一个 agent 装在多台机器上，都往**同一个** OpenViking 写，会话前缀相同
（都叫 `pi-`）。而服务端**不记录主机标识** —— 实测会话详情字段里没有 hostname / cwd /
device / peer，只有 account/user、各类时间、`message_count`、`commit_count`、
`memories_extracted`、`pending_tokens`、`keep_recent_count`。

**后果**：按前缀统计得出的结论可能根本不是本机的。实例（2026-09-22 实测）：
本机 pi 只有 24 条会话，而云端 `pi-` 有 **87** 条 —— 其中 **63 条来自另一台机器**。
一条"今天有 commit=4 / 记忆 20"的记录就属于别人，据此会得出错误结论。

**识别方法（唯一可靠）**：拿 agent 自留的**本地会话记录**与云端做 UUID 对照。

| 宿主 | 本地会话位置 | 文件形态 |
|---|---|---|
| pi | `~/.pi/agent/sessions/<cwd 编码目录>/` | `<ISO时间>_<uuid>.jsonl`；首行 JSON 含 `id` 与 `cwd` |
| 其他 | 各自不同，需先确认 | 只要文件名或内容含 UUID 即可用 |

技能脚本已内置分离：

```
node <SKILL>/scripts/ov-session-audit.mjs --agent pi --local-sessions ~/.pi/agent/sessions
```

输出「本机 / 其它主机」分组统计、未上传条数，以及"其它主机占多数"的警告。
**比对关键**：云端 id 是 `pi-<uuid>`，本地是纯 `<uuid>` → 必须先剥掉宿主前缀再比，
否则永远匹配为 0（这个 bug 实际发生过）。

**顺带能查出的东西 —— 未上传清单**（本地有、云端无）：结合扩展安装时间，
可以区分「接入前的历史会话」（正常）与「接入后失败」（要查）。

**务必控制"扩展安装时间"这个变量**：本机 08-21 装上扩展前，59 个会话 0 上传；
装上后，已信任目录 21/21 全部上传。不做这个切分，会把一堆历史会话误当成接入故障。

**根因层面的建议**：想让两台机器的记忆可区分，给它们配**不同的 `peerId`**
（pi 的 `config.json` 支持该字段）。本机当前未配置 → 两台机器混写同一个
`user/zhangjl`，检索时会互相污染。

**别把 trust 白名单当开关**：pi 有 `~/.pi/agent/trust.json`（目录信任列表），
但它与"扩展是否上传"**没有因果关系** —— 实测同一未信任目录既有失败也有成功
（`zhangjl-ai-video` 同一天一次失败一次成功）。看到相关性别急着下结论，先控制时间变量。

## 十四、同一前缀可能来自不同**宿主**（自建包借用官方前缀）

这比第十三节更隐蔽：第十三节是"同宿主多主机"，本节是**两个完全不同的 agent 共用一个前缀**。

**坑**：从官方插件包**派生**出来的自建集成，往往不改 `harness` 与 session 前缀 ——
于是它在服务端与**原宿主完全混在一起**，且没有任何字段能区分。

实测（2026-09-22）：Qoder CN 用的是 `agent-integrations/qoder/`，它是 **Claude Code 插件包的
派生版**，源码里两处都没改：

| 位置 | 值 | 后果 |
|---|---|---|
| `scripts/config.mjs` | `harness: "claude-code"` | debug log 写到 `cc-hooks.log` |
| `scripts/lib/ov-session.mjs` | `deriveHarnessSessionId("cc-", …)` | 会话进 `cc-` 命名空间 |

而真正的 Claude Code 插件（`~/.claude/plugins/cache/openviking/openviking-memory/*/scripts/lib/ov-session.mjs`）
**也是** `deriveHarnessSessionId("cc-", …)`。→ **两边都是 `cc-`，云端无法区分。**

**识别方法**：前缀不可信时，改用**本地会话 UUID 反向定归属**（同第十三节的手法，但目标不同）：

```
云端 cc- 的 4 条 UUID  →  逐个到 ~/.qoder-cn/projects/<项目>/<uuid>.jsonl 查
                       →  4/4 命中 Qoder 目录，0 命中 ~/.claude/projects
                       →  结论：cc- 下这 6 条全是 Qoder，Claude Code 实际 0 条
```

**这个错误很容易犯**：`ov-session-audit --agent claude-code` 会把 Qoder 的会话算作
Claude Code 的成绩，得出"Claude Code 很活跃"的**反向错误结论**。本技能快照表早期版本
就记错了（把 6 条 Qoder 会话记成 Claude Code 的活跃证据）。

**通用判据**：只要某前缀的会话数**与本地该宿主的会话记录对不上**，就先怀疑有别的宿主
借用了同一前缀，别急着解释成"上传率低"。

**顺带发现的两个坑**：

1. **自建包里可能缺 `servers/mcp-proxy.mjs`** —— Qoder 包的 `.mcp.json` 写的是
   `node ${CLAUDE_PLUGIN_ROOT}/servers/mcp-proxy.mjs`，但该目录**不存在**。
   实际生效的是宿主配置里的 **http 直连**（`settings.json → mcpServers.openviking`，
   `type: http` 指向服务端 `/mcp`）。→ **以宿主配置为准，别信包内的 `.mcp.json` 模板**。

2. **自带的 `ov-memory-doctor.mjs` 是 Claude Code 版，不能用来诊断派生宿主** ——
   它硬查 `~/.claude/plugins/` 与本地 `claude` CLI，对 Qoder 报出的
   「plugin files missing / installPath no longer exists / marketplace 指向缺失目录」
   **全是误报**。看到一堆红叉先确认它查的是不是你的宿主。

**正面经验（值得抄）**：Qoder 的 hook 用了 **node 绝对路径**
（`"command": "C:\\Software\\nodejs\\node.exe"` + `"args": [...]` 数组），
不依赖宿主进程 PATH —— 这正是 zcode 那条 `command: "node"` 的隐患所对应的正确做法。

### 14.1 这个坑已经能解：前缀就改在派生包里（2026-09-22 实测）

"派生包必然与原宿主混库"是**误解**。前缀就是派生包 `scripts/lib/ov-session.mjs` 里的
一个字符串字面量，且全包 hook 都经 `deriveOvSessionId()` 单点派生、
**无任何反向解析前缀的代码** → 改一个字符串即可，不存在解析错位。

本机已把 Qoder 从 `cc-` 迁到 `qd-`，改动三处：

| 改动 | 文件 | 值 |
|---|---|---|
| 会话前缀 | `agent-integrations/qoder/scripts/lib/ov-session.mjs` | `"cc-"` → `"qd-"` |
| harness | `.../scripts/config.mjs` | `"claude-code"` → `"qoder"` |
| User-Agent | `.../scripts/config.mjs` | `openviking-memory-claude-code/0.0.0` → `openviking-memory-qoder/0.4.7` |

6 条历史会话用 `POST /api/v1/fs/mv` 一并改名（会话就是目录，改目录名即改会话 id，
76266B 消息体字节数不变）。完整判据、四项连带耦合核查清单与迁移工具见
`references/harness-matrix.md` §D-1。

**顺带发现一个静默降级**：`config.mjs` 里 `buildUserAgent("claude-code",
readManifestVersion(new URL("../.claude-plugin/plugin.json", …)))` —— 派生包**没有**
`.claude-plugin/` 目录，而 `readManifestVersion()` 读不到时**静默返回 `""`**，
于是 UA 一直退化成 `openviking-memory-claude-code/0.0.0`。
**派生包必须把这个路径改指向自己的 `package.json`**，否则服务端统计里的版本号永远不可信 ——
这类"读不到就返回空串"的辅助函数不会报错，只能靠人工核对发现。

## 十五、「云端会话数远少于本机会话数」多半不是故障

这是最容易误判的一类：本机 omp 有 176 个会话，云端 `omp-` 只有 16 条来自本机
（另外 8 条属他机）→ 直觉是"只上传了 9%，链路坏了"。**实际链路完全正常。**

### 判据：用「集成落地时刻」分界，而不是用总量作比

宿主的历史会话**在接入之前就已存在**，它们永远不可能被上传。所以正确算法是：

1. 取集成落地时刻 —— 扩展/插件目录里文件的 mtime（如
   `~/.omp/agent/extensions/openviking/config.json`，实测 2026-08-29T00:46Z）
2. 本机会话按该时刻切成**落地前 / 落地后**两组
3. 只有**落地后**那组的上传率才有判读意义

omp 实测结果：

| 分组 | 本机会话 | 已上传 | 判读 |
|---|---|---|---|
| 落地**前** | 156 | 0 | ✅ 正常 —— 那时还没接入，本就不该有 |
| 落地**后** | 20 | 16（**80%**） | ✅ 健康 |

**只看总量会得出 9% 的错误结论；按落地时刻分界才是 80%。**

### 辅助判据：`pending/` 是否为空

```bash
ls -la ~/.openviking/pending/     # 空 → 没有上传失败积压
```

队列为空说明未上传的会话是**从未发起上传**（阈值未触发），而非**发起后失败**。
两者处置完全不同：前者无需处理，后者要查网络与重放。

### 未上传的常见正当原因（逐条核对，不要笼统归因）

| 原因 | 特征 | 例（omp 落地后 4 条未上传） |
|---|---|---|
| 会话过短 | 几 KB，未达 `commitTokenThreshold` | 4KB、8KB 各 1 条 |
| 安装期会话 | 时间戳紧贴落地时刻 | 落地后 4 分钟那 1 条 |
| 宿主异常终止 | 尾部有 `session_exit` 且 `kind=signal` | `reason=sighup` 1 条 |

### ⚠️ 反面教训：不要把单一特征当结论

`sighup` 看起来很像原因，但**已上传的会话里也有 2 条 `sighup`** —— 用它当判据会得出
错误结论。本次先把「退出方式」当假设、批量核对 20 条后才推翻。
**任何归因都要拿已上传组做对照组**，只盯着未上传组会看到一堆假相关。

（读 `session_exit` 的办法：会话 jsonl 尾部有
`{"type":"custom","customType":"session_exit","data":{"reason":"…","kind":"…"}}`。）
