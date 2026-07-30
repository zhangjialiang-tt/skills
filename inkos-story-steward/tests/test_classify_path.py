"""Tests for classify_path.py — zone classification of InkOS file paths."""

import sys
from pathlib import PurePosixPath

import pytest

sys.path.insert(0, "inkos-story-steward/scripts")
from classify_path import classify


# --- Green zone ---


def test_green_author_intent():
    zone, reason = classify("books/test/story/author_intent.md")
    assert zone == "green"


def test_green_book_rules():
    zone, reason = classify("books/test/story/book_rules.md")
    assert zone == "green"


def test_green_roles():
    zone, reason = classify("books/test/story/roles/主要角色/林远.md")
    assert zone == "green"


def test_green_outline():
    zone, reason = classify("books/test/story/outline/story_frame.md")
    assert zone == "green"


# --- Yellow zone ---


def test_yellow_pending_hooks():
    zone, reason = classify("books/test/story/pending_hooks.md")
    assert zone == "yellow"


def test_yellow_chapter():
    zone, reason = classify("books/test/chapters/001_foo.md")
    assert zone == "yellow"


def test_yellow_book_json():
    zone, reason = classify("books/test/book.json")
    assert zone == "yellow"


# --- Red zone ---


def test_red_index_json():
    zone, reason = classify("books/test/chapters/index.json")
    assert zone == "red"


def test_red_runtime():
    zone, reason = classify("books/test/story/runtime/x.json")
    assert zone == "red"


def test_red_snapshots():
    zone, reason = classify("books/test/story/snapshots/3/data.json")
    assert zone == "red"


def test_red_memory_db():
    zone, reason = classify("books/test/story/memory.db")
    assert zone == "red"


def test_red_write_lock():
    zone, reason = classify("books/test/.write.lock")
    assert zone == "red"


# --- Default / edge cases ---


def test_unknown_books_path_defaults_yellow():
    zone, reason = classify("books/test/some_unknown_file.xyz")
    assert zone == "yellow"


# Regression guard: a naive startswith(pattern) without component boundary
# would cause "story/runtime-backup.md" to match red pattern "story/runtime".
# The _matches_pattern helper now requires exact match or pattern + "/" prefix.
def test_runtime_backup_not_red():
    """story/runtime-backup.md must NOT be classified red — it is not inside story/runtime/."""
    zone, reason = classify("books/test/story/runtime-backup.md")
    assert zone != "red", (
        f"Prefix collision: 'story/runtime-backup.md' incorrectly matched red pattern "
        f"'story/runtime' via startswith. Got zone={zone!r}, reason={reason!r}"
    )


def test_roles_backup_not_green():
    """story/roles-backup/x.md must NOT be green — 'roles/' pattern has trailing slash so no collision."""
    zone, reason = classify("books/test/story/roles-backup/x.md")
    assert zone != "green", (
        f"Prefix collision: 'story/roles-backup/x.md' incorrectly matched green pattern "
        f"'story/roles/'. Got zone={zone!r}, reason={reason!r}"
    )
