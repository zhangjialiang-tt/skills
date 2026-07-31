#!/usr/bin/env python3
"""Verify InkOS runtime context after plan/compose.

Strictly validates that green-zone modifications are reflected in runtime output.

Modes:
  enforce (default): requires --source-file, content assertions, all three runtime files,
                     correct chapter, freshness proof. completion_proof=true on success.
  diagnostic: allows missing --source-file, but completion_proof=false always.

Usage:
    python scripts/verify_runtime_context.py \
        --project-root . --book-id test-book --chapter 6 \
        --mode enforce \
        --source-file books/test-book/story/book_rules.md \
        --expect-text "抑制剂只能延缓感染" \
        --expect-source "story/book_rules.md" \
        --reject-text "感染后无法进行任何干预"

Exit: 0 = verified, 1 = failure.
"""

import argparse
import json
import sys
from pathlib import Path


# Formal InkOS trace source fields (v1.7.2). Only these are searched for --expect-source.
TRACE_SOURCE_FIELDS = [
    "plannerInputs",
    "composerInputs",
    "selectedSources",
]

TRACE_SOURCE_NESTED = [
    ("contextTiers", "protectedSources"),
    ("contextTiers", "compressibleSources"),
    ("compression", "protectedSources"),
    ("compression", "compressedSources"),
]


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


def safe_yaml_load(path: Path) -> tuple[object | None, str | None]:
    """Load YAML using PyYAML. No fallback — PyYAML unavailable = fail."""
    try:
        import yaml
    except ImportError:
        return None, "YAML_PARSER_UNAVAILABLE: PyYAML is required. Install: pip install pyyaml"

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as e:
        return None, f"Cannot read {path.name}: {e}"

    try:
        data = yaml.safe_load(content)
        if data is None:
            return None, f"YAML file {path.name} is empty or null"
        return data, None
    except yaml.YAMLError as e:
        return None, f"YAML parse error in {path.name}: {e}"


def validate_chapter_field(data: dict, filename: str, expected: int) -> str | None:
    """Validate that data has a valid chapter field matching expected."""
    if "chapter" not in data:
        return f"{filename}: 'chapter' field missing (required by InkOS schema)"
    chapter_val = data["chapter"]
    if not isinstance(chapter_val, int):
        try:
            chapter_val = int(chapter_val)
        except (ValueError, TypeError):
            return f"{filename}: 'chapter' is not a valid integer: {data['chapter']!r}"
    if chapter_val != expected:
        return f"{filename}: chapter={chapter_val}, expected {expected}"
    return None


def collect_trace_sources(trace: dict) -> list[str]:
    """Collect source paths ONLY from formal InkOS trace fields."""
    sources = []

    # Top-level list fields
    for field in TRACE_SOURCE_FIELDS:
        val = trace.get(field)
        if isinstance(val, list):
            sources.extend(str(item) for item in val if isinstance(item, str))
        elif isinstance(val, str):
            sources.append(val)

    # Nested fields
    for parent_key, child_key in TRACE_SOURCE_NESTED:
        parent = trace.get(parent_key)
        if isinstance(parent, dict):
            val = parent.get(child_key)
            if isinstance(val, list):
                sources.extend(str(item) for item in val if isinstance(item, str))

    return sources


def source_matches(source_path: str, expect: str) -> bool:
    """Component-level path match between a trace source and expected path."""
    norm_source = source_path.replace("\\", "/").lstrip("./")
    norm_expect = expect.replace("\\", "/").lstrip("./")

    # Exact match
    if norm_source == norm_expect:
        return True

    # Suffix match at component boundary
    # e.g. "books/test-book/story/book_rules.md" matches "story/book_rules.md"
    if norm_source.endswith("/" + norm_expect):
        return True

    # Absolute path contains the relative path at component boundary
    if norm_expect in norm_source:
        idx = norm_source.rfind(norm_expect)
        if idx > 0 and norm_source[idx - 1] == "/":
            return True

    return False


def check_text_in_files(files_content: list[str], text: str) -> bool:
    """Check if text appears in any of the file contents."""
    return any(text in content for content in files_content)


