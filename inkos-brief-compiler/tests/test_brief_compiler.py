"""Tests for inkos-brief-compiler skill structure and preflight."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SKILL_DIR = Path("inkos-brief-compiler")


def run_preflight(design_root: Path) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SKILL_DIR / "scripts" / "preflight.py"),
           "--design-root", str(design_root), "--json"]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def make_frozen_package(tmp_path: Path) -> Path:
    """Create a minimal frozen SerialDesignPackage."""
    design_root = tmp_path / "story-design" / "test-story"
    serial_dir = design_root / "serial"
    serial_dir.mkdir(parents=True)
    (serial_dir / "design").mkdir()
    (serial_dir / "reviews").mkdir()

    # Source package
    source_dir = design_root / "source"
    source_dir.mkdir()
    (source_dir / "synopsis.md").write_text("# test", encoding="utf-8")
    (source_dir / "synopsis-contract.yaml").write_text("schema_version: 1", encoding="utf-8")

    # Serial contract
    contract = {
        "schema_version": 1,
        "artifact_type": "serial_design_contract",
        "identity": {"design_id": "test-story", "title": "测试", "revision": 3},
        "source": {"synopsis_contract_ref": "../source/synopsis-contract.yaml", "synopsis_revision": 1},
        "status": {"serial_design_status": "frozen", "handoff_ready": True,
                   "readiness_verdict": "pass", "accepted_risks": []},
        "serialization_target": {"form": "long_webnovel", "platform": "tomato",
                                 "genre": "悬疑", "target_chapters": 300, "chapter_words": 2500},
        "story_engine": {"engine_id": "E1", "loop": ["a", "b", "c", "d"],
                         "variable_inputs": ["x", "y", "z"], "cumulative_state": ["s1", "s2"],
                         "escalation_axes": ["e1", "e2"], "anti_repetition_rules": ["r1", "r2"]},
        "volumes": [
            {"id": "V1", "title": "卷一", "chapter_range": [1, 50], "external_goal": "g",
             "primary_opposition": "o", "major_reveal": "r", "climax": "c",
             "irreversible_state_changes": ["change1"], "ending_hook": "hook"},
            {"id": "V2", "title": "卷二", "chapter_range": [51, 120], "external_goal": "g2",
             "primary_opposition": "o2", "major_reveal": "r2", "climax": "c2",
             "irreversible_state_changes": ["change2"], "ending_hook": "hook2"},
        ],
        "endgame_convergence": {"required_upstream_ending_ref": "SYN-END-001",
                                "convergence_conditions": ["c1", "c2"],
                                "forbidden_endgame_changes": ["f1"]},
        "launch_plan": {"first_three_chapters": [
            {"chapter": 1, "required_event": "e1", "chapter_end_hook": "h1"},
            {"chapter": 2, "required_event": "e2", "chapter_end_hook": "h2"},
            {"chapter": 3, "required_event": "e3", "chapter_end_hook": "h3"},
        ]},
        "assertions": [
            {"id": "A1", "type": "story_engine", "statement": "test",
             "status": "confirmed", "importance": "critical", "source_ref": "design/02.md"},
            {"id": "A2", "type": "payoff_cadence", "statement": "test2",
             "status": "confirmed", "importance": "major", "source_ref": "design/06.md"},
        ],
        "compilation_policy": {
            "must_preserve": ["engine", "volumes"],
            "may_summarize": ["examples"],
            "may_omit": ["rationale"],
            "must_not_emit": ["rejected"],
            "block_if_missing": ["story_engine", "volume_architecture"],
        },
    }
    (serial_dir / "serial-contract.yaml").write_text(
        yaml.dump(contract, allow_unicode=True, default_flow_style=False), encoding="utf-8")

    # Gate files
    gate_a = {"gate": "serialization_architecture", "status": "approved", "serial_revision": 3}
    gate_b = {"gate": "serial_package_freeze", "status": "approved", "serial_revision": 3}
    (serial_dir / "reviews" / "gate-a-architecture.yaml").write_text(
        yaml.dump(gate_a), encoding="utf-8")
    (serial_dir / "reviews" / "gate-b-freeze.yaml").write_text(
        yaml.dump(gate_b), encoding="utf-8")

    return design_root


class TestSkillStructure:
    def test_skill_md_exists(self):
        assert (SKILL_DIR / "SKILL.md").exists()

    def test_skill_mentions_bounded_compiler(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        assert "受约束的语义编译器" in content

    def test_skill_mentions_forbidden_behaviors(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        assert "不创造" in content or "不拥有创意决策权" in content

    def test_skill_mentions_eperm(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        assert "EPERM" in content
        assert "staging" in content


class TestCompilationPolicy:
    def test_policy_valid_yaml(self):
        data = yaml.safe_load(
            (SKILL_DIR / "references" / "inkos-compilation-policy.yaml").read_text(encoding="utf-8"))
        assert data["schema_version"] == 1
        assert "profiles" in data

    def test_policy_has_all_types(self):
        data = yaml.safe_load(
            (SKILL_DIR / "references" / "inkos-compilation-policy.yaml").read_text(encoding="utf-8"))
        profiles = data["profiles"]
        expected_types = ["story_engine", "volume_architecture", "character_arc",
                          "foreshadowing", "world_pressure", "payoff_cadence",
                          "serial_promise", "launch_plan", "endgame_convergence",
                          "information_reveal", "anti_repetition",
                          "illustrative_example", "design_rationale", "rejected_direction"]
        for t in expected_types:
            assert t in profiles, f"Missing profile: {t}"

    def test_rejected_direction_prohibited(self):
        data = yaml.safe_load(
            (SKILL_DIR / "references" / "inkos-compilation-policy.yaml").read_text(encoding="utf-8"))
        assert data["profiles"]["rejected_direction"]["requirement"] == "prohibited"

    def test_story_engine_must_preserve(self):
        data = yaml.safe_load(
            (SKILL_DIR / "references" / "inkos-compilation-policy.yaml").read_text(encoding="utf-8"))
        assert data["profiles"]["story_engine"]["requirement"] == "must_preserve"
        assert data["profiles"]["story_engine"]["omission"] == "forbidden"


class TestTemplates:
    def test_mapping_plan_valid(self):
        data = yaml.safe_load(
            (SKILL_DIR / "templates" / "mapping-plan.yaml").read_text(encoding="utf-8"))
        assert data["schema_version"] == 1
        assert "mappings" in data

    def test_compilation_report_valid(self):
        data = yaml.safe_load(
            (SKILL_DIR / "templates" / "compilation-report.yaml").read_text(encoding="utf-8"))
        assert data["schema_version"] == 1
        assert "summary" in data
        assert "verdict" in data


class TestPreflight:
    def test_frozen_package_passes(self, tmp_path):
        design_root = make_frozen_package(tmp_path)
        result = run_preflight(design_root)
        data = json.loads(result.stdout)
        assert result.returncode == 0
        assert data["ready"] is True

    def test_not_frozen_fails(self, tmp_path):
        design_root = make_frozen_package(tmp_path)
        contract_path = design_root / "serial" / "serial-contract.yaml"
        data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        data["status"]["serial_design_status"] = "draft"
        contract_path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        result = run_preflight(design_root)
        out = json.loads(result.stdout)
        assert result.returncode == 1
        assert any("frozen" in e for e in out["errors"])

    def test_critical_unconfirmed_fails(self, tmp_path):
        design_root = make_frozen_package(tmp_path)
        contract_path = design_root / "serial" / "serial-contract.yaml"
        data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        data["assertions"][0]["status"] = "provisional"
        contract_path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        result = run_preflight(design_root)
        out = json.loads(result.stdout)
        assert result.returncode == 1

    def test_missing_engine_fails(self, tmp_path):
        design_root = make_frozen_package(tmp_path)
        contract_path = design_root / "serial" / "serial-contract.yaml"
        data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        data["story_engine"]["loop"] = []
        contract_path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        result = run_preflight(design_root)
        out = json.loads(result.stdout)
        assert result.returncode == 1

    def test_gate_not_approved_fails(self, tmp_path):
        design_root = make_frozen_package(tmp_path)
        gate_a_path = design_root / "serial" / "reviews" / "gate-a-architecture.yaml"
        gate_a = {"gate": "serialization_architecture", "status": "pending"}
        gate_a_path.write_text(yaml.dump(gate_a), encoding="utf-8")
        result = run_preflight(design_root)
        out = json.loads(result.stdout)
        assert result.returncode == 1

    def test_nonexistent_root_fails(self, tmp_path):
        result = run_preflight(tmp_path / "nonexistent")
        assert result.returncode == 1
