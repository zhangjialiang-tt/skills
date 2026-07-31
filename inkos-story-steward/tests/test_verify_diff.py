"""Tests for inkos-story-steward/scripts/verify_diff.py."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).resolve().parent.parent / "scripts" / "verify_diff.py")


def run_verify(*args: str, cwd: str | Path | None = None) -> subprocess.CompletedProcess:
    """Run verify_diff.py with given args, return CompletedProcess."""
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )


# ---------------------------------------------------------------------------
# Tests using --files (no git needed)
# ---------------------------------------------------------------------------


def test_red_zone_always_blocked():
    """Red zone file blocked even when explicitly in --allow."""
    r = run_verify(
        "--files", "books/test/chapters/index.json",
        "--mode", "enforce",
        "--allow", "books/test/chapters/index.json",
    )
    assert r.returncode == 1
    assert "RED ZONE" in r.stderr


def test_allowed_green_passes():
    """Green zone file in --allow passes."""
    r = run_verify(
        "--files", "books/test/story/book_rules.md",
        "--mode", "enforce",
        "--allow", "books/test/story/book_rules.md",
    )
    assert r.returncode == 0


def test_unauthorized_green_blocked():
    """Green zone file NOT in --allow is blocked."""
    r = run_verify(
        "--files", "books/test/story/book_rules.md",
        "--mode", "enforce",
        "--allow", "books/test/story/author_intent.md",
    )
    assert r.returncode == 1
    assert "UNAUTHORIZED" in r.stderr


def test_unauthorized_root_file_blocked():
    """File outside any book dir is blocked when not in --allow."""
    r = run_verify(
        "--files", "some_root_file.py",
        "--mode", "enforce",
        "--allow", "books/test/story/",
    )
    assert r.returncode == 1
    assert "UNAUTHORIZED" in r.stderr


def test_yellow_without_allow_yellow_blocked():
    """Yellow zone file blocked without --allow-yellow even if in --allow."""
    r = run_verify(
        "--files", "books/test/story/pending_hooks.md",
        "--mode", "enforce",
        "--allow", "books/test/story/pending_hooks.md",
    )
    assert r.returncode == 1
    assert "allow-yellow" in r.stderr


def test_yellow_with_allow_yellow_passes():
    """Yellow zone file passes with --allow-yellow."""
    r = run_verify(
        "--files", "books/test/story/pending_hooks.md",
        "--mode", "enforce",
        "--allow", "books/test/story/pending_hooks.md",
        "--allow-yellow",
    )
    assert r.returncode == 0


def test_enforce_no_allow_exit1():
    """Enforce mode with no --allow and no --files exits 1."""
    r = run_verify("--mode", "enforce")
    assert r.returncode == 1
    assert "requires" in r.stderr.lower() or "ERROR" in r.stderr


def test_directory_prefix_allow():
    """Directory prefix in --allow matches files within."""
    r = run_verify(
        "--files", "books/test/story/roles/char.md",
        "--mode", "enforce",
        "--allow", "books/test/story/roles/",
    )
    assert r.returncode == 0


def test_prefix_collision_roles_backup():
    """Prefix allow for roles/ must NOT match roles-backup/."""
    r = run_verify(
        "--files", "books/test/story/roles-backup/x.md",
        "--mode", "enforce",
        "--allow", "books/test/story/roles/",
    )
    assert r.returncode == 1
    assert "UNAUTHORIZED" in r.stderr


# ---------------------------------------------------------------------------
# Tests using git (tmp_path)
# ---------------------------------------------------------------------------


def _git(args: list[str], cwd: Path) -> None:
    """Run a git command, raise on failure."""
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )


def test_git_failure_exit1(tmp_path):
    """Running without git repo and without --files exits 1."""
    # tmp_path has no .git — git commands will fail
    r = run_verify(
        "--mode", "enforce",
        "--allow", "books/",
        "--project-root", str(tmp_path),
        cwd=str(tmp_path),
    )
    assert r.returncode == 1
    assert "ERROR" in r.stderr or "Blocking" in r.stderr


def test_staged_and_untracked_detected(tmp_path):
    """Staged + untracked files are detected; authorized passes, unauthorized blocked."""
    _git(["init"], tmp_path)
    _git(["config", "user.email", "test@test.com"], tmp_path)
    _git(["config", "user.name", "Test"], tmp_path)

    # Create a green-zone file and stage it
    staged_file = tmp_path / "books" / "test" / "story" / "book_rules.md"
    staged_file.parent.mkdir(parents=True)
    staged_file.write_text("# Rules\n")
    _git(["add", "books/test/story/book_rules.md"], tmp_path)

    # Create another green-zone file (untracked)
    untracked_file = tmp_path / "books" / "test" / "story" / "author_intent.md"
    untracked_file.write_text("# Intent\n")

    # With --allow covering both → exit 0
    r_pass = run_verify(
        "--mode", "enforce",
        "--allow", "books/test/story/",
        "--project-root", str(tmp_path),
        cwd=str(tmp_path),
    )
    assert r_pass.returncode == 0

    # Without --allow → exit 1 (enforce requires --allow)
    r_fail = run_verify(
        "--mode", "enforce",
        "--project-root", str(tmp_path),
        cwd=str(tmp_path),
    )
    assert r_fail.returncode == 1



# ---------------------------------------------------------------------------
# Boundary tests: enforce requires --allow; diagnostic relaxes rules
# ---------------------------------------------------------------------------


def test_explicit_files_without_allow_blocked():
    """enforce + --files + no --allow must exit 1."""
    result = run_verify("--mode", "enforce", "--files", "books/test/story/book_rules.md")
    assert result.returncode == 1


def test_diagnostic_yellow_exit0():
    """diagnostic mode: yellow zone is warning, not failure."""
    result = run_verify("--mode", "diagnostic", "--files", "books/test/story/pending_hooks.md")
    assert result.returncode == 0


def test_diagnostic_red_exit1():
    """diagnostic mode: red zone still fails."""
    result = run_verify("--mode", "diagnostic", "--files", "books/test/chapters/index.json")
    assert result.returncode == 1


def test_diagnostic_no_allow_needed():
    """diagnostic mode does not require --allow."""
    result = run_verify("--mode", "diagnostic", "--files", "books/test/story/author_intent.md")
    assert result.returncode == 0