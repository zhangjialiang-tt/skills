#!/usr/bin/env python3
"""Project-level zvec-grep (zg) setup: ignore, index, agent MCP, verify."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

BEGIN = "# zg-agent-setup:begin"
END = "# zg-agent-setup:end"
MCP_NAME = "zvec_grep"
DEFAULT_IGNORE = [
    "**/*_bak*",
    "**/*_bak.*",
    ".worktrees/**",
]
SUPPORTED_AGENTS = ("codex", "claude", "opencode", "cursor", "qwen", "qoder")


class Result:
    def __init__(self) -> None:
        self.steps: list[dict[str, Any]] = []

    def add(self, name: str, ok: bool, detail: str = "", **extra: Any) -> None:
        item = {"step": name, "ok": ok, "detail": detail, **extra}
        self.steps.append(item)
        print(f"[{'OK' if ok else 'FAIL'}] {name}: {detail}")

    def to_dict(self) -> dict[str, Any]:
        return {"steps": self.steps, "ok": all(s["ok"] for s in self.steps)}


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 180) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
        return p.returncode, out.strip()
    except FileNotFoundError as e:
        return 127, str(e)
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s: {' '.join(cmd)}"


_ZG_BIN: str | None = None


def ensure_zg() -> str:
    global _ZG_BIN
    if _ZG_BIN:
        return _ZG_BIN
    zg = which("zg")
    if not zg:
        raise SystemExit("zg not found in PATH; install @zvec/zvec-grep first")
    _ZG_BIN = zg
    return zg


def ensure_ignore(root: Path, extra: list[str], force: bool = False) -> Path:
    path = root / ".zgignore"
    rules = DEFAULT_IGNORE + [r for r in extra if r.strip()]
    block = BEGIN + "\n" + "\n".join(rules) + "\n" + END
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(
        re.escape(BEGIN) + r".*?" + re.escape(END),
        re.DOTALL,
    )
    if pattern.search(old):
        new = pattern.sub(block, old, count=1)
    elif old.strip():
        sep = "" if old.endswith("\n") else "\n"
        new = old + sep + "\n" + block + "\n"
    else:
        new = block + "\n"
    if new != old or force:
        path.write_text(new, encoding="utf-8")
    return path


def cmd_status(root: Path) -> tuple[bool, str]:
    rc, out = run([ensure_zg(), "status"], cwd=root, timeout=60)
    low = out.lower()
    # "needs an update" means the workspace changed after last index; not a hard failure
    ok = rc == 0 and ("ready" in low or "needs an update" in low or "updating" in low)
    return ok, out


def cmd_index(root: Path, rebuild: bool = False) -> tuple[bool, str]:
    args = [ensure_zg(), "index"]
    if rebuild:
        args.append("--rebuild")
    rc, out = run(args, cwd=root, timeout=900)
    return rc == 0, out


def cmd_query_smoke(root: Path, query: str) -> tuple[bool, str]:
    rc, out = run(
        [ensure_zg(), "query", "--human", query, "--limit", "3"],
        cwd=root,
        timeout=120,
    )
    ok = rc == 0 and ("Hits:" in out or "hits:" in out.lower() or "File:" in out)
    return ok, out


# --- MCP writers (idempotent, preserve foreign keys) ---


def merge_json_mcp(path: Path, server_obj: dict[str, Any], top_key: str = "mcpServers") -> bool:
    data: dict[str, Any] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            backup = path.with_suffix(path.suffix + ".zg-agent-setup.bak")
            shutil.copy2(path, backup)
            data = {}
    if not isinstance(data, dict):
        data = {}
    servers = data.get(top_key)
    if not isinstance(servers, dict):
        servers = {}
    if servers.get(MCP_NAME) == server_obj:
        return False
    servers[MCP_NAME] = server_obj
    data[top_key] = servers
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


def merge_codex_toml(path: Path) -> bool:
    """Insert [mcp_servers.zvec_grep] into project Codex config without a TOML lib."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    section = (
        f"\n[mcp_servers.{MCP_NAME}]\n"
        'command = "zg"\n'
        'args = ["server", "--stdio"]\n'
    )
    if f"[mcp_servers.{MCP_NAME}]" in text:
        # already present; leave user config intact
        return False
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text + section, encoding="utf-8")
    return True


