"""Tests for design-id derivation, manifest lifecycle, and new mode detection.

Covers spec cases A-L for the design-id isolated path structure.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPTS = str(Path("inkos-story-steward/scripts").resolve())
sys.path.insert(0, SCRIPTS)

from design_id import derive_design_id, validate_transition, VALID_TRANSITIONS


def run_preflight(project_root: Path, *extra_args: str) -> subprocess.CompletedProcess:
    """Run preflight.py with --json and return result."""
    cmd = [sys.executable, os.path.join(SCRIPTS, "preflight.py"),
           "--project-root", str(project_root), "--json"] + list(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def run_verify_diff(*args: str) -> subprocess.CompletedProcess:
    """Run verify_diff.py and return result."""
    cmd = [sys.executable, os.path.join(SCRIPTS, "verify_diff.py")] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def make_project(tmp_path: Path, books: list[str] = None) -> Path:
    """Create a minimal InkOS project."""
    (tmp_path / "inkos.json").write_text('{"name":"test"}', encoding="utf-8")
    if books:
        for b in books:
            book_dir = tmp_path / "books" / b
            book_dir.mkdir(parents=True)
            (book_dir / "book.json").write_text(f'{{"id":"{b}"}}', encoding="utf-8")
            (book_dir / "story").mkdir(exist_ok=True)
    return tmp_path


def make_manifest(tmp_path: Path, design_id: str, book_id: str = None,
                  status: str = "draft") -> Path:
    """Create a manifest.yaml for a design package."""
    design_root = tmp_path / "story-design" / design_id
    design_root.mkdir(parents=True, exist_ok=True)
    manifest = design_root / "manifest.yaml"
    content = f"""schema_version: 1
design:
  id: {design_id}
  title: {design_id}
  root: story-design/{design_id}
  status: {status}
inkos:
  project_root: .
  book_id: {"null" if book_id is None else book_id}
  book_dir: {"null" if book_id is None else f"books/{book_id}"}
  brief_path: compile/inkos/book-brief.md
lifecycle:
  created_at: null
  updated_at: null
gates:
  gate_1: passed
  gate_2: passed
  gate_3: passed
  gate_4: passed
source:
  skill: inkos-story-steward
  schema: prebuild-v2
"""
    manifest.write_text(content, encoding="utf-8")
    return manifest


# === A. New first design package ===

class TestPrebuildInProject:
    def test_empty_books_prebuild_in_project(self, tmp_path: Path):
        """InkOS project exists, books/ empty → PREBUILD_IN_PROJECT."""
        make_project(tmp_path, books=[])
        (tmp_path / "books").mkdir(exist_ok=True)
        result = run_preflight(tmp_path, "--design-id", "活着的死者")
        data = json.loads(result.stdout)
        assert data["mode"] == "PREBUILD_IN_PROJECT"
        assert data["design_id"] == "活着的死者"
        # Must NOT create books/活着的死者
        assert not (tmp_path / "books" / "活着的死者").exists()


# === B. Multi-book new design ===

class TestMultiBookNewDesign:
    def test_new_design_does_not_touch_existing(self, tmp_path: Path):
        """Existing book-a with manifest; new design book-b gets own directory."""
        make_project(tmp_path, books=["book-a"])
        make_manifest(tmp_path, "book-a", book_id="book-a", status="aligned")
        result = run_preflight(tmp_path, "--design-id", "book-b")
        data = json.loads(result.stdout)
        assert data["mode"] == "PREBUILD_IN_PROJECT"
        assert data["design_id"] == "book-b"
        # book-a manifest untouched
        assert (tmp_path / "story-design" / "book-a" / "manifest.yaml").exists()


# === C. Same-name conflict ===

class TestDesignConflict:
    def test_existing_design_root_warning(self, tmp_path: Path):
        """Existing design root without manifest triggers warning."""
        make_project(tmp_path, books=[])
        (tmp_path / "books").mkdir(exist_ok=True)
        design_dir = tmp_path / "story-design" / "活着的死者"
        design_dir.mkdir(parents=True)
        (design_dir / "design").mkdir()
        # No manifest.yaml — should warn
        result = run_preflight(tmp_path, "--design-id", "活着的死者")
        data = json.loads(result.stdout)
        assert any("without manifest" in w for w in data["warnings"])


# === D. Compile package path ===

class TestCompilePath:
    def test_new_compile_path_in_workflow(self):
        """Verify prebuild-workflow.md references new compile path."""
        content = Path("inkos-story-steward/references/prebuild-workflow.md").read_text(encoding="utf-8")
        assert "<design-root>/compile/inkos/book-brief.md" in content
        # Old path should not be the default
        assert "story-design/inkos/book-brief.md" not in content


# === E. Book creation success binding ===

class TestBookBinding:
    def test_bound_manifest_active(self, tmp_path: Path):
        """Manifest bound to existing book with chapters → ACTIVE_MAINTENANCE."""
        make_project(tmp_path, books=["活着的死者"])
        # Add chapters
        ch_dir = tmp_path / "books" / "活着的死者" / "chapters"
        ch_dir.mkdir(parents=True)
        (ch_dir / "index.json").write_text(
            '{"chapters":[{"number":1,"title":"t","path":"001_t.md"}]}', encoding="utf-8")
        (ch_dir / "001_t.md").write_text("# ch1", encoding="utf-8")
        make_manifest(tmp_path, "活着的死者", book_id="活着的死者", status="created")

        result = run_preflight(tmp_path, "--design-id", "活着的死者", "--book-id", "活着的死者")
        data = json.loads(result.stdout)
        assert data["mode"] == "ACTIVE_MAINTENANCE"
        assert data["binding_status"] == "bound"


# === F. Book creation failure ===

class TestBookCreationFailure:
    def test_bound_book_not_found(self, tmp_path: Path):
        """Manifest claims book_id that doesn't exist (other books do) → blocked."""
        make_project(tmp_path, books=["other-book"])
        make_manifest(tmp_path, "test-story", book_id="nonexistent", status="created")

        result = run_preflight(tmp_path, "--design-id", "test-story", "--book-id", "nonexistent")
        data = json.loads(result.stdout)
        assert data["write_allowed"] is False
        assert "BOOK_NOT_FOUND" in data["reason_codes"]


