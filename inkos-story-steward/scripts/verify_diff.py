#!/usr/bin/env python3
"""Verify a git diff contains no unauthorized modifications.

Modes:
  enforce (default): --allow required (even with --files), all changes must be authorized,
                     red always blocked, yellow needs --allow-yellow.
  diagnostic: report only, red → exit1, yellow/unknown → warning+exit0.
              NOT a completion proof — Steward must not treat diagnostic success as safe.

Checks unstaged + staged + untracked combined. Fail-closed on git errors.

Usage:
    python scripts/verify_diff.py --mode enforce --allow <path> [--allow <path> ...]
    python scripts/verify_diff.py --mode diagnostic
    python scripts/verify_diff.py --files <path> [...] --mode enforce --allow <path> [...]

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
            # Also allow as directory prefix (with / separator for component safety)
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

    # Enforce mode ALWAYS requires --allow, regardless of --files
    if args.mode == "enforce" and not args.allow:
        print("ERROR: --mode enforce requires at least one --allow path.", file=sys.stderr)
        print("completion_proof: false", file=sys.stderr)
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
        if args.mode == "enforce":
            print("completion_proof: true (no modifications)")
        sys.exit(0)

    red_violations = []
    unauthorized = []
    yellow_warnings = []

    allow_normalized = [normalize_path(a) for a in args.allow]

    for f in files:
        normalized = normalize_path(f)
        zone, reason = classify(normalized)

        # Red zone: ALWAYS blocked regardless of mode or allow list
        if zone == "red":
            red_violations.append((normalized, reason))
            continue

        if args.mode == "enforce":
            # Authorization check for ALL files
            if not is_authorized(normalized, allow_normalized):
                unauthorized.append((normalized, zone))
                continue

            # Yellow zone: blocked unless --allow-yellow is declared
            if zone == "yellow" and not args.allow_yellow:
                yellow_warnings.append((normalized, reason, "blocked"))
            else:
                pass  # authorized and (green or yellow-with-declaration)

        else:  # diagnostic
            # Yellow/unknown: report as warning, do NOT block
            if zone == "yellow":
                yellow_warnings.append((normalized, reason, "warning"))

    # Determine failure
    has_failure = False

    if red_violations:
        print("❌ RED ZONE VIOLATIONS (always forbidden):", file=sys.stderr)
        for f, reason in red_violations:
            print(f"  {f}: {reason}", file=sys.stderr)
        has_failure = True

    if unauthorized:
        print("❌ UNAUTHORIZED MODIFICATIONS:", file=sys.stderr)
        for f, zone in unauthorized:
            print(f"  {f} ({zone}): not in --allow list", file=sys.stderr)
        has_failure = True

    # Yellow handling differs by mode
    blocked_yellow = [(f, r) for f, r, kind in yellow_warnings if kind == "blocked"]
    warned_yellow = [(f, r) for f, r, kind in yellow_warnings if kind == "warning"]

    if blocked_yellow:
        print("❌ YELLOW ZONE without --allow-yellow (controlled operation not declared):",
              file=sys.stderr)
        for f, reason in blocked_yellow:
            print(f"  {f}: {reason}", file=sys.stderr)
        has_failure = True

    if warned_yellow:
        print("⚠️  Yellow zone modifications (diagnostic — not a completion proof):")
        for f, reason in warned_yellow:
            print(f"  {f}: {reason}")

    # Final output
    if not has_failure:
        if args.mode == "diagnostic":
            print("Diagnostic: no red zone violations. completion_proof: false")
        else:
            print("✅ All modifications authorized and within zone constraints.")
            print("completion_proof: true")

    sys.exit(1 if has_failure else 0)


if __name__ == "__main__":
    main()
