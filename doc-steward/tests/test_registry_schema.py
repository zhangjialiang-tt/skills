"""Tests for Schema validation."""

from __future__ import annotations

import pytest

from _core import validate_registry_against_schema


class TestSchemaValidation:
    """Test registry schema validation."""
    
    def test_valid_registry_loads(self):
        registry = {
            "version": "1.0",
            "config": {"document_roots": ["docs"], "exclude": []},
            "documents": [],
        }
        errors = validate_registry_against_schema(registry)
        assert errors == []
    
    def test_missing_required_field_rejected(self):
        registry = {"config": {}, "documents": []}
        errors = validate_registry_against_schema(registry)
        assert any("version" in e for e in errors)
    
    def test_invalid_status_rejected(self):
        registry = {
            "version": "1.0",
            "config": {},
            "documents": [
                {
                    "doc_id": "DOC-X",
                    "path": "docs/x.md",
                    "status": "INVALID",
                    "revision": 1,
                    "content_hash": "aa" * 64,
                    "updated_at": "2026-07-29",
                    "decision": {"by": "user", "at": "2026-07-29", "reason": "test"},
                }
            ],
        }
        errors = validate_registry_against_schema(registry)
        assert any("INVALID" in e for e in errors)
    
    def test_invalid_doc_id_pattern_rejected(self):
        registry = {
            "version": "1.0",
            "config": {},
            "documents": [
                {
                    "doc_id": "lowercase",
                    "path": "docs/x.md",
                    "status": "DRAFT",
                    "revision": 1,
                    "content_hash": "aa" * 64,
                    "updated_at": "2026-07-29",
                    "decision": {"by": "user", "at": "2026-07-29", "reason": "test"},
                }
            ],
        }
        errors = validate_registry_against_schema(registry)
        assert any("invalid doc_id" in e for e in errors)
    
    def test_superseded_without_superseded_by_rejected(self):
        registry = {
            "version": "1.0",
            "config": {},
            "documents": [
                {
                    "doc_id": "DOC-X",
                    "path": "docs/x.md",
                    "status": "SUPERSEDED",
                    "revision": 1,
                    "content_hash": "aa" * 64,
                    "updated_at": "2026-07-29",
                    "decision": {"by": "user", "at": "2026-07-29", "reason": "test"},
                }
            ],
        }
        errors = validate_registry_against_schema(registry)
        assert any("superseded_by" in e for e in errors)
    
    def test_archived_without_archive_rejected(self):
        registry = {
            "version": "1.0",
            "config": {},
            "documents": [
                {
                    "doc_id": "DOC-X",
                    "path": "docs/x.md",
                    "status": "ARCHIVED",
                    "revision": 1,
                    "content_hash": "aa" * 64,
                    "updated_at": "2026-07-29",
                    "decision": {"by": "user", "at": "2026-07-29", "reason": "test"},
                }
            ],
        }
        errors = validate_registry_against_schema(registry)
        assert any("archive" in e for e in errors)
    
    def test_duplicate_doc_id_rejected(self):
        registry = {
            "version": "1.0",
            "config": {},
            "documents": [
                {
                    "doc_id": "DOC-X",
                    "path": "docs/x1.md",
                    "status": "DRAFT",
                    "revision": 1,
                    "content_hash": "aa" * 64,
                    "updated_at": "2026-07-29",
                    "decision": {"by": "user", "at": "2026-07-29", "reason": "test"},
                },
                {
                    "doc_id": "DOC-X",
                    "path": "docs/x2.md",
                    "status": "DRAFT",
                    "revision": 1,
                    "content_hash": "bb" * 64,
                    "updated_at": "2026-07-29",
                    "decision": {"by": "user", "at": "2026-07-29", "reason": "test"},
                },
            ],
        }
        errors = validate_registry_against_schema(registry)
        assert any("duplicate doc_id" in e for e in errors)
    
    def test_duplicate_path_rejected(self):
        registry = {
            "version": "1.0",
            "config": {},
            "documents": [
                {
                    "doc_id": "DOC-X",
                    "path": "docs/x.md",
                    "status": "DRAFT",
                    "revision": 1,
                    "content_hash": "aa" * 64,
                    "updated_at": "2026-07-29",
                    "decision": {"by": "user", "at": "2026-07-29", "reason": "test"},
                },
                {
                    "doc_id": "DOC-Y",
                    "path": "docs/x.md",
                    "status": "DRAFT",
                    "revision": 1,
                    "content_hash": "bb" * 64,
                    "updated_at": "2026-07-29",
                    "decision": {"by": "user", "at": "2026-07-29", "reason": "test"},
                },
            ],
        }
        errors = validate_registry_against_schema(registry)
        assert any("duplicate path" in e for e in errors)
