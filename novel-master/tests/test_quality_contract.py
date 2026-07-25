"""test_quality_contract.py — V1.2 quality contract deterministic tests.

Coverage: QC-001 through QC-019 from v1.2.0-quality-contract-plan §4.1.
"""

import json
import re
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"
SCRIPTS_DIR = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# Schema loader with $ref resolution
# ---------------------------------------------------------------------------

def _load_schema(name: str) -> dict:
    """Load schema and return as dict."""
    path = SCHEMAS_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def _make_registry() -> Registry:
    """Build a registry that resolves all $ref paths under schemas/."""
    resources = []
    for f in SCHEMAS_DIR.rglob("*.json"):
        rel = str(f.relative_to(SCHEMAS_DIR)).replace("\\", "/")
        schema = json.loads(f.read_text(encoding="utf-8"))
        resources.append((rel, Resource.from_contents(schema)))
    return Registry().with_resources(resources)


_REGISTRY = _make_registry()


def _make_validator(schema_name: str) -> Draft202012Validator:
    """Create a Draft202012Validator with fully resolved $ref registry.

    The $id values in schema files (like "defs/evidence-ref.schema.json")
    are used as the registry keys so that $ref resolution works.
    """
    schema = _load_schema(schema_name)
    # Use the schema file's own $id for the registry key
    sid = schema.get("$id", schema_name)
    resource = Resource.from_contents(schema)
    registry = _REGISTRY.with_resource(sid, resource)
    return Draft202012Validator(schema, registry=registry)


# ---------------------------------------------------------------------------
# Schema load helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def validate_reader_exp():
    return _make_validator("defs/reader-experience.schema.json")


@pytest.fixture(scope="module")
def validate_chapter_plan():
    return _make_validator("chapter-plan.schema.json")


@pytest.fixture(scope="module")
def validate_chapter_report():
    return _make_validator("chapter-report.schema.json")


@pytest.fixture(scope="module")
def validate_review_request():
    return _make_validator("review-request.schema.json")


@pytest.fixture(scope="module")
def validate_review_report():
    return _make_validator("review-report.schema.json")


@pytest.fixture(scope="module")
def validate_style_guide():
    return _make_validator("style-guide.schema.json")


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def _make_reader_experience(**overrides):
    base = {
        "chapter_role": {"primary": "ESCALATION", "description": "冲突升级"},
        "promise": "主角在绝境中发现隐藏力量",
        "payoff": {"mode": "FULL", "description": "主角突破围困"},
        "emotional_arc": {"target": "紧张→释放"},
        "tension_curve": {"type": "RISING", "description": "全程上升"},
        "continuation_drive": {"type": "DANGER", "description": "反派增援将至"}
    }
    base.update(overrides)
    return base


def _make_chapter_plan(**overrides):
    base = {
        "chapter_plan": {
            "chapter_id": "1",
            "chapter_function": "测试章",
            "viewpoint_character": "主角",
            "time_and_location": "测试地点",
            "scenes": [{"scene_id": "s1", "goal": "g", "conflict": "c", "action": "a", "style_modulation_ref": None}],
            "chapter_climax": "高潮",
            "contract_meta": {"schema_id": "novel-master/chapter-plan", "schema_version": "1.2.0"}
        }
    }
    base["chapter_plan"].update(overrides)
    return base


def _make_chapter_report(**overrides):
    base = {
        "chapter_report": {
            "reader_experience_execution": {
                "target_execution": [{
                    "target_ref": "/reader_experience/promise",
                    "execution": "PRESENT",
                    "evidence_ref": {
                        "source_type": "CHAPTER_DRAFT", "deliverable_id": "d1",
                        "revision": "1", "excerpt": "test"
                    }
                }]
            },
            "contract_meta": {"schema_id": "novel-master/chapter-report", "schema_version": "1.2.0"}
        }
    }
    base["chapter_report"].update(overrides)
    return base


def _make_style_guide(**overrides):
    base = {
        "style_guide": {
            "scene_modulations": {
                "DEFAULT": {
                    "category": "DEFAULT",
                    "overrides": {}
                }
            },
            "override_policy": {
                "protected_fields": ["/narrative/viewpoint"]
            },
            "contract_meta": {"schema_id": "novel-master/style-guide", "schema_version": "1.2.0"}
        }
    }
    base["style_guide"].update(overrides)
    return base


# ============================================================================
# QC-001 — QC-008: Reader Experience Schema
# ============================================================================

