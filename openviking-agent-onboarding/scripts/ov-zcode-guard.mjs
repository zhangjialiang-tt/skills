#!/usr/bin/env node
/**
 * ZCode × OpenViking 注册守卫。
 *
 * 为什么需要这个脚本：
 *   ZCode 的用户级 hook 源**唯一**——`~/.zcode/cli/config.json` 的 `hooks.events`
 *   和 `mcp.servers`（源码依据：userConfigPath ?? join(home, ".zcode", "cli", "config.json")）。
 *   但 provider 管理工具（如 EasyCLIProxyAPI / cpa-gui）会成对重写
 *   `cli/config.json` + `v2/config.json`，只写它认识的 model/provider 两段，
 *   把 hooks / mcp / plugins 一起抹掉。2026-09-20 10:43 就发生过一次，
 *   导致 9/20 起 hookCount 归零、zc- 会话停止落库。
 *   → 所以每次动过 provider 配置后，用本脚本把注册补回来。
 *
 * 用法：
 *   node ov-zcode-guard.mjs            # 只检查，不改动（默认）
 *   node ov-zcode-guard.mjs --fix      # 缺失则修复（修复前自动备份）
 *   node ov-zcode-guard.mjs --json     # 机器可读输出
 *
 * 设计要点：
 *   - 幂等：重复运行不会产生重复 group（先剔除 OV 归属的 group 再追加）
 *   - 只增不删：保留 config.json 里 model / provider / plugins 等其它键
 *   - matcher 用 ".*"，见下方 MATCHER 注释
 *   - JSON 解析失败时拒绝写入，绝不覆盖损坏文件
 */

import { copyFileSync, existsSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const HOME = homedir();
const INTEGRATION_ROOT = join(HOME, ".openviking", "agent-integrations", "zcode").replaceAll("\\", "/");
const CONFIG_PATH = join(HOME, ".zcode", "cli", "config.json");

const argv = process.argv.slice(2);
const FIX = argv.includes("--fix");
const JSON_OUT = argv.includes("--json");

/**
 * matcher 取值说明（这是本脚本最容易被改错的地方）：
 *   - SessionStart 不写 matcher（zcode 侧等价于任何 matcher 为空的形式）
 *   - UserPromptSubmit / Stop 用 ".*"
 *     模板文件 `hooks/hooks.json` 里写的是 ""，但 zcode 的 toZCodeHooksEvents()
 *     会把 falsy 的 matcher 省略掉（{...n.matcher ? {matcher} : {}}），
 *     该语义未经实测；而 ".*" 是本机实际跑通过的写法（hookCount=2 且
 *     hook 阶段有真实耗时、服务端有落库），故以已验证配置为准。
 *   - PreToolUse 用工具名正则
 */
const DESIRED_GROUPS = [
  ["SessionStart", null, "session-start.mjs", 30000],
  ["UserPromptSubmit", ".*", "auto-recall.mjs", 20000],
  ["PreToolUse", "Read|Glob|Grep", "uri-guard.mjs", 5000],
  ["Stop", ".*", "auto-capture.mjs", 30000],
];

const INTEGRATION_ENV = {
  OPENVIKING_INTEGRATION_ID: "openviking-memory",
  OPENVIKING_INTEGRATION_VERSION: "0.1.1",
  OPENVIKING_HOOK_SOURCE: "zcode",
};

const report = { configPath: CONFIG_PATH, integrationRoot: INTEGRATION_ROOT, checks: [], changed: false, errors: [] };

function addCheck(name, ok, detail) {
  report.checks.push({ name, ok, detail });
}

function hookEntry(script, timeoutMs) {
  return { type: "process", command: "node", args: [`${INTEGRATION_ROOT}/scripts/${script}`], timeoutMs };
}

// ---------- 1. 集成包完整性 ----------

const REQUIRED_FILES = [
  ["hooks/hooks.json", "hook 模板"],
  ["scripts/session-start.mjs", "SessionStart 入口"],
  ["scripts/auto-recall.mjs", "UserPromptSubmit 入口"],
  ["scripts/auto-capture.mjs", "Stop 入口"],
  ["scripts/uri-guard.mjs", "PreToolUse 入口"],
  ["scripts/shared/agent-hook-runtime.mjs", "共享运行时"],
  ["servers/mcp-proxy.mjs", "MCP stdio 代理"],
];

const missingFiles = REQUIRED_FILES.filter(([rel]) => !existsSync(join(INTEGRATION_ROOT, rel)));
addCheck(
  "集成包完整",
  missingFiles.length === 0,
  missingFiles.length === 0
    ? `${REQUIRED_FILES.length} 个必需文件齐全`
    : `缺失 ${missingFiles.map(([r]) => r).join(", ")}（需重跑官方 install.sh --harness zcode）`,
);

// ---------- 2. 共享运行时是否可加载 ----------

try {
  const mod = await import(`file:///${join(INTEGRATION_ROOT, "scripts/shared/agent-hook-runtime.mjs").replaceAll("\\", "/")}`);
  const names = Object.keys(mod);
  addCheck("共享运行时可加载", names.length > 0, `导出 ${names.length} 个符号`);
} catch (err) {
  addCheck("共享运行时可加载", false, `import 失败：${err.message}`);
}

// ---------- 3. 凭据可读 ----------

const credPath = join(HOME, ".openviking", "ovcli.conf");
try {
  const cred = JSON.parse(readFileSync(credPath, "utf8"));
  const hasKey = typeof cred.api_key === "string" && cred.api_key.length > 0;
  const hasUrl = typeof cred.url === "string" && cred.url.length > 0;
  addCheck("凭据可读", hasKey && hasUrl, `url=${cred.url ?? "(缺失)"} api_key=${hasKey ? "已设置" : "缺失"}`);
} catch (err) {
  addCheck("凭据可读", false, `读取 ${credPath} 失败：${err.message}`);
}

// ---------- 4. `node` 是否可由 PATH 解析 ----------
// hook 与 MCP 都写成 command:"node"，依赖 zcode 进程的 PATH。
// 注意：这里探测的是本脚本的 PATH，与 zcode GUI 进程未必一致，仅作参考。

try {
  const { execFileSync } = await import("node:child_process");
  const cmd = process.platform === "win32" ? "where" : "which";
  const out = execFileSync(cmd, ["node"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] })
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter(Boolean);
  addCheck("node 可解析", out.length > 0, out[0] ?? "未找到");
} catch {
  addCheck("node 可解析", false, "PATH 中未找到 node —— hook 与 MCP 都会静默失效");
}

