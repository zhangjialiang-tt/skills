#!/usr/bin/env python3
"""update_registry.py — mutate registry.yaml entries with validation.

Subcommands:
    register          <path> [--title TYPE] [--domain D1,D2] [--purpose TEXT]
    promote           <doc_id> <to_status> --reason TEXT [--by user] [--at YYYY-MM-DD]
    supersede         <old_doc_id> <new_doc_id> --reason TEXT [--by user] [--at YYYY-MM-DD]
    archive           <doc_id> --reason TEXT [--by user] [--at YYYY-MM-DD]
    set               <doc_id> [--source-of-truth BOOL] [--attention-level normal|high]
                                     [--depends-on D1,D2] [--domain D1,D2]
    accept-revision   <doc_id> --reason TEXT

All mutations validate against spec §1.3 (Transition Matrix) and spec §2.3
(supersede atomicity). Tier2 transitions require `--by user` and a non-empty
`--reason`.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from _core import (
    SCHEMA_VERSION,
    assert_valid_transition,
    detect_conflicts,
    find_doc,
    find_doc_index,
    find_project_root,
    get_config,
    hash_file,
    load_registry,
    registry_path,
    save_registry,
    transition_is_tier2,
    validate_registry_against_schema,
)


def _today() -> str:
    return date.today().isoformat()


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def cmd_register(registry: dict, args: argparse.Namespace, project_root: Path) -> dict:
    """Add a new document entry (initial status always DRAFT — spec I2).
    
    Auto-saves r1 snapshot for version reconstruction.
    """
    doc_path = project_root / args.path
    if not doc_path.exists():
        raise FileNotFoundError(f"document not found: {doc_path}")
    
    # Validate path is within project root
    from _core import safe_resolve_path
    safe_resolve_path(project_root, args.path)
    
    # Deduplicate by path
    existing = find_doc(registry, args.doc_id) if args.doc_id else None
    if existing is None:
        for d in registry.get("documents", []):
            if d.get("path") == args.path:
                existing = d
                break
    if existing is not None:
        raise ValueError(
            f"path already registered: {args.path} (doc_id={existing.get('doc_id')})"
        )
    
    today = _today()
    content_hash = hash_file(doc_path)
    
    doc = {
        "doc_id": args.doc_id,
        "title": args.title or doc_path.stem,
        "path": args.path,
        "type": args.type or "other",
        "status": "DRAFT",
        "revision": 1,
        "content_hash": content_hash,
        "created_at": today,
        "updated_at": today,
        "assigned_domain": _split_csv(args.domain),
        "source_of_truth": False,
        "superseded_by": None,
        "supersedes": [],
        "depends_on": [],
        "stale": False,
        "stale_dependency": False,
        "purpose": args.purpose or "",
        "reading_hint": "",
        "attention": {"level": "normal"},
        "decision": {"by": "user", "at": today, "reason": args.reason or "initial registration"},
        "history": [],
    }
    registry.setdefault("documents", []).append(doc)
    
    # Auto-save r1 snapshot
    from snapshot_doc import snapshot as save_snapshot
    try:
        save_snapshot(project_root, registry, args.doc_id)
    except Exception as exc:
        print(f"warning: failed to save r1 snapshot: {exc}", file=sys.stderr)
    
    # Record REGISTERED event
    from _core import append_revision_event
    append_revision_event(
        registry, args.doc_id, "REGISTERED", 1, content_hash,
        args.reason or "initial registration"
    )
    
    return {"action": "register", "doc_id": args.doc_id, "status": "DRAFT"}


def cmd_promote(registry: dict, args: argparse.Namespace, project_root: Path) -> dict:
    """Transition a document's status (spec §1.3)."""
    doc = find_doc(registry, args.doc_id)
    if doc is None:
        raise KeyError(f"doc_id not found: {args.doc_id}")

    from_status = doc["status"]
    to_status = args.to_status

    assert_valid_transition(from_status, to_status)

    if transition_is_tier2(from_status, to_status):
        if args.by != "user" or not (args.reason or "").strip():
            raise ValueError(
                f"Tier2 transition {from_status} → {to_status} requires "
                f"--by user and non-empty --reason (spec §1.3)"
            )

    today = args.at or _today()
    doc["status"] = to_status
    doc["updated_at"] = today
    doc["decision"] = {"by": args.by, "at": today, "reason": args.reason or ""}

    if from_status == "FROZEN" and to_status == "ACTIVE":
        doc["stale"] = False

    return {
        "action": "promote",
        "doc_id": args.doc_id,
        "from": from_status,
        "to": to_status,
    }


