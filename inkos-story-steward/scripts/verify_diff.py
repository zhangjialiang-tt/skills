#!/usr/bin/env python3
"""Verify a git diff contains no red-zone writes and only authorized paths.

Checks unstaged + staged + untracked files combined.
Fail-closed: any git error → exit 1 (not "no changes").

Usage:
    python scripts/verify_diff.py [--project-root PATH]
    python scripts/verify_diff.py --files <path> [<path> ...]
    python scripts/verify_diff.py --allow <path> [--allow <path> ...]

Exit: 0 = clean, 1 = violation or error.
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from classify_path import classify


def git_cmd(args: list[str], cwd: Path) -> list[str]:
    """Run a git command. Raise RuntimeError on failure (fail-closed)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True, timeout=15,
            cwd=str(cwd)
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"git {' '.join(args)} failed (rc={result.returncode}): {result.stderr.strip()}"
            )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except FileNotFoundError:
        raise RuntimeError("git not found on PATH")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"git {' '.join(args)} timed out")


def get_all_modified_files(project_root: Path) -> list[str]:
    """Get combined set: unstaged + staged + untracked."""
    unstaged = git_cmd(["diff", "--name-only"], project_root)
    staged = git_cmd(["diff", "--cached", "--name-only"], project_root)
    untracked = git_cmd(["ls-files", "--others", "--exclude-standard"], project_root)
    # Deduplicate preserving order
    seen = set()
    result = []
    for f in unstaged + staged + untracked:
        if f not in seen:
            seen.add(f)
            result.append(f)
    return result


def normalize_path(f: str) -> str:
    """Normalize path separators and strip leading ./"""
    return f.replace("\\", "/").lstrip("./")


def is_book_path(normalized: str) -> bool:
    """Check if path is under books/."""
    return normalized.startswith("books/")


def main():
    parser = argparse.ArgumentParser(description="Verify no red-zone writes in diff")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--files", nargs="*", help="Explicit file list to check (skip git)")
    parser.add_argument("--allow", action="append", default=[],
                        help="Authorized paths (only these book files may be modified)")
    args = parser.parse_args()

    # Get file list
    if args.files:
        files = args.files
    else:
        try:
            files = get_all_modified_files(args.project_root)
        except RuntimeError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            print("Cannot verify safety without git. Blocking.", file=sys.stderr)
            sys.exit(1)

    if not files:
        print("No modified files to check.")
        sys.exit(0)

    violations = []
    unauthorized = []
    warnings = []

    # Normalize allow list
    allowed = set(normalize_path(a) for a in args.allow)

    for f in files:
        normalized = normalize_path(f)
        if not is_book_path(normalized):
            continue

        zone, reason = classify(normalized)

        if zone == "red":
            violations.append((normalized, reason))
        elif zone == "yellow":
            warnings.append((normalized, reason))

        # Check authorization if --allow is provided
        if allowed and normalized not in allowed:
            unauthorized.append((normalized, zone))

    # Report
    if violations:
        print("❌ RED ZONE VIOLATIONS:", file=sys.stderr)
        for f, reason in violations:
            print(f"  {f}: {reason}", file=sys.stderr)
        print("These files MUST NOT be modified. Revert immediately.", file=sys.stderr)

    if unauthorized:
        print("❌ UNAUTHORIZED MODIFICATIONS:", file=sys.stderr)
        for f, zone in unauthorized:
            print(f"  {f} ({zone}): not in --allow list", file=sys.stderr)

    if warnings and not violations:
        print("⚠️  Yellow zone modifications (verify controlled flow was used):")
        for f, reason in warnings:
            print(f"  {f}: {reason}")

    if not violations and not unauthorized and not warnings:
        print("✅ All modified book files are in green zone and authorized.")

    # Exit
    if violations or unauthorized:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