def write_agent_mcp(root: Path, agent: str) -> dict[str, Any]:
    stdio = {"command": "zg", "args": ["server", "--stdio"]}
    if agent == "claude":
        path = root / ".mcp.json"
        changed = merge_json_mcp(path, stdio, "mcpServers")
        return {"agent": agent, "path": str(path), "changed": changed, "ok": path.exists()}
    if agent == "codex":
        path = root / ".codex" / "config.toml"
        changed = merge_codex_toml(path)
        return {"agent": agent, "path": str(path), "changed": changed, "ok": path.exists()}
    if agent == "cursor":
        path = root / ".cursor" / "mcp.json"
        changed = merge_json_mcp(path, stdio, "mcpServers")
        return {"agent": agent, "path": str(path), "changed": changed, "ok": path.exists()}
    if agent == "opencode":
        path = root / "opencode.json"
        data: dict[str, Any] = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
        mcp = data.get("mcp")
        if not isinstance(mcp, dict):
            mcp = {}
        server = {"type": "local", "command": ["zg", "server", "--stdio"], "enabled": True}
        if mcp.get(MCP_NAME) == server:
            return {"agent": agent, "path": str(path), "changed": False, "ok": True}
        mcp[MCP_NAME] = server
        data["mcp"] = mcp
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return {"agent": agent, "path": str(path), "changed": True, "ok": True}
    if agent in ("qwen", "qoder"):
        # No stable project-level MCP layout verified on this machine.
        note = root / f".zg-agent-setup-{agent}-MCP.md"
        if not note.exists():
            note.write_text(
                f"# zvec_grep MCP for {agent}\n\n"
                "Project-level MCP file format is not verified on this machine.\n"
                "Install globally with: zg install --target "
                + ("qwen" if agent == "qwen" else "qoder")
                + "\n"
                "Or configure this agent's MCP UI with command `zg` args `server --stdio`.\n",
                encoding="utf-8",
            )
        return {
            "agent": agent,
            "path": str(note),
            "changed": note.exists(),
            "ok": True,
            "e2e": "missing evidence",
            "note": "no verified project-level MCP format; wrote guidance note",
        }
    raise SystemExit(f"unsupported agent: {agent}")


def verify_agent_e2e(root: Path, agent: str, query: str) -> dict[str, Any]:
    cli = which(agent)
    if agent == "claude" and not cli:
        cli = which("claude")
    if not cli:
        return {"agent": agent, "e2e": "missing evidence", "reason": f"{agent} CLI not in PATH"}

    if agent == "claude":
        mcp_path = root / ".mcp.json"
        cmd = [
            cli,
            "-p",
            "--output-format",
            "json",
            "--mcp-config",
            str(mcp_path),
            "--strict-mcp-config",
            (
                "Use the zvec_grep_search MCP tool to search the workspace for: "
                f"{query}. Reply with the top file path only."
            ),
        ]
        rc, out = run(cmd, cwd=root, timeout=180)
        ok = rc == 0 and bool(out.strip())
        return {
            "agent": agent,
            "e2e": "pass" if ok else "fail",
            "returncode": rc,
            "preview": out[:500],
        }

    if agent == "codex":
        # Project config should be auto-loaded when cwd is project root.
        cmd = [
            cli,
            "exec",
            "--sandbox",
            "read-only",
            (
                "Call the zvec_grep MCP tool if available to search for: "
                f"{query}. Output the top matching file path. "
                "If the tool is unavailable, say TOOL_UNAVAILABLE."
            ),
        ]
        rc, out = run(cmd, cwd=root, timeout=180)
        ok = rc == 0 and "TOOL_UNAVAILABLE" not in out
        return {
            "agent": agent,
            "e2e": "pass" if ok else "fail",
            "returncode": rc,
            "preview": out[:500],
        }

    if agent == "opencode":
        if not any(which(x) for x in ("opencode",)):
            return {"agent": agent, "e2e": "missing evidence", "reason": "opencode CLI not in PATH"}
        # Best-effort; opencode CLI surface may vary by version.
        cmd = [cli, "run", f"Use zvec_grep to search: {query}. Return top file path."]
        rc, out = run(cmd, cwd=root, timeout=180)
        ok = rc == 0 and bool(out.strip())
        return {
            "agent": agent,
            "e2e": "pass" if ok else "fail",
            "returncode": rc,
            "preview": out[:500],
            "note": "best-effort opencode run; treat fail as inconclusive if CLI surface differs",
        }

    return {
        "agent": agent,
        "e2e": "missing evidence",
        "reason": f"no automated e2e runner for {agent}",
    }


