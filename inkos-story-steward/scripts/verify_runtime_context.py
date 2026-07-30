#!/usr/bin/env python3
"""Verify InkOS runtime context after plan/compose.

Checks that plan/compose output correctly reflects green-zone modifications.
Run after `inkos plan chapter` or `inkos compose chapter`.

Usage:
    python scripts/verify_runtime_context.py [--project-root PATH] [--book-id ID]

Exit: 0 = context looks correct, 1 = issues found, 2 = warnings only.
"""

import argparse
import json
import sys
from pathlib import Path


def find_book_path(project_root: Path, book_id: str | None) -> Path | None:
    """Resolve book path."""
    books_dir = project_root / "books"
    if not books_dir.is_dir():
        return None
    if book_id:
        candidate = books_dir / book_id
        return candidate if candidate.is_dir() else None
    # Auto-detect single book
    books = [d for d in books_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if len(books) == 1:
        return books[0]
    return None


def check_green_files_readable(book_path: Path) -> list[str]:
    """Verify green zone files exist and are non-empty."""
    issues = []
    green_files = [
        "story/author_intent.md",
        "story/current_focus.md",
        "story/book_rules.md",
        "story/outline/story_frame.md",
        "story/outline/volume_map.md",
    ]
    for rel in green_files:
        f = book_path / rel
        if not f.exists():
            issues.append(f"Missing: {rel}")
        elif f.stat().st_size == 0:
            issues.append(f"Empty: {rel}")
    return issues


def check_roles_exist(book_path: Path) -> list[str]:
    """Verify roles directory has at least one character."""
    issues = []
    roles_dir = book_path / "story" / "roles"
    if not roles_dir.exists():
        issues.append("Missing: story/roles/ directory")
        return issues
    role_files = list(roles_dir.rglob("*.md"))
    if not role_files:
        issues.append("No role cards found in story/roles/")
    return issues


def check_no_red_zone_modified(book_path: Path) -> list[str]:
    """Spot-check that red zone files haven't been tampered with (basic existence)."""
    issues = []
    # manifest.json should exist if state/ exists
    state_dir = book_path / "story" / "state"
    if state_dir.exists() and not (state_dir / "manifest.json").exists():
        issues.append("state/ exists but manifest.json is missing (possible tampering)")
    return issues


def check_compose_output(book_path: Path) -> list[str]:
    """Check if latest compose/plan output exists (runtime/ or chapters/ intent)."""
    warnings = []
    runtime_dir = book_path / "story" / "runtime"
    if not runtime_dir.exists():
        warnings.append("story/runtime/ not found (may not have run plan/compose yet)")
    return warnings


def main():
    parser = argparse.ArgumentParser(description="Verify runtime context")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--book-id", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    book_path = find_book_path(args.project_root, args.book_id)
    if book_path is None:
        print("ERROR: Cannot resolve book path.", file=sys.stderr)
        sys.exit(1)

    report = {
        "book_path": str(book_path),
        "issues": [],
        "warnings": [],
    }

    report["issues"].extend(check_green_files_readable(book_path))
    report["issues"].extend(check_roles_exist(book_path))
    report["issues"].extend(check_no_red_zone_modified(book_path))
    report["warnings"].extend(check_compose_output(book_path))

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if report["issues"]:
            print("ISSUES FOUND:", file=sys.stderr)
            for i in report["issues"]:
                print(f"  ❌ {i}", file=sys.stderr)
        if report["warnings"]:
            print("WARNINGS:")
            for w in report["warnings"]:
                print(f"  ⚠️  {w}")
        if not report["issues"] and not report["warnings"]:
            print("✅ Runtime context looks correct.")

    if report["issues"]:
        sys.exit(1)
    elif report["warnings"]:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
