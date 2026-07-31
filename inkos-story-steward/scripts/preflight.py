#!/usr/bin/env python3
"""InkOS Story Steward preflight check.

Fail-closed guard: any uncertainty blocks writes.
Detects mode: PREBUILD_STANDALONE, PREBUILD_IN_PROJECT, FOUNDATION_ALIGNMENT,
ACTIVE_MAINTENANCE, AMBIGUOUS_BINDING.

Exit codes: 0 = write allowed, 1 = blocked, 2 = warnings only.

Usage:
    python scripts/preflight.py [--project-root PATH] [--book-id ID] [--design-id ID] [--json]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from design_id import (
    derive_design_id, detect_legacy_layout, find_all_manifests,
    find_design_root, find_manifests_for_book, VALID_STATES,
)

SUPPORTED_VERSION_RANGE = (1, 7, 2), (1, 8, 0)


def find_project_root(start: Path) -> Path | None:
    """Walk up from start to find inkos.json."""
    current = start.resolve()
    while True:
        if (current / "inkos.json").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def discover_books(project_root: Path) -> list[str]:
    """List book IDs under books/."""
    books_dir = project_root / "books"
    if not books_dir.is_dir():
        return []
    return sorted(
        d.name for d in books_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )


def check_write_lock(book_path: Path) -> bool:
    return (book_path / ".write.lock").exists()


def inspect_chapter_state(book_path: Path) -> dict:
    """Inspect chapter index and files for consistency."""
    import re as _re
    result = {
        "latest_chapter": None,
        "index_exists": False,
        "index_valid": False,
        "indexed_chapters": [],
        "chapter_files": [],
        "consistent": True,
        "error": None,
    }

    chapters_dir = book_path / "chapters"
    index_file = chapters_dir / "index.json"

    if chapters_dir.is_dir():
        for f in chapters_dir.iterdir():
            if f.suffix == ".md" and f.name != "index.json":
                m = _re.match(r"^(\d+)", f.name)
                if m:
                    result["chapter_files"].append(int(m.group(1)))
        result["chapter_files"].sort()

    if index_file.exists():
        result["index_exists"] = True
        try:
            data = json.loads(index_file.read_text(encoding="utf-8"))
            chapters = data if isinstance(data, list) else data.get("chapters", [])
            nums = [int(c.get("number", c.get("id", 0))) for c in chapters]
            result["indexed_chapters"] = sorted(nums)
            result["index_valid"] = True
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            result["index_valid"] = False

    indexed = set(result["indexed_chapters"])
    files = set(result["chapter_files"])

    if not result["index_exists"] and files:
        result["consistent"] = False
        result["error"] = "Chapter markdown files exist but index.json is missing"
    elif result["index_exists"] and not result["index_valid"]:
        result["consistent"] = False
        result["error"] = "index.json exists but is corrupt/unparseable"
    elif result["index_valid"]:
        if indexed - files:
            result["consistent"] = False
            result["error"] = f"Index references chapters with no file: {sorted(indexed - files)}"
        elif files - indexed:
            result["consistent"] = False
            result["error"] = f"Files exist but not in index: {sorted(files - indexed)}"
        elif len(result["indexed_chapters"]) != len(indexed):
            result["consistent"] = False
            result["error"] = "Duplicate chapter numbers in index"

    all_chapters = indexed | files
    if all_chapters:
        result["latest_chapter"] = max(all_chapters)

    return result


def check_inkos_version() -> tuple[int, ...] | None:
    try:
        result = subprocess.run(
            ["inkos", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None
        version_str = result.stdout.strip().split("/")[-1].strip()
        return tuple(int(p) for p in version_str.split(".")[:3])
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        return None


def check_git_clean(project_root: Path) -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10, cwd=str(project_root)
        )
        if result.returncode != 0:
            return None
        return len(result.stdout.strip()) == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def load_manifest(manifest_path: Path) -> dict | None:
    """Load and validate manifest.yaml."""
    try:
        import yaml
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="InkOS preflight check")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--book-id", type=str, default=None)
    parser.add_argument("--design-id", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = {
        "blocked": False,
        "write_allowed": True,
        "review_allowed": True,
        "review_only": False,
        "reason_codes": [],
        "errors": [],
        "warnings": [],
        "mode": None,
        "design_id": args.design_id,
        "design_root": None,
        "manifest_path": None,
        "book_id": args.book_id,
        "binding_status": "unbound",
        "legacy_layout_detected": False,
    }

    def block(code: str, msg: str):
        report["blocked"] = True
        report["write_allowed"] = False
        report["review_only"] = True
        if code not in report["reason_codes"]:
            report["reason_codes"].append(code)
        report["errors"].append(msg)

    # 1. Find project root
    project_root = find_project_root(args.project_root)

    if project_root is None:
        report["mode"] = "PREBUILD_STANDALONE"
        report["message"] = "No InkOS project found. Standalone design mode."
        # Check legacy layout in cwd
        if detect_legacy_layout(args.project_root.resolve()):
            report["legacy_layout_detected"] = True
            report["warnings"].append("Legacy flat story-design/ layout detected. Migration recommended.")
        _output(report, args.json)
        sys.exit(0)

    report["project_root"] = str(project_root)

    # 2. Detect legacy layout
    if detect_legacy_layout(project_root):
        report["legacy_layout_detected"] = True
        report["warnings"].append("Legacy flat story-design/ layout detected. Migration recommended.")

    # 3. Discover books
    books = discover_books(project_root)

    # 4. Determine mode based on design manifest and books
    manifest_data = None
    manifest_path = None

    if args.design_id:
        manifest_path = project_root / "story-design" / args.design_id / "manifest.yaml"
        if manifest_path.exists():
            manifest_data = load_manifest(manifest_path)
            if manifest_data:
                report["manifest_path"] = str(manifest_path)
                report["design_root"] = f"story-design/{args.design_id}"
                book_id_from_manifest = manifest_data.get("inkos", {}).get("book_id")
                if book_id_from_manifest:
                    report["book_id"] = book_id_from_manifest
                    report["binding_status"] = "bound"

    # 5. Mode detection
    book_id = report["book_id"]

    if book_id and book_id in books:
        # Book exists — check for chapters
        book_path = project_root / "books" / book_id
        chapter_state = inspect_chapter_state(book_path)
        report["chapter_state"] = chapter_state

        if not chapter_state["consistent"]:
            block("CHAPTER_INDEX_INCONSISTENT",
                  f"Chapter index inconsistency: {chapter_state['error']}")
            report["mode"] = "AMBIGUOUS_BINDING"
        elif chapter_state["latest_chapter"] is None:
            report["mode"] = "FOUNDATION_ALIGNMENT"
        else:
            report["mode"] = "ACTIVE_MAINTENANCE"

        # Check write lock
        if check_write_lock(book_path):
            block("WRITE_LOCK_ACTIVE", ".write.lock exists. InkOS pipeline running.")

    elif book_id and book_id not in books and books:
        # Manifest claims a book that doesn't exist
        block("BOOK_NOT_FOUND", f"Bound book_id '{book_id}' not found in project.")
        report["mode"] = "AMBIGUOUS_BINDING"

    elif books and not book_id:
        # Books exist but no binding — check for ambiguous manifests
        if args.design_id:
            # Design specified but not bound
            report["mode"] = "PREBUILD_IN_PROJECT"
        else:
            # Multiple books, no design specified
            if len(books) > 1:
                block("MULTI_BOOK_UNRESOLVED",
                      f"Multiple books {books} and no --design-id or --book-id specified.")
                report["mode"] = "AMBIGUOUS_BINDING"
            else:
                # Single book — compatible fallback
                report["book_id"] = books[0]
                report["binding_status"] = "inferred_single"
                report["warnings"].append(
                    "Single book inferred. Add explicit binding to manifest for stability.")
                book_path = project_root / "books" / books[0]
                chapter_state = inspect_chapter_state(book_path)
                report["chapter_state"] = chapter_state
                if not chapter_state["consistent"]:
                    block("CHAPTER_INDEX_INCONSISTENT", chapter_state["error"])
                    report["mode"] = "AMBIGUOUS_BINDING"
                elif chapter_state["latest_chapter"] is None:
                    report["mode"] = "FOUNDATION_ALIGNMENT"
                else:
                    report["mode"] = "ACTIVE_MAINTENANCE"

    else:
        # No books at all — PREBUILD_IN_PROJECT
        report["mode"] = "PREBUILD_IN_PROJECT"

    # Check for duplicate bindings
    if book_id and report["mode"] not in ("AMBIGUOUS_BINDING",):
        try:
            bound_manifests = find_manifests_for_book(project_root, book_id)
            if len(bound_manifests) > 1:
                block("DUPLICATE_BINDING",
                      f"Multiple manifests claim book_id '{book_id}': "
                      f"{[str(m) for m in bound_manifests]}")
                report["mode"] = "AMBIGUOUS_BINDING"
        except ImportError:
            pass  # PyYAML not available, skip binding check

    # 6. Version check (only for modes that write to books/)
    if report["mode"] in ("FOUNDATION_ALIGNMENT", "ACTIVE_MAINTENANCE"):
        version = check_inkos_version()
        if version is None:
            block("INKOS_VERSION_UNKNOWN", "InkOS CLI not found. Writes blocked.")
            report["version"] = None
        else:
            report["version"] = ".".join(map(str, version))
            lo, hi = SUPPORTED_VERSION_RANGE
            if not (lo <= version < hi):
                block("INKOS_VERSION_UNSUPPORTED",
                      f"InkOS {report['version']} outside [{lo}, {hi}). Writes blocked.")

    # 7. Git check (fail-closed)
    git_clean = check_git_clean(project_root)
    report["git_clean"] = git_clean
    if git_clean is None:
        block("GIT_BASELINE_UNAVAILABLE", "Git unavailable. Cannot establish baseline.")
    elif git_clean is False:
        block("GIT_WORKTREE_DIRTY", "Git working tree dirty. Commit first.")

    # 8. Design root existence check for PREBUILD
    if report["mode"] in ("PREBUILD_STANDALONE", "PREBUILD_IN_PROJECT") and args.design_id:
        design_root = find_design_root(project_root, args.design_id)
        if design_root.exists() and not (design_root / "manifest.yaml").exists():
            report["warnings"].append(
                f"Design root {design_root} exists without manifest. Possible conflict.")
        report["design_root"] = f"story-design/{args.design_id}"

    # Output
    _output(report, args.json)
    if not report["write_allowed"]:
        sys.exit(1)
    elif report["warnings"]:
        sys.exit(2)
    else:
        sys.exit(0)


def _output(report: dict, as_json: bool):
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if report["blocked"]:
            print(f"BLOCKED: {report['errors'][0]}", file=sys.stderr)
            for code in report["reason_codes"]:
                print(f"  [{code}]", file=sys.stderr)
        else:
            print(f"Mode: {report.get('mode', 'UNKNOWN')}")
            if report.get("design_id"):
                print(f"Design: {report['design_id']}")
            if report.get("book_id"):
                print(f"Book: {report['book_id']}")
            print(f"Write allowed: {report['write_allowed']}")
            for w in report["warnings"]:
                print(f"WARNING: {w}", file=sys.stderr)


if __name__ == "__main__":
    main()
