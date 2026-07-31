"""Tests for inkos-story-steward/scripts/preflight.py.

Runs the script as a subprocess against temp fixtures.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).resolve().parent.parent / "scripts" / "preflight.py")

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@test.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@test.com",
}


def run_preflight(project_root: Path, *extra_args: str) -> subprocess.CompletedProcess:
    """Run preflight.py with --project-root pointing at project_root."""
    cmd = [sys.executable, SCRIPT, "--project-root", str(project_root), *extra_args]
    return subprocess.run(cmd, capture_output=True, text=True)


def make_project(root: Path, *, book_id: str = "test-book") -> Path:
    """Create minimal InkOS project: inkos.json + books/<id>/book.json + author_intent."""
    (root / "inkos.json").write_text("{}", encoding="utf-8")
    book_dir = root / "books" / book_id
    book_dir.mkdir(parents=True)
    (book_dir / "book.json").write_text('{"title": "Test"}', encoding="utf-8")
    story_dir = book_dir / "story"
    story_dir.mkdir(exist_ok=True)
    (story_dir / "author_intent.md").write_text("# Intent", encoding="utf-8")
    return root


def git_init_clean(root: Path):
    """Initialize a git repo and commit everything so worktree is clean."""
    subprocess.run(["git", "init"], cwd=root, capture_output=True, env=GIT_ENV)
    subprocess.run(["git", "add", "."], cwd=root, capture_output=True, env=GIT_ENV)
    subprocess.run(
        ["git", "commit", "-m", "init", "--allow-empty"],
        cwd=root, capture_output=True, env=GIT_ENV,
    )


class TestNoProject:
    def test_no_project_prebuild_exit0(self, tmp_path: Path):
        """Empty directory → PREBUILD mode, exit 0."""
        result = run_preflight(tmp_path)
        assert result.returncode == 0
        assert "PREBUILD" in result.stdout


class TestMultiBook:
    def test_multi_book_no_id_exit1(self, tmp_path: Path):
        """Two books without --book-id → exit 1."""
        make_project(tmp_path, book_id="book-a")
        # Add second book
        book_b = tmp_path / "books" / "book-b"
        book_b.mkdir(parents=True)
        (book_b / "book.json").write_text("{}", encoding="utf-8")

        result = run_preflight(tmp_path)
        assert result.returncode == 1


class TestWriteLock:
    def test_write_lock_exit1(self, tmp_path: Path):
        """.write.lock present → exit 1, write_allowed=false in JSON."""
        make_project(tmp_path)
        (tmp_path / "books" / "test-book" / ".write.lock").write_text("", encoding="utf-8")
        git_init_clean(tmp_path)

        result = run_preflight(tmp_path, "--json")
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["write_allowed"] is False


class TestGitDirty:
    def test_git_dirty_exit1(self, tmp_path: Path):
        """Git repo with uncommitted changes → exit 1."""
        make_project(tmp_path)
        git_init_clean(tmp_path)
        # Create an untracked file to dirty the worktree
        (tmp_path / "dirty.txt").write_text("dirty", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, env=GIT_ENV)

        result = run_preflight(tmp_path, "--json")
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert "GIT_WORKTREE_DIRTY" in data["reason_codes"]


class TestNotGitRepo:
    def test_not_git_repo_exit1(self, tmp_path: Path):
        """Project exists but no .git → exit 1, GIT_BASELINE_UNAVAILABLE."""
        make_project(tmp_path)
        # No git init — check_git_clean returns None

        result = run_preflight(tmp_path, "--json")
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert "GIT_BASELINE_UNAVAILABLE" in data["reason_codes"]


class TestInkosNotInstalled:
    def test_inkos_not_installed_exit1(self, tmp_path: Path):
        """inkos CLI not on PATH → exit 1, write_allowed=false."""
        make_project(tmp_path)
        git_init_clean(tmp_path)

        result = run_preflight(tmp_path, "--json")
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["write_allowed"] is False
        assert "INKOS_VERSION_UNKNOWN" in data["reason_codes"]


class TestJsonOutput:
    def test_json_output_has_write_allowed(self, tmp_path: Path):
        """--json output always contains write_allowed field."""
        make_project(tmp_path)
        git_init_clean(tmp_path)

        result = run_preflight(tmp_path, "--json")
        data = json.loads(result.stdout)
        assert "write_allowed" in data


class TestSingleBookAutoResolved:
    def test_single_book_auto_resolved(self, tmp_path: Path):
        """One book auto-resolved, git clean, inkos missing → exit 1."""
        make_project(tmp_path)
        git_init_clean(tmp_path)

        result = run_preflight(tmp_path, "--json")
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["book_id"] == "test-book"
        assert data["write_allowed"] is False



class TestChapterIndexConsistency:
    """Tests for inspect_chapter_state via preflight --json output."""

    def _make_project_with_chapters(self, root: Path, *, book_id: str = "test-book"):
        """Create project + chapters dir, return (book_path, chapters_dir)."""
        make_project(root, book_id=book_id)
        book_path = root / "books" / book_id
        chapters_dir = book_path / "chapters"
        chapters_dir.mkdir(exist_ok=True)
        return book_path, chapters_dir

    def _write_index(self, chapters_dir: Path, numbers: list[int]):
        """Write index.json listing given chapter numbers."""
        entries = [
            {"number": n, "title": f"ch{n}", "path": f"{n:03d}_test.md"}
            for n in numbers
        ]
        (chapters_dir / "index.json").write_text(
            json.dumps({"chapters": entries}), encoding="utf-8"
        )

    def _write_chapter_file(self, chapters_dir: Path, number: int):
        """Create a chapter markdown file like 001_test.md."""
        (chapters_dir / f"{number:03d}_test.md").write_text(
            f"# Chapter {number}", encoding="utf-8"
        )

    def test_no_index_no_files_foundation(self, tmp_path: Path):
        """Empty chapters/ dir → consistent, mode=FOUNDATION_ALIGNMENT."""
        self._make_project_with_chapters(tmp_path)
        git_init_clean(tmp_path)

        result = run_preflight(tmp_path, "--json")
        data = json.loads(result.stdout)
        # inkos not installed → exit 1, but chapter state is consistent
        assert "CHAPTER_INDEX_INCONSISTENT" not in data["reason_codes"]
        assert data["chapter_state"]["consistent"] is True
        assert data["mode"] == "FOUNDATION_ALIGNMENT"

    def test_files_but_no_index_exit1(self, tmp_path: Path):
        """Chapter .md files exist but no index.json → CHAPTER_INDEX_INCONSISTENT."""
        _, chapters_dir = self._make_project_with_chapters(tmp_path)
        self._write_chapter_file(chapters_dir, 1)
        self._write_chapter_file(chapters_dir, 2)
        git_init_clean(tmp_path)

        result = run_preflight(tmp_path, "--json")
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert "CHAPTER_INDEX_INCONSISTENT" in data["reason_codes"]

    def test_corrupt_index_exit1(self, tmp_path: Path):
        """Corrupt index.json → CHAPTER_INDEX_INCONSISTENT."""
        _, chapters_dir = self._make_project_with_chapters(tmp_path)
        (chapters_dir / "index.json").write_text("{{{bad json", encoding="utf-8")
        self._write_chapter_file(chapters_dir, 1)
        git_init_clean(tmp_path)

        result = run_preflight(tmp_path, "--json")
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert "CHAPTER_INDEX_INCONSISTENT" in data["reason_codes"]

    def test_index_matches_files_active(self, tmp_path: Path):
        """Index and files match → consistent=True, mode=ACTIVE (no CHAPTER_INDEX_INCONSISTENT)."""
        _, chapters_dir = self._make_project_with_chapters(tmp_path)
        self._write_index(chapters_dir, [1, 2, 3])
        self._write_chapter_file(chapters_dir, 1)
        self._write_chapter_file(chapters_dir, 2)
        self._write_chapter_file(chapters_dir, 3)
        git_init_clean(tmp_path)

        result = run_preflight(tmp_path, "--json")
        data = json.loads(result.stdout)
        # inkos not installed → exit 1, but chapter state is fine
        assert "CHAPTER_INDEX_INCONSISTENT" not in data["reason_codes"]
        assert data["chapter_state"]["consistent"] is True
        assert data["mode"] == "ACTIVE"

    def test_index_has_chapter_no_file_exit1(self, tmp_path: Path):
        """Index lists [1,2,3] but file 003 missing → CHAPTER_INDEX_INCONSISTENT."""
        _, chapters_dir = self._make_project_with_chapters(tmp_path)
        self._write_index(chapters_dir, [1, 2, 3])
        self._write_chapter_file(chapters_dir, 1)
        self._write_chapter_file(chapters_dir, 2)
        # 003_test.md deliberately missing
        git_init_clean(tmp_path)

        result = run_preflight(tmp_path, "--json")
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert "CHAPTER_INDEX_INCONSISTENT" in data["reason_codes"]

    def test_file_exists_not_in_index_exit1(self, tmp_path: Path):
        """Index lists [1,2] but file 003 exists → CHAPTER_INDEX_INCONSISTENT."""
        _, chapters_dir = self._make_project_with_chapters(tmp_path)
        self._write_index(chapters_dir, [1, 2])
        self._write_chapter_file(chapters_dir, 1)
        self._write_chapter_file(chapters_dir, 2)
        self._write_chapter_file(chapters_dir, 3)  # not in index
        git_init_clean(tmp_path)

        result = run_preflight(tmp_path, "--json")
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert "CHAPTER_INDEX_INCONSISTENT" in data["reason_codes"]