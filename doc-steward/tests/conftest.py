"""Shared test fixtures for doc-steward tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import tempfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project with .doc-steward/registry.yaml."""
    project = tmp_path / "project"
    project.mkdir()
    steward_dir = project / ".doc-steward"
    steward_dir.mkdir()
    
    registry = {
        "version": "1.0",
        "config": {
            "document_roots": ["docs"],
            "exclude": [],
        },
        "documents": [],
    }
    
    reg_path = steward_dir / "registry.yaml"
    reg_path.write_text(yaml.dump(registry, default_flow_style=False), encoding="utf-8")
    
    docs_dir = project / "docs"
    docs_dir.mkdir()
    
    return project


@pytest.fixture
def registry_with_docs(tmp_project: Path) -> Path:
    """Create a project with several documents in various states."""
    docs_dir = tmp_project / "docs"
    
    # Create documents
    (docs_dir / "system-design.md").write_text("# System Design\n\nv1\n", encoding="utf-8")
    (docs_dir / "api-spec.md").write_text("# API Spec\n\nDraft\n", encoding="utf-8")
    (docs_dir / "release-plan.md").write_text("# Release Plan\n\nFrozen\n", encoding="utf-8")
    
    archive_dir = docs_dir / "archive"
    archive_dir.mkdir()
    (archive_dir / "old-design.md").write_text("# Old Design\n\nSuperseded\n", encoding="utf-8")
    
    # Update registry
    reg_path = tmp_project / ".doc-steward" / "registry.yaml"
    registry = {
        "version": "1.0",
        "config": {
            "document_roots": ["docs"],
            "exclude": ["docs/archive"],
        },
        "documents": [
            {
                "doc_id": "DOC-SYSTEM-DESIGN",
                "title": "System Design",
                "path": "docs/system-design.md",
                "type": "design",
                "status": "ACTIVE",
                "revision": 3,
                "content_hash": "a" * 64,
                "created_at": "2026-06-30",
                "updated_at": "2026-07-26",
                "assigned_domain": ["architecture"],
                "source_of_truth": True,
                "superseded_by": None,
                "supersedes": [],
                "depends_on": [],
                "stale": False,
                "stale_dependency": False,
                "purpose": "System architecture",
                "attention": {"level": "normal"},
                "decision": {"by": "user", "at": "2026-07-10", "reason": "approved"},
            },
            {
                "doc_id": "DOC-API-SPEC",
                "title": "API Spec",
                "path": "docs/api-spec.md",
                "type": "design",
                "status": "DRAFT",
                "revision": 1,
                "content_hash": "b" * 64,
                "created_at": "2026-07-20",
                "updated_at": "2026-07-20",
                "assigned_domain": ["api"],
                "source_of_truth": False,
                "superseded_by": None,
                "supersedes": [],
                "depends_on": ["DOC-SYSTEM-DESIGN"],
                "stale": False,
                "stale_dependency": False,
                "purpose": "API specification",
                "attention": {"level": "normal"},
                "decision": {"by": "user", "at": "2026-07-20", "reason": "initial"},
            },
            {
                "doc_id": "DOC-RELEASE-PLAN",
                "title": "Release Plan",
                "path": "docs/release-plan.md",
                "type": "plan",
                "status": "FROZEN",
                "revision": 4,
                "content_hash": "c" * 64,
                "created_at": "2026-05-01",
                "updated_at": "2026-06-01",
                "assigned_domain": ["release"],
                "source_of_truth": True,
                "superseded_by": None,
                "supersedes": [],
                "depends_on": ["DOC-SYSTEM-DESIGN"],
                "stale": False,
                "stale_dependency": False,
                "purpose": "v1.0 release",
                "attention": {"level": "normal"},
                "decision": {"by": "user", "at": "2026-06-01", "reason": "frozen"},
            },
            {
                "doc_id": "DOC-OLD-DESIGN",
                "title": "Old Design",
                "path": "docs/archive/old-design.md",
                "type": "design",
                "status": "SUPERSEDED",
                "revision": 1,
                "content_hash": "d" * 64,
                "created_at": "2026-04-01",
                "updated_at": "2026-07-10",
                "assigned_domain": ["architecture"],
                "source_of_truth": False,
                "superseded_by": "DOC-SYSTEM-DESIGN@r3",
                "supersedes": [],
                "depends_on": [],
                "stale": False,
                "stale_dependency": False,
                "purpose": "superseded by v3",
                "attention": {"level": "normal"},
                "decision": {"by": "user", "at": "2026-07-10", "reason": "superseded"},
            },
        ],
    }
    
    reg_path.write_text(yaml.dump(registry, default_flow_style=False), encoding="utf-8")
    return tmp_project
