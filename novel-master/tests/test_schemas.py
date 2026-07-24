"""test_schemas.py - JSON Schema 校验测试。

覆盖 prompt §13.1 要求的 10 个场景。
"""

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"
EXAMPLES_VALID = ROOT / "examples" / "valid"
EXAMPLES_INVALID = ROOT / "examples" / "invalid"


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_validator(schema_name: str) -> Draft202012Validator:
    schema = load_json(SCHEMAS_DIR / schema_name)
    return Draft202012Validator(schema)


def find_objects_without_additional_properties(
    node: object,
    path: str = "$",
) -> list[str]:
    """返回未声明 additionalProperties 策略的 object Schema 路径。"""
    missing: list[str] = []
    if isinstance(node, dict):
        node_type = node.get("type")
        is_object = node_type == "object" or (
            isinstance(node_type, list) and "object" in node_type
        )
        if (
            is_object
            and "additionalProperties" not in node
        ):
            missing.append(path)
        for key, value in node.items():
            missing.extend(
                find_objects_without_additional_properties(
                    value,
                    f"{path}/{key}",
                )
            )
    elif isinstance(node, list):
        for index, value in enumerate(node):
            missing.extend(
                find_objects_without_additional_properties(
                    value,
                    f"{path}/{index}",
                )
            )
    return missing


# ---------------------------------------------------------------------------
# 1. 合法 TaskEnvelope
# ---------------------------------------------------------------------------

class TestValidExamples:
    """合法样例必须全部通过。"""

    def test_valid_task_envelope(self):
        v = get_validator("task-envelope.schema.json")
        data = load_json(EXAMPLES_VALID / "task-envelope-valid.json")
        errors = list(v.iter_errors(data))
        assert errors == [], f"合法 TaskEnvelope 校验失败: {errors}"

    def test_valid_skill_result(self):
        v = get_validator("skill-result.schema.json")
        data = load_json(EXAMPLES_VALID / "skill-result-valid.json")
        errors = list(v.iter_errors(data))
        assert errors == [], f"合法 SkillResult 校验失败: {errors}"

    def test_valid_approval_ref(self):
        v = get_validator("approval-ref.schema.json")
        data = load_json(EXAMPLES_VALID / "approval-ref-valid.json")
        errors = list(v.iter_errors(data))
        assert errors == [], f"合法 ApprovalRef 校验失败: {errors}"

    def test_valid_changeset(self):
        v = get_validator("changeset.schema.json")
        data = load_json(EXAMPLES_VALID / "changeset-valid.json")
        errors = list(v.iter_errors(data))
        assert errors == [], f"合法 ChangeSet 校验失败: {errors}"

    def test_valid_context_pack(self):
        v = get_validator("context-pack.schema.json")
        data = load_json(EXAMPLES_VALID / "context-pack-valid.json")
        errors = list(v.iter_errors(data))
        assert errors == [], f"合法 ContextPack 校验失败: {errors}"

    def test_valid_master_result(self):
        v = get_validator("master-result.schema.json")
        data = load_json(EXAMPLES_VALID / "master-result-valid.json")
        errors = list(v.iter_errors(data))
        assert errors == [], f"合法 MasterResult 校验失败: {errors}"

    def test_valid_recovery_report(self):
        v = get_validator("recovery-report.schema.json")
        data = load_json(EXAMPLES_VALID / "recovery-report-valid.json")
        errors = list(v.iter_errors(data))
        assert errors == [], f"合法 RecoveryReport 校验失败: {errors}"


# ---------------------------------------------------------------------------
# 2-6. 非法样例
# ---------------------------------------------------------------------------

