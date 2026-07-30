#!/usr/bin/env python3
"""doc_steward.py — unified CLI entry point for doc-steward.

Provides a single command-line interface for all doc-steward operations:
    doc_steward inspect    — read-only scan, output current state
    doc_steward focus      — output minimal reading set
    doc_steward sync       — sync document status (--dry-run or --apply)
    doc_steward register   — register a new document
    doc_steward transition — state migration
    doc_steward supersede   — atomic supersede
    doc_steward archive    — logical archive
    doc_steward validate   — validate registry invariants
    doc_steward dashboard  — generate dashboard
    doc_steward accept-revision — accept a new revision

Usage:
    python doc_steward.py <command> [options]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from _core import (
    ChangeSet,
    validate_registry_against_schema,
    find_project_root,
    load_registry,
    save_registry,
    registry_path,
    detect_conflicts,
)


def cmd_inspect(args: argparse.Namespace) -> int:
    """Read-only scan, output current state."""
    from scan_docs import scan
    
    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)
    
    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1
    
    registry = load_registry(reg_path)
    report = scan(root, registry)
    
    # Add schema validation
    errors = validate_registry_against_schema(registry)
    if errors:
        report["schema_errors"] = errors
    
    # Add conflicts
    conflicts = detect_conflicts(registry)
    report["conflicts"] = [
        {"domain": c.domain, "contenders": c.contenders}
        for c in conflicts
    ]
    
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


def cmd_focus(args: argparse.Namespace) -> int:
    """Output minimal reading set."""
    from scan_docs import scan
    from validate_links import validate
    
    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)
    
    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1
    
    registry = load_registry(reg_path)
    scan_report = scan(root, registry)
    validation = validate(registry)
    
    # Build focus output
    focus = {
        "blocked": [],
        "needs_attention": [],
        "change_only": [],
        "no_need": [],
    }
    
    # Schema errors are blocking
    schema_errors = validate_registry_against_schema(registry)
    for err in schema_errors:
        focus["blocked"].append({"type": "schema_error", "message": err})
    
    # Conflicts are blocking
    for conflict in validation.conflicts:
        focus["blocked"].append({
            "type": "source_of_truth_conflict",
            "domain": conflict.domain,
            "contenders": conflict.contenders,
        })
    
    # Missing files are blocking
    for missing in scan_report.get("missing", []):
        focus["blocked"].append({
            "type": "missing_file",
            "doc_id": missing.get("doc_id"),
            "path": missing.get("path"),
        })
    
    # Stale dependencies need attention
    for doc_id in validation.stale_dependencies:
        focus["needs_attention"].append({
            "doc_id": doc_id,
            "reason": "stale_dependency",
        })
    
    # Modified files need attention
    for modified in scan_report.get("modified", []):
        doc_id = modified.get("doc_id")
        if doc_id not in [d.get("doc_id") for d in focus["needs_attention"]]:
            focus["change_only"].append({
                "doc_id": doc_id,
                "path": modified.get("path"),
                "reason": "content_modified",
            })
    
    # REVIEWING status needs attention
    for doc in registry.get("documents", []):
        if doc.get("status") == "REVIEWING":
            doc_id = doc.get("doc_id")
            if doc_id not in [d.get("doc_id") for d in focus["needs_attention"]]:
                focus["needs_attention"].append({
                    "doc_id": doc_id,
                    "reason": "status_reviewing",
                })
    
    output = json.dumps(focus, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    """Sync document status."""
    from scan_docs import scan
    
    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)
    
    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1
    
    registry = load_registry(reg_path)
    
    # Pre-validate
    errors = validate_registry_against_schema(registry)
    if errors:
        print("registry validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 2
    
    report = scan(root, registry)
    
    if args.dry_run:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    
    if args.apply:
        # Accept revisions for modified documents
        from update_registry import cmd_accept_revision
        
        accepted = []
        failed = []
        
        for modified in report.get("modified", []):
            doc_id = modified.get("doc_id")
            
            class AcceptArgs:
                def __init__(self):
                    self.doc_id = doc_id
                    self.reason = "auto-accepted via sync --apply"
            
            try:
                result = cmd_accept_revision(registry, AcceptArgs(), root)
                accepted.append(result)
            except (ValueError, KeyError, FileNotFoundError, RuntimeError) as exc:
                failed.append({"doc_id": doc_id, "error": str(exc)})
        
        save_registry(reg_path, registry)
        
        output = {
            "action": "sync_apply",
            "accepted": accepted,
            "failed": failed,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0
    
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0

def cmd_register(args: argparse.Namespace) -> int:
    """Register a new document."""
    from update_registry import cmd_register
    
    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)
    
    # Load or create registry
    if reg_path.exists():
        registry = load_registry(reg_path)
        # Pre-validate
        errors = validate_registry_against_schema(registry)
        if errors:
            print("registry validation errors:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 2
    else:
        # Create new registry
        registry = {
            "version": "1.0",
            "config": {"document_roots": ["docs"], "exclude": []},
            "documents": [],
        }
        reg_path.parent.mkdir(parents=True, exist_ok=True)
    
    class RegisterArgs:
        def __init__(self):
            self.path = args.path
            self.doc_id = args.doc_id
            self.title = args.title
            self.type = args.type
            self.domain = args.domain
            self.purpose = args.purpose
            self.reason = args.reason
    
    register_args = RegisterArgs()
    
    if args.dry_run:
        cs = ChangeSet()
        cs.add("register", args.doc_id, path=args.path)
        print(json.dumps(cs.to_dict(), indent=2, ensure_ascii=False))
        return 0
    
    try:
        result = cmd_register(registry, register_args, root)
        save_registry(reg_path, registry)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

def cmd_accept_revision(args: argparse.Namespace) -> int:
    """Accept a new revision for a document."""
    from update_registry import cmd_accept_revision
    
    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)
    
    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1
    
    registry = load_registry(reg_path)
    
    # Pre-validate
    errors = validate_registry_against_schema(registry)
    if errors:
        print("registry validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 2
    
    class AcceptArgs:
        def __init__(self):
            self.doc_id = args.doc_id
            self.reason = args.reason
    
    try:
        result = cmd_accept_revision(registry, AcceptArgs(), root)
        save_registry(reg_path, registry)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_transition(args: argparse.Namespace) -> int:
    """State migration."""
    from update_registry import cmd_promote
    
    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)
    
    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1
    
    registry = load_registry(reg_path)
    
    # Pre-validate
    errors = validate_registry_against_schema(registry)
    if errors:
        print("registry validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 2
    
    class PromoteArgs:
        def __init__(self):
            self.doc_id = args.doc_id
            self.to_status = args.to_status
            self.by = args.by
            self.at = args.at
            self.reason = args.reason
    
    promote_args = PromoteArgs()
    
    if args.dry_run:
        from _core import transition_is_allowed, transition_is_tier2
        
        doc = None
        for d in registry.get("documents", []):
            if d.get("doc_id") == args.doc_id:
                doc = d
                break
        
        if doc is None:
            print(f"doc_id not found: {args.doc_id}", file=sys.stderr)
            return 1
        
        from_status = doc["status"]
        to_status = args.to_status
        
        if not transition_is_allowed(from_status, to_status):
            print(f"illegal transition: {from_status} -> {to_status}", file=sys.stderr)
            return 2
        
        cs = ChangeSet()
        cs.add("promote", args.doc_id, from_status=from_status, to_status=to_status)
        
        if transition_is_tier2(from_status, to_status):
            cs.entries[-1].details["tier2_required"] = True
            cs.entries[-1].details["approved"] = (args.by == "user" and bool(args.reason))
        
        print(json.dumps(cs.to_dict(), indent=2, ensure_ascii=False))
        return 0
    
    try:
        result = cmd_promote(registry, promote_args, root)
        save_registry(reg_path, registry)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_supersede(args: argparse.Namespace) -> int:
    """Atomic supersede."""
    from update_registry import cmd_supersede
    
    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)
    
    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1
    
    registry = load_registry(reg_path)
    
    # Pre-validate
    errors = validate_registry_against_schema(registry)
    if errors:
        print("registry validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 2
    
    class SupersedeArgs:
        def __init__(self):
            self.old_doc_id = args.old_doc_id
            self.new_doc_id = args.new_doc_id
            self.by = args.by
            self.at = args.at
            self.reason = args.reason
    
    supersede_args = SupersedeArgs()
    
    if args.dry_run:
        cs = ChangeSet()
        cs.add("supersede", args.old_doc_id, superseded_by=args.new_doc_id)
        cs.add("update_supersedes", args.new_doc_id, supersedes=args.old_doc_id)
        cs.entries[-1].details["tier2_required"] = True
        cs.entries[-1].details["approved"] = (args.by == "user" and bool(args.reason))
        
        print(json.dumps(cs.to_dict(), indent=2, ensure_ascii=False))
        return 0
    
    try:
        result = cmd_supersede(registry, supersede_args, root)
        save_registry(reg_path, registry)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_archive(args: argparse.Namespace) -> int:
    """Logical archive."""
    from update_registry import cmd_archive
    
    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)
    
    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1
    
    registry = load_registry(reg_path)
    
    # Pre-validate
    errors = validate_registry_against_schema(registry)
    if errors:
        print("registry validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 2
    
    class ArchiveArgs:
        def __init__(self):
            self.doc_id = args.doc_id
            self.by = args.by
            self.at = args.at
            self.reason = args.reason
    
    archive_args = ArchiveArgs()
    
    if args.dry_run:
        cs = ChangeSet()
        cs.add("archive", args.doc_id, reason=args.reason)
        print(json.dumps(cs.to_dict(), indent=2, ensure_ascii=False))
        return 0
    
    try:
        result = cmd_archive(registry, archive_args, root)
        save_registry(reg_path, registry)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate registry invariants."""
    root = Path(args.root).resolve()
    reg_path = Path(args.registry) if args.registry else registry_path(root)
    
    if not reg_path.exists():
        print(f"registry not found: {reg_path}", file=sys.stderr)
        return 1
    
    registry = load_registry(reg_path)
    
    errors = validate_registry_against_schema(registry)
    conflicts = detect_conflicts(registry)
    
    report = {
        "valid": not (errors or conflicts),
        "schema_errors": errors,
        "conflicts": [
            {"domain": c.domain, "contenders": c.contenders}
            for c in conflicts
        ],
    }
    
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 2


