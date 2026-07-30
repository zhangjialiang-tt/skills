"""Tests for path safety validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from _core import safe_resolve_path


class TestPathSafety:
    """Test path safety validation."""
    
    def test_relative_path_accepted(self, tmp_path: Path):
        result = safe_resolve_path(tmp_path, "docs/test.md")
        assert result == tmp_path / "docs" / "test.md"
    
    def test_absolute_path_rejected(self, tmp_path: Path):
        with pytest.raises(ValueError, match="absolute path|escapes project root"):
            safe_resolve_path(tmp_path, "/etc/passwd")
    
    def test_dotdot_escape_rejected(self, tmp_path: Path):
        with pytest.raises(ValueError, match="escapes project root"):
            safe_resolve_path(tmp_path, "../etc/passwd")
    
    def test_nested_path_accepted(self, tmp_path: Path):
        result = safe_resolve_path(tmp_path, "docs/subfolder/test.md")
        assert result == tmp_path / "docs" / "subfolder" / "test.md"
    
    def test_current_dir_path_accepted(self, tmp_path: Path):
        result = safe_resolve_path(tmp_path, "test.md")
        assert result == tmp_path / "test.md"
