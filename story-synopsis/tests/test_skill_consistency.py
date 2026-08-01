"""Consistency and quality regression tests for the story-synopsis package."""
import json
from pathlib import Path

import yaml

REPO_ROOT = Path(".")
SKILL_PATH = REPO_ROOT / "story-synopsis" / "SKILL.md"
DESIGN_PATH = REPO_ROOT / "story-synopsis" / "docs" / "design.md"
EVALS_PATH = REPO_ROOT / "story-synopsis" / "evals" / "evals.json"
TRIGGER_CASES_PATH = REPO_ROOT / "story-synopsis" / "evals" / "trigger_cases.json"
SEMANTIC_CONFIG_PATH = REPO_ROOT / "story-synopsis" / "evals" / "semantic_config.json"
INTERFACE_PATH = REPO_ROOT / "story-synopsis" / "agents" / "interface.yaml"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestSkillDesignConsistency:
    """SKILL.md is the operative entrypoint; design.md must not contradict it."""

    def test_one_question_rule_identical(self):
        skill = read_text(SKILL_PATH)
        design = read_text(DESIGN_PATH)
        rule = "绝不在同一轮中提出多个问题"
        assert rule in skill
        assert rule in design
        assert "最多提出三个" not in design

    def test_core_output_numbers_match(self):
        skill = read_text(SKILL_PATH)
        design = read_text(DESIGN_PATH)
        for marker in ("3000～5000", "最多三个"):
            assert marker in skill
            assert marker in design

    def test_design_doc_defers_to_skill_md(self):
        design = read_text(DESIGN_PATH)
        assert "运行期以 `SKILL.md` 为准" in design


class TestEvalCoverage:
    def test_evals_cover_all_levels(self):
        data = json.loads(read_text(EVALS_PATH))
        levels = {entry.get("level") for entry in data["evals"]}
        for level in ("L0", "L1", "L2", "L3", "L4", "exclusion"):
            assert level in levels, f"missing eval level {level}"
        assert len(data["evals"]) >= 8

    def test_trigger_cases_balanced(self):
        data = json.loads(read_text(TRIGGER_CASES_PATH))
        assert len(data["should_trigger"]) >= 5
        assert len(data["should_not_trigger"]) >= 5
        assert len(data["near_neighbor"]) >= 3
        assert isinstance(data["recommended_threshold"], (int, float))

    def test_semantic_config_covers_trigger_families(self):
        cases = json.loads(read_text(TRIGGER_CASES_PATH))
        config = json.loads(read_text(SEMANTIC_CONFIG_PATH))
        concept_names = set(config["positive_concepts"]) | set(config["negative_concepts"])
        sibling_labels = {
            "webnovel_serial_designer",
            "inkos_story_steward",
            "inkos_brief_compiler",
            "novel_coach",
            "novel_master",
        }
        for bucket in ("should_trigger", "should_not_trigger", "near_neighbor"):
            for item in cases[bucket]:
                family = item.get("family")
                assert family in concept_names or family in sibling_labels, (
                    f"family {family} has no concept or sibling label"
                )


class TestInterfaceYaml:
    def test_interface_yaml_exists_and_valid(self):
        assert INTERFACE_PATH.exists()
        data = yaml.safe_load(read_text(INTERFACE_PATH))
        iface = data["interface"]
        assert iface["display_name"]
        assert iface["short_description"]
        assert iface["default_prompt"]
        compat = data["compatibility"]
        assert compat["activation"]["mode"] == "implicit"
        assert "claude" in compat["adapter_targets"]
        assert compat["trust"]["source_tier"] == "local"
        assert data.get("owner")
        assert data.get("review_cadence")


class TestSkillMdReferencesEvals:
    def test_skill_md_references_evals_and_interface(self):
        skill = read_text(SKILL_PATH)
        assert "evals/" in skill
        assert "trigger_eval" in skill
        assert "agents/interface.yaml" in skill


class TestFlowOnlySkillMd:
    """SKILL.md must stay a flow entrypoint, with method detail in references/."""

    def test_skill_md_stays_under_300_lines(self):
        lines = read_text(SKILL_PATH).splitlines()
        assert len(lines) < 300, (
            f"SKILL.md is {len(lines)} lines; keep SKILL.md flow-only"
        )

    def test_skill_md_references_all_method_references(self):
        skill = read_text(SKILL_PATH)
        for ref in (
            "maturity-levels.md",
            "synopsis-output-structure.md",
            "review-standards.md",
            "interaction-guide.md",
            "handoff-contract.md",
        ):
            assert ref in skill, f"SKILL.md must reference {ref}"
        assert "scripts/emit_package.py" in skill

    def test_method_detail_moved_out_of_entrypoint(self):
        skill = read_text(SKILL_PATH)
        assert "典型首次响应" not in skill
        assert "反模式一" not in skill
        assert "情绪兑现" not in skill

    def test_references_retain_moved_content(self):
        guide = read_text(REPO_ROOT / "story-synopsis" / "references" / "interaction-guide.md")
        assert "典型首次响应" in guide
        assert "反模式" in guide
        review = read_text(REPO_ROOT / "story-synopsis" / "references" / "review-standards.md")
        assert "情绪兑现" in review
        structure = read_text(
            REPO_ROOT / "story-synopsis" / "references" / "synopsis-output-structure.md"
        )
        assert "中点转折" in structure
        maturity = read_text(REPO_ROOT / "story-synopsis" / "references" / "maturity-levels.md")
        assert "L4" in maturity
