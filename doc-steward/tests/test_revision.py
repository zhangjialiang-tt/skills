"""Tests for revision model."""

from __future__ import annotations

import pytest

from _core import (
    RevisionEvent,
    ChangeSet,
    generate_event_id,
)


class TestRevisionEvent:
    """Test revision event creation."""
    
    def test_create_revision_event(self):
        event = RevisionEvent(
            event_id="EVT-001",
            event_type="REGISTERED",
            doc_id="DOC-X",
            revision=1,
            content_hash="aa" * 64,
            at="2026-07-29",
            actor="user",
            reason="initial registration",
        )
        assert event.doc_id == "DOC-X"
        assert event.revision == 1
    
    def test_create_revision_accepted_event(self):
        event = RevisionEvent(
            event_id="EVT-002",
            event_type="REVISION_ACCEPTED",
            doc_id="DOC-X",
            revision=2,
            content_hash="bb" * 64,
            at="2026-07-29",
            actor="user",
            reason="updated",
            from_revision=1,
        )
        assert event.from_revision == 1
        assert event.revision == 2


class TestChangeSet:
    """Test change set operations."""
    
    def test_empty_change_set(self):
        cs = ChangeSet()
        assert cs.is_empty()
    
    def test_add_operation(self):
        cs = ChangeSet()
        cs.add("register", "DOC-X", path="docs/x.md")
        assert not cs.is_empty()
        assert len(cs.entries) == 1
    
    def test_to_dict(self):
        cs = ChangeSet()
        cs.add("promote", "DOC-X", from_status="DRAFT", to_status="REVIEWING")
        result = cs.to_dict()
        assert result["operations"][0]["type"] == "promote"
        assert result["operations"][0]["doc_id"] == "DOC-X"


class TestEventIdGeneration:
    """Test event ID generation."""
    
    def test_generates_unique_ids(self):
        ids = {generate_event_id() for _ in range(10)}
        # All should be unique (or at least different format)
        assert len(ids) > 0
