"""Tests for revision closure (Milestone B)."""

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


def test_register_creates_r1_snapshot(tmp_path: Path):
    """Test that register auto-saves r1 snapshot."""
    project = tmp_path / "project"
    project.mkdir()
    steward_dir = project / ".doc-steward"
    steward_dir.mkdir()
    
    reg_path = steward_dir / "registry.yaml"
    reg_path.write_text(yaml.dump({
        "version": "1.0",
        "config": {"document_roots": ["docs"], "exclude": []},
        "documents": [],
    }, default_flow_style=False), encoding="utf-8")
    
    docs_dir = project / "docs"
    docs_dir.mkdir()
    (docs_dir / "test-doc.md").write_text("# Test\n\nv1\n", encoding="utf-8")
    
    result = run_doc_steward(project, "register", "docs/test-doc.md",
                            "--doc-id", "DOC-TEST", "--reason", "initial")
    
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["action"] == "register"
    
    # Check snapshot was created
    snap_path = steward_dir / "snapshots" / "DOC-TEST"
    assert snap_path.exists()
    assert len(list(snap_path.glob("*.md"))) == 1
    
    # Check history was recorded
    reg = yaml.safe_load(reg_path.read_text())
    doc = reg["documents"][0]
    assert "history" in doc
    assert len(doc["history"]) == 1
    assert doc["history"][0]["event_type"] == "REGISTERED"


def test_content_drift_detection(tmp_path: Path):
    """Test that content drift is detected when file changes."""
    project = tmp_path / "project"
    project.mkdir()
    steward_dir = project / ".doc-steward"
    steward_dir.mkdir()
    
    docs_dir = project / "docs"
    docs_dir.mkdir()
    doc_path = docs_dir / "test-doc.md"
    doc_path.write_text("# Test\n\nv1\n", encoding="utf-8")
    
    # Register first
    result = run_doc_steward(project, "register", "docs/test-doc.md",
                            "--doc-id", "DOC-TEST", "--reason", "initial")
    assert result.returncode == 0
    
    # Now modify the file
    doc_path.write_text("# Test\n\nv2 - updated\n", encoding="utf-8")
    
    # Inspect should show modified
    result = run_doc_steward(project, "inspect")
    assert result.returncode == 0
    output = json.loads(result.stdout)
    
    # Should have modified entries
    assert len(output["modified"]) >= 1
    modified_doc = [m for m in output["modified"] if m["doc_id"] == "DOC-TEST"]
    assert len(modified_doc) == 1


def test_revision_not_auto_incremented(tmp_path: Path):
    """Test that sync --dry-run does not auto-increment revision."""
    project = tmp_path / "project"
    project.mkdir()
    steward_dir = project / ".doc-steward"
    steward_dir.mkdir()
    
    docs_dir = project / "docs"
    docs_dir.mkdir()
    doc_path = docs_dir / "test-doc.md"
    doc_path.write_text("# Test\n\nv1\n", encoding="utf-8")
    
    # Register
    run_doc_steward(project, "register", "docs/test-doc.md",
                   "--doc-id", "DOC-TEST", "--reason", "initial")
    
    # Modify file
    doc_path.write_text("# Test\n\nv2\n", encoding="utf-8")
    
    # Dry run should not change revision
    result = run_doc_steward(project, "sync", "--dry-run")
    assert result.returncode == 0
    
    reg_path = steward_dir / "registry.yaml"
    reg = yaml.safe_load(reg_path.read_text())
    doc = reg["documents"][0]
    assert doc["revision"] == 1  # still r1


def test_accept_revision_creates_r2(tmp_path: Path):
    """Test that accept-revision creates r2 snapshot."""
    project = tmp_path / "project"
    project.mkdir()
    steward_dir = project / ".doc-steward"
    steward_dir.mkdir()
    
    docs_dir = project / "docs"
    docs_dir.mkdir()
    doc_path = docs_dir / "test-doc.md"
    doc_path.write_text("# Test\n\nv1\n", encoding="utf-8")
    
    # Register
    run_doc_steward(project, "register", "docs/test-doc.md",
                   "--doc-id", "DOC-TEST", "--reason", "initial")
    
    # Modify file
    doc_path.write_text("# Test\n\nv2 - updated content\n", encoding="utf-8")
    
    # Accept revision
    result = run_doc_steward(project, "accept-revision", "DOC-TEST",
                            "--reason", "updated to v2")
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["action"] == "accept_revision"
    assert output["from_revision"] == 1
    assert output["to_revision"] == 2
    
    # Check snapshot r2 exists
    snap_dir = steward_dir / "snapshots" / "DOC-TEST"
    assert (snap_dir / "r2.md").exists() or any("r2" in f.name for f in snap_dir.glob("*.md"))
    
    # Check registry updated
    reg_path = steward_dir / "registry.yaml"
    reg = yaml.safe_load(reg_path.read_text())
    doc = reg["documents"][0]
    assert doc["revision"] == 2
    assert len(doc["history"]) == 2  # REGISTERED + REVISION_ACCEPTED


