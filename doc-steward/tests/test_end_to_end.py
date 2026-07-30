"""End-to-end tests for doc-steward workflows."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


def run_doc_steward(project: Path, *args: str) -> subprocess.CompletedProcess:
    """Run doc_steward.py in the project directory."""
    cmd = [
        sys.executable,
        str(Path(__file__).parent.parent / "scripts" / "doc_steward.py"),
        "--root", str(project),
        *args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


class TestInspect:
    """Test inspect command."""
    
    def test_inspect_empty_registry(self, tmp_project: Path):
        result = run_doc_steward(tmp_project, "inspect")
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "new" in output
        assert "modified" in output
        assert "missing" in output
    
    def test_inspect_with_docs(self, registry_with_docs: Path):
        result = run_doc_steward(registry_with_docs, "inspect")
        assert result.returncode == 0
        output = json.loads(result.stdout)
        # docs exist but hashes don't match registry → modified
        assert len(output["modified"]) >= 1


class TestFocus:
    """Test focus command."""
    
    def test_focus_empty_registry(self, tmp_project: Path):
        result = run_doc_steward(tmp_project, "focus")
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "blocked" in output
        assert "needs_attention" in output
        assert "change_only" in output
        assert "no_need" in output
    
    def test_focus_detects_conflict(self, tmp_project: Path):
        """Test that focus detects source-of-truth conflicts."""
        reg_path = tmp_project / ".doc-steward" / "registry.yaml"
        docs_dir = tmp_project / "docs"
        (docs_dir / "a.md").write_text("# A\n", encoding="utf-8")
        (docs_dir / "b.md").write_text("# B\n", encoding="utf-8")
        
        registry = {
            "version": "1.0",
            "config": {"document_roots": ["docs"], "exclude": []},
            "documents": [
                {
                    "doc_id": "DOC-A",
                    "title": "A",
                    "path": "docs/a.md",
                    "type": "design",
                    "status": "ACTIVE",
                    "revision": 1,
                    "content_hash": "aa" * 64,
                    "created_at": "2026-07-29",
                    "updated_at": "2026-07-29",
                    "assigned_domain": ["arch"],
                    "source_of_truth": True,
                    "superseded_by": None,
                    "supersedes": [],
                    "depends_on": [],
                    "stale": False,
                    "stale_dependency": False,
                    "purpose": "A",
                    "attention": {"level": "normal"},
                    "decision": {"by": "user", "at": "2026-07-29", "reason": "test"},
                },
                {
                    "doc_id": "DOC-B",
                    "title": "B",
                    "path": "docs/b.md",
                    "type": "design",
                    "status": "ACTIVE",
                    "revision": 1,
                    "content_hash": "bb" * 64,
                    "created_at": "2026-07-29",
                    "updated_at": "2026-07-29",
                    "assigned_domain": ["arch"],
                    "source_of_truth": True,
                    "superseded_by": None,
                    "supersedes": [],
                    "depends_on": [],
                    "stale": False,
                    "stale_dependency": False,
                    "purpose": "B",
                    "attention": {"level": "normal"},
                    "decision": {"by": "user", "at": "2026-07-29", "reason": "test"},
                },
            ],
        }
        reg_path.write_text(yaml.dump(registry, default_flow_style=False), encoding="utf-8")
        
        result = run_doc_steward(tmp_project, "focus")
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert len(output["blocked"]) > 0
        assert any("conflict" in str(b).lower() or "source_of_truth" in str(b).lower() for b in output["blocked"])


class TestValidate:
    """Test validate command."""
    
    def test_validate_valid_registry(self, registry_with_docs: Path):
        result = run_doc_steward(registry_with_docs, "validate")
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["valid"] is True
    
    def test_validate_invalid_registry(self, tmp_project: Path):
        """Test that validate catches schema errors."""
        reg_path = tmp_project / ".doc-steward" / "registry.yaml"
        registry = {
            "version": "1.0",
            "config": {},
            "documents": [
                {
                    "doc_id": "bad-id",  # lowercase
                    "path": "docs/x.md",
                    "status": "DRAFT",
                    "revision": 1,
                    "content_hash": "aa" * 64,
                    "updated_at": "2026-07-29",
                    "decision": {"by": "user", "at": "2026-07-29", "reason": "test"},
                }
            ],
        }
        reg_path.write_text(yaml.dump(registry, default_flow_style=False), encoding="utf-8")
        
        result = run_doc_steward(tmp_project, "validate")
        assert result.returncode == 2  # validation error
        output = json.loads(result.stdout)
        assert output["valid"] is False
        assert len(output["schema_errors"]) > 0


class TestTransitionDryRun:
    """Test transition dry-run."""
    
    def test_dry_run_no_changes(self, registry_with_docs: Path):
        result = run_doc_steward(
            registry_with_docs, "transition", "DOC-API-SPEC", "REVIEWING",
            "--reason", "ready for review", "--dry-run"
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "operations" in output
    
    def test_illegal_transition_rejected(self, registry_with_docs: Path):
        result = run_doc_steward(
            registry_with_docs, "transition", "DOC-API-SPEC", "FROZEN",
            "--reason", "skip level", "--dry-run"
        )
        assert result.returncode == 2  # illegal transition


class TestSupersedeDryRun:
    """Test supersede dry-run."""
    
    def test_dry_run_shows_change_set(self, registry_with_docs: Path):
        result = run_doc_steward(
            registry_with_docs, "supersede", "DOC-OLD-DESIGN", "DOC-SYSTEM-DESIGN",
            "--by", "user", "--reason", "replaced by v3", "--dry-run"
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "operations" in output


class TestArchiveDryRun:
    """Test archive dry-run."""
    
    def test_dry_run_shows_change_set(self, registry_with_docs: Path):
        result = run_doc_steward(
            registry_with_docs, "archive", "DOC-RELEASE-PLAN",
            "--reason", "old release", "--dry-run"
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "operations" in output
