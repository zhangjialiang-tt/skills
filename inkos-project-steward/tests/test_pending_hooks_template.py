"""Tests for inkos-story-steward/templates/inkos/pending-hooks.md.

Replicates InkOS parsePendingHooksMarkdown() behavior to verify the template
produces exactly the expected hooks with valid field values.
"""
import re
from pathlib import Path

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "inkos" / "pending-hooks.md"


# ---------------------------------------------------------------------------
# Local re-implementations matching InkOS source (Narcooo/inkos master)
# ---------------------------------------------------------------------------

def parse_markdown_table_rows(markdown: str) -> list[list[str]]:
    return [
        [cell.strip() for cell in line.split("|")[1:-1]]
        for line in markdown.split("\n")
        if line.strip().startswith("|")
        and "---" not in line
        and any(cell.strip() for cell in line.split("|")[1:-1])
    ]


def normalize_hook_id(value: str) -> str:
    normalized = value.strip()
    for pat in [r"^`(.+)$", r"^\*\*(.+)\*\*$", r"^\*(.+)\*$"]:
        m = re.match(pat, normalized)
        if m:
            normalized = m.group(1).strip()
    normalized = re.sub(r"-{2,}", "-", normalized).strip("- ").strip()
    return normalized if re.search(r"[a-z0-9\u4e00-\u9fff]", normalized, re.I) else ""


def parse_pending_hooks(markdown: str) -> list[dict]:
    rows = parse_markdown_table_rows(markdown)
    rows = [r for r in rows if (r[0] if r else "").lower() != "hook_id"]
    if rows:
        return [
            {"hook_id": normalize_hook_id(r[0]), "row": r}
            for r in rows
            if normalize_hook_id(r[0])
        ]
    # Fallback: bullet lines
    lines = [
        l.strip().lstrip("- ")
        for l in markdown.split("\n")
        if l.strip().startswith("-")
    ]
    return [{"hook_id": f"hook-{i+1}", "notes": l} for i, l in enumerate(lines) if l]


# ---------------------------------------------------------------------------
# Column indices (0-based) matching the template header
# ---------------------------------------------------------------------------
COL_HOOK_ID = 0
COL_STATUS = 3
COL_PAYOFF_TIMING = 6
COL_PROMOTED = 11
EXPECTED_COLUMNS = 13

VALID_STATUSES = {"open", "progressing", "deferred", "resolved"}
VALID_TIMINGS = {"immediate", "near-term", "mid-arc", "slow-burn", "endgame", ""}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _load_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def _hooks() -> list[dict]:
    return parse_pending_hooks(_load_template())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_exactly_two_hooks():
    hooks = _hooks()
    assert len(hooks) == 2, f"Expected 2 hooks, got {len(hooks)}: {[h['hook_id'] for h in hooks]}"


def test_hook_ids_are_h001_h002():
    ids = [h["hook_id"] for h in _hooks()]
    assert ids == ["H001", "H002"], f"Unexpected hook ids: {ids}"


def test_no_fake_hooks_from_field_description():
    """The 字段说明 section uses bullet lists, not a table.
    parse_pending_hooks must NOT produce hooks from it."""
    hooks = _hooks()
    hook_ids = {h["hook_id"] for h in hooks}
    # Field description bullets start with bold field names like **hook_id**
    # None of them should appear as hook ids
    for hid in hook_ids:
        assert hid in ("H001", "H002"), f"Fake hook detected from field description: {hid}"


def test_status_values_valid():
    for h in _hooks():
        row = h["row"]
        status = row[COL_STATUS].strip().lower()
        assert status in VALID_STATUSES, (
            f"Hook {h['hook_id']}: invalid status '{row[COL_STATUS]}', "
            f"expected one of {VALID_STATUSES}"
        )


def test_payoff_timing_valid():
    for h in _hooks():
        row = h["row"]
        timing = row[COL_PAYOFF_TIMING].strip().lower()
        assert timing in VALID_TIMINGS, (
            f"Hook {h['hook_id']}: invalid timing '{row[COL_PAYOFF_TIMING]}', "
            f"expected one of {VALID_TIMINGS}"
        )


def test_promoted_semantics():
    """'是' means promoted=True (active hook debt); '否' means seed."""
    for h in _hooks():
        row = h["row"]
        promoted_raw = row[COL_PROMOTED].strip()
        assert promoted_raw in ("是", "否"), (
            f"Hook {h['hook_id']}: promoted value '{promoted_raw}' must be '是' or '否'"
        )
        is_promoted = promoted_raw == "是"
        # H001 should be promoted (是), H002 should be seed (否)
        if h["hook_id"] == "H001":
            assert is_promoted, "H001 should be promoted (是)"
        elif h["hook_id"] == "H002":
            assert not is_promoted, "H002 should be seed (否)"


def test_13_columns():
    rows = parse_markdown_table_rows(_load_template())
    # Skip header row
    data_rows = [r for r in rows if (r[0] if r else "").lower() != "hook_id"]
    for i, row in enumerate(data_rows):
        assert len(row) == EXPECTED_COLUMNS, (
            f"Row {i}: expected {EXPECTED_COLUMNS} columns, got {len(row)}: {row}"
        )