def parse_agents(raw: str | None) -> list[str]:
    if not raw:
        return []
    agents = [a.strip().lower() for a in raw.replace(" ", ",").split(",") if a.strip()]
    bad = [a for a in agents if a not in SUPPORTED_AGENTS]
    if bad:
        raise SystemExit(f"unsupported agents: {bad}; supported={list(SUPPORTED_AGENTS)}")
    return agents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project-level zg setup")
    parser.add_argument(
        "command",
        choices=["all", "ensure-ignore", "index", "mcp", "verify"],
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--agents", default="", help="comma list: codex,claude,opencode,...")
    parser.add_argument("--ignore-rule", action="append", default=[], help="extra .zgignore rule")
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--no-e2e", action="store_true")
    parser.add_argument(
        "--query",
        default="main module clock reset or top-level entry",
        help="smoke/e2e search query",
    )
    parser.add_argument("--report", default="", help="write JSON report to this path")
    args = parser.parse_args(argv)

    root = Path(args.project_root).resolve()
    if not root.is_dir():
        raise SystemExit(f"project root not found: {root}")
    agents = parse_agents(args.agents)
    ensure_zg()
    result = Result()

    if args.command in ("all", "ensure-ignore"):
        path = ensure_ignore(root, args.ignore_rule)
        result.add("ensure-ignore", True, f"wrote {path}")

    if args.command in ("all", "index"):
        ok, out = cmd_index(root, rebuild=args.rebuild)
        result.add("index", ok, out[-400:] if out else "")

    if args.command in ("all", "mcp"):
        if not agents:
            result.add("mcp", False, "no --agents given")
        for agent in agents:
            info = write_agent_mcp(root, agent)
            result.add(
                f"mcp:{agent}",
                bool(info.get("ok")),
                f"{info.get('path')} changed={info.get('changed')} {info.get('note','')}",
                **{k: v for k, v in info.items() if k not in ("ok",)},
            )

    if args.command in ("all", "verify"):
        ok_status, status_out = cmd_status(root)
        result.add("zg-status", ok_status, status_out[:400])
        ok_q, q_out = cmd_query_smoke(root, args.query)
        result.add("zg-query", ok_q, "has hits" if ok_q else q_out[:400])
        if agents and not args.no_e2e:
            for agent in agents:
                info = verify_agent_e2e(root, agent, args.query)
                level = info.get("e2e", "unknown")
                result.add(
                    f"e2e:{agent}",
                    level in ("pass", "missing evidence"),
                    json.dumps(info, ensure_ascii=False)[:500],
                    e2e=level,
                )
        elif agents and args.no_e2e:
            result.add("e2e", True, "skipped (--no-e2e)")

    report = result.to_dict()
    report["project_root"] = str(root)
    report["agents"] = agents
    if args.report:
        Path(args.report).write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # missing evidence still exits 0 if config/zg itself succeeded
    hard_fail = any(not s["ok"] for s in result.steps if not str(s.get("step", "")).startswith("e2e:"))
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