class TestInvalidExamples:
    """非法样例必须被拒绝。"""

    def test_missing_request_id(self):
        """缺少 request_id 必须失败。"""
        v = get_validator("task-envelope.schema.json")
        data = load_json(EXAMPLES_INVALID / "task-envelope-missing-request-id.json")
        errors = list(v.iter_errors(data))
        assert len(errors) > 0, "缺少 request_id 应被拒绝"

    def test_bad_enum(self):
        """非法枚举值必须失败。"""
        v = get_validator("task-envelope.schema.json")
        data = load_json(EXAMPLES_INVALID / "task-envelope-bad-enum.json")
        errors = list(v.iter_errors(data))
        assert len(errors) > 0, "非法枚举应被拒绝"

    def test_commit_state_wrong_skill(self):
        """COMMIT_STATE 指向非 continuity-keeper 必须失败。"""
        v = get_validator("task-envelope.schema.json")
        data = load_json(EXAMPLES_INVALID / "task-envelope-commit-state-wrong-skill.json")
        errors = list(v.iter_errors(data))
        assert len(errors) > 0, "COMMIT_STATE 指向错误 Skill 应被拒绝"

    def test_readonly_mutation(self):
        """READ_ONLY 但 source_mutation_allowed=true 必须失败。"""
        v = get_validator("task-envelope.schema.json")
        data = load_json(EXAMPLES_INVALID / "task-envelope-readonly-mutation.json")
        errors = list(v.iter_errors(data))
        assert len(errors) > 0, "READ_ONLY 允许 mutation 应被拒绝"

    def test_changeset_canon_delete(self):
        """DELETE 操作针对 Canon 文件必须失败。"""
        v = get_validator("changeset.schema.json")
        data = load_json(EXAMPLES_INVALID / "changeset-canon-delete.json")
        errors = list(v.iter_errors(data))
        assert len(errors) > 0, "Canon DELETE 应被拒绝"

    def test_non_accepted_chapter_commit(self):
        """DRAFT 来源的提交输入必须在生命周期语义层被拒绝。"""
        data = load_json(
            EXAMPLES_INVALID / "commit-input-non-accepted-chapter.json"
        )
        changeset_validator = get_validator("changeset.schema.json")
        assert list(
            changeset_validator.iter_errors(data["change_set"])
        ) == []

        sys.path.insert(0, str(ROOT / "scripts"))
        from commit_changeset import validate_source_deliverable

        errors = validate_source_deliverable(
            data["change_set"],
            data["source_deliverable"],
        )
        assert any("ACCEPTED" in error for error in errors)

    def test_changeset_path_outside_project(self):
        """路径逃逸样例必须直接被 ChangeSet Schema 拒绝。"""
        validator = get_validator("changeset.schema.json")
        data = load_json(
            EXAMPLES_INVALID / "changeset-path-outside-project.json"
        )
        errors = list(validator.iter_errors(data))
        assert errors

    def test_task_envelope_wrong_write_zone(self):
        """Schema 合法但目标路径不属于目标 Skill 时必须语义拒绝。"""
        validator = get_validator("task-envelope.schema.json")
        data = load_json(
            EXAMPLES_INVALID / "task-envelope-wrong-write-zone.json"
        )
        assert list(validator.iter_errors(data)) == []

        sys.path.insert(0, str(ROOT / "scripts"))
        from validate_paths import validate_paths

        results = validate_paths(
            Path("C:/novels/dragon-ascension"),
            data["task"]["target_skill"],
            data["output"]["target_paths"],
        )
        assert not results[0]["valid"]

    def test_proposal_in_committed_updates(self):
        """通用 SkillResult 不得携带未定义的 committed_updates。"""
        validator = get_validator("skill-result.schema.json")
        data = load_json(
            EXAMPLES_INVALID
            / "skill-result-proposal-in-committed-updates.json"
        )
        errors = list(validator.iter_errors(data))
        assert errors


# ---------------------------------------------------------------------------
# 7-10. 额外契约测试
# ---------------------------------------------------------------------------

