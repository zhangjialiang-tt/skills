"""test_lifecycle.py - 章节生命周期测试。

覆盖 prompt §13.2 要求的状态转换。
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_contract import (
    ALLOWED_CHAPTER_TRANSITIONS,
    can_commit_chapter_state,
    is_valid_chapter_transition,
)

class TestLifecycleTransitions:
    """章节生命周期状态转换。"""

    def test_planned_to_draft(self):
        assert is_valid_chapter_transition("PLANNED", "DRAFT")

    def test_draft_to_reviewed(self):
        assert is_valid_chapter_transition("DRAFT", "REVIEWED")

    def test_draft_to_accepted(self):
        assert is_valid_chapter_transition("DRAFT", "ACCEPTED")

    def test_reviewed_to_draft(self):
        assert is_valid_chapter_transition("REVIEWED", "DRAFT")

    def test_reviewed_to_accepted(self):
        assert is_valid_chapter_transition("REVIEWED", "ACCEPTED")

    def test_accepted_to_superseded(self):
        assert is_valid_chapter_transition("ACCEPTED", "SUPERSEDED")

    def test_accepted_to_deprecated(self):
        assert is_valid_chapter_transition("ACCEPTED", "DEPRECATED")

    def test_accepted_to_published(self):
        assert is_valid_chapter_transition("ACCEPTED", "PUBLISHED")


class TestInvalidTransitions:
    """未列出的状态转换必须被拒绝。"""

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            ("PLANNED", "ACCEPTED"),       # 不能跳过 DRAFT
            ("PLANNED", "REVIEWED"),       # 不能跳过 DRAFT
            ("DRAFT", "PUBLISHED"),        # 不能跳过 ACCEPTED
            ("DRAFT", "SUPERSEDED"),       # 不能跳过 ACCEPTED
            ("DRAFT", "DEPRECATED"),       # 不能跳过 ACCEPTED
            ("REVIEWED", "PUBLISHED"),     # 不能跳过 ACCEPTED
            ("REVIEWED", "SUPERSEDED"),    # 不能跳过 ACCEPTED
            ("SUPERSEDED", "DRAFT"),       # 终态不可转换
            ("DEPRECATED", "DRAFT"),       # 终态不可转换
            ("PUBLISHED", "DRAFT"),        # 终态不可转换
            ("ACCEPTED", "DRAFT"),         # 不能回退到 DRAFT
            ("ACCEPTED", "REVIEWED"),      # 不能回退到 REVIEWED
            ("PLANNED", "PUBLISHED"),      # 不能跳过所有中间状态
        ],
    )
    def test_invalid_transition(self, from_state, to_state):
        assert not is_valid_chapter_transition(from_state, to_state), (
            f"{from_state} -> {to_state} 应被拒绝"
        )


class TestCommitEligibility:
    """COMMIT_CHAPTER_STATE 来源状态限制。"""

    def test_accepted_can_commit(self):
        assert can_commit_chapter_state("ACCEPTED")

    def test_published_can_commit(self):
        assert can_commit_chapter_state("PUBLISHED")

    @pytest.mark.parametrize(
        "status",
        ["PLANNED", "DRAFT", "REVIEWED", "SUPERSEDED", "DEPRECATED"],
    )
    def test_non_eligible_cannot_commit(self, status):
        assert not can_commit_chapter_state(status), (
            f"{status} 不应允许 COMMIT_CHAPTER_STATE"
        )


class TestTerminalStates:
    """终态不可再转换。"""

    @pytest.mark.parametrize("terminal", ["SUPERSEDED", "DEPRECATED", "PUBLISHED"])
    def test_terminal_no_outgoing(self, terminal):
        """终态没有任何出向转换。"""
        outgoing = [
            (from_state, to_state)
            for from_state, to_state in ALLOWED_CHAPTER_TRANSITIONS
            if from_state == terminal
        ]
        assert outgoing == [], f"{terminal} 不应有出向转换"
