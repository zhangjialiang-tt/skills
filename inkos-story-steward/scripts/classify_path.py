#!/usr/bin/env python3
"""Classify a file path into red/yellow/green zone.

Usage:
    python scripts/classify_path.py <relative-path> [--book-id ID]

Output: zone (green|yellow|red) + reason.
Exit: 0 = green (safe to write), 1 = red (forbidden), 2 = yellow (controlled).
"""

import argparse
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
    "chapters/",  # any chapter file
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
    """Return (zone, reason) for a path relative to book root."""
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


def main():
    parser = argparse.ArgumentParser(description="Classify InkOS file path into zone")
    parser.add_argument("path", help="File path (relative to book root or project root)")
    parser.add_argument("--book-id", help="Book ID (for context, not used in classification)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    zone, reason = classify(args.path)

    if args.json:
        import json
        print(json.dumps({"path": args.path, "zone": zone, "reason": reason}))
    else:
        print(f"{zone.upper()}: {args.path}")
        print(f"  {reason}")

    if zone == "red":
        sys.exit(1)
    elif zone == "yellow":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