def test_frozen_drift_blocks_accept(tmp_path: Path):
    """Test that FROZEN document cannot accept revision."""
    project = tmp_path / "project"
    project.mkdir()
    steward_dir = project / ".doc-steward"
    steward_dir.mkdir()
    
    docs_dir = project / "docs"
    docs_dir.mkdir()
    doc_path = docs_dir / "test-doc.md"
    doc_path.write_text("# Test\n\nv1\n", encoding="utf-8")
    
    # Register and freeze
    run_doc_steward(project, "register", "docs/test-doc.md",
                   "--doc-id", "DOC-TEST", "--reason", "initial")
    run_doc_steward(project, "transition", "DOC-TEST", "REVIEWING",
                   "--by", "user", "--reason", "ready for review")
    run_doc_steward(project, "transition", "DOC-TEST", "ACTIVE",
                   "--by", "user", "--reason", "approved")
    run_doc_steward(project, "transition", "DOC-TEST", "FROZEN",
                   "--by", "user", "--reason", "freeze for release")
    
    # Modify file
    doc_path.write_text("# Test\n\nv2\n", encoding="utf-8")
    
    # Try to accept revision - should fail
    result = run_doc_steward(project, "accept-revision", "DOC-TEST",
                            "--reason", "try to update frozen")
    assert result.returncode == 1
    assert "FROZEN" in result.stderr


def test_sync_apply_accepts_revisions(tmp_path: Path):
    """Test that sync --accept accepts all modified revisions."""
    project = tmp_path / "project"
    project.mkdir()
    steward_dir = project / ".doc-steward"
    steward_dir.mkdir()
    
    docs_dir = project / "docs"
    docs_dir.mkdir()
    
    # Register two documents
    (docs_dir / "doc-a.md").write_text("# A\n\nv1\n", encoding="utf-8")
    (docs_dir / "doc-b.md").write_text("# B\n\nv1\n", encoding="utf-8")
    
    run_doc_steward(project, "register", "docs/doc-a.md",
                   "--doc-id", "DOC-A", "--reason", "initial")
    run_doc_steward(project, "register", "docs/doc-b.md",
                   "--doc-id", "DOC-B", "--reason", "initial")
    
    # Modify both
    (docs_dir / "doc-a.md").write_text("# A\n\nv2\n", encoding="utf-8")
    (docs_dir / "doc-b.md").write_text("# B\n\nv2\n", encoding="utf-8")
    
    # sync --apply
    result = run_doc_steward(project, "sync", "--apply")
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["action"] == "sync_apply"
    assert len(output["accepted"]) == 2


def test_sync_idempotent(tmp_path: Path):
    """Test that repeated sync does not duplicate revisions."""
    project = tmp_path / "project"
    project.mkdir()
    steward_dir = project / ".doc-steward"
    steward_dir.mkdir()
    
    docs_dir = project / "docs"
    docs_dir.mkdir()
    doc_path = docs_dir / "test-doc.md"
    doc_path.write_text("# Test\n\nv1\n", encoding="utf-8")
    
    # Register
    run_doc_steward(project, "register", "docs/test-doc.md",
                   "--doc-id", "DOC-TEST", "--reason", "initial")
    
    # Modify once
    doc_path.write_text("# Test\n\nv2\n", encoding="utf-8")
    
    # Accept revision
    run_doc_steward(project, "accept-revision", "DOC-TEST", "--reason", "v2")
    
    # Second sync should not create r3
    result = run_doc_steward(project, "sync", "--dry-run")
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert len(output["modified"]) == 0  # no more changes


def test_revision_history_preserved(tmp_path: Path):
    """Test that revision history is preserved across multiple revisions."""
    project = tmp_path / "project"
    project.mkdir()
    steward_dir = project / ".doc-steward"
    steward_dir.mkdir()
    
    docs_dir = project / "docs"
    docs_dir.mkdir()
    doc_path = docs_dir / "test-doc.md"
    doc_path.write_text("# Test\n\nv1\n", encoding="utf-8")
    
    # Register
    run_doc_steward(project, "register", "docs/test-doc.md",
                   "--doc-id", "DOC-TEST", "--reason", "initial")
    
    # Multiple revisions
    for i in range(2, 4):
        doc_path.write_text(f"# Test\n\nv{i}\n", encoding="utf-8")
        run_doc_steward(project, "accept-revision", "DOC-TEST",
                       "--reason", f"update to v{i}")
    
    # Check history
    reg_path = steward_dir / "registry.yaml"
    reg = yaml.safe_load(reg_path.read_text())
    doc = reg["documents"][0]
    
    assert doc["revision"] == 3
    assert len(doc["history"]) == 3
    assert doc["history"][0]["event_type"] == "REGISTERED"
    assert doc["history"][1]["event_type"] == "REVISION_ACCEPTED"
    assert doc["history"][2]["event_type"] == "REVISION_ACCEPTED"