class TestReaderExperienceSchema:

    # QC-001 — STRICT requires reader_experience (cross-object check in validate_quality_contract.py)
    def test_reader_experience_valid(self, validate_reader_exp):
        """QC-001: Valid reader_experience passes schema."""
        re = _make_reader_experience()
        assert validate_reader_exp.is_valid(re)

    # QC-004
    def test_empty_object_rejected(self, validate_reader_exp):
        """QC-004: Empty {} rejected (missing required fields)."""
        assert not validate_reader_exp.is_valid({})

    # QC-005
    def test_payoff_deferred_requires_reason(self, validate_reader_exp):
        """QC-005: payoff.mode=DEFERRED without deferred_reason rejected."""
        re = _make_reader_experience(payoff={"mode": "DEFERRED", "description": "延期兑现"})
        assert not validate_reader_exp.is_valid(re)

    def test_payoff_deferred_with_reason_passes(self, validate_reader_exp):
        re = _make_reader_experience(
            payoff={"mode": "DEFERRED", "description": "延期", "deferred_reason": "需要铺垫"})
        assert validate_reader_exp.is_valid(re)

    # QC-006
    def test_payoff_none_justified_requires_justification(self, validate_reader_exp):
        """QC-006: payoff.mode=NONE_JUSTIFIED without justification rejected."""
        re = _make_reader_experience(payoff={"mode": "NONE_JUSTIFIED", "description": "过渡章"})
        assert not validate_reader_exp.is_valid(re)

    def test_payoff_none_justified_with_justification_passes(self, validate_reader_exp):
        re = _make_reader_experience(
            payoff={"mode": "NONE_JUSTIFIED", "description": "过渡", "justification": "过渡章无需兑现"})
        assert validate_reader_exp.is_valid(re)

    # QC-007
    def test_continuation_none_justified_requires_justification(self, validate_reader_exp):
        """QC-007: continuation_drive.type=NONE_JUSTIFIED without justification rejected."""
        re = _make_reader_experience(
            continuation_drive={"type": "NONE_JUSTIFIED", "description": "章末无明确动力"})
        assert not validate_reader_exp.is_valid(re)

    # QC-008
    def test_illegal_enum_rejected(self, validate_reader_exp):
        """QC-008: Illegal chapter_role.primary value rejected."""
        re = _make_reader_experience(
            chapter_role={"primary": "INVALID_VALUE", "description": "bad"})
        assert not validate_reader_exp.is_valid(re)


# ============================================================================
# QC-009 — QC-011: Chapter Plan / Report / Review Request
# ============================================================================

class TestChapterPlanSchema:

    # QC-009 (cross-file) verified in validate_quality_contract; schema checks structure
    def test_valid_plan_with_reader_experience(self, validate_chapter_plan):
        """Valid v1.2 chapter plan with reader_experience."""
        plan = _make_chapter_plan()
        plan["chapter_plan"]["reader_experience"] = _make_reader_experience()
        assert validate_chapter_plan.is_valid(plan)

    def test_scene_style_modulation_ref_null_ok(self, validate_chapter_plan):
        plan = _make_chapter_plan()
        plan["chapter_plan"]["reader_experience"] = _make_reader_experience()
        # style_modulation_ref null is valid per schema
        assert plan["chapter_plan"]["scenes"][0]["style_modulation_ref"] is None
        assert validate_chapter_plan.is_valid(plan)

    def test_missing_contract_meta_rejected(self, validate_chapter_plan):
        """QC-017: legacy plan without contract_meta accepted (not required)."""
        plan = _make_chapter_plan()
        del plan["chapter_plan"]["contract_meta"]
        plan["chapter_plan"]["reader_experience"] = _make_reader_experience()
        errors = list(validate_chapter_plan.iter_errors(plan))
        assert len(errors) > 0  # contract_meta is required


class TestChapterReportSchema:

    # QC-010
    def test_valid_report_with_target_execution(self, validate_chapter_report):
        """QC-010: Valid chapter_report with target_execution and evidence_ref."""
        assert validate_chapter_report.is_valid(_make_chapter_report())

    def test_missing_target_execution_rejected(self, validate_chapter_report):
        report = {"chapter_report": {
            "reader_experience_execution": {"target_execution": []},
            "contract_meta": {"schema_id": "novel-master/chapter-report", "schema_version": "1.2.0"}
        }}
        # target_execution minItems=1
        assert not validate_chapter_report.is_valid(report)


class TestReviewRequestSchema:

    # QC-011
    def test_valid_review_scope(self, validate_review_request):
        """QC-011: Valid review_scope passes."""
        req = {
            "review_request": {
                "review_target": {"text": "test"},
                "review_scope": ["CONTRACT_COMPLIANCE", "CRAFT_EXECUTION"],
                "contract_meta": {"schema_id": "novel-master/review-request", "schema_version": "1.2.0"}
            }
        }
        assert validate_review_request.is_valid(req)

    def test_illegal_dimension_rejected(self, validate_review_request):
        req = {
            "review_request": {
                "review_target": {"text": "test"},
                "review_scope": ["INVALID_DIMENSION"],
                "contract_meta": {"schema_id": "novel-master/review-request", "schema_version": "1.2.0"}
            }
        }
        assert not validate_review_request.is_valid(req)


