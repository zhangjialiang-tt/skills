#!/usr/bin/env node
/**
 * ov-session-audit.mjs — 只读落库审计：各 Agent 的会话是否真的写进了 OpenViking
 *
 * 这是「验证第 4 级」的工具：注册 hook 后跑一轮真实会话，再用它回服务端确认。
 * 只发 GET 请求，不写入、不 commit、不删除。
 *
 * 用法：
 *   node ov-session-audit.mjs                 # 全部前缀统计
 *   node ov-session-audit.mjs --agent codex   # 只看某宿主（含 commit/记忆深度统计 + 判据）
 *   node ov-session-audit.mjs --agent pi --local-sessions ~/.pi/agent/sessions
 *                                             # ★同一 agent 装在多台机器上时必用★
 *                                             # 用本机自留会话分离「本机 / 其它主机」
 *   node ov-session-audit.mjs --agent pi --fast     # 跳过深度统计（少发请求）
 *   node ov-session-audit.mjs --agent pi --limit 20 # 限制深度统计抽样条数
 *   node ov-session-audit.mjs --detail cx-    # 抽样某前缀的会话，读 message_count
 *   node ov-session-audit.mjs --json          # 输出 JSON（供其它脚本消费）
 *
 * 两个高频误判（详见 references/pitfalls.md 第十二、十三节）：
 *   1. 有消息但零 commit → 多半是 commit 阈值未触发，不是接入失效
 *   2. 同前缀多主机混合 → 不分离主机就统计，会把别的机器当成本机
 *
 * 凭据来源（按序）：环境变量 OPENVIKING_URL/OPENVIKING_API_KEY → ~/.openviking/ovcli.conf
 */

import { readFileSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

/** 前缀 → 宿主。未登记的前缀会原样列出，提示补记到 harness-matrix.md */
const PREFIX_MAP = {
  "cc-": "claude-code",
  "cx-": "codex",
  "pi-": "pi",
  "omp-": "omp",
  "zc-": "zcode",
  "oc-": "opencode",
  "ag-": "antigravity",
  "wb-": "workbuddy",
  "qd-": "qoder",
  "dsh-": "dsh",
};

/** --agent 的别名 → 前缀 */
const AGENT_ALIAS = {
  claude: "cc-", "claude-code": "cc-", codex: "cx-", "codex-cli": "cx-", "codex-app": "cx-",
  pi: "pi-", omp: "omp-", opm: "omp-", zcode: "zc-", opencode: "oc-", oc: "oc-",
  antigravity: "ag-", agy: "ag-", workbuddy: "wb-", wb: "wb-", dsh: "dsh-",
  qoder: "qd-", "qoder-cn": "qd-", qd: "qd-",
};

/**
 * 已知「多个宿主共用同一前缀」的情况。
 * 自建集成从官方插件包派生时，常不改 harness 与 session 前缀，于是与会原宿主混库，
 * 且服务端无字段可区分 → 按前缀统计会张冠李戴（详见 references/pitfalls.md 第十四节）。
 * 每个条目附带该宿主的**本地会话目录**，用于 UUID 反向定归属。
 *
 * 2026-09-22：Qoder 原先借用 claude 的 `cc-`，已在自己的派生包里把前缀改成 `qd-`
 * 并把历史会话一并迁移，`cc-` 恢复为 claude-code 独占 → 本表清空。
 * 前缀不是不可改的：它就是派生包 `scripts/lib/ov-session.mjs` 里的一个字符串字面量。
 * 若将来又有派生包忘记改，在这里登记。
 */
const SHARED_PREFIX = {};

/**
 * 宿主 → 本机会话目录（供 `--local-sessions` 做 UUID 归属比对）。
 * 均已实测可用。新增宿主时补记于此，并同步 references/harness-matrix.md 的「宿主会话位置」表。
 * 注意 omp 的目录里还有一层「会话子文件」（`<uuid>/<name>.jsonl`），
 * 主会话文件名仍是 `<ISO>_<uuid>.jsonl`，去重后即本机会话数。
 */
const LOCAL_SESSION_DIR = {
  pi: "~/.pi/agent/sessions",
  omp: "~/.omp/agent/sessions",
  "claude-code": "~/.claude/projects",
  qoder: "~/.qoder-cn/projects",
};

function resolveCredentials() {
  const url = process.env.OPENVIKING_URL;
  const apiKey = process.env.OPENVIKING_API_KEY;
  if (url && apiKey) return { url: url.replace(/\/$/, ""), apiKey, source: "env" };
  const confPath = process.env.OPENVIKING_CLI_CONFIG_FILE || join(homedir(), ".openviking", "ovcli.conf");
  try {
    const conf = JSON.parse(readFileSync(confPath, "utf8"));
    if (conf.url && conf.api_key) {
      return { url: String(conf.url).replace(/\/$/, ""), apiKey: conf.api_key, source: confPath };
    }
  } catch {
    /* fallthrough */
  }
  return null;
}

async function getJSON(base, apiKey, path, timeoutMs = 20000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${base}${path}`, {
      headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
      signal: controller.signal,
    });
    const text = await res.text();
    let body = {};
    try {
      body = JSON.parse(text);
    } catch {
      body = { raw: text.slice(0, 300) };
    }
    return { ok: res.ok, status: res.status, body };
  } catch (error) {
    return { ok: false, status: 0, body: { error: error?.message || String(error) } };
  } finally {
    clearTimeout(timer);
  }
}

function prefixOf(sessionId) {
  const m = String(sessionId || "").match(/^([a-z]{2,5})-/) || String(sessionId || "").match(/^([a-z]+)-/);
  return m ? `${m[1]}-` : "<none>-";
}

/**
 * 深度统计：逐条拉会话详情，统计 commit 与记忆提取。
 *
 * 为什么必须看这两个数：消息同步（每轮写）与 commit+记忆提取（阈值触发）是两条独立路径。
 * 「有消息但零 commit」多半是阈值未触发，不是接入失效 —— 判据见 pitfalls 第十二节：
 * 有记忆提取的会话数 == 有 commit 的会话数（严格一一对应）且 > 0 即为链路正常。
 */
async function deepStats(allSessions, prefix, limit) {
  const targets = allSessions
    .filter((s) => prefixOf(s.session_id) === prefix)
    .sort((a, b) => String(b.mod_time || "").localeCompare(String(a.mod_time || "")))
    .slice(0, limit);

  const rows = [];
  const CONC = 8;
  for (let i = 0; i < targets.length; i += CONC) {
    const batch = targets.slice(i, i + CONC);
    const res = await Promise.all(
      batch.map(async (s) => {
        const d = await getJSON(
          cred.url,
          cred.apiKey,
          `/api/v1/sessions/${encodeURIComponent(s.session_id)}`,
        );
        const r = d.body?.result || d.body || {};
        const me = r.memories_extracted;
        const num = (v) => (typeof v === "number" ? v : null);
        return {
          id: s.session_id,
          mod: s.mod_time || "",
          messages: num(r.message_count),
          commits: num(r.commit_count),
          memories: me && typeof me === "object" ? num(me.total ?? 0) : num(me),
        };
      }),
    );
    rows.push(...res);
  }

  const withContent = rows.filter((r) => (r.messages ?? 0) > 0).length;
  const withCommit = rows.filter((r) => (r.commits ?? 0) > 0).length;
  const withMemory = rows.filter((r) => (r.memories ?? 0) > 0).length;
  const sumMessages = rows.reduce((a, r) => a + (r.messages ?? 0), 0);
  const sumMemories = rows.reduce((a, r) => a + (r.memories ?? 0), 0);

  return { rows, sampled: rows.length, totalInPrefix: allSessions.filter((s) => prefixOf(s.session_id) === prefix).length, withContent, withCommit, withMemory, sumMessages, sumMemories };
}

/**
 * 从本地会话目录递归提取 UUID。
 *
 * 用途：**同一前缀可能来自多台主机**（同一个 agent 装在多台机器上，都往同一个
 * OpenViking 写，前缀一样）。此时服务端按前缀统计会把多台机器混在一起，
 * 得出"某天有活动"之类的结论可能根本不是本机的。
 * 用本机 agent 自留的会话记录（文件名里带 UUID）与云端对照，即可精确分离。
 *
 * 已实测可用的目录：pi → `~/.pi/agent/sessions`（文件形如 `<时间ISO>_<uuid>.jsonl`）
 */
/**
 * 归一化 shell 传来的路径。
 *
 * ⚠️ 实测踩过的坑：Git Bash / MSYS 下 `~/.omp/agent/sessions` 会被 shell 展开成
 * `/c/Users/<u>/.omp/agent/sessions`，Node 在 Windows 上不认这个前缀 →
 * readdirSync 抛错、被 catch 吞掉 → 脚本报「没找到任何带 UUID 的会话文件」，
 * **把路径格式问题误报成目录填错**（实际发生过，排查成本高）。
 * 这里统一转成 `C:/Users/...`；同时兜住引号包裹导致 shell 未展开的字面量 `~/`。
 */
function normalizeLocalDir(p) {
  let s = String(p);
  if (s === "~" || s.startsWith("~/") || s.startsWith("~\\")) s = join(homedir(), s.slice(2));
  const m = s.match(/^\/([a-zA-Z])\/(.*)$/); // /c/Users/... → C:/Users/...
  if (m) s = `${m[1].toUpperCase()}:/${m[2]}`;
  return s;
}

/** 返回 { ids, dirExists, normalized }，便于把「路径不存在」与「目录里没有 UUID」分开报。 */
function extractLocalIds(rawDir) {
  const UUID_RE = /([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;
  const dir = normalizeLocalDir(rawDir);
  const ids = new Set();
  let dirExists = false;
  (function walk(d, depth) {
    if (depth > 4) return;
    let entries = [];
    try {
      entries = readdirSync(d, { withFileTypes: true });
      if (depth === 0) dirExists = true;
    } catch {
      return;
    }
    for (const e of entries) {
      const p = join(d, e.name);
      if (e.isDirectory()) {
        walk(p, depth + 1);
        continue;
      }
      const m = e.name.match(UUID_RE);
      if (m) ids.add(m[1].toLowerCase());
    }
  })(dir, 0);
  return { ids, dirExists, normalized: dir };
}

const args = process.argv.slice(2);
const asJson = args.includes("--json");
const detailIdx = args.indexOf("--detail");
const detailPrefix = detailIdx >= 0 ? args[detailIdx + 1] : null;
const agentIdx = args.indexOf("--agent");
const agentArg = agentIdx >= 0 ? args[agentIdx + 1] : null;
const fast = args.includes("--fast");
const limitIdx = args.indexOf("--limit");
const limitArg = limitIdx >= 0 ? Number(args[limitIdx + 1]) : null;
const localDirIdx = args.indexOf("--local-sessions");
const localDirArg = localDirIdx >= 0 ? args[localDirIdx + 1] : null;

const cred = resolveCredentials();
if (!cred) {
  console.error("找不到 OpenViking 凭据。");
  console.error("  期望：OPENVIKING_URL + OPENVIKING_API_KEY 环境变量，或 ~/.openviking/ovcli.conf");
  process.exit(1);
}

const health = await getJSON(cred.url, cred.apiKey, "/health", 12000);
if (!health.ok) {
  console.error(`服务端不可达或鉴权失败：${cred.url} → status=${health.status}`);
  // 常见误判提示：curl 在本机可能失败而 node fetch 正常，所以这里出问题才是真问题
  console.error(JSON.stringify(health.body).slice(0, 300));
  process.exit(2);
}

if (!asJson) {
  const h = health.body || {};
  console.log(`OpenViking ${h.version || "?"} @ ${cred.url}`);
  console.log(`账号 ${h.account_id || "?"} / 用户 ${h.user_id || "?"}  凭据来源 ${cred.source}`);
}

const sessions = await getJSON(cred.url, cred.apiKey, "/api/v1/sessions");
if (!sessions.ok) {
  console.error(`拉取会话列表失败：status=${sessions.status}`);
  process.exit(3);
}
const list = Array.isArray(sessions.body?.result) ? sessions.body.result : [];

const stats = new Map();
for (const s of list) {
  const key = prefixOf(s.session_id);
  const cur = stats.get(key) || { count: 0, latest: null };
  cur.count += 1;
  if (!cur.latest || String(s.mod_time || "") > cur.latest) cur.latest = String(s.mod_time || "");
  stats.set(key, cur);
}
const sorted = [...stats.entries()].sort((a, b) => b[1].count - a[1].count);

if (agentArg) {
  const prefix = AGENT_ALIAS[agentArg] || (agentArg.endsWith("-") ? agentArg : `${agentArg}-`);
  const hit = stats.get(prefix);
  console.log(`\n[${agentArg}] 前缀 ${prefix}`);
  if (!hit) {
    console.log("  ❌ 服务端没有该前缀的会话 → 会话从未写入（客户端配置可能看着像接入了）");
    console.log("  排查顺序：hook 是否触发 → hook 是否真含同步逻辑 → pending 队列是否积压 → 链路/服务端");
    process.exit(4);
  }
  console.log(`  ✅ ${hit.count} 条会话，最近活动 ${hit.latest}`);

  // 前缀被多个宿主共用时，必须提示——否则会张冠李戴（pitfalls 第十四节）
  const shared = SHARED_PREFIX[prefix];
  if (shared) {
    const others = shared.filter((s) => s.host !== agentArg);
    console.log(`  ⚠️  前缀 ${prefix} 被 ${shared.length} 个宿主共用：${shared.map((s) => s.host).join(" / ")}`);
    console.log(`      → 这 ${hit.count} 条**不一定是** ${agentArg} 的，服务端没有字段能区分。`);
    if (others.length) {
      for (const o of others) {
        console.log(`      ${o.host} 的本地会话目录：${o.local}`);
      }
    }
    console.log(`      定归属：用 --local-sessions <目录> 做 UUID 对照，命中该目录的才算本宿主的。`);
    console.log(`      例：--agent ${agentArg} --local-sessions ${SHARED_PREFIX[prefix].find((s) => s.host === agentArg)?.local || "<本地会话目录>"}`);
  }

  // 给了 --local-sessions 就必须全量拉详情（否则分组不完整）
  const sampleLimit = limitArg ?? (localDirArg ? Number.MAX_SAFE_INTEGER : 60);
  let deep = null;
  if (!fast) {
    deep = await deepStats(list, prefix, sampleLimit);
    const d = deep;
    console.log(`\n  深度统计（按时间倒序取 ${d.sampled}/${d.totalInPrefix} 条）`);
    console.log(`    有内容(message_count>0) : ${d.withContent}/${d.sampled}`);
    console.log(`    有 commit               : ${d.withCommit}/${d.sampled}`);
    console.log(`    有记忆提取              : ${d.withMemory}/${d.sampled}`);
    console.log(`    累计消息 / 累计记忆      : ${d.sumMessages} / ${d.sumMemories}`);
    if (d.withCommit === 0 && d.withMemory === 0) {
      console.log("    ⚠️  commit 与记忆提取均为 0：宿主的 commit 触发条件可能从未满足，");
      console.log("        或服务端提取任务积压。消息在写但从不 commit 属异常（见 pitfalls 第十二节）");
    } else if (d.withCommit === d.withMemory) {
      console.log(`    ✅ 判据通过：有 commit 的会话数 == 有记忆提取的会话数（${d.withCommit}），且 > 0`);
      console.log("       → 「commit → 提取」链路正常；未 commit 的会话属阈值未触发，不代表失效");
    } else {
      console.log(`    ⚠️  有 commit 的会话(${d.withCommit}) ≠ 有记忆提取的会话(${d.withMemory})`);
      console.log("       → 存在已 commit 但未提取的会话，查服务端提取任务");
    }
  }

  // ---- 主机分离：同一前缀可能来自多台机器，必须区分开 ----
  if (localDirArg && deep) {
    const { ids: localIds, dirExists, normalized } = extractLocalIds(localDirArg);
    if (!localIds.size) {
      if (!dirExists) {
        console.log(`\n  ⚠️  本地会话目录不存在：${normalized}`);
        console.log("      路径已在脚本内归一化（Git Bash 的 /c/... 会自动转 C:/...）；请核对目录名。");
      } else {
        console.log(`\n  ⚠️  目录存在，但没有文件名带 UUID 的会话文件：${normalized}`);
        console.log("      该宿主的会话命名可能不含标准 UUID，无法用此法定归属；");
        console.log("      改用其它线索（mtime / 内容特征）判断，或让适配层直接记录 host 标识。");
      }
    } else {
      // 云端 id 形如 "pi-<uuid>"，本地文件名里是纯 uuid → 比对前必须剥掉宿主前缀
      const uuidOf = (id) => String(id).replace(/^[a-z]+-/, "").toLowerCase();
      const isUuid = (s) => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(s);
      // 非 UUID 命名的会话（如手工探测会话 `qd-qoder-probe-0001`）无法参与归属比对，
      // 必须单列 —— 否则会被误算成「其它主机」（这个误判实际发生过）。
      const named = deep.rows.filter((r) => !isUuid(uuidOf(r.id)));
      const candidates = deep.rows.filter((r) => isUuid(uuidOf(r.id)));
      const cloudIds = new Set(candidates.map((r) => uuidOf(r.id)));
      const mine = candidates.filter((r) => localIds.has(uuidOf(r.id)));
      const other = candidates.filter((r) => !localIds.has(uuidOf(r.id)));
      const notUp = [...localIds].filter((id) => !cloudIds.has(id));
      const agg = (arr) => ({
        n: arr.length,
        msg: arr.reduce((s, r) => s + (r.messages ?? 0), 0),
        commit: arr.reduce((s, r) => s + (r.commits ?? 0), 0),
        mem: arr.reduce((s, r) => s + (r.memories ?? 0), 0),
        wc: arr.filter((r) => (r.commits ?? 0) > 0).length,
      });
      const a = agg(mine);
      const b = agg(other);
      const normNote = normalized === localDirArg ? "" : "（路径已自动归一化）";
      console.log(`\n  主机分离（本地会话库 ${normalized}${normNote} → ${localIds.size} 个会话）`);
      console.log("    主机          会话   消息    commit  记忆   有commit会话");
      console.log(`    本机          ${String(a.n).padStart(4)}  ${String(a.msg).padStart(5)}  ${String(a.commit).padStart(6)}  ${String(a.mem).padStart(5)}  ${String(a.wc).padStart(6)}`);
      console.log(`    其它主机      ${String(b.n).padStart(4)}  ${String(b.msg).padStart(5)}  ${String(b.commit).padStart(6)}  ${String(b.mem).padStart(5)}  ${String(b.wc).padStart(6)}`);
      console.log(`    本机有、云端无（未上传）: ${notUp.length} 条`);
      if (named.length) {
        console.log(`    无法判定归属（session id 非 UUID 格式）: ${named.length} 条`);
        console.log(`      ${named.slice(0, 5).map((r) => r.id).join(" · ")}${named.length > 5 ? " · …" : ""}`);
        console.log("      这类多为手工探测/测试会话，不参与主机归属比对");
      }
      if (b.n > 0 && b.n > a.n) {
        console.log(`    ⚠️  云端该前缀下「其它主机」占多数（${b.n}/${deep.sampled}）——`);
        console.log(`        单看前缀统计会把别的机器误当成本机，必须先分离再下结论`);
      }
    }
  } else if (!localDirArg) {
    console.log("\n  提示：同一前缀可能来自多台主机。若该 agent 装在多台机器上，");
    const known = LOCAL_SESSION_DIR[agentArg] || LOCAL_SESSION_DIR[PREFIX_MAP[prefix]];
    if (known) {
      console.log(`        加 --local-sessions ${known} 可精确分离本机 / 其它主机。`);
    } else {
      console.log("        加 --local-sessions <本机会话目录> 可精确分离（已登记目录见本脚本 LOCAL_SESSION_DIR）");
    }
  }
  process.exit(0);
}

if (detailPrefix) {
  const targets = list.filter((s) => prefixOf(s.session_id) === detailPrefix).slice(0, 8);
  if (!targets.length) {
    console.log(`\n前缀 ${detailPrefix} 下没有会话。`);
    process.exit(4);
  }
  console.log(`\n抽样 ${targets.length} 条（prefix=${detailPrefix}）`);
  let nonEmpty = 0;
  for (const s of targets) {
    const d = await getJSON(cred.url, cred.apiKey, `/api/v1/sessions/${encodeURIComponent(s.session_id)}`);
    const r = d.body?.result || d.body || {};
    const mc = r.message_count ?? "?";
    const cc = r.commit_count ?? "?";
    const meRaw = r.memories_extracted;
    const me = meRaw && typeof meRaw === "object" ? JSON.stringify(meRaw) : (meRaw ?? "?");
    if (typeof mc === "number" && mc > 0) nonEmpty += 1;
    console.log(`  ${s.session_id}`);
    console.log(`     messages=${mc}  commits=${cc}  memories_extracted=${me}  mod=${s.mod_time || "?"}`);
  }
  console.log(
    nonEmpty
      ? `\n✅ ${nonEmpty}/${targets.length} 条有内容 → 链路在真实写入`
      : `\n❌ 抽样会话 message_count 全为 0 → 会话被创建但内容没送达（查 pending 队列与写入路径）`,
  );
  process.exit(nonEmpty ? 0 : 5);
}

if (asJson) {
  console.log(JSON.stringify({ url: cred.url, total: list.length, prefixes: Object.fromEntries(sorted) }, null, 2));
  process.exit(0);
}

console.log(`\n共 ${list.length} 条会话，按前缀分组：\n`);
const pad = Math.max(...sorted.map(([k]) => k.length), 6);
for (const [prefix, info] of sorted) {
  const who = PREFIX_MAP[prefix] || "未登记（请补进 harness-matrix.md）";
  console.log(`  ${prefix.padEnd(pad)}  ${String(info.count).padStart(4)} 条   最近 ${info.latest}   ${who}`);
}

const known = Object.keys(PREFIX_MAP);
const missing = known.filter((k) => !stats.has(k));
if (missing.length) {
  console.log(`\n⚠️  以下前缀在云端没有任何会话：${missing.join(", ")}`);
  console.log(`   逐个确认：node ov-agent-probe.mjs <agent>  # 看客户端配置是否真的两层都挂上了`);
}
console.log("\n提示：会话存在 ≠ 有内容，重要变更后用 --detail <前缀> 抽样确认 message_count。");
