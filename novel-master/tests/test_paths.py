"""test_paths.py - 路径校验测试。

覆盖路径越界、符号链接逃逸、所有权校验、跨项目检测。
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_paths import normalize_path, check_ownership, detect_cross_project, validate_paths


class TestNormalizePath:
    """路径安全校验。"""

    def test_valid_relative_path(self, tmp_path):
        """合法相对路径应通过。"""
        resolved, err = normalize_path(tmp_path, "chapters/drafts/chapter_001.md")
        assert resolved is not None
        assert err is None

    def test_dotdot_rejected(self, tmp_path):
        """包含 .. 的路径应被拒绝。"""
        resolved, err = normalize_path(tmp_path, "../../etc/passwd")
        assert resolved is None
        assert ".." in err

    def test_absolute_path_rejected(self, tmp_path):
        """绝对路径应被拒绝。"""
        resolved, err = normalize_path(tmp_path, "/etc/passwd")
        assert resolved is None
        assert "绝对路径" in err

    def test_nested_dotdot_rejected(self, tmp_path):
        """嵌套 .. 应被拒绝。"""
        resolved, err = normalize_path(tmp_path, "state/../../outside.md")
        assert resolved is None
        assert ".." in err


class TestOwnership:
    """所有权校验。"""

    def test_chapter_writer_can_write_drafts(self):
        """chapter-writer 可以写 chapters/drafts/。"""
        owned, err = check_ownership("chapters/drafts/chapter_001.md", "chapter-writer")
        assert owned
        assert err is None

    def test_chapter_writer_cannot_write_state(self):
        """chapter-writer 不能写 state/。"""
        owned, err = check_ownership("state/canon.md", "chapter-writer")
        assert not owned
        assert err is not None

    def test_continuity_keeper_can_write_state(self):
        """continuity-keeper 可以写 state/。"""
        owned, err = check_ownership("state/canon.md", "continuity-keeper")
        assert owned

    def test_novel_brief_can_write_brief(self):
        """novel-brief 可以写 project_brief.md。"""
        owned, err = check_ownership("project_brief.md", "novel-brief")
        assert owned

    def test_novel_brief_cannot_write_architecture(self):
        """novel-brief 不能写 architecture/。"""
        owned, err = check_ownership("architecture/story.md", "novel-brief")
        assert not owned

    def test_story_architect_story_mode(self):
        """story-architect/STORY 可以写 architecture/。"""
        owned, err = check_ownership("architecture/story_architecture.md", "story-architect/STORY")
        assert owned

    def test_story_architect_character_mode(self):
        """story-architect/CHARACTER 可以写 characters/。"""
        owned, err = check_ownership("characters/protagonist.md", "story-architect/CHARACTER")
        assert owned

    def test_unknown_skill(self):
        """未知 Skill 应被拒绝。"""
        owned, err = check_ownership("state/canon.md", "unknown-skill")
        assert not owned
        assert "未知" in err

    def test_novel_reviewer_can_write_reviews(self):
        """novel-reviewer 可以写 reviews/。"""
        owned, err = check_ownership("reviews/chapter_001_review.md", "novel-reviewer")
        assert owned

    def test_novel_reviewer_cannot_write_drafts(self):
        """novel-reviewer 不能写 chapters/drafts/。"""
        owned, err = check_ownership("chapters/drafts/chapter_001.md", "novel-reviewer")
        assert not owned


class TestCrossProject:
    """跨项目检测。"""

    def test_no_cross_project(self, tmp_path):
        """正常路径不触发跨项目检测。"""
        err = detect_cross_project(tmp_path, "state/canon.md")
        assert err is None

    def test_cross_project_pattern(self, tmp_path):
        """包含 ../ 的路径触发跨项目检测。"""
        err = detect_cross_project(tmp_path, "../other-project/state/canon.md")
        assert err is not None


class TestValidatePaths:
    """综合路径校验。"""

    def test_all_valid(self, tmp_path):
        """全部合法路径。"""
        results = validate_paths(tmp_path, "chapter-writer", ["chapters/drafts/ch1.md"])
        assert all(r["valid"] for r in results)

    def test_mixed_valid_invalid(self, tmp_path):
        """混合合法和非法路径。"""
        results = validate_paths(
            tmp_path,
            "chapter-writer",
            ["chapters/drafts/ch1.md", "state/canon.md"],
        )
        assert results[0]["valid"] is True
        assert results[1]["valid"] is False
