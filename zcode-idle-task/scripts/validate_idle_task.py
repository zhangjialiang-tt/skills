"""Validate a ZCode idle-task contract.

Usage:
    python validate_idle_task.py path/to/task.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED = (
    "title",
    "workspace",
    "objective",
    "scope",
    "deliverables",
    "constraints",
    "acceptance",
    "stop_conditions",
)

LIST_FIELDS = ("scope", "deliverables", "constraints", "acceptance", "stop_conditions")

VALID_PERMISSIONS = {"read_only", "modify_files", "modify_and_commit"}


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    # ── Required fields exist and are non-empty ──────────
    for key in REQUIRED:
        value = payload.get(key)
        if value is None or value == "" or value == []:
            errors.append(f"missing or empty field: {key}")

    # ── List fields must be lists of non-empty strings ───
    for key in LIST_FIELDS:
        val = payload.get(key)
        if val is None:
            continue  # already reported as missing
        if not isinstance(val, list):
            errors.append(f"field must be a list: {key}")
            continue
        for i, item in enumerate(val):
            if not isinstance(item, str) or item.strip() == "":
                errors.append(f"{key}[{i}] must be a non-empty string")

    # ── Title quality ────────────────────────────────────
    title = payload.get("title")
    if isinstance(title, str):
        if len(title.strip()) < 8:
            errors.append("title too short (min 8 chars), avoid vague labels like '帮我看看'")
        vague = ("帮我看看", "全面检查", "全面优化", "分析工程")
        if any(v in title for v in vague):
            errors.append(f"title too vague, avoid generic labels")

    # ── Workspace path format ────────────────────────────
    ws = payload.get("workspace")
    if isinstance(ws, str) and ws.strip():
        if not (ws.startswith("/") or ws.startswith("C:\\") or ws.startswith("D:\\")
                or ws.startswith("./") or "/" in ws):
            errors.append("workspace should be an absolute or relative path, not a bare name")

    # ── Execution block ──────────────────────────────────
    execution = payload.get("execution", {})
    if execution and not isinstance(execution, dict):
        errors.append("field must be an object: execution")
    elif isinstance(execution, dict):
        perm = execution.get("permission")
        if perm is not None and perm not in VALID_PERMISSIONS:
            errors.append(f"unsupported execution.permission: {perm} (expected one of {VALID_PERMISSIONS})")

    # ── Permission-specific constraints ──────────────────
    perm = payload.get("execution", {}).get("permission", "read_only") if isinstance(execution, dict) else "read_only"
    joined = " ".join(str(item).lower() for item in payload.get("constraints", []))

    if perm == "read_only":
        if not any(token in joined for token in ("不修改", "只读", "read-only", "read_only")):
            errors.append("read_only task must state its no-modification constraint")
    elif perm == "modify_files":
        if not any(token in joined for token in ("只修改", "允许修改", "modify", "allowed_files")):
            errors.append("modify_files task must list allowed files in constraints")
    elif perm == "modify_and_commit":
        if not any(token in joined for token in ("提交", "commit", "提交范围")):
            errors.append("modify_and_commit task must specify commit scope in constraints")
        if not any(token in joined for token in ("不push", "不 push", "no push", "不reset")):
            errors.append("modify_and_commit task must state no-push/no-reset constraint")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_idle_task.py TASK_JSON", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict):
        print("ERROR: task contract must be a JSON object", file=sys.stderr)
        return 2

    errors = validate(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("PASS: ZCode idle-task contract is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
