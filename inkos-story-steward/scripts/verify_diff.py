#!/usr/bin/env python3
"""Verify a git diff contains no unauthorized modifications.

Modes:
  enforce (default): --allow required, all changes must be authorized, red always blocked.
  diagnostic: report only, no --allow required, but exit 1 on red zone.

Checks unstaged + staged + untracked combined. Fail-closed on git errors.

Usage:
    python scripts/verify_diff.py --mode enforce --allow <path> [--allow <path> ...]
    python scripts/verify_diff.py --mode diagnostic
    python scripts/verify_diff.py --files <path> [<path> ...] --mode enforce --allow <path>

Exit: 0 = clean, 1 = violation or error.
"""

import argparse
import subprocess
import sys
from pathlib import Path, PurePosixPath

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


def is_authorized(normalized: str, allow_list: list[str]) -> bool:
    """Check if path is in allow list (exact match or directory prefix with component boundary)."""
    for allowed in allow_list:
        a = normalize_path(allowed)
        if normalized == a:
            return True
        # Directory prefix: must end with / and match at component boundary
        if a.endswith("/"):
            if normalized.startswith(a):
                return True
        else:
            # Treat as directory prefix too (with / separator)
            if normalized.startswith(a + "/"):
                return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Verify no unauthorized modifications")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--files", nargs="*", help="Explicit file list (skip git)")
    parser.add_argument("--allow", action="append", default=[],
                        help="Authorized paths (exact file or directory prefix)")
    parser.add_argument("--allow-yellow", action="store_true",
                        help="Allow yellow-zone files in allow list (controlled operation declared)")
    parser.add_argument("--mode", choices=["enforce", "diagnostic"], default="enforce",
                        help="enforce: require --allow, block unauthorized; diagnostic: report only")
    args = parser.parse_args()

    # Enforce mode requires --allow
    if args.mode == "enforce" and not args.allow and not args.files:
        print("ERROR: --mode enforce requires at least one --allow path.", file=sys.stderr)
        sys.exit(1)

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
    yellow_uncontrolled = []

    allow_normalized = [normalize_path(a) for a in args.allow]

    for f in files:
        normalized = normalize_path(f)
        zone, reason = classify(normalized)

        # Red zone: ALWAYS blocked regardless of allow list
        if zone == "red":
            violations.append((normalized, reason))
            continue

        # In enforce mode, check authorization for ALL files (not just books/)
        if args.mode == "enforce" and allow_normalized:
            if not is_authorized(normalized, allow_normalized):
                unauthorized.append((normalized, zone))
                continue

        # Yellow zone: blocked unless --allow-yellow is declared
        if zone == "yellow" and not args.allow_yellow:
            yellow_uncontrolled.append((normalized, reason))

    # Report
    has_failure = False

    if violations:
        print("❌ RED ZONE VIOLATIONS (always forbidden):", file=sys.stderr)
        for f, reason in violations:
            print(f"  {f}: {reason}", file=sys.stderr)
        has_failure = True

    if unauthorized:
        print("❌ UNAUTHORIZED MODIFICATIONS:", file=sys.stderr)
        for f, zone in unauthorized:
            print(f"  {f} ({zone}): not in --allow list", file=sys.stderr)
        has_failure = True

    if yellow_uncontrolled:
        print("❌ YELLOW ZONE without --allow-yellow (controlled operation not declared):",
              file=sys.stderr)
        for f, reason in yellow_uncontrolled:
            print(f"  {f}: {reason}", file=sys.stderr)
        has_failure = True

    if not has_failure:
        if args.mode == "diagnostic":
            print("✅ Diagnostic: no red zone violations found.")
        else:
            print("✅ All modifications authorized and within zone constraints.")

    sys.exit(1 if has_failure else 0)


if __name__ == "__main__":
    main()
