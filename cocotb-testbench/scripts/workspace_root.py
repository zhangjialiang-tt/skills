#!/usr/bin/env python3
"""Locate the workspace root containing the nearest .git entry."""

from __future__ import annotations

import argparse
from pathlib import Path


def find_workspace_root(start: Path) -> Path:
    # Keep the lexical workspace path. RTL trees are often exposed through a
    # junction/symlink; resolving it would jump outside the workspace and hide
    # the workspace's own .git entry.
    current = start.absolute()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise FileNotFoundError(f"no workspace root containing .git found above {start}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Find the nearest workspace root.")
    parser.add_argument("--start", default=".", help="File or directory to start from")
    args = parser.parse_args()
    print(find_workspace_root(Path(args.start)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
