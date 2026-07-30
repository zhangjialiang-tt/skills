#!/usr/bin/env python3
"""InkOS Story Steward preflight check.

Read-only guard: detects project, version, lock, git state, latest chapter.
Exit codes: 0 = safe to proceed, 1 = blocked (reason on stderr), 2 = warning.

Usage:
    python scripts/preflight.py [--project-root PATH] [--book-id ID]
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


def get_latest_chapter(book_path: Path) -> int | None:
    """Return latest chapter number from index.json, or None."""
    index_file = book_path / "chapters" / "index.json"
    if not index_file.exists():
        return None
    try:
        data = json.loads(index_file.read_text(encoding="utf-8"))
        chapters = data if isinstance(data, list) else data.get("chapters", [])
        if not chapters:
            return None
        nums = [c.get("number", c.get("id", 0)) for c in chapters]
        return max(nums) if nums else None
    except (json.JSONDecodeError, KeyError):
        return None


def check_inkos_version() -> tuple[int, ...] | None:
    """Get InkOS version tuple, or None if not installed."""
    try:
        result = subprocess.run(
            ["inkos", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None
        # Parse version from output like "inkos/1.7.2" or "1.7.2"
        version_str = result.stdout.strip().split("/")[-1].strip()
        parts = version_str.split(".")
        return tuple(int(p) for p in parts[:3])
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        return None


def check_git_clean(project_root: Path) -> bool | None:
    """Return True if git working tree is clean, False if dirty, None if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
            cwd=str(project_root)
        )
        if result.returncode != 0:
            return None
        return len(result.stdout.strip()) == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


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

    report = {"blocked": False, "warnings": [], "errors": []}

    # 1. Find project root
    project_root = find_project_root(args.project_root)
    if project_root is None:
        report["mode"] = "PREBUILD"
        report["message"] = "No InkOS project found. PREBUILD mode."
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print("Mode: PREBUILD (no InkOS project found)")
        sys.exit(0)

    report["project_root"] = str(project_root)

    # 2. Discover books
    books = discover_books(project_root)
    if not books:
        report["mode"] = "PREBUILD"
        report["message"] = "Project exists but no books. PREBUILD mode."
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print("Mode: PREBUILD (no books found)")
        sys.exit(0)

    # 3. Resolve book ID
    book_id = args.book_id
    if book_id is None:
        if len(books) == 1:
            book_id = books[0]
        else:
            report["blocked"] = True
            report["errors"].append(
                f"Multiple books found: {books}. Specify --book-id."
            )
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print(f"BLOCKED: Multiple books {books}. Specify --book-id.", file=sys.stderr)
            sys.exit(1)

    if book_id not in books:
        report["blocked"] = True
        report["errors"].append(f"Book '{book_id}' not found. Available: {books}")
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"BLOCKED: Book '{book_id}' not found.", file=sys.stderr)
        sys.exit(1)

    book_path = project_root / "books" / book_id
    report["book_id"] = book_id

    # 4. Check version
    version = check_inkos_version()
    if version is None:
        report["warnings"].append("InkOS CLI not found or version check failed.")
        report["version"] = None
    else:
        report["version"] = ".".join(map(str, version))
        lo, hi = SUPPORTED_VERSION_RANGE
        if not (lo <= version < hi):
            report["warnings"].append(
                f"InkOS version {report['version']} outside supported range "
                f"[{'.'.join(map(str, lo))}, {'.'.join(map(str, hi))}). "
                f"Switching to review-only mode."
            )
            report["review_only"] = True

    # 5. Check write lock
    if check_write_lock(book_path):
        report["blocked"] = True
        report["errors"].append(
            ".write.lock exists. InkOS pipeline is running. Wait for it to finish."
        )

    # 6. Determine mode
    latest_chapter = get_latest_chapter(book_path)
    report["latest_chapter"] = latest_chapter
    if latest_chapter is None:
        report["mode"] = "FOUNDATION_ALIGNMENT"
    else:
        report["mode"] = "ACTIVE"

    # 7. Check state files
    report["state_files"] = check_state_files(book_path)

    # 8. Check git
    git_clean = check_git_clean(project_root)
    report["git_clean"] = git_clean
    if git_clean is False:
        report["warnings"].append("Git working tree is dirty. Consider committing before modifications.")

    # Output
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if report["blocked"]:
            print(f"BLOCKED: {report['errors'][0]}", file=sys.stderr)
        else:
            print(f"Mode: {report['mode']}")
            print(f"Book: {book_id}")
            print(f"Latest chapter: {latest_chapter or 'none'}")
            print(f"Version: {report.get('version', 'unknown')}")
            for w in report["warnings"]:
                print(f"WARNING: {w}", file=sys.stderr)

    sys.exit(1 if report["blocked"] else (2 if report["warnings"] else 0))


if __name__ == "__main__":
    main()
