# 自建适配器：复用共享运行时，只写宿主差异

> 适用于官方 install.sh 未覆盖、但宿主具备生命周期 hook / extension 机制的情况。
> 权威依据：官方 `docs/zh/agent-integrations/18-plugin-development.md`。
> 本文件是**落地路径**，不替代那份标准的验收清单。

## 核心原则

> **同一行为只有一个权威实现。共享模块拥有规则，适配器只提供宿主事实。**

官方明确禁止：复制后改名的 client/recall/doctor、在共享函数里密集判断 harness 名、
为每个新宿主复制一整套 Claude Code / Codex 目录。

## 两种实现形态

| 形态 | 适用 | 共享代码怎么来 | 本机实例 |
|---|---|---|---|
| **薄宿主适配器**（首选） | 宿主用配置文件注册 hook/MCP，公共调度足以表达生命周期 | `import` `~/.openviking/agent-integrations/memory-plugin-shared/lib/agent-hook-runtime.mjs` | Antigravity |
| **完整 vendored 插件** | 宿主需要独立 manifest、独立目录、独立生命周期入口 | vendor 整个 `lib/*.mjs` 到自己的 `scripts/shared/`，写 `PROVENANCE.md` 记录来源 | WorkBuddy、ZCode |

**先试薄适配器。** 只有当宿主强制要求独立 manifest 或常驻状态时才升级为完整插件。
WorkBuddy 最后走了 vendored 路线，是因为要挂 `~/.workbuddy/settings.json` 且需要独立启动器。

## 共享运行时 API（`agent-hook-runtime.mjs`）

实测导出（2026-09，262 行）：

| 函数 | 职责 | 注意 |
|---|---|---|
| `loadAgentHookConfig(clientId)` | 读全部开关与凭据，含 `timeoutMs`、`autoRecall`、`autoCapture`、`commitTurnThreshold`、`writePathAsync` 等 | 凭据由 `credentials.mjs` 解析（env → `ovcli.conf`），**不要自己读 key** |
| `createAgentLogger(clientId, hookName, cfg)` | 统一日志，写到 `~/.openviking/logs/<clientId>-hooks.log` | 日志走文件，**不要写 stdout**（会污染宿主上下文） |
| `readHookInput()` | 读 stdin 并 JSON.parse，失败返回 `{}` | 只调一次；不要在多处重复读 |
| `resolveAgentCwd(input)` | 依次取 `cwd` → `workspace_roots[0]` → `CURSOR_PROJECT_DIR` → `process.cwd()` | 宿主 cwd 语义异常时需在此层归一化 |
| `resolveNativeSessionId(input)` | 取 `conversation_id`/`session_id`/`sessionId`/`generation_id`，否则从 `transcript_path` 抽 UUID | 都拿不到时退化为 `cwd-<hash>` |
| `deriveAgentSessionId(prefix, input)` | 生成带前缀的 OV 会话 id | 前缀自选，记回 `harness-matrix.md` |
| `withAgentHookLock(clientId, sid, cb)` | 会话级文件锁（5s 获取超时，60s 陈旧锁回收） | **多窗口/并发事件必须包住**；返回 `null` 表示拿锁失败，要静默退出 |
| `readHookState` / `writeHookState` | 状态读写；写入走临时文件 + 原子 `rename`，权限 0600 | 状态目录可用 `OPENVIKING_HOOK_STATE_DIR` 隔离 |
| `makeAgentFetchJSON(cfg, cwd)` | 返回 `{ fetchJSON, effectivePeer }`，自动带 `Authorization`、`X-OpenViking-Account/User`、`X-OpenViking-Actor-Peer`、`User-Agent`，并做超时与错误归一 | 返回 `{ok,result,status,error,traceId}`，**不抛异常** |
| `addAgentMessage` / `addAgentMessages` | 写入会话消息；可重试失败自动入 pending 队列 | 批量接口单批上限 100 条 |
| `commitAgentSession(fetchJSON, sid, log)` | 触发 OV 抽取，产出持久记忆 | 失败可重试时同样入队 |
| `replayAgentPending` | 重放 pending 队列 | 只在会话首次事件调用，别每轮都跑 |
| `recallForPrompt(fetchJSON, cfg, prompt, cwd, log, {sessionId})` | 构造 `<relevant-memories>` 块 | **传 `sessionId` 才会打开服务端 query expansion 与跨轮去重** |
| `buildAgentProfile(fetchJSON, cfg, cwd)` | 启动时注入 profile.md + preferences/entities 摘要 | 每会话只注入一次 |
| `shouldBypassAgent(cfg, input)` | 判断是否命中 bypass 规则 | 采集/召回前都要判 |