def cmd_supersede(registry: dict, args: argparse.Namespace, project_root: Path) -> dict:
    """Atomically supersede old_doc with new_doc (spec §2.3)."""
    old = find_doc(registry, args.old_doc_id)
    new = find_doc(registry, args.new_doc_id)
    if old is None:
        raise KeyError(f"old doc_id not found: {args.old_doc_id}")
    if new is None:
        raise KeyError(f"new doc_id not found: {args.new_doc_id}")

    from_status = old["status"]
    assert_valid_transition(from_status, "SUPERSEDED")

    if transition_is_tier2(from_status, "SUPERSEDED"):
        if args.by != "user" or not (args.reason or "").strip():
            raise ValueError(
                "Tier2 supersede requires --by user and non-empty --reason"
            )

    today = args.at or _today()
    rev_new = new.get("revision", 1)
    superseded_by_value = f"{args.new_doc_id}@r{rev_new}"

    old["status"] = "SUPERSEDED"
    old["superseded_by"] = superseded_by_value
    old["source_of_truth"] = False
    old["updated_at"] = today
    old["decision"] = {"by": args.by, "at": today, "reason": args.reason or ""}

    new.setdefault("supersedes", [])
    old_ref = f"{args.old_doc_id}@r{old.get('revision', 1)}"
    if old_ref not in new["supersedes"]:
        new["supersedes"].append(old_ref)

    if old.get("source_of_truth") and new.get("assigned_domain"):
        new["source_of_truth"] = True

    stale_dependents = []
    for doc in registry.get("documents", []):
        if doc.get("status") not in ("ACTIVE", "FROZEN"):
            continue
        if args.old_doc_id in (doc.get("depends_on") or []):
            doc["stale_dependency"] = True
            stale_dependents.append(doc.get("doc_id"))

    return {
        "action": "supersede",
        "old_doc_id": args.old_doc_id,
        "new_doc_id": args.new_doc_id,
        "stale_dependents": stale_dependents,
    }


def cmd_archive(registry: dict, args: argparse.Namespace, project_root: Path) -> dict:
    """Archive a document (logical-only by default — spec §1.6)."""
    doc = find_doc(registry, args.doc_id)
    if doc is None:
        raise KeyError(f"doc_id not found: {args.doc_id}")

    from_status = doc["status"]
    if from_status not in ("DRAFT", "REVIEWING", "ACTIVE", "FROZEN", "SUPERSEDED"):
        raise ValueError(f"cannot archive from status {from_status}")

    today = args.at or _today()
    doc["status"] = "ARCHIVED"
    doc["updated_at"] = today
    doc["archive"] = {
        "reason": args.reason or "",
        "archived_at": today,
        "last_status": from_status,
    }
    doc["decision"] = {"by": args.by, "at": today, "reason": args.reason or ""}

    return {"action": "archive", "doc_id": args.doc_id, "last_status": from_status}


def cmd_set(registry: dict, args: argparse.Namespace, project_root: Path) -> dict:
    """Update mutable fields on a document entry."""
    doc = find_doc(registry, args.doc_id)
    if doc is None:
        raise KeyError(f"doc_id not found: {args.doc_id}")

    changed = []
    if args.source_of_truth is not None:
        doc["source_of_truth"] = args.source_of_truth
        changed.append(("source_of_truth", args.source_of_truth))
    if args.attention_level is not None:
        doc.setdefault("attention", {})["level"] = args.attention_level
        changed.append(("attention.level", args.attention_level))
    if args.depends_on is not None:
        doc["depends_on"] = _split_csv(args.depends_on)
        changed.append(("depends_on", doc["depends_on"]))
    if args.domain is not None:
        doc["assigned_domain"] = _split_csv(args.domain)
        changed.append(("assigned_domain", doc["assigned_domain"]))

    if changed:
        doc["updated_at"] = args.at or _today()

    return {"action": "set", "doc_id": args.doc_id, "changed": changed}


