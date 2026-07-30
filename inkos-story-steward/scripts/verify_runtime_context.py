#!/usr/bin/env python3
"""Verify InkOS runtime context after plan/compose.

Actually reads chapter context.json, rule-stack.yaml, and trace.json
to confirm green-zone modifications are reflected in runtime output.

Usage:
    python scripts/verify_runtime_context.py \
        --project-root PATH --book-id ID --chapter N \
        [--expect-text "text that should appear"] \
        [--expect-source "story/book_rules.md"] \
        [--reject-text "old text that should be gone"]

Exit: 0 = verified, 1 = issues found or missing files, 2 = warnings only.
"""

import argparse
import json
import sys
import time
from pathlib import Path


def find_book_path(project_root: Path, book_id: str | None) -> Path | None:
    """Resolve book path."""
    books_dir = project_root / "books"
    if not books_dir.is_dir():
        return None
    if book_id:
        candidate = books_dir / book_id
        return candidate if candidate.is_dir() else None
    books = [d for d in books_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if len(books) == 1:
        return books[0]
    return None


def find_runtime_files(book_path: Path, chapter: int) -> dict[str, Path | None]:
    """Locate runtime context files for a chapter."""
    runtime_dir = book_path / "story" / "runtime"
    if not runtime_dir.is_dir():
        return {"context": None, "rule_stack": None, "trace": None, "runtime_dir": None}

    # Search for files matching this chapter number
    # InkOS may use various naming: chapter-0006.context.json, 006.context.json, etc.
    patterns = [
        f"chapter-{chapter:04d}.context.json",
        f"chapter-{chapter}.context.json",
        f"{chapter:03d}.context.json",
        f"{chapter}.context.json",
    ]

    context_file = None
    for p in patterns:
        candidate = runtime_dir / p
        if candidate.exists():
            context_file = candidate
            break

    # Also search subdirectories (some versions nest under chapter dirs)
    if context_file is None:
        for f in runtime_dir.rglob("*.context.json"):
            if f"{chapter:04d}" in f.name or f"{chapter:03d}" in f.name or f".{chapter}." in f.name:
                context_file = f
                break

    # Rule stack
    rule_stack = None
    for p in [f"chapter-{chapter:04d}.rule-stack.yaml", f"chapter-{chapter}.rule-stack.yaml",
              f"{chapter:03d}.rule-stack.yaml", f"{chapter}.rule-stack.yaml"]:
        candidate = runtime_dir / p
        if candidate.exists():
            rule_stack = candidate
            break
    if rule_stack is None:
        for f in runtime_dir.rglob("*.rule-stack.yaml"):
            if f"{chapter:04d}" in f.name or f"{chapter:03d}" in f.name:
                rule_stack = f
                break

    # Trace
    trace = None
    for p in [f"chapter-{chapter:04d}.trace.json", f"chapter-{chapter}.trace.json",
              f"{chapter:03d}.trace.json", f"{chapter}.trace.json"]:
        candidate = runtime_dir / p
        if candidate.exists():
            trace = candidate
            break
    if trace is None:
        for f in runtime_dir.rglob("*.trace.json"):
            if f"{chapter:04d}" in f.name or f"{chapter:03d}" in f.name:
                trace = f
                break

    return {"context": context_file, "rule_stack": rule_stack, "trace": trace, "runtime_dir": runtime_dir}


def check_freshness(files: dict[str, Path | None], max_age_seconds: float = 3600) -> list[str]:
    """Check if runtime files are recent (not stale from a previous run)."""
    warnings = []
    now = time.time()
    for name, path in files.items():
        if path and path.exists():
            age = now - path.stat().st_mtime
            if age > max_age_seconds:
                warnings.append(
                    f"{name} is {age/3600:.1f}h old — may be stale. "
                    f"Re-run plan/compose after green-zone edits."
                )
    return warnings


def check_expect_text(files: dict[str, Path | None], expect_text: str) -> list[str]:
    """Verify expected text appears in context or rule-stack."""
    issues = []
    found = False
    for name in ["context", "rule_stack"]:
        path = files.get(name)
        if path and path.exists():
            content = path.read_text(encoding="utf-8", errors="replace")
            if expect_text in content:
                found = True
                break
    if not found:
        issues.append(
            f"Expected text not found in runtime context: \"{expect_text}\""
        )
    return issues


def check_expect_source(files: dict[str, Path | None], expect_source: str) -> list[str]:
    """Verify trace references the expected source file."""
    issues = []
    trace_path = files.get("trace")
    if not trace_path or not trace_path.exists():
        issues.append(f"No trace file found — cannot verify source: {expect_source}")
        return issues

    content = trace_path.read_text(encoding="utf-8", errors="replace")
    if expect_source not in content:
        issues.append(
            f"Trace does not reference expected source: \"{expect_source}\""
        )
    return issues


def check_reject_text(files: dict[str, Path | None], reject_text: str) -> list[str]:
    """Verify old/rejected text is NOT in context or rule-stack."""
    issues = []
    for name in ["context", "rule_stack"]:
        path = files.get(name)
        if path and path.exists():
            content = path.read_text(encoding="utf-8", errors="replace")
            if reject_text in content:
                issues.append(
                    f"Rejected text still present in {name}: \"{reject_text}\""
                )
    return issues


def check_chapter_number(files: dict[str, Path | None], expected_chapter: int) -> list[str]:
    """Verify runtime files are for the expected chapter."""
    issues = []
    context_path = files.get("context")
    if not context_path:
        return issues  # Already reported as missing

    # Try to extract chapter number from context.json content
    try:
        data = json.loads(context_path.read_text(encoding="utf-8"))
        file_chapter = data.get("chapter", data.get("chapterNumber"))
        if file_chapter is not None and int(file_chapter) != expected_chapter:
            issues.append(
                f"Runtime context is for chapter {file_chapter}, expected {expected_chapter}"
            )
    except (json.JSONDecodeError, ValueError):
        pass  # Can't parse, skip this check
    return issues


def check_green_files_exist(book_path: Path) -> list[str]:
    """Basic check that green zone files exist."""
    issues = []
    green_files = [
        "story/author_intent.md",
        "story/book_rules.md",
        "story/outline/story_frame.md",
    ]
    for rel in green_files:
        f = book_path / rel
        if not f.exists():
            issues.append(f"Missing green file: {rel}")
        elif f.stat().st_size == 0:
            issues.append(f"Empty green file: {rel}")
    return issues


def main():
    parser = argparse.ArgumentParser(description="Verify runtime context after plan/compose")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--book-id", type=str, default=None)
    parser.add_argument("--chapter", type=int, required=True,
                        help="Chapter number whose runtime context to verify")
    parser.add_argument("--expect-text", type=str, default=None,
                        help="Text that must appear in context/rule-stack")
    parser.add_argument("--expect-source", type=str, default=None,
                        help="Source file that must appear in trace")
    parser.add_argument("--reject-text", type=str, default=None,
                        help="Old text that must NOT appear in context/rule-stack")
    parser.add_argument("--max-age", type=float, default=3600,
                        help="Max age in seconds for runtime files (default 3600)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    book_path = find_book_path(args.project_root, args.book_id)
    if book_path is None:
        print("ERROR: Cannot resolve book path.", file=sys.stderr)
        sys.exit(1)

    report = {"book_path": str(book_path), "chapter": args.chapter, "issues": [], "warnings": []}

    # Find runtime files
    files = find_runtime_files(book_path, args.chapter)

    if files["runtime_dir"] is None:
        report["issues"].append("story/runtime/ directory does not exist. Run inkos plan/compose first.")
    elif files["context"] is None:
        report["issues"].append(
            f"No context.json found for chapter {args.chapter}. "
            f"Run: inkos compose chapter"
        )

    # Freshness check
    report["warnings"].extend(check_freshness(files, args.max_age))

    # Content checks (only if files exist)
    if files["context"] or files["rule_stack"]:
        if args.expect_text:
            report["issues"].extend(check_expect_text(files, args.expect_text))
        if args.reject_text:
            report["issues"].extend(check_reject_text(files, args.reject_text))

    if args.expect_source:
        report["issues"].extend(check_expect_source(files, args.expect_source))

    # Chapter number check
    report["issues"].extend(check_chapter_number(files, args.chapter))

    # Green file existence
    report["issues"].extend(check_green_files_exist(book_path))

    # Output
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if report["issues"]:
            print("❌ ISSUES:", file=sys.stderr)
            for i in report["issues"]:
                print(f"  {i}", file=sys.stderr)
        if report["warnings"]:
            print("⚠️  WARNINGS:")
            for w in report["warnings"]:
                print(f"  {w}")
        if not report["issues"] and not report["warnings"]:
            print(f"✅ Runtime context for chapter {args.chapter} verified.")

    if report["issues"]:
        sys.exit(1)
    elif report["warnings"]:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
