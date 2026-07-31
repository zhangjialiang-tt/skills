#!/usr/bin/env python3
"""InkOS Story Steward preflight check.

Fail-closed guard: any uncertainty blocks writes.
Exit codes: 0 = write allowed, 1 = blocked, 2 = warnings only (write still allowed).

Usage:
    python scripts/preflight.py [--project-root PATH] [--book-id ID] [--json]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SUPPORTED_VERSION_RANGE = (1, 7, 2), (1, 8, 0)  # >=1.7.2 <1.8.0


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
    """Return True if .write.lock exists (BLOCKED)."""
    return (book_path / ".write.lock").exists()


def inspect_chapter_state(book_path: Path) -> dict:
    """Inspect chapter index and files for consistency.
    Returns dict with: latest_chapter, index_exists, index_valid,
    indexed_chapters, chapter_files, consistent, error."""
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

    # Discover chapter markdown files on disk
    if chapters_dir.is_dir():
        import re
        for f in chapters_dir.iterdir():
            if f.suffix == ".md" and f.name != "index.json":
                m = re.match(r"^(\d+)", f.name)
                if m:
                    result["chapter_files"].append(int(m.group(1)))
        result["chapter_files"].sort()

    # Read index
    if index_file.exists():
        result["index_exists"] = True
        try:
            data = json.loads(index_file.read_text(encoding="utf-8"))
            chapters = data if isinstance(data, list) else data.get("chapters", [])
            nums = []
            for c in chapters:
                n = c.get("number", c.get("id"))
                if n is not None:
                    nums.append(int(n))
            result["indexed_chapters"] = sorted(nums)
            result["index_valid"] = True
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            result["index_valid"] = False

    # Consistency checks
    indexed = set(result["indexed_chapters"])
    files = set(result["chapter_files"])

    if not result["index_exists"] and files:
        result["consistent"] = False
        result["error"] = "Chapter markdown files exist but index.json is missing"
    elif result["index_exists"] and not result["index_valid"]:
        result["consistent"] = False
        result["error"] = "index.json exists but is corrupt/unparseable"
    elif result["index_valid"]:
        missing_files = indexed - files
        unindexed_files = files - indexed
        if missing_files:
            result["consistent"] = False
            result["error"] = f"Index references chapters with no markdown file: {sorted(missing_files)}"
        elif unindexed_files:
            result["consistent"] = False
            result["error"] = f"Markdown files exist but not in index: {sorted(unindexed_files)}"
        # Check duplicates
        if result["index_valid"] and len(result["indexed_chapters"]) != len(indexed):
            result["consistent"] = False
            result["error"] = "Duplicate chapter numbers in index"

    # Determine latest chapter
    all_chapters = indexed | files
    if all_chapters:
        result["latest_chapter"] = max(all_chapters)

    return result


def check_inkos_version() -> tuple[int, ...] | None:
    """Get InkOS version tuple, or None if not installed."""
    try:
        result = subprocess.run(
            ["inkos", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None
        version_str = result.stdout.strip().split("/")[-1].strip()
        parts = version_str.split(".")
        return tuple(int(p) for p in parts[:3])
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        return None


def check_git_clean(project_root: Path) -> bool | None:
    """Return True if clean, False if dirty, None if git unavailable/failed."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
            cwd=str(project_root)
        )
        if result.returncode != 0:
            return None  # Git command failed
        return len(result.stdout.strip()) == 0
    except FileNotFoundError:
        return None  # Git not installed
    except subprocess.TimeoutExpired:
        return None  # Git timed out


def check_state_files(book_path: Path) -> dict:
    """Check which state/*.json files exist."""
    state_dir = book_path / "story" / "state"
    return {
        "manifest.json": (state_dir / "manifest.json").exists(),
        "current_state.json": (state_dir / "current_state.json").exists(),
        "hooks.json": (state_dir / "hooks.json").exists(),
        "chapter_summaries.json": (state_dir / "chapter_summaries.json").exists(),
    }


