#!/usr/bin/env node
/**
 * ov-session-reprefix.mjs — 把某个前缀下的会话批量改名为另一个前缀
 *
 * 用途：某个自建派生包借用了官方宿主的前缀（如 Qoder 曾借用 claude 的 `cc-`），
 * 在派生包里改掉前缀后，服务端**历史会话仍留在旧前缀下**。本脚本把它们迁到新前缀，
 * 让命名空间彻底干净、审计时能凭前缀定归属。
 *
 * 原理：服务端会话就是普通目录（`messages.jsonl` + `history/archive_*` + `tool-results/`），
 * `GET /api/v1/sessions` 的列表由目录扫描派生，且存在 `POST /api/v1/fs/mv` →
 * **改目录名即改会话 id**，不需要重建会话，消息与归档原样保留。
 *
 * 用法：
 *   node ov-session-reprefix.mjs --from cc- --to qd-            # 预演（默认，只读）
 *   node ov-session-reprefix.mjs --from cc- --to qd- --apply    # 真正执行，写映射文件
 *   node ov-session-reprefix.mjs --from cc- --to qd- --json     # 机器可读
 *   node ov-session-reprefix.mjs --undo <映射文件>               # 按映射回滚
 *
 * 安全性：
 *   - 默认只读预演，必须显式 `--apply` 才写服务端
 *   - 目标 id 已存在时中止（改名会互相覆盖）
 *   - 改名前后逐条比对 `messages.jsonl` 字节数，不一致立即告警（内容可能没迁全）
 *   - 映射文件落在 `~/.openviking/session-rename-<from>-to-<to>.<时间戳>.json`，供 `--undo`
 *   - 只改名，**从不删除**任何会话；空会话与探针会话一并保留
 *
 * ⚠️ 改名前先确认旧前缀**确实没有别的宿主在用**（用 ov-session-audit 的
 *    `--local-sessions` 做 UUID 反向定归属），否则会把别人的会话一起搬走。
 *
 * 凭据来源（按序）：环境变量 OPENVIKING_URL/OPENVIKING_API_KEY → ~/.openviking/ovcli.conf
 */

import { readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

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

async function api(base, apiKey, path, init = {}, timeoutMs = 30000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${base}${path}`, {
      ...init,
      headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
      signal: controller.signal,
    });
    return { status: res.status, body: await res.json().catch(() => ({})) };
  } catch (error) {
    return { status: 0, body: { error: error?.message || String(error) } };
  } finally {
    clearTimeout(timer);
  }
}

function parseArgs(argv) {
  const out = { from: "", to: "", apply: false, json: false, undo: "", help: false };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--apply") out.apply = true;
    else if (a === "--json") out.json = true;
    else if (a === "--from") out.from = argv[++i] || "";
    else if (a === "--to") out.to = argv[++i] || "";
    else if (a === "--undo") out.undo = argv[++i] || "";
    else if (a === "-h" || a === "--help") out.help = true;
  }
  return out;
}

const USAGE = `用法:
  node ov-session-reprefix.mjs --from cc- --to qd-            预演（只读）
  node ov-session-reprefix.mjs --from cc- --to qd- --apply    执行
  node ov-session-reprefix.mjs --from cc- --to qd- --json     机器可读
  node ov-session-reprefix.mjs --undo <映射文件>               回滚

前缀写法：带或不带结尾的 \`-\` 都接受（cc / cc- 等价）。`;

/** 统一前缀写法：确保以单个 `-` 结尾 */
function normPrefix(v) {
  const s = String(v || "").trim().replace(/-+$/, "");
  return s ? `${s}-` : "";
}

/**
 * 会话所在的根 URI（`viking://user/<user>/sessions`）。
 * 从服务端返回的真实样本里取，避免把用户名写死在脚本里。
 */
function sessionsRoot(all, fallbackUser) {
  for (const s of all) {
    const m = String(s.uri || "").match(/^(viking:\/\/[^/]+\/[^/]+\/sessions)\//);
    if (m) return m[1];
  }
  return `viking://user/${fallbackUser}/sessions`;
}

async function listSessions(base, apiKey) {
  const r = await api(base, apiKey, "/api/v1/sessions?limit=2000");
  if (r.status >= 300 || r.body?.status !== "ok") {
    throw new Error(`列会话失败：HTTP ${r.status} ${JSON.stringify(r.body).slice(0, 200)}`);
  }
  return r.body.result || [];
}

/** 读某会话的 messages.jsonl 字节数，用于改名前后比对 */
async function messageSize(base, apiKey, sessionUri) {
  const r = await api(base, apiKey, `/api/v1/fs/ls?uri=${encodeURIComponent(sessionUri)}&recursive=false`);
  const hit = (r.body?.result || []).find((f) => String(f.uri).endsWith("messages.jsonl"));
  return hit ? hit.size : null;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help || (!opts.undo && (!opts.from || !opts.to))) {
    console.log(USAGE);
    process.exit(opts.help ? 0 : 2);
  }

  const cred = resolveCredentials();
  if (!cred) {
    console.error("❌ 找不到凭据：设 OPENVIKING_URL/OPENVIKING_API_KEY，或检查 ~/.openviking/ovcli.conf");
    process.exit(3);
  }
  const { url: base, apiKey, source } = cred;

  const all = await listSessions(base, apiKey);
  const root = sessionsRoot(all, process.env.OPENVIKING_USER || "default");
  const existing = new Set(all.map((s) => String(s.session_id)));
  const uriOf = (id) => `${root}/${id}`;

  const rows = [];
  let fromPrefix = "";
  let toPrefix = "";

  if (opts.undo) {
    let map;
    try {
      map = JSON.parse(readFileSync(opts.undo, "utf8"));
    } catch (error) {
      console.error(`❌ 读不到映射文件 ${opts.undo}：${error?.message || error}`);
      process.exit(3);
    }
    if (!Array.isArray(map) || !map.length) {
      console.error("❌ 映射文件为空或格式不对（应为数组）");
      process.exit(3);
    }
    for (const e of map) {
      if (e?.oldId && e?.newId) rows.push({ from: String(e.newId), to: String(e.oldId), applied: e.applied });
    }
    console.log(`回滚模式：按 ${opts.undo} 反向改回，共 ${rows.length} 条`);
    console.log(`凭据：${source}\n`);
  } else {
    fromPrefix = normPrefix(opts.from);
    toPrefix = normPrefix(opts.to);
    if (!fromPrefix || !toPrefix) {
      console.error("❌ 前缀不能为空");
      process.exit(2);
    }
    if (fromPrefix === toPrefix) {
      console.error("❌ --from 与 --to 相同，无事可做");
      process.exit(2);
    }
    for (const s of all) {
      const id = String(s.session_id);
      if (!id.startsWith(fromPrefix)) continue;
      rows.push({ from: id, to: `${toPrefix}${id.slice(fromPrefix.length)}` });
    }
    console.log(`凭据：${source}`);
    console.log(`服务端共 ${all.length} 条会话，${fromPrefix} 开头 ${rows.length} 条 → 目标前缀 ${toPrefix}\n`);
    if (!rows.length) {
      console.log("无需迁移。");
      process.exit(0);
    }
  }

  // 目标 id 冲突检查：改名会覆盖已有会话，必须先拦住
  // （成对互换的情况除外——那两条彼此让位，不是真冲突）
  const fromSet = new Set(rows.map((r) => r.from));
  const clashes = rows.filter((r) => existing.has(r.to) && !fromSet.has(r.to));
  if (clashes.length) {
    console.error("❌ 目标 id 已存在，改名会互相覆盖，已中止：");
    for (const c of clashes) console.error(`   ${c.from} -> ${c.to}`);
    process.exit(5);
  }

  console.log(`模式：${opts.apply ? "执行" : "预演（只读）"}\n`);

  const results = [];
  let ok = 0;
  let fail = 0;
  let warn = 0;

  for (const r of rows) {
    const fromUri = uriOf(r.from);
    const toUri = uriOf(r.to);
    const before = await messageSize(base, apiKey, fromUri);

    if (!opts.apply) {
      console.log(`  [预演] ${r.from}  ->  ${r.to}   messages.jsonl=${before ?? "?"}B`);
      results.push({ oldId: r.from, newId: r.to, applied: false, sizeBefore: before });
      continue;
    }

    const res = await api(base, apiKey, "/api/v1/fs/mv", {
      method: "POST",
      body: JSON.stringify({ from_uri: fromUri, to_uri: toUri }),
    });
    const moved = res.status < 300 && res.body?.status === "ok";
    const after = moved ? await messageSize(base, apiKey, toUri) : null;
    const intact = moved && before === after;
    if (moved) ok += 1; else fail += 1;
    if (moved && !intact) warn += 1;

    console.log(
      `  ${moved ? (intact ? "OK  " : "WARN") : "FAIL"} ${r.from}  ->  ${r.to}` +
        `   [HTTP ${res.status}] messages.jsonl ${before ?? "?"}B -> ${after ?? "?"}B` +
        (moved && !intact ? "  ⚠️ 字节数不一致，请人工核对" : ""),
    );
    results.push({
      oldId: r.from, newId: r.to, applied: moved, status: res.status,
      sizeBefore: before, sizeAfter: after, intact: moved ? intact : null,
      error: moved ? "" : JSON.stringify(res.body).slice(0, 200),
    });
  }

  if (opts.json) {
    console.log(JSON.stringify({ from: fromPrefix, to: toPrefix, applied: opts.apply, results }, null, 2));
  } else if (opts.apply) {
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const tag = opts.undo ? "undo" : `${fromPrefix.replace(/-$/, "")}-to-${toPrefix.replace(/-$/, "")}`;
    const mapPath = join(homedir(), ".openviking", `session-rename-${tag}.${stamp}.json`);
    writeFileSync(mapPath, JSON.stringify(results, null, 2), "utf8");
    console.log(`\n成功 ${ok} / 失败 ${fail}${warn ? ` / 字节数告警 ${warn}` : ""}`);
    console.log(`映射文件：${mapPath}`);
    console.log(`回滚：node ov-session-reprefix.mjs --undo <上面的映射文件>`);
    if (fail || warn) process.exit(1);
  } else {
    console.log("\n这是预演，未改动任何数据。加 --apply 才真正执行。");
  }
}

main().catch((error) => {
  console.error(`❌ ${error?.message || error}`);
  process.exit(1);
});
