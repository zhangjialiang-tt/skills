#!/usr/bin/env python3
"""Classify a file path into zone.

Supports two classification levels:
1. InkOS book zones (red/yellow/green) — for paths under books/<bookId>/
2. Design package zones — for paths under story-design/<design-id>/
3. Extended classification — returns specific zone names

Usage:
    python scripts/classify_path.py <relative-path> [--book-id ID] [--extended]

Output: zone + reason.
Exit: 0 = safe to write (green/design_source/compiled), 1 = red/forbidden, 2 = controlled.
"""

import argparse
import re
import sys
from pathlib import PurePosixPath

# Red zone patterns (relative to book root: books/<bookId>/)
RED_PATTERNS = [
    ".write.lock",
    "chapters/index.json",
    "story/runtime",
    "story/state/manifest.json",
    "story/memory.db",
    "story/story_bible.md",
    "story/character_matrix.md",
    "story/snapshots",
]

# Yellow zone patterns
YELLOW_PATTERNS = [
    "book.json",
    "chapters/",
    "story/current_state.md",
    "story/pending_hooks.md",
    "story/emotional_arcs.md",
    "story/state/current_state.json",
    "story/state/hooks.json",
    "story/state/chapter_summaries.json",
]

# Green zone patterns
GREEN_PATTERNS = [
    "story/author_intent.md",
    "story/current_focus.md",
    "story/style_guide.md",
    "story/book_rules.md",
    "story/outline/",
    "story/roles/",
    "story/brief.md",
]


def _matches_pattern(path: str, pattern: str) -> bool:
    """Component-level pattern match. Prevents prefix collisions like
    'story/runtime' matching 'story/runtime-backup.md'."""
    if path == pattern:
        return True
    if pattern.endswith("/"):
        # Directory prefix: pattern already includes trailing /
        return path.startswith(pattern)
    else:
        # Require component boundary: exact or followed by /
        return path.startswith(pattern + "/")


def classify(path_str: str) -> tuple[str, str]:
    """Return (zone, reason) for a path relative to book root.
    Zones: green, yellow, red."""
    # Normalize to posix
    path = PurePosixPath(path_str.replace("\\", "/"))
    path_str_norm = str(path)

    # Strip books/<bookId>/ prefix if present
    parts = path.parts
    if len(parts) >= 3 and parts[0] == "books":
        path_str_norm = str(PurePosixPath(*parts[2:]))

    # Check red
    for pattern in RED_PATTERNS:
        if _matches_pattern(path_str_norm, pattern):
            return "red", f"Matches red zone pattern: {pattern}"

    # Check green (before yellow because story/ paths overlap)
    for pattern in GREEN_PATTERNS:
        if _matches_pattern(path_str_norm, pattern):
            return "green", f"Matches green zone pattern: {pattern}"

    # Check yellow
    for pattern in YELLOW_PATTERNS:
        if _matches_pattern(path_str_norm, pattern):
            return "yellow", f"Matches yellow zone pattern: {pattern}"

    # Unknown
    return "yellow", "Unknown path — defaulting to yellow (conservative). Verify manually."


def classify_extended(path_str: str) -> tuple[str, str]:
    """Extended classification returning specific zone names.

    Zones:
      inkos_book_green   — green zone within books/<bookId>/
      inkos_book_yellow  — yellow zone within books/<bookId>/
      inkos_book_red     — red zone within books/<bookId>/
      design_manifest    — story-design/<id>/manifest.yaml
      design_source      — story-design/<id>/design/**
      compiled_inkos     — story-design/<id>/compile/inkos/**
      legacy_design      — story-design/<flat-file> (old layout)
      outside_project    — not under books/ or story-design/
    """
    normalized = path_str.replace("\\", "/").lstrip("./")

    # Design package paths
    if normalized.startswith("story-design/"):
        remainder = normalized[len("story-design/"):]

        # Legacy flat layout: story-design/00-project-brief.md etc
        if re.match(r"^\d{2}-", remainder) or remainder.startswith("inkos/"):
            return "legacy_design", f"Legacy flat design layout: {normalized}"

        # New layout: story-design/<design-id>/...
        parts = remainder.split("/", 1)
        if len(parts) < 2:
            # Just story-design/<design-id> with no subpath
            return "design_source", f"Design root: {normalized}"

        design_id, subpath = parts[0], parts[1]

        if subpath == "manifest.yaml":
            return "design_manifest", f"Design manifest for '{design_id}'"
        elif subpath.startswith("design/") or subpath == "design":
            return "design_source", f"Design source for '{design_id}'"
        elif subpath.startswith("compile/"):
            return "compiled_inkos", f"Compiled InkOS package for '{design_id}'"
        else:
            return "design_source", f"Design package file for '{design_id}'"

    # Book paths
    if normalized.startswith("books/"):
        zone, reason = classify(normalized)
        return f"inkos_book_{zone}", reason

    # Outside project
    return "outside_project", f"Path not under books/ or story-design/: {normalized}"


def main():
    parser = argparse.ArgumentParser(description="Classify InkOS file path into zone")
    parser.add_argument("path", help="File path (relative to project root)")
    parser.add_argument("--book-id", help="Book ID (for context)")
    parser.add_argument("--extended", action="store_true",
                        help="Use extended classification with specific zone names")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.extended:
        zone, reason = classify_extended(args.path)
    else:
        zone, reason = classify(args.path)

    if args.json:
        import json
        print(json.dumps({"path": args.path, "zone": zone, "reason": reason}))
    else:
        print(f"{zone.upper()}: {args.path}")
        print(f"  {reason}")

    # Exit codes: 0 = safe, 1 = forbidden, 2 = controlled
    if zone in ("red", "inkos_book_red"):
        sys.exit(1)
    elif zone in ("yellow", "inkos_book_yellow", "outside_project"):
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
