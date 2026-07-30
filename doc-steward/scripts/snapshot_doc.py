#!/usr/bin/env python3
"""snapshot_doc.py — save a pre-edit snapshot of a document's current content.

Snapshots are written under `.doc-steward/snapshots/<doc_id>/<revision>-<hash8>.md`.
Invoked automatically by the Skill before any content mutation to guarantee
recoverability (spec §1.6).

Usage:
    python snapshot_doc.py <doc_id> [--registry .doc-steward/registry.yaml] [--root .]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from _core import (
    find_doc,
    find_project_root,
    hash_file,
    load_registry,
    registry_path,
    snapshots_dir,
)


def snapshot(project_root: Path, registry: dict, doc_id: str) -> Path:
    doc = find_doc(registry, doc_id)
    if doc is None:
        raise KeyError(f"doc_id not found in registry: {doc_id}")

    src = project_root / doc["path"]
    if not src.exists():
        raise FileNotFoundError(f"document file missing: {src}")

    content_hash = hash_file(src)
    revision = doc.get("revision", 1)

    dest_dir = snapshots_dir(project_root) / doc_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"r{revision}-{content_hash[:8]}.md"

    if not dest.exists():
        shutil.copy2(src, dest)

    # Write a sidecar meta file
    meta = dest.with_suffix(".meta.yaml")
    if not meta.exists():
        import yaml
        meta.write_text(
            yaml.dump(
                {
                    "doc_id": doc_id,
                    "revision": revision,
                    "content_hash": content_hash,
                    "status": doc.get("status"),
                    "path": doc["path"],
                },
                default_flow_style=False,
            ),
            encoding="utf-8",
        )

    return dest


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Save a snapshot of a document.")
    p.add_argument("doc_id")
    p.add_argument("--root", default=".")
    p.add_argument("--registry")
    args = p.parse_args(argv)

    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)
    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1

    registry = load_registry(reg_path)
    try:
        dest = snapshot(root, registry, args.doc_id)
    except (KeyError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
