#!/usr/bin/env python3
"""Verify a git diff contains no red-zone writes.

Usage:
    python scripts/verify_diff.py [--project-root PATH] [--staged]

Reads git diff, checks each modified file against red zone patterns.
Exit: 0 = clean, 1 = red zone violation detected.
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Import classify from sibling
sys.path.insert(0, str(Path(__file__).parent))
from classify_path import classify


def get_diff_files(project_root: Path, staged: bool = False) -> list[str]:
    """Get list of modified file paths from git diff."""
    cmd = ["git", "diff", "--name-only"]
    if staged:
        cmd.append("--cached")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10,
            cwd=str(project_root)
        )
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def main():
    parser = argparse.ArgumentParser(description="Verify no red-zone writes in diff")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--staged", action="store_true", help="Check staged changes")
    parser.add_argument("--files", nargs="*", help="Explicit file list to check")
    args = parser.parse_args()

    if args.files:
        files = args.files
    else:
        files = get_diff_files(args.project_root, args.staged)

    if not files:
        print("No modified files to check.")
        sys.exit(0)

    violations = []
    warnings = []

    for f in files:
        # Only check files under books/
        if "/books/" not in f.replace("\\", "/"):
            continue
        zone, reason = classify(f)
        if zone == "red":
            violations.append((f, reason))
        elif zone == "yellow":
            warnings.append((f, reason))

    if violations:
        print("RED ZONE VIOLATIONS DETECTED:", file=sys.stderr)
        for f, reason in violations:
            print(f"  ❌ {f}: {reason}", file=sys.stderr)
        print("\nThese files MUST NOT be modified. Revert changes.", file=sys.stderr)
        sys.exit(1)

    if warnings:
        print("Yellow zone modifications (verify controlled flow was used):")
        for f, reason in warnings:
            print(f"  ⚠️  {f}: {reason}")

    if not violations and not warnings:
        print("✅ All modified files are in green zone or outside books/.")

    sys.exit(0)


if __name__ == "__main__":
    main()