class TestContractRules:
    """基于冻结契约的额外校验规则。"""

    def _make_task_envelope(self, **overrides) -> dict:
        """构造最小合法 TaskEnvelope 并应用覆盖。"""
        base = load_json(EXAMPLES_VALID / "task-envelope-valid.json")
        for key, value in overrides.items():
            keys = key.split(".")
            obj = base
            for k in keys[:-1]:
                obj = obj[k]
            obj[keys[-1]] = value
        return base

    def test_non_accepted_chapter_commit(self):
        """非 ACCEPTED/PUBLISHED 来源必须被提交语义校验拒绝。"""
        data = load_json(
            EXAMPLES_INVALID / "commit-input-non-accepted-chapter.json"
        )
        sys.path.insert(0, str(ROOT / "scripts"))
        from commit_changeset import validate_source_deliverable

        errors = validate_source_deliverable(
            data["change_set"],
            data["source_deliverable"],
        )
        assert any("ACCEPTED" in error for error in errors)

    def test_approval_ref_revision_mismatch(self):
        """ApprovalRef revision 不匹配必须被语义校验拒绝。"""
        data = load_json(EXAMPLES_INVALID / "approval-ref-revision-mismatch.json")
        validator = get_validator("approval-ref.schema.json")
        assert list(validator.iter_errors(data)) == []

        sys.path.insert(0, str(ROOT / "scripts"))
        from validate_approval import validate_approval

        errors = validate_approval(
            data,
            operation="COMMIT_CANON",
            target_files=["state/canon.md"],
            current_revision="rev-canon-42",
            request_id=data["request_id"],
        )
        assert any("based_on_revision 不一致" in error for error in errors)

    def test_path_outside_project(self):
        """路径越出项目根目录：由 validate_paths.py 校验。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        from validate_paths import normalize_path
        resolved, err = normalize_path(Path("/tmp/project"), "../../etc/passwd")
        assert resolved is None
        assert err is not None
        assert ".." in err

    def test_skill_write_wrong_zone(self):
        """Skill 写入非所有权区域：由 validate_paths.py 校验。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        from validate_paths import check_ownership
        # chapter-writer 试图写 state/
        owned, err = check_ownership("state/canon.md", "chapter-writer")
        assert not owned
        assert err is not None

    def test_proposal_in_committed_updates(self):
        """Proposal 出现在 committed_updates 必须被 SkillResult 契约拒绝。"""
        validator = get_validator("skill-result.schema.json")
        data = load_json(
            EXAMPLES_INVALID
            / "skill-result-proposal-in-committed-updates.json"
        )
        assert list(validator.iter_errors(data))


class TestSchemaStrictness:
    """所有对象 Schema 必须显式声明扩展字段策略。"""

    @pytest.mark.parametrize(
        "schema_path",
        sorted(SCHEMAS_DIR.glob("*.schema.json")),
        ids=lambda path: path.name,
    )
    def test_object_schema_declares_additional_properties(self, schema_path):
        schema = load_json(schema_path)
        Draft202012Validator.check_schema(schema)
        missing = find_objects_without_additional_properties(schema)
        assert missing == [], (
            f"{schema_path.name} 以下 object 未声明 additionalProperties: "
            f"{missing}"
        )

    @pytest.mark.parametrize("operation", ["EDIT_L4", "RETCON"])
    def test_high_risk_approval_requires_single_use(self, operation):
        validator = get_validator("approval-ref.schema.json")
        approval = load_json(EXAMPLES_VALID / "approval-ref-valid.json")
        approval["operation"] = operation
        approval["expires_after_use"] = False

        errors = list(validator.iter_errors(approval))

        assert errors, f"{operation} 必须要求 expires_after_use=true"

    def test_content_hash_requires_lowercase_sha256(self):
        validator = get_validator("skill-result.schema.json")
        result = load_json(EXAMPLES_VALID / "skill-result-valid.json")
        result["deliverables"][0]["content_hash"] = "A" * 64

        errors = list(validator.iter_errors(result))

        assert errors, "content_hash 必须是 64 位小写 SHA-256"

    def test_revision_rejects_ambiguous_whitespace(self):
        validator = get_validator("skill-result.schema.json")
        result = load_json(EXAMPLES_VALID / "skill-result-valid.json")
        result["deliverables"][0]["revision"] = "rev draft 1"

        errors = list(validator.iter_errors(result))

        assert errors, "revision 不得包含空白或无法递增的格式"
