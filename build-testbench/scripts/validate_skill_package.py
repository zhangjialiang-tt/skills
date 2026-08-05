#!/usr/bin/env python3
"""Validate that every path referenced in SKILL.md exists in the skill package.

Lightweight self-check: scans SKILL.md for ``references/...``, ``assets/...``,
``scripts/...`` and ``docs/...`` tokens and confirms each target file exists.
Does NOT touch RTL parsing logic — safe to run anytime.

Exit code 0 = all referenced paths present, 1 = missing paths.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Match relative paths inside SKILL.md that point into the skill package.
# Captures things like references/foo.md, assets/bar.template, scripts/baz.py, docs/qux.md
REFERENCE_RE = re.compile(
    r"(?<![\w./-])((?:references|assets|scripts|docs)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+)"
)


def extract_referenced_paths(skill_md: Path) -> list[str]:
    """Return the set of package-relative paths mentioned in SKILL.md."""
    text = skill_md.read_text(encoding="utf-8")
    seen: list[str] = []
    for match in REFERENCE_RE.finditer(text):
        path = match.group(1)
        if path not in seen:
            seen.append(path)
    return seen


def validate(skill_root: Path) -> tuple[list[str], list[str]]:
    """Return (missing, present) lists of referenced paths."""
    skill_md = skill_root / "SKILL.md"
    missing: list[str] = []
    present: list[str] = []
    for rel in extract_referenced_paths(skill_md):
        # Normalize: strip any trailing punctuation that snuck in.
        rel = rel.rstrip(".,;:)")
        target = skill_root / rel
        if target.exists():
            present.append(rel)
        else:
            missing.append(rel)
    return missing, present


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate SKILL.md referenced paths exist in the package."
    )
    parser.add_argument(
        "--skill-root",
        default=str(Path(__file__).resolve().parent.parent),
        help="Skill root directory containing SKILL.md (default: this script's parent/..)",
    )
    args = parser.parse_args(argv)

    skill_root = Path(args.skill_root).resolve()
    skill_md = skill_root / "SKILL.md"
    if not skill_md.exists():
        print(f"ERROR: SKILL.md not found at {skill_md}", file=sys.stderr)
        return 1

    missing, present = validate(skill_root)
    print(f"Referenced paths checked: {len(present) + len(missing)}")
    print(f"  present: {len(present)}")
    print(f"  missing: {len(missing)}")
    for rel in sorted(missing):
        print(f"  MISSING: {rel}", file=sys.stderr)
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
