"""test_changeset.py - ChangeSet 事务测试。

覆盖 prompt §13.3 要求的场景。
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import commit_changeset as changeset_module
from commit_changeset import (
    ALLOWED_WRITE_PREFIXES,
    CANON_PREFIXES,
    commit_changeset,
    compute_sha256,
    execute_changeset,
    load_yaml_or_json,
    validate_changeset,
)


class TestChangeSetValidation:
    """ChangeSet 校验规则。"""

    def _make_changeset(self, **overrides) -> dict:
        """构造合法 ChangeSet 并应用覆盖。"""
        base = {
            "change_set_id": "cs-001",
            "request_id": "req-001",
            "source_ref": "chapter_001 draft",
            "base_revision": {"state/canon.md": "3"},
            "target_updates": [
                {
                    "target_file": "state/canon.md",
                    "operation": "MODIFY",
                    "content": "# Canon\n\n主角出生于临海城。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }
        base.update(overrides)
        return base

    def test_allowed_write_prefixes(self):
        """只允许修改 state/ 和 workflow/change_log.md。"""
        assert "state/" in ALLOWED_WRITE_PREFIXES
        assert "workflow/change_log.md" in ALLOWED_WRITE_PREFIXES

    def test_canon_delete_prohibited(self, tmp_path):
        """Canon 项不允许通过 DELETE 移除。"""
        cs = self._make_changeset(
            target_updates=[
                {
                    "target_file": "state/canon.md",
                    "operation": "DELETE",
                    "content": "",
                }
            ]
        )
        errors = validate_changeset(cs, tmp_path, "req-001")
        assert errors, "Canon DELETE 必须在 Schema 或语义校验阶段被拒绝"

    def test_changeset_schema_valid(self):
        """合法 ChangeSet 通过 schema 校验。"""
        from jsonschema import Draft202012Validator
        schema_path = ROOT / "schemas" / "changeset.schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        v = Draft202012Validator(schema)
        cs = self._make_changeset()
        errors = list(v.iter_errors(cs))
        assert errors == [], f"合法 ChangeSet 校验失败: {errors}"

    def test_changeset_status_enum(self):
        """ChangeSet status 必须是合法枚举。"""
        from jsonschema import Draft202012Validator
        schema_path = ROOT / "schemas" / "changeset.schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        v = Draft202012Validator(schema)
        cs = self._make_changeset(status="INVALID_STATUS")
        errors = list(v.iter_errors(cs))
        assert len(errors) > 0, "非法 status 应被拒绝"


class TestChangeSetTransaction:
    """ChangeSet 事务流程测试（使用临时目录）。"""

    def _setup_project(self, tmp_path: Path) -> Path:
        """创建最小项目结构。"""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        workflow_dir = tmp_path / "workflow"
        workflow_dir.mkdir()
        (workflow_dir / "backups").mkdir()
        (workflow_dir / "changesets").mkdir()

        # 创建初始状态文件
        canon = state_dir / "canon.md"
        canon.write_text("# Canon\n\n初始内容。\n", encoding="utf-8")

        # 创建 .revisions.json
        revisions = {
            "state/canon.md": {
                "revision": 1,
                "content_hash": compute_sha256(canon),
            }
        }
        (tmp_path / ".revisions.json").write_text(
            json.dumps(revisions, ensure_ascii=False), encoding="utf-8"
        )

        # 创建 change_log
        (workflow_dir / "change_log.md").write_text(
            "# 变更日志\n", encoding="utf-8"
        )

        return tmp_path

    def _modify_canon_changeset(
        self,
        request_id: str = "req-commit",
        change_set_id: str = "cs-commit",
    ) -> dict:
        return {
            "change_set_id": change_set_id,
            "request_id": request_id,
            "source_ref": "chapter-001@rev-1",
            "base_revision": {"state/canon.md": "1"},
            "target_updates": [
                {
                    "target_file": "state/canon.md",
                    "operation": "MODIFY",
                    "content": "# Canon\n\n已提交的新内容。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

    def test_normal_commit(self, tmp_path):
        """正常提交流程。"""
        project = self._setup_project(tmp_path)
        canon = project / "state" / "canon.md"
        result = execute_changeset(
            self._modify_canon_changeset(),
            project,
        )
        revisions = json.loads(
            (project / ".revisions.json").read_text(encoding="utf-8")
        )

        assert result["status"] == "COMMITTED"
        assert canon.read_text(encoding="utf-8") == "# Canon\n\n已提交的新内容。\n"
        assert revisions["state/canon.md"]["revision"] == 2

    def test_add_creates_missing_state_file(self, tmp_path):
        """ADD 对不存在的状态文件创建内容并记录 revision。"""
        project = self._setup_project(tmp_path)
        changeset = {
            "change_set_id": "cs-add",
            "request_id": "req-add",
            "source_ref": "chapter-001@rev-1",
            "base_revision": {},
            "target_updates": [
                {
                    "target_file": "state/chapter_summaries.md",
                    "operation": "ADD",
                    "content": "## 第1章\n摘要内容。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        errors = validate_changeset(changeset, project, "req-add")
        assert errors == []

        result = execute_changeset(changeset, project)
        target = project / "state" / "chapter_summaries.md"
        revisions = json.loads(
            (project / ".revisions.json").read_text(encoding="utf-8")
        )

        assert result["status"] == "COMMITTED"
        assert target.read_text(encoding="utf-8") == "## 第1章\n摘要内容。\n"
        assert "state/chapter_summaries.md" in revisions

    def test_add_appends_to_existing_state_file(self, tmp_path):
        """ADD 保留已有内容，并把新结构项追加到文件末尾。"""
        project = self._setup_project(tmp_path)
        target = project / "state" / "chapter_summaries.md"
        target.write_text("## 第1章\n旧摘要。\n", encoding="utf-8")
        revisions = json.loads(
            (project / ".revisions.json").read_text(encoding="utf-8")
        )
        revisions["state/chapter_summaries.md"] = {
            "revision": 1,
            "content_hash": compute_sha256(target),
        }
        (project / ".revisions.json").write_text(
            json.dumps(revisions, ensure_ascii=False),
            encoding="utf-8",
        )
        changeset = {
            "change_set_id": "cs-add-existing",
            "request_id": "req-add-existing",
            "source_ref": "chapter-002@rev-1",
            "base_revision": {"state/chapter_summaries.md": "1"},
            "target_updates": [
                {
                    "target_file": "state/chapter_summaries.md",
                    "operation": "ADD",
                    "content": "## 第2章\n新摘要。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        assert validate_changeset(
            changeset, project, "req-add-existing"
        ) == []
        result = execute_changeset(changeset, project)

        assert result["status"] == "COMMITTED"
        assert target.read_text(encoding="utf-8") == (
            "## 第1章\n旧摘要。\n\n## 第2章\n新摘要。\n"
        )

    def test_change_log_failure_rolls_back_add_and_revisions(
        self, tmp_path, monkeypatch
    ):
        """日志提交失败时，新文件和 revision 必须一起回滚。"""
        project = self._setup_project(tmp_path)
        revisions_path = project / ".revisions.json"
        revisions_before = revisions_path.read_bytes()
        real_append_change_log = changeset_module.append_change_log
        calls = 0

        def fail_first_log_write(project_root, message):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("injected change_log failure")
            real_append_change_log(project_root, message)

        monkeypatch.setattr(
            changeset_module,
            "append_change_log",
            fail_first_log_write,
        )
        changeset = {
            "change_set_id": "cs-log-failure",
            "request_id": "req-log-failure",
            "source_ref": "chapter-003@rev-1",
            "base_revision": {},
            "target_updates": [
                {
                    "target_file": "state/chapter_summaries.md",
                    "operation": "ADD",
                    "content": "## 第3章\n不应残留。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        result = execute_changeset(changeset, project)

        assert result["status"] == "ROLLED_BACK"
        assert not (project / "state" / "chapter_summaries.md").exists()
        assert revisions_path.read_bytes() == revisions_before
        assert "CHANGESET_ROLLED_BACK" in (
            project / "workflow" / "change_log.md"
        ).read_text(encoding="utf-8")

    def test_commit_canon_without_approval_is_rejected(self, tmp_path):
        """COMMIT_CANON 缺少 ApprovalRef 时不得进入写入阶段。"""
        project = self._setup_project(tmp_path)
        canon = project / "state" / "canon.md"
        content_before = canon.read_text(encoding="utf-8")
        changeset = {
            "change_set_id": "cs-no-approval",
            "request_id": "req-no-approval",
            "source_ref": "canon-proposal@rev-1",
            "base_revision": {"state/canon.md": "1"},
            "target_updates": [
                {
                    "target_file": "state/canon.md",
                    "operation": "MODIFY",
                    "content": "# Canon\n\n未经授权的内容。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        result = commit_changeset(
            changeset,
            project,
            request_id="req-no-approval",
            operation="COMMIT_CANON",
        )

        assert result["status"] == "VALIDATION_FAILED"
        assert any("ApprovalRef" in error for error in result["errors"])
        assert canon.read_text(encoding="utf-8") == content_before

    def test_commit_canon_consumes_one_time_approval(self, tmp_path):
        """高风险提交成功后，一次性 ApprovalRef 必须持久化为 USED。"""
        project = self._setup_project(tmp_path)
        lock_path = project / "workflow" / ".write.lock"
        lock_path.write_text(
            yaml.safe_dump({"request_id": "req-approved"}),
            encoding="utf-8",
        )
        approval = {
            "approval_id": "appr-approved",
            "request_id": "req-approved",
            "approved_by": "user",
            "approved_at": "2026-07-24T10:00:00+08:00",
            "operation": "COMMIT_CANON",
            "approved_scope": {
                "files": ["state/canon.md"],
                "items": [],
            },
            "based_on_revision": "proposal-rev-1",
            "expires_after_use": True,
            "status": "ACTIVE",
        }
        approval_path = project / "workflow" / "approvals" / "appr-approved.json"
        approval_path.parent.mkdir(parents=True)
        approval_path.write_text(
            json.dumps(approval, ensure_ascii=False),
            encoding="utf-8",
        )
        changeset = {
            "change_set_id": "cs-approved",
            "request_id": "req-approved",
            "source_ref": "canon-proposal@proposal-rev-1",
            "base_revision": {"state/canon.md": "1"},
            "target_updates": [
                {
                    "target_file": "state/canon.md",
                    "operation": "MODIFY",
                    "content": "# Canon\n\n已授权的新内容。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        result = commit_changeset(
            changeset,
            project,
            request_id="req-approved",
            operation="COMMIT_CANON",
            approval=approval,
            approval_current_revision="proposal-rev-1",
            approval_path=approval_path,
        )

        assert result["status"] == "COMMITTED"
        persisted = json.loads(approval_path.read_text(encoding="utf-8"))
        assert persisted["status"] == "USED"

    def test_prefixed_revision_increments_after_modify(self, tmp_path):
        """冻结合同样例中的前缀 revision 应保持前缀并递增。"""
        project = self._setup_project(tmp_path)
        revisions_path = project / ".revisions.json"
        revisions = json.loads(revisions_path.read_text(encoding="utf-8"))
        revisions["state/canon.md"]["revision"] = "rev-canon-42"
        revisions_path.write_text(
            json.dumps(revisions, ensure_ascii=False),
            encoding="utf-8",
        )
        changeset = {
            "change_set_id": "cs-prefixed-revision",
            "request_id": "req-prefixed-revision",
            "source_ref": "chapter-004@rev-1",
            "base_revision": {"state/canon.md": "rev-canon-42"},
            "target_updates": [
                {
                    "target_file": "state/canon.md",
                    "operation": "MODIFY",
                    "content": "# Canon\n\n前缀 revision 新内容。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        assert validate_changeset(
            changeset,
            project,
            "req-prefixed-revision",
        ) == []
        result = execute_changeset(changeset, project)

        assert result["status"] == "COMMITTED"
        updated = json.loads(revisions_path.read_text(encoding="utf-8"))
        assert updated["state/canon.md"]["revision"] == "rev-canon-43"

    def test_failed_commit_does_not_consume_approval(
        self, tmp_path, monkeypatch
    ):
        """事务失败回滚时，一次性授权必须保持 ACTIVE。"""
        project = self._setup_project(tmp_path)
        canon = project / "state" / "canon.md"
        canon_before = canon.read_bytes()
        revisions_path = project / ".revisions.json"
        revisions_before = revisions_path.read_bytes()
        (project / "workflow" / ".write.lock").write_text(
            yaml.safe_dump({"request_id": "req-rollback-approval"}),
            encoding="utf-8",
        )
        approval = {
            "approval_id": "appr-rollback",
            "request_id": "req-rollback-approval",
            "approved_by": "user",
            "approved_at": "2026-07-24T10:00:00+08:00",
            "operation": "COMMIT_CANON",
            "approved_scope": {
                "files": ["state/canon.md"],
                "items": [],
            },
            "based_on_revision": "proposal-rev-2",
            "expires_after_use": True,
            "status": "ACTIVE",
        }
        approval_path = project / "workflow" / "approvals" / "rollback.json"
        approval_path.parent.mkdir(parents=True)
        approval_path.write_text(
            json.dumps(approval, ensure_ascii=False),
            encoding="utf-8",
        )
        real_append_change_log = changeset_module.append_change_log
        calls = 0

        def fail_first_log_write(project_root, message):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("injected approval transaction failure")
            real_append_change_log(project_root, message)

        monkeypatch.setattr(
            changeset_module,
            "append_change_log",
            fail_first_log_write,
        )
        changeset = {
            "change_set_id": "cs-rollback-approval",
            "request_id": "req-rollback-approval",
            "source_ref": "canon-proposal@proposal-rev-2",
            "base_revision": {"state/canon.md": "1"},
            "target_updates": [
                {
                    "target_file": "state/canon.md",
                    "operation": "MODIFY",
                    "content": "# Canon\n\n本次提交应回滚。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        result = commit_changeset(
            changeset,
            project,
            request_id="req-rollback-approval",
            operation="COMMIT_CANON",
            approval=approval,
            approval_current_revision="proposal-rev-2",
            approval_path=approval_path,
        )

        assert result["status"] == "ROLLED_BACK"
        assert canon.read_bytes() == canon_before
        assert revisions_path.read_bytes() == revisions_before
        persisted = json.loads(approval_path.read_text(encoding="utf-8"))
        assert persisted["status"] == "ACTIVE"
        assert approval["status"] == "ACTIVE"

    def test_second_file_replace_failure_restores_all_targets(
        self, tmp_path, monkeypatch
    ):
        """多文件 APPLY 中途失败时，不得留下首个文件的部分提交。"""
        project = self._setup_project(tmp_path)
        character = project / "state" / "character_state.md"
        character.write_text("# 人物状态\n\n旧状态。\n", encoding="utf-8")
        revisions_path = project / ".revisions.json"
        revisions = json.loads(revisions_path.read_text(encoding="utf-8"))
        revisions["state/character_state.md"] = {
            "revision": 1,
            "content_hash": compute_sha256(character),
        }
        revisions_path.write_text(
            json.dumps(revisions, ensure_ascii=False),
            encoding="utf-8",
        )
        canon = project / "state" / "canon.md"
        canon_before = canon.read_bytes()
        character_before = character.read_bytes()
        revisions_before = revisions_path.read_bytes()
        (project / "workflow" / ".write.lock").write_text(
            yaml.safe_dump({"request_id": "req-two-files"}),
            encoding="utf-8",
        )
        real_replace = changeset_module.os.replace

        def fail_character_replace(source, destination):
            if Path(destination).name == "character_state.md":
                raise OSError("injected second replace failure")
            real_replace(source, destination)

        monkeypatch.setattr(
            changeset_module.os,
            "replace",
            fail_character_replace,
        )
        changeset = {
            "change_set_id": "cs-two-files",
            "request_id": "req-two-files",
            "source_ref": "chapter-005@rev-1",
            "base_revision": {
                "state/canon.md": "1",
                "state/character_state.md": "1",
            },
            "target_updates": [
                {
                    "target_file": "state/canon.md",
                    "operation": "MODIFY",
                    "content": "# Canon\n\n新事实。\n",
                },
                {
                    "target_file": "state/character_state.md",
                    "operation": "MODIFY",
                    "content": "# 人物状态\n\n新状态。\n",
                },
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        result = commit_changeset(
            changeset,
            project,
            request_id="req-two-files",
            operation="REBUILD_DERIVED_STATE",
        )

        assert result["status"] == "ROLLED_BACK"
        assert canon.read_bytes() == canon_before
        assert character.read_bytes() == character_before
        assert revisions_path.read_bytes() == revisions_before

    def test_draft_source_cannot_commit_chapter_state(self, tmp_path):
        """DRAFT 来源不得进入 COMMIT_CHAPTER_STATE 写入阶段。"""
        project = self._setup_project(tmp_path)
        canon = project / "state" / "canon.md"
        canon_before = canon.read_bytes()
        (project / "workflow" / ".write.lock").write_text(
            yaml.safe_dump({"request_id": "req-draft-source"}),
            encoding="utf-8",
        )
        changeset = {
            "change_set_id": "cs-draft-source",
            "request_id": "req-draft-source",
            "source_ref": "chapter-006@rev-1",
            "base_revision": {"state/canon.md": "1"},
            "target_updates": [
                {
                    "target_file": "state/canon.md",
                    "operation": "MODIFY",
                    "content": "# Canon\n\nDRAFT 不得提交。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }
        source_deliverable = {
            "deliverable_id": "chapter-006",
            "revision": "rev-1",
            "content_hash": "a" * 64,
            "chapter_lifecycle_status": "DRAFT",
        }

        result = commit_changeset(
            changeset,
            project,
            request_id="req-draft-source",
            operation="COMMIT_CHAPTER_STATE",
            source_deliverable=source_deliverable,
        )

        assert result["status"] == "VALIDATION_FAILED"
        assert any("ACCEPTED" in error for error in result["errors"])
        assert canon.read_bytes() == canon_before

    def test_execute_rejects_unknown_operation_without_false_commit(
        self, tmp_path
    ):
        """即使直接调用执行入口，未知操作也不能返回 COMMITTED。"""
        project = self._setup_project(tmp_path)
        changeset = {
            "change_set_id": "cs-create-alias",
            "request_id": "req-create-alias",
            "source_ref": "chapter-007@rev-1",
            "base_revision": {},
            "target_updates": [
                {
                    "target_file": "state/unknown.md",
                    "operation": "CREATE",
                    "content": "不允许的别名。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        result = execute_changeset(changeset, project)

        assert result["status"] == "VALIDATION_FAILED"
        assert not (project / "state" / "unknown.md").exists()

    def test_modify_without_content_change_is_not_committed(self, tmp_path):
        """内容未变化时不得伪造提交或递增 revision。"""
        project = self._setup_project(tmp_path)
        canon = project / "state" / "canon.md"
        revisions_path = project / ".revisions.json"
        revisions_before = revisions_path.read_bytes()
        changeset = {
            "change_set_id": "cs-no-change",
            "request_id": "req-no-change",
            "source_ref": "chapter-008@rev-1",
            "base_revision": {"state/canon.md": "1"},
            "target_updates": [
                {
                    "target_file": "state/canon.md",
                    "operation": "MODIFY",
                    "content": canon.read_text(encoding="utf-8"),
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        result = execute_changeset(changeset, project)

        assert result["status"] == "VALIDATION_FAILED"
        assert revisions_path.read_bytes() == revisions_before

    def test_accepted_source_commits_chapter_state(self, tmp_path):
        """ACCEPTED 来源绑定 revision/hash 后可以提交状态。"""
        project = self._setup_project(tmp_path)
        (project / "workflow" / ".write.lock").write_text(
            yaml.safe_dump({"request_id": "req-accepted-source"}),
            encoding="utf-8",
        )
        changeset = {
            "change_set_id": "cs-accepted-source",
            "request_id": "req-accepted-source",
            "source_ref": "chapter-009@rev-2",
            "base_revision": {"state/canon.md": "1"},
            "target_updates": [
                {
                    "target_file": "state/canon.md",
                    "operation": "MODIFY",
                    "content": "# Canon\n\n已接受章节产生的新事实。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        result = commit_changeset(
            changeset,
            project,
            request_id="req-accepted-source",
            operation="COMMIT_CHAPTER_STATE",
            source_deliverable={
                "deliverable_id": "chapter-009",
                "revision": "rev-2",
                "content_hash": "b" * 64,
                "chapter_lifecycle_status": "ACCEPTED",
            },
        )

        assert result["status"] == "COMMITTED"
        assert "已接受章节产生的新事实" in (
            project / "state" / "canon.md"
        ).read_text(encoding="utf-8")

    def test_state_prefix_with_parent_traversal_is_rejected(self, tmp_path):
        """state/ 前缀不能掩盖规范化后的项目根目录逃逸。"""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        project = self._setup_project(project_dir)
        escaped = tmp_path / "escaped.md"
        changeset = {
            "change_set_id": "cs-path-escape",
            "request_id": "req-path-escape",
            "source_ref": "chapter-010@rev-1",
            "base_revision": {},
            "target_updates": [
                {
                    "target_file": "state/../../escaped.md",
                    "operation": "ADD",
                    "content": "不得写出项目目录。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        result = execute_changeset(changeset, project)

        assert result["status"] == "VALIDATION_FAILED"
        assert not escaped.exists()

    def test_cli_commits_accepted_chapter_state(self, tmp_path):
        """命令行入口必须经过锁、生命周期和统一事务后完成提交。"""
        project = self._setup_project(tmp_path)
        (project / "workflow" / ".write.lock").write_text(
            yaml.safe_dump({"request_id": "req-cli"}),
            encoding="utf-8",
        )
        changeset = {
            "change_set_id": "cs-cli",
            "request_id": "req-cli",
            "source_ref": "chapter-cli@rev-1",
            "base_revision": {"state/canon.md": "1"},
            "target_updates": [
                {
                    "target_file": "state/canon.md",
                    "operation": "MODIFY",
                    "content": "# Canon\n\nCLI 提交内容。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }
        source_deliverable = {
            "deliverable_id": "chapter-cli",
            "revision": "rev-1",
            "content_hash": "c" * 64,
            "chapter_lifecycle_status": "ACCEPTED",
        }
        changeset_path = project / "workflow" / "changesets" / "cs-cli.json"
        changeset_path.write_text(
            json.dumps(changeset, ensure_ascii=False),
            encoding="utf-8",
        )
        source_path = project / "workflow" / "source-deliverable.json"
        source_path.write_text(
            json.dumps(source_deliverable, ensure_ascii=False),
            encoding="utf-8",
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "commit_changeset.py"),
                "--project-root",
                str(project),
                "--changeset",
                str(changeset_path),
                "--request-id",
                "req-cli",
                "--operation",
                "COMMIT_CHAPTER_STATE",
                "--source-deliverable",
                str(source_path),
            ],
            cwd=ROOT,
            env={**os.environ, "PYTHONUTF8": "1"},
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        assert completed.returncode == 0, completed.stderr
        result = json.loads(completed.stdout)
        assert result["status"] == "COMMITTED"
        assert "CLI 提交内容" in (
            project / "state" / "canon.md"
        ).read_text(encoding="utf-8")

    def test_verify_failure_never_applies_temp_file(
        self, tmp_path, monkeypatch
    ):
        """VERIFY 检测到临时内容不一致时，正式文件保持未创建。"""
        project = self._setup_project(tmp_path)
        revisions_path = project / ".revisions.json"
        revisions_before = revisions_path.read_bytes()
        real_compute_sha256 = changeset_module.compute_sha256

        def corrupt_temp_hash(path):
            if Path(path).suffix == ".tmp":
                return "0" * 64
            return real_compute_sha256(path)

        monkeypatch.setattr(
            changeset_module,
            "compute_sha256",
            corrupt_temp_hash,
        )
        changeset = {
            "change_set_id": "cs-verify-failure",
            "request_id": "req-verify-failure",
            "source_ref": "chapter-011@rev-1",
            "base_revision": {},
            "target_updates": [
                {
                    "target_file": "state/chapter_summaries.md",
                    "operation": "ADD",
                    "content": "## 第11章\n临时校验失败。\n",
                }
            ],
            "status": "PREPARED",
            "created_at": "2026-07-24T10:00:00+08:00",
            "committed_at": None,
        }

        result = execute_changeset(changeset, project)

        assert result["status"] == "ROLLED_BACK"
        assert not (project / "state" / "chapter_summaries.md").exists()
        assert revisions_path.read_bytes() == revisions_before

    def test_revision_stale_detection(self, tmp_path):
        """revision 过期检测。"""
        project = self._setup_project(tmp_path)
        changeset = self._modify_canon_changeset()
        changeset["base_revision"]["state/canon.md"] = "999"
        errors = validate_changeset(changeset, project, "req-commit")
        assert any("STALE_CONTEXT" in error for error in errors)

    def test_backup_creation(self, tmp_path):
        """备份创建。"""
        project = self._setup_project(tmp_path)
        canon = project / "state" / "canon.md"
        original = canon.read_text(encoding="utf-8")
        result = execute_changeset(
            self._modify_canon_changeset(change_set_id="cs-test"),
            project,
        )
        backup_file = (
            project
            / "workflow"
            / "backups"
            / "cs-test"
            / "state"
            / "canon.md"
        )

        assert result["status"] == "COMMITTED"
        assert backup_file.exists()
        assert backup_file.read_text(encoding="utf-8") == original

    def test_rollback_from_backup(self, tmp_path):
        """执行失败后由生产事务从备份恢复。"""
        project = self._setup_project(tmp_path)
        canon = project / "state" / "canon.md"
        original_content = canon.read_text(encoding="utf-8")
        real_save_revisions = changeset_module.save_revisions

        def fail_save_revisions(project_root, data):
            raise OSError("injected revision failure")

        changeset_module.save_revisions = fail_save_revisions
        try:
            result = execute_changeset(
                self._modify_canon_changeset(change_set_id="cs-rollback"),
                project,
            )
        finally:
            changeset_module.save_revisions = real_save_revisions

        assert result["status"] == "ROLLED_BACK"
        assert canon.read_text(encoding="utf-8") == original_content

    def test_no_lock_commit_rejected(self, tmp_path):
        """无锁提交应被拒绝。"""
        project = self._setup_project(tmp_path)
        result = commit_changeset(
            self._modify_canon_changeset(request_id="req-no-lock"),
            project,
            request_id="req-no-lock",
            operation="REBUILD_DERIVED_STATE",
        )
        assert result["status"] == "LOCK_FAILED"

    def test_lock_conflict(self, tmp_path):
        """锁被其他 request 占用。"""
        project = self._setup_project(tmp_path)
        lock_path = project / "workflow" / ".write.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_data = {
            "request_id": "req-other",
            "created_at": "2026-07-24T10:00:00+08:00",
            "process_id": None,
        }
        with open(lock_path, "w", encoding="utf-8") as f:
            yaml.dump(lock_data, f)

        result = commit_changeset(
            self._modify_canon_changeset(request_id="req-current"),
            project,
            request_id="req-current",
            operation="REBUILD_DERIVED_STATE",
        )
        assert result["status"] == "LOCK_FAILED"
        assert "req-other" in result["errors"][0]

    def test_change_log_update(self, tmp_path):
        """change_log 更新。"""
        project = self._setup_project(tmp_path)
        change_log = project / "workflow" / "change_log.md"
        result = execute_changeset(
            self._modify_canon_changeset(change_set_id="cs-log"),
            project,
        )

        assert result["status"] == "COMMITTED"
        assert "CHANGESET_COMMITTED: id='cs-log'" in change_log.read_text(
            encoding="utf-8"
        )