def cmd_dashboard(args: argparse.Namespace) -> int:
    """Generate dashboard."""
    print("dashboard generation not yet implemented (Milestone C)", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    p = argparse.ArgumentParser(
        prog="doc_steward.py",
        description="Unified CLI for doc-steward document governance.",
    )
    p.add_argument("--root", default=".", help="project root directory")
    p.add_argument("--registry", help="path to registry.yaml (auto-detected if omitted)")
    p.add_argument("--format", choices=["json", "text"], default="json", help="output format")
    
    sub = p.add_subparsers(dest="cmd", required=True)
    
    # inspect
    sp = sub.add_parser("inspect", help="read-only scan, output current state")
    sp.add_argument("--output", help="write output to file")
    
    # focus
    sp = sub.add_parser("focus", help="output minimal reading set")
    sp.add_argument("--output", help="write output to file")
    
    # sync
    sp = sub.add_parser("sync", help="sync document status")
    sp.add_argument("--dry-run", action="store_true", help="only detect, do not modify")
    sp.add_argument("--apply", action="store_true", help="accept detected changes")
    
    # register
    sp = sub.add_parser("register", help="register a new document")
    sp.add_argument("path", help="relative path to document")
    sp.add_argument("--doc-id", required=True, help="stable doc_id")
    sp.add_argument("--title", help="human-readable title")
    sp.add_argument("--type", help="design|prd|plan|spec|adr|note|other")
    sp.add_argument("--domain", help="comma-separated domain keys")
    sp.add_argument("--purpose", help="L0 purpose line")
    sp.add_argument("--reason", default="initial registration")
    sp.add_argument("--dry-run", action="store_true", help="preview change set")
    
    # transition
    sp = sub.add_parser("transition", help="state migration")
    sp.add_argument("doc_id", help="document ID")
    sp.add_argument("to_status", choices=["DRAFT", "REVIEWING", "ACTIVE", "FROZEN", "SUPERSEDED", "ARCHIVED"])
    sp.add_argument("--by", default="user", help="approval actor")
    sp.add_argument("--at", help="approval date (YYYY-MM-DD)")
    sp.add_argument("--reason", default="", help="migration reason")
    sp.add_argument("--dry-run", action="store_true", help="preview change set")
    
    # supersede
    sp = sub.add_parser("supersede", help="atomic supersede")
    sp.add_argument("old_doc_id", help="old document ID")
    sp.add_argument("new_doc_id", help="new document ID")
    sp.add_argument("--by", default="user", help="approval actor")
    sp.add_argument("--at", help="approval date (YYYY-MM-DD)")
    sp.add_argument("--reason", default="", help="supersede reason")
    sp.add_argument("--dry-run", action="store_true", help="preview change set")
    
    # archive
    sp = sub.add_parser("archive", help="logical archive")
    sp.add_argument("doc_id", help="document ID")
    sp.add_argument("--by", default="user", help="approval actor")
    sp.add_argument("--at", help="approval date (YYYY-MM-DD)")
    sp.add_argument("--reason", default="", help="archive reason")
    sp.add_argument("--dry-run", action="store_true", help="preview change set")
    
    # validate
    sub.add_parser("validate", help="validate registry invariants")
    
    # dashboard
    sp = sub.add_parser("dashboard", help="generate dashboard")
    sp.add_argument("--output", help="write output to file")
    
    # accept-revision
    sp = sub.add_parser("accept-revision", help="accept a new revision")
    sp.add_argument("doc_id", help="document ID")
    sp.add_argument("--reason", default="revision accepted", help="reason for accepting")
    
    return p


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    args = build_parser().parse_args(argv)
    
    commands = {
        "inspect": cmd_inspect,
        "focus": cmd_focus,
        "sync": cmd_sync,
        "register": cmd_register,
        "transition": cmd_transition,
        "supersede": cmd_supersede,
        "archive": cmd_archive,
        "validate": cmd_validate,
        "dashboard": cmd_dashboard,
        "accept-revision": cmd_accept_revision,
    }
    
    return commands[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