## 最小适配器骨架

照 Antigravity 的形状（本机已跑通的实现）：

```js
#!/usr/bin/env node
import {
  addAgentMessages, buildAgentProfile, commitAgentSession, createAgentLogger,
  deriveAgentSessionId, loadAgentHookConfig, makeAgentFetchJSON, readHookInput,
  readHookState, recallForPrompt, replayAgentPending, resolveAgentCwd,
  shouldBypassAgent, withAgentHookLock, writeHookState,
} from "../../memory-plugin-shared/lib/agent-hook-runtime.mjs";
import { extractUnseenTurns, extractLatestUserPrompt } from "./myhost-turns.mjs";

const eventName = process.env.MYHOST_HOOK_EVENT || process.argv[2] || "";
const CLIENT = "myhost";                       // 与 clientId / 会话前缀 / 日志名一致
const cfg = loadAgentHookConfig(CLIENT);
const { log, logError } = createAgentLogger(CLIENT, eventName, cfg);

const outputJson = (data) => process.stdout.write(JSON.stringify(data) + "\n");

const input = await readHookInput();
if (shouldBypassAgent(cfg, input)) { outputJson({}); process.exit(0); }

const cwd = resolveAgentCwd(input);
const nativeSessionId = /* 宿主的原生 session id */;
const sessionId = deriveAgentSessionId("xx-", input);   // xx- 前缀
const { fetchJSON } = makeAgentFetchJSON(cfg, cwd);

if (eventName === "SessionStart") {
  // 1) 重放 pending（只在启动时）2) 注入 profile
}

if (eventName === "UserPromptSubmit") {
  // recallForPrompt(...) → 用宿主约定字段注入，记得带 { sessionId }
}

if (eventName === "Stop") {
  // withAgentHookLock 包住 → 读 state 游标 → 取新 turns → addAgentMessages
  // → 达到阈值则 commitAgentSession → 推进游标
}
```

**每个分支只输出一次**，未命中分支输出 `{}` 或直接 `process.exit(0)`。

## 可靠写入的不变量

写入顺序（官方 §5.4）：

```text
读取新记录 → 解码与过滤 → 按顺序发送
                          ├─ 服务端确认        → 推进已发送进度
                          ├─ 已持久化到 pending → 可推进交接进度（仍未送达）
                          └─ 发送与入队都失败    → 保留原游标，等恢复
```

必须做到：

1. **游标只推进到连续确认的位置** —— `sent` 与 `queued` 分开记
2. **去重优先用稳定 ID**（turnId / 消息 uuid / transcript 行号），别用文本 hash
3. **多进程更新同一状态必须加会话锁**，状态写入用临时文件 + 原子的 `rename`
4. **transcript 截短 / resume / compaction 不能让游标永久越过新记录**
5. **子代理记录由明确一方采集**，避免重复导入

重试分类：网络失败、408、429、5xx 可重试；409 仅在 `error.details.retryable` 为真时可重试；
**401/403 与参数错误绝不能反复入队**（会污染队列并消耗重试额度）。

## 事件映射决策

| 通用责任 | 宿主有该事件 | 宿主没有该事件 |
|---|---|---|
| 会话启动 / profile 注入 | 挂在启动事件 | 挂到首个提交事件，用 state 标记 `profileInjected` |
| 逐轮 recall | 挂在提交事件 | 若无提交事件，降级为 MCP-only 或挂到轮次结束 |
| 增量采集 | 挂在轮次结束事件 | 挂到宿主最接近"轮次结束"的事件 |
| 压缩前提交 | `PreCompact` | **不注册**；由阈值提交兜底 |
| 会话结束提交 | `SessionEnd` | **必须显式选替代提交点**，如"轮次结束 + 阈值"或"轮次结束 + 空闲超时" |

**绝对不要**为了"看起来很完整"而注册宿主不支持的事件 —— 它们不会报错，只会永远不触发。

## 采集内容处理

- **采集前必须 strip 自己注入的内容**：`<relevant-memories>`、`<openviking-context>`、
  `<system-reminder>`、`[Subagent Context]` 以及 null 字节。否则注入内容会被当成用户内容写回，形成自反馈膨胀。