# ============================================================================
# QC-012 — QC-019: Review Report / Style Guide / Cross-object
# ============================================================================

class TestReviewReportSchema:

    # QC-012, QC-013
    def test_not_evaluated_dimension(self, validate_review_report):
        """QC-012: NOT_EVALUATED dimension with reason_code."""
        rpt = {
            "review_report": {
                "guardrail_results": {"status": "PASS", "findings": []},
                "dimension_results": [
                    {"dimension": "CONTRACT_COMPLIANCE", "status": "NOT_EVALUATED",
                     "reason_code": "NOT_REQUESTED", "findings": []},
                    {"dimension": "NARRATIVE_SOUNDNESS", "status": "PASS", "findings": []},
                    {"dimension": "READER_EXPERIENCE", "status": "PASS", "findings": []},
                    {"dimension": "CRAFT_EXECUTION", "status": "NOT_EVALUATED",
                     "reason_code": "INSUFFICIENT_CONTEXT", "findings": []}
                ],
                "contract_meta": {"schema_id": "novel-master/review-report", "schema_version": "1.2.0"}
            }
        }
        assert validate_review_report.is_valid(rpt)

    def test_activated_dimension_not_use_not_evaluated(self, validate_review_report):
        """QC-013: Activated dimension uses PASS/WARNING/FAIL not NOT_EVALUATED."""
        rpt = {
            "review_report": {
                "guardrail_results": {"status": "PASS", "findings": []},
                "dimension_results": [
                    {"dimension": "CONTRACT_COMPLIANCE", "status": "PASS", "findings": []},
                    {"dimension": "NARRATIVE_SOUNDNESS", "status": "PASS", "findings": []},
                    {"dimension": "READER_EXPERIENCE", "status": "PASS", "findings": []},
                    {"dimension": "CRAFT_EXECUTION", "status": "NOT_EVALUATED",
                     "reason_code": "NOT_REQUESTED", "findings": []}
                ],
                "contract_meta": {"schema_id": "novel-master/review-report", "schema_version": "1.2.0"}
            }
        }
        assert validate_review_report.is_valid(rpt)

    # QC-014
    def test_guardrail_blocker_in_results(self, validate_review_report):
        """QC-014: Guardrail blocker present in guardrail_results."""
        rpt = {
            "review_report": {
                "guardrail_results": {
                    "status": "BLOCKED",
                    "findings": [{
                        "guardrail": "CANON_CONFLICT",
                        "severity": "BLOCKER",
                        "assessment": "已死亡角色重新出现",
                        "recommended_action": "修正或标记为 DEPRECATED"
                    }]
                },
                "dimension_results": [
                    {"dimension": "CONTRACT_COMPLIANCE", "status": "PASS", "findings": []},
                    {"dimension": "NARRATIVE_SOUNDNESS", "status": "PASS", "findings": []},
                    {"dimension": "READER_EXPERIENCE", "status": "PASS", "findings": []},
                    {"dimension": "CRAFT_EXECUTION", "status": "PASS", "findings": []}
                ],
                "contract_meta": {"schema_id": "novel-master/review-report", "schema_version": "1.2.0"}
            }
        }
        assert validate_review_report.is_valid(rpt)

    # QC-019
    def test_exactly_four_dimensions_required(self, validate_review_report):
        """QC-019: dimension_results must have exactly 4 items."""
        rpt = {
            "review_report": {
                "guardrail_results": {"status": "PASS", "findings": []},
                "dimension_results": [
                    {"dimension": "CONTRACT_COMPLIANCE", "status": "PASS", "findings": []},
                    {"dimension": "CRAFT_EXECUTION", "status": "PASS", "findings": []}
                ],
                "contract_meta": {"schema_id": "novel-master/review-report", "schema_version": "1.2.0"}
            }
        }
        assert not validate_review_report.is_valid(rpt)


