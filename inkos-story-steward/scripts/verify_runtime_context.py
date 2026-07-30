#!/usr/bin/env python3
"""Verify InkOS runtime context after plan/compose.

Strictly validates that green-zone modifications are reflected in runtime output.
Requires all three runtime files, at least one content assertion, and source freshness.

Usage:
    python scripts/verify_runtime_context.py \
        --project-root . --book-id test-book --chapter 6 \
        --source-file books/test-book/story/book_rules.md \
        --expect-text "抑制剂只能延缓感染" \
        --expect-source "story/book_rules.md" \
        --reject-text "感染后无法进行任何干预"

Exit: 0 = verified, 1 = failure (missing files, parse error, assertion failed, stale).
"""

import argparse
import json
import os
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
    books = [d for d in books_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if len(books) == 1:
        return books[0]
    return None


def find_runtime_file(runtime_dir: Path, chapter: int, suffix: str) -> Path | None:
    """Find a runtime file for a given chapter and suffix."""
    patterns = [
        f"chapter-{chapter:04d}{suffix}",
        f"chapter-{chapter}{suffix}",
        f"{chapter:03d}{suffix}",
        f"{chapter}{suffix}",
    ]
    for p in patterns:
        candidate = runtime_dir / p
        if candidate.exists():
            return candidate
    # Search subdirectories
    for f in runtime_dir.rglob(f"*{suffix}"):
        name = f.name
        if (f"{chapter:04d}" in name or f"{chapter:03d}" in name or
                f"-{chapter}." in name or f"-{chapter}-" in name):
            return f
    return None


def safe_json_load(path: Path) -> tuple[dict | None, str | None]:
    """Load JSON, return (data, error)."""
    try:
        content = path.read_text(encoding="utf-8")
        return json.loads(content), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path.name}: {e}"
    except OSError as e:
        return None, f"Cannot read {path.name}: {e}"


