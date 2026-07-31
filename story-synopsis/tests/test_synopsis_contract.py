"""Tests for story-synopsis StorySynopsisPackage contract template and rules."""
import sys
from pathlib import Path

import pytest
import yaml

TEMPLATE_PATH = Path("story-synopsis/templates/synopsis-contract.yaml")
REFERENCE_PATH = Path("story-synopsis/references/handoff-contract.md")
SKILL_PATH = Path("story-synopsis/SKILL.md")


@pytest.fixture
def template_content():
    return TEMPLATE_PATH.read_text(encoding="utf-8")


@pytest.fixture
def template_data(template_content):
    return yaml.safe_load(template_content)


class TestTemplateExists:
    def test_template_file_exists(self):
        assert TEMPLATE_PATH.exists(), "synopsis-contract.yaml template must exist"

    def test_reference_file_exists(self):
        assert REFERENCE_PATH.exists(), "handoff-contract.md reference must exist"

    def test_template_is_valid_yaml(self, template_data):
        assert isinstance(template_data, dict)

    def test_schema_version(self, template_data):
        assert template_data["schema_version"] == 1

    def test_artifact_type(self, template_data):
        assert template_data["artifact_type"] == "story_synopsis_contract"


class TestRequiredSections:
    def test_identity_section(self, template_data):
        identity = template_data["identity"]
        assert "design_id" in identity
        assert "title" in identity
        assert "language" in identity

    def test_source_section(self, template_data):
        source = template_data["source"]
        assert "synopsis_ref" in source
        assert "synopsis_revision" in source

    def test_status_section(self, template_data):
        status = template_data["status"]
        assert "synopsis_status" in status
        assert "handoff_ready" in status
        assert "review_status" in status
        assert "blocking_issues" not in status  # blocking_issues is in quality

    def test_story_core_section(self, template_data):
        core = template_data["story_core"]
        required = ["premise", "genre", "tone", "central_question", "story_promise"]
        for field in required:
            assert field in core, f"story_core.{field} required"

    def test_protagonist_section(self, template_data):
        protag = template_data["protagonist"]
        required = ["name", "identity", "external_desire", "internal_need",
                    "starting_belief", "flaw", "agency", "arc"]
        for field in required:
            assert field in protag, f"protagonist.{field} required"

    def test_protagonist_arc_fields(self, template_data):
        arc = template_data["protagonist"]["arc"]
        required = ["start", "turning_point", "final_choice", "end"]
        for field in required:
            assert field in arc, f"protagonist.arc.{field} required"

    def test_opposition_section(self, template_data):
        opp = template_data["opposition"]
        assert "type" in opp
        assert "primary_opponent" in opp
        opponent = opp["primary_opponent"]
        required = ["identity", "goal", "motivation", "logic"]
        for field in required:
            assert field in opponent, f"opposition.primary_opponent.{field} required"

    def test_core_conflict_section(self, template_data):
        conflict = template_data["core_conflict"]
        required = ["external", "internal", "stakes"]
        for field in required:
            assert field in conflict, f"core_conflict.{field} required"

    def test_world_rules_section(self, template_data):
        rules = template_data["world_rules"]
        assert isinstance(rules, list)
        assert len(rules) >= 1
        rule = rules[0]
        required = ["id", "statement", "boundary", "cost", "frozen"]
        for field in required:
            assert field in rule, f"world_rules[0].{field} required"

    def test_story_truth_section(self, template_data):
        truth = template_data["story_truth"]
        required = ["hidden_truth", "truth_origin", "protagonist_connection"]
        for field in required:
            assert field in truth, f"story_truth.{field} required"

    def test_ending_section(self, template_data):
        ending = template_data["ending"]
        required = ["external_outcome", "final_choice", "personal_cost",
                    "thematic_answer", "ending_type", "frozen"]
        for field in required:
            assert field in ending, f"ending.{field} required"
        assert ending["frozen"] is True

    def test_turning_points_section(self, template_data):
        turns = template_data["major_turning_points"]
        assert isinstance(turns, list)
        assert len(turns) >= 3, "At least 3 turning points required"
        for turn in turns:
            assert "id" in turn
            assert "stage" in turn
            assert "event" in turn
            assert "state_change" in turn
            assert "frozen" in turn

    def test_adaptation_boundaries_section(self, template_data):
        bounds = template_data["adaptation_boundaries"]
        required = ["frozen_facts", "expandable_zones", "prohibited_directions"]
        for field in required:
            assert field in bounds, f"adaptation_boundaries.{field} required"
            assert isinstance(bounds[field], list)
            assert len(bounds[field]) >= 1, f"adaptation_boundaries.{field} must have ≥1 item"

    def test_quality_section(self, template_data):
        quality = template_data["quality"]
        assert "blocking_issues" in quality
        assert isinstance(quality["blocking_issues"], list)


class TestHandoffSemantics:
    def test_handoff_ready_is_boolean(self, template_data):
        assert isinstance(template_data["status"]["handoff_ready"], bool)

    def test_synopsis_status_valid_values(self, template_data):
        # Template shows user_confirmed as the handoff state
        assert template_data["status"]["synopsis_status"] == "user_confirmed"

    def test_ending_frozen_true(self, template_data):
        assert template_data["ending"]["frozen"] is True


class TestSkillMdIntegration:
    def test_skill_mentions_package(self):
        content = SKILL_PATH.read_text(encoding="utf-8")
        assert "StorySynopsisPackage" in content
        assert "synopsis-contract.yaml" in content
        assert "handoff_ready" in content

    def test_skill_mentions_design_id(self):
        content = SKILL_PATH.read_text(encoding="utf-8")
        assert "design-id" in content

    def test_skill_mentions_downstream(self):
        content = SKILL_PATH.read_text(encoding="utf-8")
        assert "webnovel-serial-designer" in content


class TestReferenceContent:
    def test_reference_defines_trigger(self):
        content = REFERENCE_PATH.read_text(encoding="utf-8")
        assert "生成触发条件" in content
        assert "用户明确表示定稿意图" in content

    def test_reference_defines_extraction_rules(self):
        content = REFERENCE_PATH.read_text(encoding="utf-8")
        assert "已确认事实" in content
        assert "暂定事实" in content

    def test_reference_defines_revision_rules(self):
        content = REFERENCE_PATH.read_text(encoding="utf-8")
        assert "revision" in content

    def test_reference_defines_prohibited(self):
        content = REFERENCE_PATH.read_text(encoding="utf-8")
        assert "prohibited_directions" in content