// ---------- 5. config.json 注册状态 ----------

let config = null;
if (!existsSync(CONFIG_PATH)) {
  addCheck("config.json 存在", false, `${CONFIG_PATH} 不存在`);
} else {
  try {
    config = JSON.parse(readFileSync(CONFIG_PATH, "utf8"));
    addCheck("config.json 存在", true, `${statSync(CONFIG_PATH).size} 字节`);
  } catch (err) {
    addCheck("config.json 存在", false, `JSON 解析失败，拒绝覆盖：${err.message}`);
    report.errors.push(`config.json 损坏，已中止：${err.message}`);
  }
}

const ownedByOV = (group) =>
  JSON.stringify(group).includes("agent-integrations/zcode") || JSON.stringify(group).includes("openviking-memory");

if (config) {
  const events = config.hooks?.events ?? {};
  const present = [];
  const missing = [];
  for (const [event, matcher, script, timeoutMs] of DESIRED_GROUPS) {
    const hit = (events[event] ?? []).find(
      (g) => ownedByOV(g) && JSON.stringify(g).includes(script) && (g.matcher ?? null) === matcher,
    );
    (hit ? present : missing).push(event);
    void timeoutMs;
  }
  addCheck(
    "hooks 注册",
    missing.length === 0,
    missing.length === 0 ? `${present.length}/4 事件齐全` : `缺失/不匹配：${missing.join(", ")}`,
  );

  const mcpServer = config.mcp?.servers?.openviking;
  addCheck(
    "MCP 注册",
    Boolean(mcpServer && JSON.stringify(mcpServer).includes("mcp-proxy.mjs")),
    mcpServer ? `stdio → ${mcpServer.args?.[0] ?? "?"}` : "mcp.servers.openviking 缺失",
  );

  if (config.hooks && config.hooks.enabled !== true) {
    addCheck("hooks.enabled", false, `当前为 ${JSON.stringify(config.hooks.enabled)}`);
  }
}

// ---------- 6. 修复 ----------

if (FIX && config && report.checks.some((c) => !c.ok && ["hooks 注册", "MCP 注册", "hooks.enabled"].includes(c.name))) {
  const backupPath = `${CONFIG_PATH}.pre-guard-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.bak`;
  try {
    copyFileSync(CONFIG_PATH, backupPath);
    report.backupPath = backupPath;

    config.hooks = config.hooks ?? {};
    config.hooks.enabled = true;
    config.hooks.events = config.hooks.events ?? {};
    for (const [event, matcher, script, timeoutMs] of DESIRED_GROUPS) {
      const kept = (config.hooks.events[event] ?? []).filter((g) => !ownedByOV(g));
      const group = matcher === null ? { hooks: [hookEntry(script, timeoutMs)] } : { matcher, hooks: [hookEntry(script, timeoutMs)] };
      config.hooks.events[event] = [...kept, group];
    }

    config.mcp = config.mcp ?? {};
    config.mcp.servers = config.mcp.servers ?? {};
    const existing = config.mcp.servers.openviking;
    if (existing && !JSON.stringify(existing).includes("openviking-memory")) {
      throw new Error("mcp.servers.openviking 已存在且不属于 OpenViking，拒绝覆盖");
    }
    config.mcp.servers.openviking = {
      type: "stdio",
      command: "node",
      args: [`${INTEGRATION_ROOT}/servers/mcp-proxy.mjs`],
      env: INTEGRATION_ENV,
    };

    writeFileSync(CONFIG_PATH, `${JSON.stringify(config, null, 2)}\n`);
    report.changed = true;
  } catch (err) {
    report.errors.push(`修复失败：${err.message}`);
  }
}

// ---------- 输出 ----------

if (JSON_OUT) {
  console.log(JSON.stringify(report, null, 2));
} else {
  console.log(`ZCode × OpenViking 注册守卫${FIX ? "（修复模式）" : "（只检查）"}`);
  console.log(`  config : ${CONFIG_PATH}`);
  console.log(`  集成包 : ${INTEGRATION_ROOT}`);
  console.log();
  for (const c of report.checks) {
    console.log(`  ${c.ok ? "✅" : "⚠️ "} ${c.name.padEnd(14)} ${c.detail}`);
  }
  console.log();
  if (report.changed) {
    console.log(`  已修复。备份：${report.backupPath}`);
    console.log("  重启 ZCode 后生效；用 ov-session-audit.mjs 观察 zc- 是否恢复落库。");
  } else if (!FIX && report.checks.some((c) => !c.ok)) {
    console.log("  检测到问题。加 --fix 参数执行修复。");
  } else {
    console.log("  无需修复。");
  }
  for (const e of report.errors) console.log(`  ❌ ${e}`);
}

process.exit(report.errors.length > 0 || report.checks.some((c) => !c.ok) ? 1 : 0);
