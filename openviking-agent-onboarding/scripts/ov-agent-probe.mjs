#!/usr/bin/env node
/**
 * ov-agent-probe.mjs — 只读探测：某 Agent 的 OpenViking 接入面
 *
 * 零副作用：只 stat / read 本地文件，不发任何网络请求、不写任何文件。
 *
 * 用法：
 *   node ov-agent-probe.mjs codex            # 单查已知宿主
 *   node ov-agent-probe.mjs --all            # 扫全部已知宿主
 *   node ov-agent-probe.mjs --scan ~/.foo    # 扫描任意目录（官方未收录的宿主）
 *   node ov-agent-probe.mjs --list           # 列出已知宿主键名
 *
 * 判定分两层（两层都过才算 integrated）：
 *   只读层 mcp  —— MCP 配置里有 OV 注册
 *   同步层 hook —— hook 注册存在，且追到实际执行的脚本里含 OV 逻辑
 *
 * 结论：not-found / not-integrated / mcp-only / integrated
 * 附加时效标记：日志 mtime 超过 STALE_DAYS 天 → 标 (stale)
 */

import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { basename, join, resolve } from "node:path";

const MAX_READ = 2 * 1024 * 1024; // 超过 2MB 不读正文
const STALE_DAYS = 14; // 日志超过这么久没动静 → 视为已断
const H = homedir();
const p = (...seg) => join(H, ...seg);

