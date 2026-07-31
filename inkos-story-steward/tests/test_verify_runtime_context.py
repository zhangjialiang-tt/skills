"""Tests for verify_runtime_context.py — exit codes and parsed results."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).resolve().parents[1] / "scripts" / "verify_runtime_context.py")


def _make_fixture(tmp_path: Path) -> Path:
    """Create the full fixture tree and return the project root (tmp_path)."""
    book_dir = tmp_path / "books" / "test-book"
    runtime_dir = book_dir / "story" / "runtime"
    runtime_dir.mkdir(parents=True)

    # context.json
    (runtime_dir / "chapter-0006.context.json").write_text(
        json.dumps({"chapter": 6, "rules": ["抑制剂只能延缓感染"]}, ensure_ascii=False),
        encoding="utf-8",
    )

    # rule-stack.yaml
    (runtime_dir / "chapter-0006.rule-stack.yaml").write_text(
        "rules:\n  - 抑制剂只能延缓感染\n  - source: story/book_rules.md\n",
        encoding="utf-8",
    )

    # trace.json
    (runtime_dir / "chapter-0006.trace.json").write_text(
        json.dumps(
            {"chapter": 6, "selectedSources": ["story/book_rules.md", "story/outline/story_frame.md"]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # book_rules.md
    (book_dir / "story" / "book_rules.md").write_text("抑制剂只能延缓感染", encoding="utf-8")
    # Age the source file so it is older than runtime files (freshness check).
    _past = time.time() - 1000
    os.utime(book_dir / "story" / "book_rules.md", (_past, _past))

    # book.json
    (book_dir / "book.json").write_text(json.dumps({"id": "test-book"}), encoding="utf-8")

    # inkos.json (project marker)
    (tmp_path / "inkos.json").write_text(json.dumps({"version": "1.0"}), encoding="utf-8")

    return tmp_path


def _run(tmp_path: Path, *extra_args: str) -> subprocess.CompletedProcess:
    """Invoke the script with project root set to tmp_path."""
    cmd = [
        sys.executable, SCRIPT,
        "--project-root", str(tmp_path),
        "--book-id", "test-book",
        "--chapter", "6",
        *extra_args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def _runtime_dir(tmp_path: Path) -> Path:
    return tmp_path / "books" / "test-book" / "story" / "runtime"


class TestVerifyRuntimeContext:
    """13 deterministic tests for verify_runtime_context.py."""

    def test_all_pass_exit0(self, tmp_path):
        _make_fixture(tmp_path)
        source = tmp_path / "books" / "test-book" / "story" / "book_rules.md"
        r = _run(tmp_path, "--expect-text", "抑制剂只能延缓感染",
                 "--expect-source", "story/book_rules.md",
                 "--source-file", str(source))
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

    def test_missing_context_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        (_runtime_dir(tmp_path) / "chapter-0006.context.json").unlink()
        r = _run(tmp_path, "--expect-text", "抑制剂只能延缓感染")
        assert r.returncode == 1

    def test_missing_rule_stack_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        (_runtime_dir(tmp_path) / "chapter-0006.rule-stack.yaml").unlink()
        r = _run(tmp_path, "--expect-text", "抑制剂只能延缓感染")
        assert r.returncode == 1

    def test_missing_trace_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        (_runtime_dir(tmp_path) / "chapter-0006.trace.json").unlink()
        r = _run(tmp_path, "--expect-text", "抑制剂只能延缓感染")
        assert r.returncode == 1

    def test_corrupt_context_json_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        (_runtime_dir(tmp_path) / "chapter-0006.context.json").write_text("{{{", encoding="utf-8")
        r = _run(tmp_path, "--expect-text", "抑制剂只能延缓感染")
        assert r.returncode == 1

    def test_corrupt_trace_json_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        (_runtime_dir(tmp_path) / "chapter-0006.trace.json").write_text("{{{", encoding="utf-8")
        r = _run(tmp_path, "--expect-source", "story/book_rules.md")
        assert r.returncode == 1

    def test_chapter_mismatch_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        ctx = _runtime_dir(tmp_path) / "chapter-0006.context.json"
        ctx.write_text(json.dumps({"chapter": 7, "rules": ["抑制剂只能延缓感染"]}, ensure_ascii=False), encoding="utf-8")
        r = _run(tmp_path, "--expect-text", "抑制剂只能延缓感染")
        assert r.returncode == 1

    def test_expect_text_not_found_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        r = _run(tmp_path, "--expect-text", "不存在的内容")
        assert r.returncode == 1

    def test_reject_text_present_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        r = _run(tmp_path, "--reject-text", "抑制剂只能延缓感染")
        assert r.returncode == 1

    def test_expect_source_not_found_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        r = _run(tmp_path, "--expect-source", "story/nonexistent.md")
        assert r.returncode == 1

    def test_runtime_older_than_source_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        source = tmp_path / "books" / "test-book" / "story" / "book_rules.md"
        future = time.time() + 100
        os.utime(source, (future, future))
        r = _run(tmp_path, "--expect-text", "抑制剂只能延缓感染", "--source-file", str(source))
        assert r.returncode == 1

    def test_no_assertions_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        r = _run(tmp_path)
        assert r.returncode == 1

    def test_multiple_expect_text(self, tmp_path):
        _make_fixture(tmp_path)
        r = _run(tmp_path, "--expect-text", "抑制剂只能延缓感染", "--expect-text", "不存在的第二条")
        assert r.returncode == 1

    # --- Boundary tests: mode / source-file contract ---

    def test_enforce_no_source_file_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        r = _run(tmp_path, "--mode", "enforce", "--expect-text", "抑制剂只能延缓感染")
        assert r.returncode == 1

    def test_diagnostic_no_source_file_no_proof(self, tmp_path):
        _make_fixture(tmp_path)
        r = _run(tmp_path, "--mode", "diagnostic", "--expect-text", "抑制剂只能延缓感染")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
        assert "completion_proof: false" in r.stdout

    # --- Boundary tests: --expect-source only searches formal trace fields ---

    def test_source_only_in_notes_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        (_runtime_dir(tmp_path) / "chapter-0006.trace.json").write_text(
            json.dumps(
                {"chapter": 6, "selectedSources": [], "notes": ["story/book_rules.md was excluded"]},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        r = _run(tmp_path, "--mode", "diagnostic", "--expect-source", "story/book_rules.md")
        assert r.returncode == 1

    def test_source_in_selected_sources_exit0(self, tmp_path):
        _make_fixture(tmp_path)
        (_runtime_dir(tmp_path) / "chapter-0006.trace.json").write_text(
            json.dumps({"chapter": 6, "selectedSources": ["story/book_rules.md"]}, ensure_ascii=False),
            encoding="utf-8",
        )
        source = tmp_path / "books" / "test-book" / "story" / "book_rules.md"
        r = _run(tmp_path, "--mode", "enforce",
                 "--expect-source", "story/book_rules.md",
                 "--source-file", str(source))
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

    # --- Boundary tests: mandatory chapter field ---

    def test_context_missing_chapter_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        (_runtime_dir(tmp_path) / "chapter-0006.context.json").write_text(
            json.dumps({"rules": ["x"]}, ensure_ascii=False), encoding="utf-8")
        r = _run(tmp_path, "--mode", "diagnostic", "--expect-text", "x")
        assert r.returncode == 1

    def test_trace_missing_chapter_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        (_runtime_dir(tmp_path) / "chapter-0006.trace.json").write_text(
            json.dumps({"selectedSources": []}, ensure_ascii=False), encoding="utf-8")
        r = _run(tmp_path, "--mode", "diagnostic", "--expect-text", "抑制剂只能延缓感染")
        assert r.returncode == 1

    def test_context_chapter_invalid_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        (_runtime_dir(tmp_path) / "chapter-0006.context.json").write_text(
            json.dumps({"chapter": "garbage"}, ensure_ascii=False), encoding="utf-8")
        r = _run(tmp_path, "--mode", "diagnostic", "--expect-text", "抑制剂只能延缓感染")
        assert r.returncode == 1

    # --- Boundary tests: YAML parsing / PyYAML availability ---

    def test_corrupt_yaml_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        (_runtime_dir(tmp_path) / "chapter-0006.rule-stack.yaml").write_text(
            "{{{invalid yaml", encoding="utf-8")
        r = _run(tmp_path, "--mode", "diagnostic", "--expect-text", "抑制剂只能延缓感染")
        assert r.returncode == 1

    def test_pyyaml_unavailable_exit1(self, tmp_path):
        _make_fixture(tmp_path)
        # Wrapper blocks `import yaml` (None in sys.modules -> ImportError) then runs the script.
        wrapper = tmp_path / "no_yaml_wrapper.py"
        wrapper.write_text(
            "import sys, runpy\n"
            "sys.modules['yaml'] = None\n"
            "script = sys.argv[1]\n"
            "sys.argv = sys.argv[1:]\n"
            "runpy.run_path(script, run_name='__main__')\n",
            encoding="utf-8",
        )
        cmd = [
            sys.executable, str(wrapper), SCRIPT,
            "--project-root", str(tmp_path),
            "--book-id", "test-book",
            "--chapter", "6",
            "--mode", "diagnostic",
            "--expect-text", "抑制剂只能延缓感染",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        assert r.returncode == 1, f"stdout={r.stdout}\nstderr={r.stderr}"
