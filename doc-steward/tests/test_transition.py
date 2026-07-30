"""Tests for state transitions."""

from __future__ import annotations

import pytest

from _core import (
    transition_is_allowed,
    transition_is_tier2,
    assert_valid_transition,
    ALLOWED_TRANSITIONS,
)


class TestTransitionMatrix:
    """Test state transition rules."""
    
    def test_draft_to_reviewing_allowed(self):
        assert transition_is_allowed("DRAFT", "REVIEWING")
    
    def test_reviewing_to_active_allowed(self):
        assert transition_is_allowed("REVIEWING", "ACTIVE")
    
    def test_active_to_frozen_allowed(self):
        assert transition_is_allowed("ACTIVE", "FROZEN")
    
    def test_frozen_to_active_allowed(self):
        assert transition_is_allowed("FROZEN", "ACTIVE")
    
    def test_active_to_superseded_allowed(self):
        assert transition_is_allowed("ACTIVE", "SUPERSEDED")
    
    def test_archived_to_superseded_allowed(self):
        assert transition_is_allowed("ARCHIVED", "SUPERSEDED")
    
    def test_skip_level_draft_to_active_rejected(self):
        assert not transition_is_allowed("DRAFT", "ACTIVE")
    
    def test_skip_level_reviewing_to_frozen_rejected(self):
        assert not transition_is_allowed("REVIEWING", "FROZEN")
    
    def test_resurrection_superseded_to_draft_rejected(self):
        assert not transition_is_allowed("SUPERSEDED", "DRAFT")
    
    def test_resurrection_archived_to_draft_rejected(self):
        assert not transition_is_allowed("ARCHIVED", "DRAFT")
    def test_same_status_noop(self):
        """Same status is always allowed (no-op)."""
        for status in ["DRAFT", "REVIEWING", "ACTIVE", "FROZEN", "SUPERSEDED", "ARCHIVED"]:
            # Same status is a no-op, assert_valid_transition treats it as valid
            assert_valid_transition(status, status)


class TestTier2Transitions:
    """Test Tier2 approval requirements."""
    
    def test_active_to_frozen_is_tier2(self):
        assert transition_is_tier2("ACTIVE", "FROZEN")
    
    def test_frozen_to_active_is_tier2(self):
        assert transition_is_tier2("FROZEN", "ACTIVE")
    
    def test_active_to_superseded_is_tier2(self):
        assert transition_is_tier2("ACTIVE", "SUPERSEDED")
    
    def test_draft_to_reviewing_not_tier2(self):
        assert not transition_is_tier2("DRAFT", "REVIEWING")
    
    def test_reviewing_to_active_not_tier2(self):
        assert not transition_is_tier2("REVIEWING", "ACTIVE")


class TestAssertValidTransition:
    """Test assert_valid_transition function."""
    
    def test_legal_transition_no_error(self):
        assert_valid_transition("DRAFT", "REVIEWING")
    
    def test_illegal_transition_raises(self):
        with pytest.raises(ValueError, match="illegal transition"):
            assert_valid_transition("DRAFT", "ACTIVE")
    
    def test_same_status_no_error(self):
        assert_valid_transition("ACTIVE", "ACTIVE")