def main():
    parser = argparse.ArgumentParser(description="Verify runtime context after plan/compose")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--book-id", type=str, default=None)
    parser.add_argument("--chapter", type=int, required=True,
                        help="Chapter number whose runtime context to verify")
    parser.add_argument("--mode", choices=["enforce", "diagnostic"], default="enforce",
                        help="enforce: full proof required; diagnostic: best-effort, no proof")
    parser.add_argument("--expect-text", action="append", default=[],
                        help="Text that must appear in context or rule-stack (repeatable)")
    parser.add_argument("--expect-source", action="append", default=[],
                        help="Source file that must appear in formal trace fields (repeatable)")
    parser.add_argument("--reject-text", action="append", default=[],
                        help="Old text that must NOT appear (repeatable)")
    parser.add_argument("--source-file", action="append", default=[],
                        help="Source files whose mtime must be <= runtime files (repeatable)")
    parser.add_argument("--max-age", type=float, default=None,
                        help="Optional: max age in seconds for runtime files (warning)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    issues = []
    warnings = []
    checked_sources = []
    runtime_files_found = {}

    # Mode-specific requirements
    if args.mode == "enforce":
        if not args.source_file:
            issues.append(
                "enforce mode requires at least one --source-file to prove freshness. "
                "Without it, cannot verify this session's modifications entered runtime.")
        if not args.expect_text and not args.expect_source and not args.reject_text:
            issues.append(
                "enforce mode requires at least one content assertion "
                "(--expect-text, --expect-source, or --reject-text).")

    # Even diagnostic needs at least one assertion to be useful
    if not args.expect_text and not args.expect_source and not args.reject_text:
        if args.mode == "diagnostic" and not issues:
            warnings.append("No content assertions — diagnostic only, cannot prove modification entered runtime.")
        elif not issues:
            issues.append("No content assertions provided.")

    # Early exit if fundamental requirements missing
    if issues and args.mode == "enforce":
        _finish(issues, warnings, args)
        return

    # Resolve book path
    book_path = find_book_path(args.project_root, args.book_id)
    if book_path is None:
        issues.append("Cannot resolve book path.")
        _finish(issues, warnings, args)
        return

    runtime_dir = book_path / "story" / "runtime"
    if not runtime_dir.is_dir():
        issues.append("story/runtime/ directory does not exist. Run inkos plan/compose first.")
        _finish(issues, warnings, args)
        return

    # Find all three required files
    context_path = find_runtime_file(runtime_dir, args.chapter, ".context.json")
    rule_stack_path = find_runtime_file(runtime_dir, args.chapter, ".rule-stack.yaml")
    trace_path = find_runtime_file(runtime_dir, args.chapter, ".trace.json")

    if context_path is None:
        issues.append(f"Missing: chapter-{args.chapter:04d}.context.json")
    else:
        runtime_files_found["context"] = str(context_path)
    if rule_stack_path is None:
        issues.append(f"Missing: chapter-{args.chapter:04d}.rule-stack.yaml")
    else:
        runtime_files_found["rule_stack"] = str(rule_stack_path)
    if trace_path is None:
        issues.append(f"Missing: chapter-{args.chapter:04d}.trace.json")
    else:
        runtime_files_found["trace"] = str(trace_path)

    if issues:
        _finish(issues, warnings, args)
        return

    # Parse files — all must succeed
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
        _finish(issues, warnings, args)
        return

    # Chapter field validation — mandatory
    ctx_chapter_err = validate_chapter_field(context_data, "context.json", args.chapter)
    if ctx_chapter_err:
        issues.append(ctx_chapter_err)

    trace_chapter_err = validate_chapter_field(trace_data, "trace.json", args.chapter)
    if trace_chapter_err:
        issues.append(trace_chapter_err)

    if issues:
        _finish(issues, warnings, args)
        return

    # Freshness: runtime files must be newer than ALL source files
    if args.source_file:
        runtime_paths = [context_path, rule_stack_path, trace_path]
        runtime_mtimes = [p.stat().st_mtime for p in runtime_paths]
        earliest_runtime_mtime = min(runtime_mtimes)

        source_mtimes = []
        for sf in args.source_file:
            sf_path = Path(sf)
            if not sf_path.exists():
                sf_path = args.project_root / sf
            if not sf_path.exists():
                issues.append(f"Source file not found: {sf}")
                continue
            source_mtimes.append(sf_path.stat().st_mtime)
            checked_sources.append(str(sf))

        if source_mtimes:
            latest_source_mtime = max(source_mtimes)
            if earliest_runtime_mtime < latest_source_mtime:
                issues.append(
                    "Runtime files are OLDER than source file(s). "
                    "Re-run plan/compose after editing green-zone files.")

    # Content assertions
    context_content = context_path.read_text(encoding="utf-8", errors="replace")
    rule_stack_content = rule_stack_path.read_text(encoding="utf-8", errors="replace")
    searchable_contents = [context_content, rule_stack_content]

    for text in args.expect_text:
        if not check_text_in_files(searchable_contents, text):
            issues.append(f"Expected text not found in context/rule-stack: \"{text}\"")

    for text in args.reject_text:
        if check_text_in_files(searchable_contents, text):
            issues.append(f"Rejected text still present in context/rule-stack: \"{text}\"")

    # Source verification — ONLY from formal trace fields
    for source in args.expect_source:
        trace_sources = collect_trace_sources(trace_data)
        if not any(source_matches(ts, source) for ts in trace_sources):
            issues.append(
                f"Expected source not found in formal trace fields: \"{source}\". "
                f"Searched: {TRACE_SOURCE_FIELDS} + nested contextTiers/compression. "
                f"Found sources: {trace_sources[:10]}")

    # Optional max-age warning
    if args.max_age is not None:
        import time
        now = time.time()
        for p in [context_path, rule_stack_path, trace_path]:
            age = now - p.stat().st_mtime
            if age > args.max_age:
                warnings.append(f"{p.name} is {age:.0f}s old (max-age={args.max_age}s)")

    _finish(issues, warnings, args, checked_sources, runtime_files_found)


def _finish(issues: list[str], warnings: list[str], args,
            checked_sources: list[str] | None = None,
            runtime_files: dict | None = None):
    passed = len(issues) == 0
    completion_proof = passed and args.mode == "enforce"
    proof_level = "enforced" if args.mode == "enforce" else "diagnostic"

    if args.json:
        print(json.dumps({
            "mode": args.mode,
            "chapter": args.chapter,
            "passed": passed,
            "completion_proof": completion_proof,
            "proof_level": proof_level,
            "issues": issues,
            "warnings": warnings,
            "checked_sources": checked_sources or [],
            "runtime_files": runtime_files or {},
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
        if passed:
            print(f"✅ Runtime context for chapter {args.chapter} verified.")
            print(f"completion_proof: {str(completion_proof).lower()}")
            print(f"proof_level: {proof_level}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