- **工具调用与结果要保留关联**（哪个调用产生哪个结果），但工具输出通常极长 —— 用
  `captureToolMaxChars` / `captureMaxLength` 截断，并把截断标记写进内容。
- 宿主 transcript 是权威增量来源时优先读它；payload 只作兼容兜底。

## peer 策略（最容易打碎记忆库的地方）

`peer` 决定记忆归属哪个命名空间，默认按 **git 身份**派生（`peer.source: git`）：

- 有 git 仓库 → `github.com-org-repo`，任何机器、任何子目录、任何 worktree 都收敛到同一个 peer
- **非 git 目录 → 不发 peer**，记忆落到用户级空间

因此两种宿主语义要区别对待：

| 宿主 cwd 语义 | 处理 |
|---|---|
| cwd = 项目目录 | 直接用默认派生，可与其它宿主交叉检索 |
| cwd = 每次会话的临时目录（如 `<home>/Agent/<时间戳>`） | **必须归一化**，否则每个会话生成一个新 peer，记忆库被打碎 |

需要显式指定时：仓库内放 `<repo>/.openviking/config.json` → `{"version":1,"peer":{"id":"my-project"}}`，
或设 `OPENVIKING_PEER_ID`。

## B 路径派生包必做：换掉 harness 与前缀

从官方插件包**派生**出的宿主集成（B 路径）默认继承原宿主的 `harness` 与会话前缀，
写进服务端后与原宿主混在一起，而服务端**没有任何字段能区分来源**。
派生时必须改两处，缺一不可：

| 位置 | 改什么 | 不改的后果 |
|---|---|---|
| `scripts/lib/ov-session.mjs` | `deriveHarnessSessionId("<prefix>-", …)` 的前缀 | 与原宿主**共用命名空间**，按前缀审计会张冠李戴 |
| `scripts/config.mjs` | `harness: "<host>"`、`buildUserAgent("<host>", …)` | 只影响日志名与统计标识，但留着会误导排障 |

**为什么改前缀是安全的**：全部 hook 都经由 `deriveOvSessionId()` 单点派生，
且全包**无任何反向解析前缀的代码**（无 `startsWith("<prefix>-")`、无 `replace(/^<prefix>-/)`）
→ 改一个字符串字面量即可。

改之前把四项连带耦合逐一核掉（照抄这张表逐条查，别凭直觉）：

| 疑点 | 怎么查 |
|---|---|
| `harness` 是否参与配置分节 | 看 `loadPluginSettings()` 的**实参**（本机实测传的是 `HARNESS_KEYS.claudeCode` = `claude_code`，带下划线，与 `harness` 标签不是同一条线） |
| `harness` 是否参与 peer 身份 | 看默认 `peer.source` 模板含不含 `{harness}`（默认 `git` → `{git_remote}`/`{git_root}`，不含） |
| 本地队列/状态有无旧前缀残留 | `grep -r "<prefix>-" ~/.openviking/pending ~/.openviking/hook-state` |
| 已落库会话的归属 | UUID 逐个到各宿主本地会话目录反查（见 pitfalls §13/§14），确认归属后才敢迁移 |

历史会话必须一并迁移，否则旧前缀下仍留着你的数据、审计照样分不清：

```bash
node <SKILL>/scripts/ov-session-reprefix.mjs --from cc- --to qd-            # 预演
node <SKILL>/scripts/ov-session-reprefix.mjs --from cc- --to qd- --apply    # 执行
```

**顺带检查 User-Agent**：官方模板写的是 `readManifestVersion(new URL("../.claude-plugin/plugin.json", …))`，
派生包通常没有 `.claude-plugin/`，而该函数读不到时**静默返回 `""`** → UA 退化成 `.../0.0.0`。
把它改指向自己的 `package.json`。

## 验收要点

- 复用官方契约测试：`agent-hook-runtime.test.mjs`、`capture-utils.test.mjs`、`pending-queue.test.mjs`、
  `mcp-proxy-core.test.mjs`；新 proxy 必须补进 `mcp-hook-parity.test.mjs`
- 合并前跑：`node examples/memory-plugin-shared/sync.mjs`（改了共享源码时）
- **注意**：CI 通过不等于 Windows 上的 detach、路径引用、进程回收已验证 —— 这三项要单独实测
