#!/usr/bin/env python3
"""Design-id derivation and manifest utilities for inkos-story-steward.

design-id rules (frozen):
1. Derived from work title.
2. Remove Windows-illegal path characters: \\ / : * ? " < > |
3. Strip trailing dots and spaces.
4. Collapse internal whitespace to single hyphen.
5. Empty result → "untitled-story".
6. Chinese and other Unicode letters preserved.
7. No third-party slug dependency.
"""

import re
from pathlib import Path

# Windows illegal characters in filenames
_ILLEGAL_CHARS = re.compile(r'[\\/:*?"<>|]')
# Whitespace sequences
_WHITESPACE = re.compile(r'\s+')


def derive_design_id(title: str) -> str:
    """Derive a filesystem-safe design-id from a work title.

    Examples:
        "活着的死者" → "活着的死者"
        "测试:故事?第一部" → "测试故事第一部"
        "  My Story  " → "My-Story"
        "" → "untitled-story"
        ":::" → "untitled-story"
    """
    # Remove illegal characters
    cleaned = _ILLEGAL_CHARS.sub('', title)
    # Strip leading/trailing whitespace and dots
    cleaned = cleaned.strip().strip('.')
    # Collapse internal whitespace to hyphen
    cleaned = _WHITESPACE.sub('-', cleaned.strip())
    # Strip again after collapse
    cleaned = cleaned.strip('-').strip('.')

    if not cleaned:
        return "untitled-story"
    return cleaned


# Valid lifecycle states
VALID_STATES = frozenset([
    "draft", "reviewing", "ready_to_create",
    "creating", "created", "aligned", "archived",
])

# Valid state transitions (from → set of allowed targets)
VALID_TRANSITIONS = {
    "draft": {"reviewing", "ready_to_create", "archived"},
    "reviewing": {"draft", "ready_to_create", "archived"},
    "ready_to_create": {"creating", "draft", "archived"},
    "creating": {"created", "ready_to_create"},  # failure → back to ready
    "created": {"aligned", "archived"},
    "aligned": {"archived"},
    "archived": set(),  # terminal
}

# Valid gate values
VALID_GATE_VALUES = frozenset(["pending", "passed", "accepted_with_risk"])


def validate_transition(current: str, target: str) -> bool:
    """Check if a lifecycle state transition is legal."""
    if current not in VALID_TRANSITIONS:
        return False
    return target in VALID_TRANSITIONS[current]


def find_design_root(project_root: Path, design_id: str) -> Path:
    """Return the design root path for a given design-id."""
    return project_root / "story-design" / design_id


def find_manifest(project_root: Path, design_id: str) -> Path | None:
    """Find manifest.yaml for a design-id, or None."""
    manifest = find_design_root(project_root, design_id) / "manifest.yaml"
    return manifest if manifest.exists() else None


def detect_legacy_layout(project_root: Path) -> bool:
    """Detect old flat story-design/ layout without design-id isolation."""
    sd = project_root / "story-design"
    if not sd.is_dir():
        return False
    # Legacy: has 00-project-brief.md directly, no */manifest.yaml
    has_flat = (sd / "00-project-brief.md").exists()
    has_manifest = any(sd.glob("*/manifest.yaml"))
    return has_flat and not has_manifest


def find_all_manifests(project_root: Path) -> list[Path]:
    """Find all manifest.yaml files under story-design/."""
    sd = project_root / "story-design"
    if not sd.is_dir():
        return []
    return sorted(sd.glob("*/manifest.yaml"))


def find_manifests_for_book(project_root: Path, book_id: str) -> list[Path]:
    """Find all manifests that claim binding to a given book_id."""
    import yaml
    results = []
    for manifest_path in find_all_manifests(project_root):
        try:
            data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            if data and data.get("inkos", {}).get("book_id") == book_id:
                results.append(manifest_path)
        except Exception:
            continue
    return results
