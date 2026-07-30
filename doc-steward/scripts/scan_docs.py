#!/usr/bin/env python3
"""scan_docs.py — scan document_roots for new / modified / missing documents.

Outputs a JSON report to stdout (or --output file) with three buckets:
  - new:       paths on disk with no registry entry
  - modified:  registry entries whose content_hash no longer matches disk
  - missing:   registry entries whose path no longer exists on disk

Usage:
    python scan_docs.py [--root .] [--registry .doc-steward/registry.yaml] [--output report.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _core import (
    find_project_root,
    get_config,
    hash_file,
    is_excluded,
    load_registry,
    registry_path,
)


def scan(
    project_root: Path,
    registry: dict,
) -> dict[str, list[dict]]:
    config = get_config(registry)
    roots = config.get("document_roots", ["docs"])
    exclude = config.get("exclude", [])

    # Collect every markdown file under document_roots
    on_disk: dict[str, str] = {}  # rel_path -> content_hash
    for root_name in roots:
        root_dir = project_root / root_name
        if not root_dir.is_dir():
            continue
        for path in root_dir.rglob("*.md"):
            rel = path.relative_to(project_root).as_posix()
            if is_excluded(rel, exclude):
                continue
            on_disk[rel] = hash_file(path)

    registered: dict[str, dict] = {
        doc["path"]: doc for doc in registry.get("documents", [])
    }

    new = [
        {"path": p, "content_hash": h}
        for p, h in on_disk.items()
        if p not in registered
    ]
    modified = [
        {
            "path": p,
            "doc_id": registered[p].get("doc_id"),
            "registered_hash": registered[p].get("content_hash"),
            "disk_hash": h,
        }
        for p, h in on_disk.items()
        if p in registered and registered[p].get("content_hash") != h
    ]
    missing = [
        {"path": p, "doc_id": doc.get("doc_id"), "status": doc.get("status")}
        for p, doc in registered.items()
        if p not in on_disk
    ]

    return {"new": new, "modified": modified, "missing": missing}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Scan document_roots for changes.")
    p.add_argument("--root", default=".", help="project root (default: cwd)")
    p.add_argument("--registry", help="path to registry.yaml (auto-detected if omitted)")
    p.add_argument("--output", help="write JSON report to file instead of stdout")
    args = p.parse_args(argv)

    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)
    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1

    registry = load_registry(reg_path)
    report = scan(root, registry)

    out = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(out + "\n", encoding="utf-8")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
