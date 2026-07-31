"""Tests for webnovel-serial-designer skill structure and preflight."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SKILL_DIR = Path("webnovel-serial-designer")
SCRIPTS = str((SKILL_DIR / "scripts").resolve())


def run_preflight(design_root: Path, *extra: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SKILL_DIR / "scripts" / "preflight.py"),
           "--design-root", str(design_root), "--json"] + list(extra)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def make_valid_package(tmp_path: Path) -> Path:
    """Create a minimal valid StorySynopsisPackage."""
    design_root = tmp_path / "story-design" / "test-story"
    source = design_root / "source"
    source.mkdir(parents=True)

    (source / "synopsis.md").write_text("# 完整故事梗概\n测试内容", encoding="utf-8")

    contract = {
        "schema_version": 1,
        "artifact_type": "story_synopsis_contract",
        "identity": {"design_id": "test-story", "title": "测试", "language": "zh"},
        "source": {"synopsis_ref": "source/synopsis.md", "synopsis_revision": 1},
        "status": {"synopsis_status": "user_confirmed", "handoff_ready": True,
                   "review_status": "passed", "accepted_risks": []},
        "story_core": {"premise": "测试前提", "genre": "悬疑", "tone": ["克制"],
                       "central_question": "测试问题？", "story_promise": "测试承诺"},
        "protagonist": {"name": "主角", "identity": "法医", "external_desire": "找到真相",
                        "internal_need": "接受改变", "starting_belief": "相信证据",
                        "flaw": "逃避情感", "agency": "主动调查",
                        "arc": {"start": "相信", "turning_point": "怀疑",
                                "final_choice": "接受", "end": "放下"}},
        "opposition": {"type": "person_and_system",
                       "primary_opponent": {"identity": "处理中心", "goal": "清除",
                                            "motivation": "控制风险", "logic": "社会安全"}},
        "core_conflict": {"external": "保护vs清除", "internal": "证据vs情感",
                          "stakes": {"personal": "失去姐姐", "thematic": "身份意义"}},
        "world_rules": [{"id": "R1", "statement": "七天后归来", "boundary": "仅接触者",
                         "cost": "情感衰退", "frozen": True}],
        "story_truth": {"hidden_truth": "主角也是归来者", "truth_origin": "实验失控",
                        "protagonist_connection": "他自己就是"},
        "ending": {"external_outcome": "公开真相", "final_choice": "承认身份",
                   "personal_cost": "失去身份", "thematic_answer": "选择定义人",
                   "ending_type": "bittersweet", "frozen": True},
        "major_turning_points": [
            {"id": "T1", "stage": "inciting", "event": "姐姐归来", "state_change": "隐瞒", "frozen": True},
            {"id": "T2", "stage": "midpoint", "event": "发现真相", "state_change": "怀疑", "frozen": True},
            {"id": "T3", "stage": "climax", "event": "公开", "state_change": "接受", "frozen": True},
        ],
        "adaptation_boundaries": {
            "frozen_facts": ["主角是归来者", "姐姐最终死亡"],
            "expandable_zones": ["其他归来者个案"],
            "prohibited_directions": ["不能鬼魂解释"],
            "unresolved_non_blocking": [],
        },
        "quality": {"blocking_issues": [], "non_blocking_risks": []},
    }
    (source / "synopsis-contract.yaml").write_text(
        yaml.dump(contract, allow_unicode=True, default_flow_style=False), encoding="utf-8")
    return design_root


class TestSkillStructure:
    def test_skill_md_exists(self):
        assert (SKILL_DIR / "SKILL.md").exists()

    def test_skill_mentions_input_validation(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        assert "handoff_ready" in content
        assert "story-synopsis" in content

    def test_skill_mentions_two_gates(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        assert "Gate A" in content
        assert "Gate B" in content

    def test_skill_mentions_decision_levels(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        assert "L0" in content
        assert "L3" in content

    def test_skill_mentions_escalation(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        assert "SynopsisRevisionProposal" in content


class TestTemplates:
    def test_serial_contract_valid_yaml(self):
        data = yaml.safe_load((SKILL_DIR / "templates" / "serial-contract.yaml").read_text(encoding="utf-8"))
        assert data["schema_version"] == 1
        assert data["artifact_type"] == "serial_design_contract"

    def test_serial_contract_has_assertions(self):
        data = yaml.safe_load((SKILL_DIR / "templates" / "serial-contract.yaml").read_text(encoding="utf-8"))
        assert "assertions" in data
        assert isinstance(data["assertions"], list)

    def test_serial_contract_has_compilation_policy(self):
        data = yaml.safe_load((SKILL_DIR / "templates" / "serial-contract.yaml").read_text(encoding="utf-8"))
        policy = data["compilation_policy"]
        assert "must_preserve" in policy
        assert "must_not_emit" in policy

    def test_gate_a_valid_yaml(self):
        data = yaml.safe_load((SKILL_DIR / "templates" / "gate-a-architecture.yaml").read_text(encoding="utf-8"))
        assert data["gate"] == "serialization_architecture"
        assert data["status"] == "pending"

    def test_gate_b_valid_yaml(self):
        data = yaml.safe_load((SKILL_DIR / "templates" / "gate-b-freeze.yaml").read_text(encoding="utf-8"))
        assert data["gate"] == "serial_package_freeze"

    def test_readiness_review_valid_yaml(self):
        data = yaml.safe_load((SKILL_DIR / "templates" / "readiness-review.yaml").read_text(encoding="utf-8"))
        assert "checks" in data
        assert "verdict" in data


class TestReferences:
    def test_workflow_exists(self):
        assert (SKILL_DIR / "references" / "serialization-workflow.md").exists()

    def test_engine_design_exists(self):
        assert (SKILL_DIR / "references" / "story-engine-design.md").exists()

    def test_readiness_checklist_exists(self):
        assert (SKILL_DIR / "references" / "readiness-checklist.md").exists()

    def test_workflow_has_11_stages(self):
        content = (SKILL_DIR / "references" / "serialization-workflow.md").read_text(encoding="utf-8")
        assert "阶段 0" in content or "Stage 0" in content or "00-" in content
        assert "Readiness" in content


class TestPreflight:
    def test_valid_package_passes(self, tmp_path):
        design_root = make_valid_package(tmp_path)
        result = run_preflight(design_root)
        data = json.loads(result.stdout)
        assert result.returncode == 0
        assert data["ready"] is True

    def test_missing_contract_fails(self, tmp_path):
        design_root = tmp_path / "story-design" / "test"
        (design_root / "source").mkdir(parents=True)
        (design_root / "source" / "synopsis.md").write_text("# test", encoding="utf-8")
        result = run_preflight(design_root)
        data = json.loads(result.stdout)
        assert result.returncode == 1
        assert data["ready"] is False

    def test_handoff_not_ready_fails(self, tmp_path):
        design_root = make_valid_package(tmp_path)
        # Modify contract to set handoff_ready: false
        contract_path = design_root / "source" / "synopsis-contract.yaml"
        data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        data["status"]["handoff_ready"] = False
        contract_path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        result = run_preflight(design_root)
        out = json.loads(result.stdout)
        assert result.returncode == 1
        assert any("handoff_ready" in e for e in out["errors"])

    def test_blocking_issues_fail(self, tmp_path):
        design_root = make_valid_package(tmp_path)
        contract_path = design_root / "source" / "synopsis-contract.yaml"
        data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        data["quality"]["blocking_issues"] = ["结局未确定"]
        contract_path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        result = run_preflight(design_root)
        out = json.loads(result.stdout)
        assert result.returncode == 1

    def test_missing_protagonist_field_fails(self, tmp_path):
        design_root = make_valid_package(tmp_path)
        contract_path = design_root / "source" / "synopsis-contract.yaml"
        data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        data["protagonist"]["flaw"] = ""
        contract_path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        result = run_preflight(design_root)
        out = json.loads(result.stdout)
        assert result.returncode == 1

    def test_ending_not_frozen_fails(self, tmp_path):
        design_root = make_valid_package(tmp_path)
        contract_path = design_root / "source" / "synopsis-contract.yaml"
        data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        data["ending"]["frozen"] = False
        contract_path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        result = run_preflight(design_root)
        out = json.loads(result.stdout)
        assert result.returncode == 1

    def test_nonexistent_design_root_fails(self, tmp_path):
        result = run_preflight(tmp_path / "nonexistent")
        assert result.returncode == 1
