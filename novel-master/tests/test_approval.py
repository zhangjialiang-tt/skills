"""test_approval.py - ApprovalRef 校验测试。

覆盖 prompt §13.1 中 ApprovalRef 相关场景。
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_approval import (
    check_scope_coverage,
    load_approval,
    validate_approval,
)


class TestApprovalValidation:
    """ApprovalRef 校验。"""

    def _make_approval(self, **overrides) -> dict:
        """构造合法 ApprovalRef 并应用覆盖。"""
        base = {
            "approval_id": "appr-001",
            "request_id": "req-001",
            "approved_by": "user",
            "approved_at": "2026-07-24T10:00:00+08:00",
            "operation": "COMMIT_CANON",
            "approved_scope": {
                "files": ["state/canon.md"],
                "items": ["主角出生于临海城"],
            },
            "based_on_revision": "3",
            "expires_after_use": True,
            "status": "ACTIVE",
        }
        base.update(overrides)
        return base

    def test_valid_approval(self, tmp_path):
        """合法 ApprovalRef 能通过完整语义校验。"""
        appr = self._make_approval()
        path = tmp_path / "appr.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(appr, f, allow_unicode=True)
        loaded = load_approval(path)
        errors = validate_approval(
            loaded,
            operation="COMMIT_CANON",
            target_files=["state/canon.md"],
            current_revision="3",
            request_id="req-001",
        )
        assert errors == []

    def test_scope_coverage_match(self):
        """approved_scope 覆盖目标文件。"""
        errors = check_scope_coverage(["state/canon.md", "state/timeline.md"], ["state/canon.md"])
        assert errors == []

    def test_scope_coverage_missing(self):
        """approved_scope 未覆盖目标文件。"""
        errors = check_scope_coverage(["state/canon.md"], ["state/timeline.md"])
        assert len(errors) > 0

    def test_status_not_active(self):
        """status 不是 ACTIVE 时应被拒绝（语义校验）。"""
        appr = self._make_approval(status="USED")
        errors = validate_approval(
            appr,
            operation="COMMIT_CANON",
            target_files=["state/canon.md"],
            current_revision="3",
            request_id="req-001",
        )
        assert any("status 不是 ACTIVE" in error for error in errors)

    def test_expires_after_use(self):
        """L4/RETCON 必须 expires_after_use=true。"""
        appr = self._make_approval(
            operation="RETCON",
            expires_after_use=False,
        )
        errors = validate_approval(
            appr,
            operation="RETCON",
            target_files=["state/canon.md"],
            current_revision="3",
            request_id="req-001",
        )
        assert any("expires_after_use=true" in error for error in errors)

    def test_operation_mismatch(self):
        """operation 不匹配时应被拒绝。"""
        appr = self._make_approval(operation="COMMIT_CANON")
        errors = validate_approval(
            appr,
            operation="EDIT_L4",
            target_files=["state/canon.md"],
            current_revision="3",
            request_id="req-001",
        )
        assert any("operation 不匹配" in error for error in errors)

    def test_revision_mismatch(self):
        """批准后来源 revision 变化时授权失效。"""
        errors = validate_approval(
            self._make_approval(),
            operation="COMMIT_CANON",
            target_files=["state/canon.md"],
            current_revision="4",
            request_id="req-001",
        )
        assert any("based_on_revision 不一致" in error for error in errors)

    def test_request_mismatch(self):
        """ApprovalRef 不得跨 request 使用。"""
        errors = validate_approval(
            self._make_approval(),
            operation="COMMIT_CANON",
            target_files=["state/canon.md"],
            current_revision="3",
            request_id="req-other",
        )
        assert any("request_id 不匹配" in error for error in errors)

    def test_init_project_can_authorize_initial_commit_canon(self):
        """冻结合同允许 INIT_PROJECT 覆盖同一初始化范围的首次 Canon 提交。"""
        approval = self._make_approval(operation="INIT_PROJECT")
        errors = validate_approval(
            approval,
            operation="COMMIT_CANON",
            target_files=["state/canon.md"],
            current_revision="3",
            request_id="req-001",
        )
        assert errors == []

    def test_approval_file_not_found(self, tmp_path):
        """不存在的文件应抛出异常。"""
        with pytest.raises(FileNotFoundError):
            load_approval(tmp_path / "nonexistent.yaml")
