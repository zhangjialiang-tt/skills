#!/usr/bin/env python3
"""generate_diff.py — generate an L2 revision diff summary.

Compares two snapshot files (or a snapshot against the current document)
and emits a structured markdown summary suitable for the "只需了解变化"
bucket in the dashboard. The summary is pure text; the Skill wraps it
with provenance metadata.

Usage:
    python generate_diff.py <doc_id> [--from-rev N] [--to-rev M] [--root .]
"""

from __future__ import annotations

import argparse
import difflib
import sys
from datetime import date
from pathlib import Path

from _core import (
    find_doc,
    find_project_root,
    load_registry,
    registry_path,
    snapshots_dir,
)


def _read(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def _snapshot_for(snap_dir: Path, revision: int) -> Path | None:
    if not snap_dir.exists():
        return None
    candidates = sorted(snap_dir.glob(f"r{revision}-*.md"))
    return candidates[0] if candidates else None


def generate_diff(
    project_root: Path,
    registry: dict,
    doc_id: str,
    from_revision: int | None = None,
    to_revision: int | None = None,
) -> str:
    doc = find_doc(registry, doc_id)
    if doc is None:
        raise KeyError(f"doc_id not found: {doc_id}")

    revision = doc.get("revision", 1)
    snap_dir = snapshots_dir(project_root) / doc_id

    # Resolve "from": previous snapshot (default: revision - 1)
    from_rev = from_revision if from_revision is not None else max(1, revision - 1)
    from_path = _snapshot_for(snap_dir, from_rev)

    # Resolve "to": current document file (default)
    to_path = project_root / doc["path"]
    if to_revision is not None:
        tagged = _snapshot_for(snap_dir, to_revision)
        if tagged is None:
            raise FileNotFoundError(f"snapshot for revision {to_revision} not found")
        to_path = tagged
    elif not to_path.exists():
        # Fall back to latest snapshot if doc file is missing (archived)
        latest = _snapshot_for(snap_dir, revision)
        if latest is None:
            raise FileNotFoundError(f"no snapshot or file for {doc_id}")
        to_path = latest

    if from_path is None or from_revision == 0:
        # No prior version — emit a "first revision" marker
        to_text = _read(to_path)
        header = (
            f"# L2 变化摘要 — {doc_id} r{revision}\n\n"
            f"> 源版本：无（首次登记）\n"
            f"> 目标版本：r{revision}\n\n"
            f"文档共 {len(to_text)} 行。\n"
        )
        return header

    from_lines = _read(from_path)
    to_lines = _read(to_path)

    diff = list(
        difflib.unified_diff(
            from_lines,
            to_lines,
            fromfile=f"{doc_id}@r{from_rev}",
            tofile=f"{doc_id}@r{revision}",
            lineterm="",
        )
    )

    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

    today = date.today().isoformat()
    summary_lines = [
        f"# L2 变化摘要 — {doc_id}",
        "",
        f"> 源版本：r{from_rev}",
        f"> 目标版本：r{revision}",
        f"> 生成日期：{today}",
        f"> +{added} / -{removed} 行",
        "",
        "```diff",
        *diff,
        "```",
    ]
    return "\n".join(summary_lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate L2 diff summary for a document.")
    p.add_argument("doc_id")
    p.add_argument("--from-rev", type=int, default=None)
    p.add_argument("--to-rev", type=int, default=None)
    p.add_argument("--root", default=".")
    args = p.parse_args(argv)

    root = Path(args.root).resolve()
    reg_path = registry_path(root)
    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1

    registry = load_registry(reg_path)
    try:
        summary = generate_diff(root, registry, args.doc_id, args.from_rev, args.to_rev)
    except (KeyError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