def cmd_accept_revision(registry: dict, args: argparse.Namespace, project_root: Path) -> dict:
    """Accept a new revision for a document.
    
    Saves current live content as snapshot rN+1, updates revision and hash.
    FROZEN documents cannot accept revisions (must unfreeze first).
    """
    doc = find_doc(registry, args.doc_id)
    if doc is None:
        raise KeyError(f"doc_id not found: {args.doc_id}")
    
    status = doc["status"]
    if status == "FROZEN":
        raise ValueError(
            f"cannot accept revision for FROZEN document: {args.doc_id}. "
            f"Unfreeze first (transition to ACTIVE)."
        )
    
    if status not in ("DRAFT", "REVIEWING", "ACTIVE"):
        raise ValueError(
            f"cannot accept revision from status {status}: {args.doc_id}"
        )
    
    from snapshot_doc import snapshot as save_snapshot
    from _core import append_revision_event
    
    # Compute new hash
    doc_path = project_root / doc["path"]
    if not doc_path.exists():
        raise FileNotFoundError(f"document file missing: {doc_path}")
    
    new_hash = hash_file(doc_path)
    old_revision = doc["revision"]
    new_revision = old_revision + 1
    
    # Update revision BEFORE snapshot so snapshot gets new revision number
    doc["revision"] = new_revision
    
    # Save snapshot with new revision number
    try:
        save_snapshot(project_root, registry, args.doc_id)
    except Exception as exc:
        # Rollback on failure
        doc["revision"] = old_revision
        raise RuntimeError(f"failed to save snapshot: {exc}")
    
    # Update registry
    doc["content_hash"] = new_hash
    doc["updated_at"] = _today()
    
    # Record event
    event = append_revision_event(
        registry, args.doc_id, "REVISION_ACCEPTED", new_revision, new_hash,
        args.reason or "revision accepted",
        from_revision=old_revision,
    )
    
    return {
        "action": "accept_revision",
        "doc_id": args.doc_id,
        "from_revision": old_revision,
        "to_revision": new_revision,
        "content_hash": new_hash,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="update_registry.py",
        description="Mutate doc-steward registry.yaml with validation.",
    )
    p.add_argument("--root", default=".", help="project root")
    p.add_argument("--registry", help="path to registry.yaml")
    p.add_argument("--dry-run", action="store_true", help="preview without saving")
    sub = p.add_subparsers(dest="cmd", required=True)

    # register
    sp = sub.add_parser("register", help="register a new document")
    sp.add_argument("path", help="relative path to document")
    sp.add_argument("--doc-id", required=True, help="stable doc_id")
    sp.add_argument("--title", help="human-readable title")
    sp.add_argument("--type", help="design|prd|plan|spec|adr|note|other")
    sp.add_argument("--domain", help="comma-separated domain keys")
    sp.add_argument("--purpose", help="L0 purpose line")
    sp.add_argument("--reason", default="initial registration")

    # promote
    sp = sub.add_parser("promote", help="transition status")
    sp.add_argument("doc_id")
    sp.add_argument("to_status", choices=["DRAFT", "REVIEWING", "ACTIVE", "FROZEN", "SUPERSEDED", "ARCHIVED"])
    sp.add_argument("--by", default="user")
    sp.add_argument("--at", help="YYYY-MM-DD (default: today)")
    sp.add_argument("--reason", default="")

    # supersede
    sp = sub.add_parser("supersede", help="atomically supersede old with new")
    sp.add_argument("old_doc_id")
    sp.add_argument("new_doc_id")
    sp.add_argument("--by", default="user")
    sp.add_argument("--at")
    sp.add_argument("--reason", default="")

    # archive
    sp = sub.add_parser("archive", help="archive a document")
    sp.add_argument("doc_id")
    sp.add_argument("--by", default="user")
    sp.add_argument("--at")
    sp.add_argument("--reason", default="")

    # set
    sp = sub.add_parser("set", help="update mutable fields")
    sp.add_argument("doc_id")
    sp.add_argument("--source-of-truth", type=lambda x: x.lower() == "true")
    sp.add_argument("--attention-level", choices=["normal", "high"])
    sp.add_argument("--depends-on", help="comma-separated doc_ids")
    sp.add_argument("--domain", help="comma-separated domain keys")
    sp.add_argument("--at")

    # accept-revision
    sp = sub.add_parser("accept-revision", help="accept a new revision")
    sp.add_argument("doc_id")
    sp.add_argument("--reason", default="revision accepted")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)

    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1

    registry = load_registry(reg_path)
    
    # Pre-validate schema
    errors = validate_registry_against_schema(registry)
    if errors:
        print("registry validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 2

    commands = {
        "register": cmd_register,
        "promote": cmd_promote,
        "supersede": cmd_supersede,
        "archive": cmd_archive,
        "set": cmd_set,
        "accept-revision": cmd_accept_revision,
    }
    try:
        result = commands[args.cmd](registry, args, root)
    except (ValueError, KeyError, FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Dry-run: don't save
    if getattr(args, "dry_run", False):
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    save_registry(reg_path, registry)

    # Re-validate conflicts after mutation
    conflicts = detect_conflicts(registry)
    result["conflicts"] = [
        {"domain": c.domain, "contenders": c.contenders} for c in conflicts
    ]

    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