def safe_yaml_load(path: Path) -> tuple[dict | list | None, str | None]:
    """Load YAML safely. Uses yaml if available, else minimal parser."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as e:
        return None, f"Cannot read {path.name}: {e}"

    try:
        import yaml
        data = yaml.safe_load(content)
        if data is None:
            return None, f"YAML file {path.name} is empty or null"
        return data, None
    except ImportError:
        # Minimal fallback: just verify it's not empty and looks like YAML
        stripped = content.strip()
        if not stripped:
            return None, f"YAML file {path.name} is empty"
        # Basic sanity: should have at least one key: value or - item
        if ":" not in stripped and not stripped.startswith("-"):
            return None, f"YAML file {path.name} does not appear to be valid YAML"
        return {"_raw": content}, None
    except Exception as e:
        return None, f"YAML parse error in {path.name}: {e}"


def extract_chapter_from_json(data: dict) -> int | None:
    """Try to extract chapter number from context/trace JSON."""
    for key in ["chapter", "chapterNumber", "chapter_number", "targetChapter"]:
        if key in data:
            try:
                return int(data[key])
            except (ValueError, TypeError):
                pass
    return None


def check_source_in_trace(trace_data: dict, expect_source: str) -> bool:
    """Check if expect_source appears in structured trace fields."""
    # Normalize the expected source for comparison
    norm_expect = expect_source.replace("\\", "/").lstrip("./")

    # Fields to search in trace
    search_fields = [
        "plannerInputs", "composerInputs", "selectedSources",
        "sources", "inputs", "files",
    ]

    # Also check nested contextTiers and compression
    for tier_key in ["contextTiers", "compression"]:
        tier = trace_data.get(tier_key)
        if isinstance(tier, dict):
            for sub_key in ["protectedSources", "compressibleSources",
                            "compressedSources", "sources"]:
                sub = tier.get(sub_key)
                if isinstance(sub, list):
                    search_fields.append(f"{tier_key}.{sub_key}")

    def matches(path_str: str) -> bool:
        """Component-level path match."""
        norm = path_str.replace("\\", "/").lstrip("./")
        # Exact match
        if norm == norm_expect:
            return True
        # Suffix match at component boundary (e.g. "story/book_rules.md" matches
        # "books/test-book/story/book_rules.md")
        if norm.endswith("/" + norm_expect) or norm.endswith(norm_expect):
            # Verify component boundary
            idx = norm.rfind(norm_expect)
            if idx == 0 or norm[idx - 1] == "/":
                return True
        return False

    # Deep search through the trace structure
    def search_obj(obj) -> bool:
        if isinstance(obj, str):
            return matches(obj)
        elif isinstance(obj, list):
            return any(search_obj(item) for item in obj)
        elif isinstance(obj, dict):
            return any(search_obj(v) for v in obj.values())
        return False

    return search_obj(trace_data)


def check_text_in_files(files_content: list[str], text: str) -> bool:
    """Check if text appears in any of the file contents."""
    return any(text in content for content in files_content)


def main():
    parser = argparse.ArgumentParser(description="Verify runtime context after plan/compose")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--book-id", type=str, default=None)
    parser.add_argument("--chapter", type=int, required=True,
                        help="Chapter number whose runtime context to verify")
    parser.add_argument("--expect-text", action="append", default=[],
                        help="Text that must appear in context or rule-stack (repeatable)")
    parser.add_argument("--expect-source", action="append", default=[],
                        help="Source file that must appear in trace (repeatable)")
    parser.add_argument("--reject-text", action="append", default=[],
                        help="Old text that must NOT appear (repeatable)")
    parser.add_argument("--source-file", action="append", default=[],
                        help="Source files whose mtime must be <= runtime files (repeatable)")
    parser.add_argument("--max-age", type=float, default=None,
                        help="Optional: max age in seconds for runtime files (warning only)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    issues = []

    # Require at least one content assertion
    if not args.expect_text and not args.expect_source and not args.reject_text:
        issues.append(
            "No content assertions provided. At least one of --expect-text, "
            "--expect-source, or --reject-text is required. "
            "Weak verification cannot prove modifications entered runtime."
        )
        _finish(issues, [], args.json, args.chapter)
        return

    # Resolve book path
    book_path = find_book_path(args.project_root, args.book_id)
    if book_path is None:
        issues.append("Cannot resolve book path.")
        _finish(issues, [], args.json, args.chapter)
        return

    runtime_dir = book_path / "story" / "runtime"
    if not runtime_dir.is_dir():
        issues.append("story/runtime/ directory does not exist. Run inkos plan/compose first.")
        _finish(issues, [], args.json, args.chapter)
        return

    # Find all three required files
    context_path = find_runtime_file(runtime_dir, args.chapter, ".context.json")
    rule_stack_path = find_runtime_file(runtime_dir, args.chapter, ".rule-stack.yaml")
    trace_path = find_runtime_file(runtime_dir, args.chapter, ".trace.json")

    if context_path is None:
        issues.append(f"Missing: chapter-{args.chapter:04d}.context.json. Run: inkos compose chapter")
    if rule_stack_path is None:
        issues.append(f"Missing: chapter-{args.chapter:04d}.rule-stack.yaml. Run: inkos compose chapter")
    if trace_path is None:
        issues.append(f"Missing: chapter-{args.chapter:04d}.trace.json. Run: inkos compose chapter")

    # If any file missing, fail immediately
    if issues:
        _finish(issues, [], args.json, args.chapter)
        return

    # Parse files
    context_data, ctx_err = safe_json_load(context_path)
    if ctx_err:
        issues.append(ctx_err)

    trace_data, trace_err = safe_json_load(trace_path)
    if trace_err:
        issues.append(trace_err)

    rule_stack_data, yaml_err = safe_yaml_load(rule_stack_path)
    if yaml_err:
        issues.append(yaml_err)

    if issues:
        _finish(issues, [], args.json, args.chapter)
        return

    # Chapter consistency: verify chapter number in files matches --chapter
    if context_data:
        file_chapter = extract_chapter_from_json(context_data)
        if file_chapter is not None and file_chapter != args.chapter:
            issues.append(
                f"context.json chapter={file_chapter}, expected {args.chapter}")

    if trace_data:
        file_chapter = extract_chapter_from_json(trace_data)
        if file_chapter is not None and file_chapter != args.chapter:
            issues.append(
                f"trace.json chapter={file_chapter}, expected {args.chapter}")

    # Freshness: runtime files must be newer than source files
    if args.source_file:
        runtime_paths = [context_path, rule_stack_path, trace_path]
        runtime_mtimes = [p.stat().st_mtime for p in runtime_paths]
        min_runtime_mtime = min(runtime_mtimes)

        for sf in args.source_file:
            sf_path = Path(sf)
            if not sf_path.exists():
                # Try relative to project root
                sf_path = args.project_root / sf
            if not sf_path.exists():
                issues.append(f"Source file not found: {sf}")
                continue
            sf_mtime = sf_path.stat().st_mtime
            if min_runtime_mtime < sf_mtime:
                issues.append(
                    f"Runtime files are OLDER than source file {sf}. "
                    f"Re-run plan/compose after editing green-zone files.")
                break  # One staleness error is enough

    # Content assertions
    # Read raw content for text matching
    context_content = context_path.read_text(encoding="utf-8", errors="replace")
    rule_stack_content = rule_stack_path.read_text(encoding="utf-8", errors="replace")
    searchable_contents = [context_content, rule_stack_content]

    for text in args.expect_text:
        if not check_text_in_files(searchable_contents, text):
            issues.append(f"Expected text not found in context/rule-stack: \"{text}\"")

    for text in args.reject_text:
        if check_text_in_files(searchable_contents, text):
            issues.append(f"Rejected text still present in context/rule-stack: \"{text}\"")

    for source in args.expect_source:
        if trace_data and not check_source_in_trace(trace_data, source):
            issues.append(f"Expected source not found in trace: \"{source}\"")
        elif trace_data is None:
            issues.append(f"Cannot verify source (trace not parsed): \"{source}\"")

    # Optional max-age warning
    warnings = []
    if args.max_age is not None:
        import time
        now = time.time()
        for p in [context_path, rule_stack_path, trace_path]:
            age = now - p.stat().st_mtime
            if age > args.max_age:
                warnings.append(f"{p.name} is {age:.0f}s old (max-age={args.max_age}s)")

    _finish(issues, warnings, args.json, args.chapter)


def _finish(issues: list[str], warnings: list[str], as_json: bool, chapter: int):
    if as_json:
        print(json.dumps({
            "chapter": chapter,
            "issues": issues,
            "warnings": warnings,
            "passed": len(issues) == 0,
        }, ensure_ascii=False, indent=2))
    else:
        if issues:
            print("❌ RUNTIME VERIFICATION FAILED:", file=sys.stderr)
            for i in issues:
                print(f"  {i}", file=sys.stderr)
        if warnings:
            print("⚠️  WARNINGS:")
            for w in warnings:
                print(f"  {w}")
        if not issues and not warnings:
            print(f"✅ Runtime context for chapter {chapter} verified.")

    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