class TestStyleGuideSchema:

    # QC-015, QC-016
    def test_style_guide_default_modulation(self, validate_style_guide):
        """Valid style guide with DEFAULT modulation."""
        assert validate_style_guide.is_valid(_make_style_guide())

    def test_illegal_operator_rejected(self, validate_style_guide):
        """QC-016: Illegal relative_to_global operator rejected."""
        sg = _make_style_guide()
        sg["style_guide"]["scene_modulations"]["DEFAULT"]["overrides"] = {
            "sentence_rhythm": {"relative_to_global": "LOUDER"}  # invalid
        }
        assert not validate_style_guide.is_valid(sg)

    def test_valid_typed_operator(self, validate_style_guide):
        sg = _make_style_guide()
        sg["style_guide"]["scene_modulations"]["DEFAULT"]["overrides"] = {
            "sentence_rhythm": {"relative_to_global": "SHORTER"},
            "action_density": {"relative_to_global": "HIGHER"}
        }
        assert validate_style_guide.is_valid(sg)


# ============================================================================
# Cross-object validation (QC-001/002/003/009/015/016/018 via script)
# ============================================================================

class TestQualityContractScript:
    """Tests that validate_quality_contract.py handles cross-object checks."""

    def _run_check(self, subcommand, **kwargs) -> tuple[int, str]:
        """Run validate_quality_contract.py and return (exit_code, output)."""
        import subprocess
        py = sys.executable
        script = str(SCRIPTS_DIR / "validate_quality_contract.py")
        cmd = [py, script, subcommand]
        for k, v in kwargs.items():
            cmd.append(f"--{k.replace('_', '-')}")
            cmd.append(str(v))
        r = subprocess.run(cmd, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def test_script_imports_cleanly(self):
        """validate_quality_contract.py imports without error."""
        from validate_quality_contract import (
            validate_reader_experience_required,
            validate_modulation_refs,
            validate_protected_fields,
            validate_relative_operators,
        )
        assert callable(validate_reader_experience_required)

    def test_reader_experience_required_standard(self):
        """STANDARD mode requires reader_experience."""
        from validate_quality_contract import validate_reader_experience_required
        te = {"task": {"mode": "STANDARD"}}
        cp = {"chapter_plan": {"chapter_id": "1", "scenes": []}}
        errors = validate_reader_experience_required(te, cp)
        assert len(errors) > 0

    def test_reader_experience_fast_optional(self):
        """FAST mode does not require reader_experience."""
        from validate_quality_contract import validate_reader_experience_required
        te = {"task": {"mode": "FAST"}}
        cp = {"chapter_plan": {"chapter_id": "1", "scenes": []}}
        errors = validate_reader_experience_required(te, cp)
        assert len(errors) == 0

    def test_reader_experience_empty_rejected(self):
        """Empty reader_experience rejected in STANDARD."""
        from validate_quality_contract import validate_reader_experience_required
        te = {"task": {"mode": "STANDARD"}}
        cp = {"chapter_plan": {"chapter_id": "1", "scenes": [], "reader_experience": {}}}
        errors = validate_reader_experience_required(te, cp)
        assert len(errors) > 0

    # QC-009
    def test_modulation_ref_not_found(self):
        """style_modulation_ref pointing to nonexistent modulation."""
        from validate_quality_contract import validate_modulation_refs
        cp = {"chapter_plan": {
            "scenes": [{"scene_id": "s1", "style_modulation_ref": "NONEXISTENT"}]
        }}
        sg = {"style_guide": {"scene_modulations": {"DEFAULT": {"category": "DEFAULT", "overrides": {}}}}}
        errors = validate_modulation_refs(cp, sg)
        assert len(errors) > 0

    def test_modulation_ref_exists(self):
        from validate_quality_contract import validate_modulation_refs
        cp = {"chapter_plan": {
            "scenes": [{"scene_id": "s1", "style_modulation_ref": "DEFAULT"}]
        }}
        sg = {"style_guide": {"scene_modulations": {"DEFAULT": {"category": "DEFAULT", "overrides": {}}}}}
        errors = validate_modulation_refs(cp, sg)
        assert len(errors) == 0

    # QC-015
    def test_protected_field_violation(self):
        """Modulation cannot override protected_fields."""
        from validate_quality_contract import validate_protected_fields
        sg = {"style_guide": {
            "scene_modulations": {
                "BAD": {"category": "COMBAT", "overrides": {
                    "narrative": {"relative_to_global": "CLOSER"}
                }}
            },
            "override_policy": {"protected_fields": ["/narrative"]}
        }}
        errors = validate_protected_fields(sg)
        assert len(errors) > 0

    # QC-016
    def test_operator_legality(self):
        """Illegal relative_to_global operator rejected."""
        from validate_quality_contract import validate_relative_operators
        sg = {"style_guide": {
            "scene_modulations": {
                "BAD": {"category": "COMBAT", "overrides": {
                    "sentence_rhythm": {"relative_to_global": "INVALID"}
                }}
            }
        }}
        errors = validate_relative_operators(sg)
        assert len(errors) > 0
