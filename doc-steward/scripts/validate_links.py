#!/usr/bin/env python3
"""validate_links.py — check dependencies, detect conflicts, and surface drift.

Implements the rules from spec §2 (fact source, conflict detection,
supersede semantics, drift detection). Outputs a JSON report to stdout.

Usage:
    python validate_links.py [--root .] [--registry .doc-steward/registry.yaml]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _core import (
    ValidationResult,
    detect_conflicts,
    find_project_root,
    load_registry,
    registry_path,
)


def validate(registry: dict) -> ValidationResult:
    result = ValidationResult()

    # 1. Conflicts: ≥2 ACTIVE/FROZEN + source_of_truth on same domain (spec §2.2)
    result.conflicts = detect_conflicts(registry)

    # 2. Stale dependencies: depends_on doc that is SUPERSEDED (spec §2.3 (6))
    superseded_ids = {
        d.get("doc_id")
        for d in registry.get("documents", [])
        if d.get("status") == "SUPERSEDED"
    }
    for doc in registry.get("documents", []):
        if doc.get("status") not in ("ACTIVE", "FROZEN"):
            continue
        deps = doc.get("depends_on") or []
        if any(dep in superseded_ids for dep in deps):
            doc["stale_dependency"] = True
            result.stale_dependencies.append(doc.get("doc_id"))
        elif doc.get("stale_dependency") and not any(
            dep in superseded_ids for dep in deps
        ):
            # Clear stale flag if deps were fixed
            doc["stale_dependency"] = False

    # 3. Invariant checks
    seen_ids = set()
    for doc in registry.get("documents", []):
        doc_id = doc.get("doc_id")

        # I1: unique doc_id
        if doc_id in seen_ids:
            result.errors.append(f"duplicate doc_id: {doc_id}")
        seen_ids.add(doc_id)

        status = doc.get("status")

        # I3: SUPERSEDED → superseded_by present and valid
        if status == "SUPERSEDED":
            sb = doc.get("superseded_by")
            if not sb:
                result.errors.append(f"{doc_id}: SUPERSEDED without superseded_by")
            elif not (isinstance(sb, str) and "@r" in sb):
                result.errors.append(f"{doc_id}: malformed superseded_by: {sb}")

        # I4: ARCHIVED → archive present with triple
        if status == "ARCHIVED":
            arch = doc.get("archive")
            if not arch:
                result.errors.append(f"{doc_id}: ARCHIVED without archive block")
            else:
                for key in ("reason", "archived_at", "last_status"):
                    if not arch.get(key):
                        result.errors.append(
                            f"{doc_id}: ARCHIVED archive missing {key}"
                        )

        # I5: FROZEN + content hash drift — flag for operator attention
        # (we do not modify; only report)
        if status == "FROZEN" and doc.get("stale"):
            result.drifts.append(
                f"{doc_id}: FROZEN but content changed since last revision"
            )

    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate registry links and invariants.")
    p.add_argument("--root", default=".")
    p.add_argument("--registry")
    p.add_argument("--output", help="write JSON report to file instead of stdout")
    args = p.parse_args(argv)

    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)
    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1

    registry = load_registry(reg_path)
    result = validate(registry)

    report = {
        "valid": not (result.errors or result.conflicts),
        "conflicts": [
            {"domain": c.domain, "contenders": c.contenders}
            for c in result.conflicts
        ],
        "stale_dependencies": result.stale_dependencies,
        "drifts": result.drifts,
        "errors": result.errors,
    }
    out = json.dumps(report, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(out + "\n", encoding="utf-8")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