/** OV 特征：出现在配置或被指向的脚本里，即视为该层已接 */
const OV_RE = /openviking|OPENVIKING_|ovcli|agent-integrations|:1933|\/api\/v1\/sessions|mcp-proxy/iu;
const SCRIPT_RE = /["'`]?([A-Za-z]:[\\/][^"'`\s]*?\.(?:sh|cmd|bat|ps1|mjs|cjs|js|py))["'`]?/gu;

/** 已知宿主。layer: mcp / hook / pkg（pkg 只作佐证，不参与判定） */
const HOSTS = {
  claude: {
    label: "Claude Code", official: true, prefix: "cc-", clientId: "claude",
    probes: [
      { path: p(".claude", "settings.json"), layer: "hook" },
      { path: p(".claude.json"), layer: "mcp" },
    ],
  },
  codex: {
    label: "Codex CLI / App", official: true, prefix: "cx-", clientId: "codex",
    probes: [
      { path: p(".codex", "config.toml"), layer: "both" },
      { path: p(".codex", "plugins", "cache", "openviking"), layer: "pkg", kind: "dir" },
    ],
  },
  cursor: {
    label: "Cursor", official: true, prefix: null, clientId: "cursor",
    probes: [
      { path: p(".cursor", "hooks.json"), layer: "hook" },
      { path: p(".cursor", "mcp.json"), layer: "mcp" },
    ],
  },
  trae: {
    label: "TRAE", official: true, prefix: null, clientId: "trae",
    probes: [
      { path: p(".trae", "hooks.json"), layer: "hook" },
      { path: p(".trae", "mcp.json"), layer: "mcp" },
    ],
  },
  "trae-cn": {
    label: "TRAE CN", official: true, prefix: null, clientId: "trae-cn",
    probes: [
      { path: p(".trae-cn", "hooks.json"), layer: "hook" },
      { path: p(".trae-cn", "mcp.json"), layer: "mcp" },
    ],
  },
  zcode: {
    label: "ZCode", official: true, prefix: "zc-", clientId: "zcode",
    probes: [
      // 用户级 hook 源唯一就是 cli/config.json 的 hooks.events，不存在独立的 hooks.json
      { path: p(".zcode", "cli", "config.json"), layer: "both" },
      { path: p(".openviking", "agent-integrations", "zcode"), layer: "pkg", kind: "dir" },
    ],
  },
  qoder: {
    label: "Qoder CN（官方未收录，本机自建装配；集成包是 Claude Code 插件派生版，前缀已改为 qd-）",
    official: false, prefix: "qd-", clientId: "qoder",
    probes: [
      { path: p(".qoder-cn", "settings.json"), layer: "both" },
      { path: p(".openviking", "agent-integrations", "qoder"), layer: "pkg", kind: "dir" },
    ],
  },
  opencode: {
    label: "OpenCode", official: true, prefix: "oc-", clientId: "opencode",
    probes: [
      { path: p(".config", "opencode", "opencode.json"), layer: "both" },
      { path: p(".config", "opencode", "openviking-config.json"), layer: "both" },
      { path: p(".config", "opencode", "plugins", "openviking"), layer: "pkg", kind: "dir" },
    ],
  },
  pi: {
    label: "pi coding agent", official: true, prefix: "pi-", clientId: "pi",
    probes: [{ path: p(".pi", "agent", "extensions", "openviking"), layer: "both", kind: "dir" }],
  },
  omp: {
    label: "omp（oh-my-pi 系，官方未收录）", official: false, prefix: "omp-", clientId: "omp",
    probes: [{ path: p(".omp", "agent", "extensions", "openviking"), layer: "both", kind: "dir" }],
  },
  antigravity: {
    label: "Antigravity / Gemini 系（官方未收录）", official: false, prefix: "ag-", clientId: "antigravity",
    probes: [
      { path: p(".gemini", "settings.json"), layer: "mcp" },
      { path: p(".gemini", "config", "hooks.json"), layer: "hook" },
      { path: p(".openviking", "agent-integrations", "antigravity"), layer: "pkg", kind: "dir" },
    ],
  },
  mimocode: {
    label: "MiMo Code（小米）", official: false, prefix: null, clientId: "mimocode",
    probes: [{ path: p(".config", "mimocode", "mimocode.jsonc"), layer: "both" }],
  },
  workbuddy: {
    label: "WorkBuddy", official: false, prefix: "wb-", clientId: "workbuddy",
    probes: [
      { path: p(".workbuddy", "settings.json"), layer: "hook" },
      { path: p(".workbuddy", "hooks", "ov"), layer: "hook", kind: "dir" },
    ],
  },
};

const CANDIDATE_NAMES = [
  "settings.json", "settings.jsonc", "config.json", "config.jsonc", "config.toml",
  "config.yml", "config.yaml", "hooks.json", "mcp.json", "mcp_config.json",
  "opencode.json", "mimocode.jsonc", "mcpServers.json",
];

// ---------------------------------------------------------------- 工具函数

function readText(path) {
  try {
    const st = statSync(path);
    if (!st.isFile()) return null;
    if (st.size > MAX_READ) return null;
    return readFileSync(path, "utf8");
  } catch {
    return null;
  }
}

/**
 * 判断一个路径"命中哪一层"。
 * - 目录名含 openviking（扩展/集成包）→ 两层一体，视为 mcp+hook
 * - 文件名含 openviking（OV 专属配置）→ 同上
 * - 其它文件：按内容区分 —— 出现 mcp 配置键 vs 出现 hook 事件名 / 插件声明
 * - 兜底追溯：配置里指向的脚本含 OV 逻辑 → 该 hook 处理器已接（WorkBuddy 的 run-ov-hook.sh 靠这一步）
 */
function probePath(target, depth = 0) {
  let st;
  try {
    st = statSync(target);
  } catch {
    return { exists: false, mcp: false, hook: false, via: null };
  }

  if (st.isDirectory()) {
    if (/openviking/i.test(basename(target))) return { exists: true, mcp: true, hook: true, via: null };
    if (depth < 2) {
      let entries = [];
      try {
        entries = readdirSync(target, { withFileTypes: true });
      } catch {
        /* ignore */
      }
      for (const e of entries.slice(0, 60)) {
        const sub = probePath(join(target, e.name), depth + 1);
        if (sub.mcp || sub.hook) return { ...sub, via: sub.via || join(target, e.name) };
      }
    }
    return { exists: true, mcp: false, hook: false, via: null };
  }

  const nameIsOV = /openviking/i.test(basename(target));
  const text = readText(target);
  if (text === null) return { exists: true, mcp: null, hook: null, via: null };

  if (!nameIsOV && !OV_RE.test(text)) {
    // 追溯配置里指向的脚本
    const seen = new Set();
    for (const m of text.matchAll(SCRIPT_RE)) {
      const raw = m[1];
      if (seen.has(raw) || seen.size > 12) continue;
      seen.add(raw);
      const scriptText = readText(raw);
      if (scriptText && OV_RE.test(scriptText)) {
        return { exists: true, mcp: false, hook: true, via: raw, scriptOnly: true };
      }
    }
    return { exists: true, mcp: false, hook: false, via: null };
  }

  if (nameIsOV) return { exists: true, mcp: true, hook: true, via: null };

  const mcp = /(mcpServers|mcp_servers|mcp\.servers|"mcp"\s*:|\[mcp_servers)/i.test(text);
  const hook =
    /(SessionStart|UserPromptSubmit|PreInvocation|PostInvocation|PreCompact|SessionEnd|PostToolUse|PreToolUse|HOOK_EVENT|\[hooks|"hooks"\s*:)/i.test(text) ||
    /(?:plugin|extension)s?[^\n]{0,200}openviking|openviking[^\n]{0,120}(?:plugin|extension)/i.test(text);
  return { exists: true, mcp, hook, via: null };
}

/** 读 ~/.openviking/logs/<clientId>-hooks.log 的 mtime，判断链路是否还活着 */
function loadHookLogs() {
  const dir = p(".openviking", "logs");
  const map = new Map();
  let entries = [];
  try {
    entries = readdirSync(dir);
  } catch {
    return map;
  }
  for (const name of entries) {
    const m = name.match(/^(.+)-hooks\.log$/);
    if (!m) continue;
    const full = join(dir, name);
    try {
      const st = statSync(full);
      map.set(m[1], { path: full, mtime: st.mtime, size: st.size });
    } catch {
      /* ignore */
    }
  }
  return map;
}

const daysAgo = (d) => Math.floor((Date.now() - new Date(d).getTime()) / 86400000);

const LOGS = loadHookLogs();

// ---------------------------------------------------------------- 探测

function probeHost(name) {
  const host = HOSTS[name];
  const findings = [];
  let anyPathExists = false;
  let mcpHit = false;
  let hookHit = false;
  let unknown = false;

  for (const probe of host.probes) {
    const res = probePath(probe.path);
    if (!res.exists) {
      findings.push({ ...probe, exists: false, mcp: false, hook: false, via: null });
      continue;
    }
    anyPathExists = true;
    if (res.mcp === null || res.hook === null) unknown = true;
    findings.push({ ...probe, exists: true, mcp: res.mcp === true, hook: res.hook === true, via: res.via });
    if (res.mcp === true && (probe.layer === "mcp" || probe.layer === "both")) mcpHit = true;
    if (res.hook === true && (probe.layer === "hook" || probe.layer === "both")) hookHit = true;
  }

  let verdict;
  if (!anyPathExists) verdict = "not-found";
  else if (hookHit) verdict = "integrated";
  else if (mcpHit) verdict = "mcp-only";
  else verdict = unknown ? "indeterminate" : "not-integrated";

  const log = host.clientId ? LOGS.get(host.clientId) : null;

  return { name, label: host.label, official: host.official, prefix: host.prefix, sharedPrefixWith: host.sharedPrefixWith, verdict, findings, log };
}

function printHost(r) {
  const badge = {
    integrated: "✅ integrated ",
    "mcp-only": "⚠️  mcp-only   ",
    "not-integrated": "❌ not-integrated",
    "not-found": "—  not-found ",
    indeterminate: "?  indeterminate",
  }[r.verdict];

  let stale = "";
  if (r.log) {
    const d = daysAgo(r.log.mtime);
    // 该日志只在宿主开了 hook debug 时才写（debugLogPath 未配置时是 noop）。
    // 文件近乎空 → mtime 极旧属于正常，不能当作"链路失效"的证据；否则会误报。
    const nearEmpty = (r.log.size ?? 0) < 500;
    stale = nearEmpty
      ? "  日志近乎空（未开 hook debug，不能据此判断失效）"
      : d > STALE_DAYS
        ? `  ⏸ 日志 ${d} 天未更新`
        : `  日志 ${d === 0 ? "今日" : `${d} 天前`}更新`;
  }

  console.log(`\n${badge}  [${r.name}] ${r.label}${stale}`);
  console.log(`  官方 install.sh: ${r.official ? "支持" : "不支持（需自建/装配）"}   会话前缀: ${r.prefix || "未登记"}`);
  if (Array.isArray(r.sharedPrefixWith) && r.sharedPrefixWith.length) {
    console.log(`  ⚠️  前缀 ${r.prefix} 与 ${r.sharedPrefixWith.join(" / ")} **共用** → 服务端无法区分，`);
    console.log(`      按前缀统计会张冠李戴。用 ov-session-audit.mjs --local-sessions 做 UUID 反向定归属。`);
  }
  for (const f of r.findings) {
    const mark = !f.exists ? "  " : f.mcp || f.hook ? "● " : "○ ";
    const flags = f.exists ? `[${f.mcp ? "M" : "-"}${f.hook ? "H" : "-"}]` : "";
    const tail = f.via ? `   ← 经 ${f.via}` : "";
    console.log(`  ${mark}${String(f.layer).padEnd(5)} ${flags.padEnd(6)} ${f.path}${tail}`);
  }
  if (r.verdict === "mcp-only") {
    console.log("  ⚠️  只有只读层：模型能 search，但会话不会入库 → 建议补 hooks");
  }
  if (r.verdict === "not-integrated" && r.findings.some((f) => f.layer === "pkg" && f.exists)) {
    console.log("  ℹ️  集成包已就位，但宿主配置里没有注册 → 需要补注册（或注册已被覆盖）");
  }
}

function scanGeneric(dirRaw) {
  const root = resolve(dirRaw.replace(/^~(?=$|[/\\])/, H));
  if (!existsSync(root)) {
    console.log(`路径不存在：${root}`);
    return;
  }
  console.log(`\n扫描 ${root}`);
  const found = [];
  const walk = (d, depth) => {
    if (depth > 2) return;
    let entries = [];
    try {
      entries = readdirSync(d, { withFileTypes: true });
    } catch {
      return;
    }
    for (const e of entries) {
      if (e.isDirectory()) {
        if (/node_modules|\.git$|cache|logs|artifacts|projects|sessions/i.test(e.name)) continue;
        walk(join(d, e.name), depth + 1);
      } else if (CANDIDATE_NAMES.includes(e.name.toLowerCase())) {
        found.push(join(d, e.name));
      }
    }
  };
  walk(root, 0);

  if (!found.length) {
    console.log("  未发现常见配置文件。该宿主可能用其它命名 —— 查它官方文档里的 hook / MCP 配置路径。");
    return;
  }
  for (const f of found) {
    const res = probePath(f);
    const mark = res.mcp || res.hook ? "● 含 OV" : res.mcp === null ? "? 过大未读" : "○ 无痕迹";
    const tail = res.via ? `   ← 经 ${res.via}` : "";
    console.log(`  ${mark}  ${f}${tail}`);
  }
  console.log("\n下一步：打开命中的文件，区分 MCP 注册还是 hook 注册，据此判层，再对照 references/host-contract.md 核实契约。");
}

// ---------------------------------------------------------------- 入口

const args = process.argv.slice(2);
if (!args.length || args[0] === "--help" || args[0] === "-h") {
  console.log("用法：ov-agent-probe.mjs <agent> | --all | --list | --scan <dir>");
  process.exit(0);
}
if (args[0] === "--list") {
  for (const [k, v] of Object.entries(HOSTS)) console.log(`${k.padEnd(12)} ${v.label}`);
  process.exit(0);
}
if (args[0] === "--all") {
  const results = Object.keys(HOSTS).map(probeHost);
  results.forEach(printHost);
  console.log("\n—— 汇总 ——");
  for (const v of ["integrated", "mcp-only", "not-integrated", "indeterminate", "not-found"]) {
    const names = results.filter((r) => r.verdict === v).map((r) => r.name);
    if (names.length) console.log(`${v.padEnd(16)} ${names.join(", ")}`);
  }
  // 日志近乎空 = 宿主没开 hook debug，其 mtime 旧属正常，**不能**作为「无活动」的证据。
  // （zcode 就踩过：日志仅 1 行却报「26 天未更新」，实际链路是好的。）
  const stale = results.filter(
    (r) => r.verdict === "integrated" && r.log && (r.log.size ?? 0) >= 500 && daysAgo(r.log.mtime) > STALE_DAYS,
  );
  const logUnusable = results.filter(
    (r) => r.verdict === "integrated" && r.log && (r.log.size ?? 0) < 500,
  );
  if (stale.length) {
    console.log(`\n⏸  配置在但近期无活动：${stale.map((r) => r.name).join(", ")}`);
    console.log(`   （可能是最近没用；也可能是静默失效 —— 查解释器路径与日志）`);
  }
  if (logUnusable.length) {
    console.log(`\n· 日志不可作判据（近乎空 = 未开 hook debug）：${logUnusable.map((r) => r.name).join(", ")}`);
    console.log(`   要判断这些宿主的活性，改用服务端审计：ov-session-audit.mjs --agent <名字>`);
  }
  process.exit(0);
}
if (args[0] === "--scan") {
  if (!args[1]) {
    console.log("--scan 需要目录参数");
    process.exit(1);
  }
  scanGeneric(args[1]);
  process.exit(0);
}
const name = args[0];
if (!HOSTS[name]) {
  console.log(`未知宿主 "${name}"。已知键名：${Object.keys(HOSTS).join(", ")}`);
  console.log("新宿主请用通用扫描：--scan <该宿主的配置目录>");
  process.exit(1);
}
printHost(probeHost(name));