def main():
    parser = argparse.ArgumentParser(description="InkOS preflight check")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--book-id", type=str, default=None)
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    report = {
        "blocked": False,
        "write_allowed": True,
        "review_allowed": True,
        "review_only": False,
        "reason_codes": [],
        "errors": [],
        "warnings": [],
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
        report["mode"] = "PREBUILD"
        report["message"] = "No InkOS project found. PREBUILD mode."
        # PREBUILD doesn't need write permission checks
        _output(report, args.json)
        sys.exit(0)

    report["project_root"] = str(project_root)

    # 2. Discover books
    books = discover_books(project_root)
    if not books:
        report["mode"] = "PREBUILD"
        report["message"] = "Project exists but no books. PREBUILD mode."
        _output(report, args.json)
        sys.exit(0)

    # 3. Resolve book ID
    book_id = args.book_id
    if book_id is None:
        if len(books) == 1:
            book_id = books[0]
        else:
            block("MULTI_BOOK_UNRESOLVED",
                  f"Multiple books found: {books}. Specify --book-id.")
            report["mode"] = "UNKNOWN"
            _output(report, args.json)
            sys.exit(1)

    if book_id not in books:
        block("BOOK_NOT_FOUND", f"Book '{book_id}' not found. Available: {books}")
        report["mode"] = "UNKNOWN"
        _output(report, args.json)
        sys.exit(1)

    book_path = project_root / "books" / book_id
    report["book_id"] = book_id

    # 4. Check version
    version = check_inkos_version()
    if version is None:
        block("INKOS_VERSION_UNKNOWN",
              "InkOS CLI not found or version check failed. Writes blocked.")
        report["version"] = None
    else:
        report["version"] = ".".join(map(str, version))
        lo, hi = SUPPORTED_VERSION_RANGE
        if not (lo <= version < hi):
            block("INKOS_VERSION_UNSUPPORTED",
                  f"InkOS version {report['version']} outside supported range "
                  f"[{'.'.join(map(str, lo))}, {'.'.join(map(str, hi))}). Writes blocked.")

    # 5. Check write lock
    if check_write_lock(book_path):
        block("WRITE_LOCK_ACTIVE",
              ".write.lock exists. InkOS pipeline is running. Wait for it to finish.")

    # 6. Determine mode with chapter index consistency
    chapter_state = inspect_chapter_state(book_path)
    report["chapter_state"] = chapter_state
    report["latest_chapter"] = chapter_state["latest_chapter"]

    if not chapter_state["consistent"]:
        block("CHAPTER_INDEX_INCONSISTENT",
              f"Chapter index inconsistency: {chapter_state['error']}. "
              f"Do NOT modify chapters/index.json (red zone). "
              f"Use InkOS repair/audit or re-confirm project state.")
        report["mode"] = "UNKNOWN"
    elif chapter_state["latest_chapter"] is None:
        report["mode"] = "FOUNDATION_ALIGNMENT"
    else:
        report["mode"] = "ACTIVE"

    # 7. Check state files
    report["state_files"] = check_state_files(book_path)

    # 8. Check git — fail-closed on ANY uncertainty
    git_clean = check_git_clean(project_root)
    report["git_clean"] = git_clean
    if git_clean is None:
        block("GIT_BASELINE_UNAVAILABLE",
              "Git unavailable, not a repo, or command failed. "
              "Cannot establish clean baseline. Writes blocked.")
    elif git_clean is False:
        block("GIT_WORKTREE_DIRTY",
              "Git working tree is dirty. Commit or stash before modifications. "
              "Writes blocked.")

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
            if "book_id" in report:
                print(f"Book: {report['book_id']}")
            print(f"Latest chapter: {report.get('latest_chapter', 'none')}")
            print(f"Version: {report.get('version', 'unknown')}")
            print(f"Write allowed: {report['write_allowed']}")
            for w in report["warnings"]:
                print(f"WARNING: {w}", file=sys.stderr)


if __name__ == "__main__":
    main()