# === G. FOUNDATION_ALIGNMENT precise location ===

class TestFoundationAlignment:
    def test_manifest_locates_design(self, tmp_path: Path):
        """Multiple designs + books; manifest binding finds correct one."""
        make_project(tmp_path, books=["book-a", "book-b"])
        make_manifest(tmp_path, "design-a", book_id="book-a", status="created")
        make_manifest(tmp_path, "design-b", book_id="book-b", status="created")

        result = run_preflight(tmp_path, "--design-id", "design-b", "--book-id", "book-b")
        data = json.loads(result.stdout)
        assert data["mode"] == "FOUNDATION_ALIGNMENT"
        assert data["book_id"] == "book-b"
        assert data["design_id"] == "design-b"


# === H. Duplicate binding ===

class TestDuplicateBinding:
    def test_two_manifests_same_book(self, tmp_path: Path):
        """Two manifests claim same book_id → AMBIGUOUS_BINDING."""
        make_project(tmp_path, books=["book-a"])
        make_manifest(tmp_path, "design-x", book_id="book-a", status="created")
        make_manifest(tmp_path, "design-y", book_id="book-a", status="created")

        result = run_preflight(tmp_path, "--design-id", "design-x", "--book-id", "book-a")
        data = json.loads(result.stdout)
        assert data["write_allowed"] is False
        assert "DUPLICATE_BINDING" in data["reason_codes"]


# === I. Legacy layout detection ===

class TestLegacyLayout:
    def test_legacy_detected(self, tmp_path: Path):
        """Flat story-design/00-project-brief.md without manifests → legacy."""
        make_project(tmp_path, books=[])
        (tmp_path / "books").mkdir(exist_ok=True)
        sd = tmp_path / "story-design"
        sd.mkdir()
        (sd / "00-project-brief.md").write_text("# brief", encoding="utf-8")
        (sd / "inkos").mkdir()
        (sd / "inkos" / "book-brief.md").write_text("# brief", encoding="utf-8")

        result = run_preflight(tmp_path, "--design-id", "new-story")
        data = json.loads(result.stdout)
        assert data["legacy_layout_detected"] is True


# === J. Path write boundary ===

class TestPrebuildWriteBoundary:
    def test_prebuild_blocks_books_write(self):
        """PREBUILD mode: verify_diff --prebuild blocks writes to books/."""
        result = run_verify_diff(
            "--mode", "enforce", "--prebuild",
            "--files", "books/test/story/author_intent.md",
            "--allow", "books/test/story/author_intent.md",
        )
        assert result.returncode == 1

    def test_cross_design_blocked(self):
        """Cannot write to another design-id's files."""
        result = run_verify_diff(
            "--mode", "enforce",
            "--design-root", "story-design/my-story",
            "--files", "story-design/other-story/design/00-project-brief.md",
            "--allow", "story-design/other-story/design/00-project-brief.md",
        )
        assert result.returncode == 1


# === K. Windows path characters ===

class TestDesignIdDerivation:
    def test_chinese_preserved(self):
        assert derive_design_id("活着的死者") == "活着的死者"

    def test_illegal_chars_removed(self):
        result = derive_design_id('测试:故事?第一部')
        assert ":" not in result
        assert "?" not in result
        assert result == "测试故事第一部"

    def test_empty_fallback(self):
        assert derive_design_id("") == "untitled-story"
        assert derive_design_id(":::") == "untitled-story"

    def test_spaces_to_hyphens(self):
        assert derive_design_id("  My Story  ") == "My-Story"

    def test_trailing_dots_removed(self):
        result = derive_design_id("故事...")
        assert not result.endswith(".")

    def test_deterministic(self):
        """Same input always produces same output."""
        assert derive_design_id("测试:故事?第一部") == derive_design_id("测试:故事?第一部")


# === L. Lifecycle illegal jumps ===

class TestLifecycleTransitions:
    def test_valid_transitions(self):
        assert validate_transition("draft", "reviewing") is True
        assert validate_transition("draft", "ready_to_create") is True
        assert validate_transition("ready_to_create", "creating") is True
        assert validate_transition("creating", "created") is True
        assert validate_transition("creating", "ready_to_create") is True  # failure rollback
        assert validate_transition("created", "aligned") is True

    def test_illegal_jumps(self):
        assert validate_transition("draft", "aligned") is False
        assert validate_transition("draft", "created") is False
        assert validate_transition("reviewing", "created") is False
        assert validate_transition("aligned", "draft") is False
        assert validate_transition("archived", "draft") is False

    def test_all_states_have_transitions(self):
        """Every valid state appears in the transition table."""
        for state in ["draft", "reviewing", "ready_to_create", "creating", "created", "aligned", "archived"]:
            assert state in VALID_TRANSITIONS
