"""Tests for story-synopsis scripts/emit_package.py (StorySynopsisPackage emission)."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(".")
EMIT_SCRIPT = REPO_ROOT / "story-synopsis" / "scripts" / "emit_package.py"
SERIAL_PREFLIGHT = REPO_ROOT / "webnovel-serial-designer" / "scripts" / "preflight.py"


def run_script(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


def load_emit_module():
    spec = importlib.util.spec_from_file_location("emit_package", EMIT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_contract() -> dict:
    return {
        "schema_version": 1,
        "artifact_type": "story_synopsis_contract",
        "identity": {"design_id": "活着的死者", "title": "活着的死者", "language": "zh"},
        "source": {"synopsis_ref": "source/synopsis.md", "synopsis_revision": 1},
        "status": {"synopsis_status": "user_confirmed", "handoff_ready": True,
                   "review_status": "passed", "accepted_risks": []},
        "story_core": {"premise": "死者七天后归来", "genre": "都市悬疑", "tone": ["克制", "压迫"],
                       "central_question": "归来者是否还是原来的人？", "story_promise": "调查真相"},
        "protagonist": {"name": "林默", "identity": "法医助理", "external_desire": "证明姐姐身份",
                        "internal_need": "接受改变", "starting_belief": "记忆连续即人格连续",
                        "flaw": "用技术逃避情感", "agency": "主动隐瞒并调查",
                        "arc": {"start": "坚信", "turning_point": "发现自己是归来者",
                                "final_choice": "公开身份", "end": "接受"}},
        "opposition": {"type": "person_and_system",
                       "primary_opponent": {"identity": "处理中心负责人", "goal": "清除归来者",
                                            "motivation": "社会安全", "logic": "无法承担失控风险"}},
        "core_conflict": {"external": "保护vs清除", "internal": "证据vs情感",
                          "stakes": {"personal": "姐姐被销毁", "thematic": "身份的意义"}},
        "world_rules": [{"id": "R1", "statement": "七天后归来", "boundary": "仅接触者",
                         "cost": "情感衰退", "frozen": True}],
        "story_truth": {"hidden_truth": "主角也是归来者", "truth_origin": "实验失控",
                        "protagonist_connection": "幼年死亡被重构"},
        "ending": {"external_outcome": "公开真相", "final_choice": "承认身份",
                   "personal_cost": "失去原有身份", "thematic_answer": "选择定义人",
                   "ending_type": "bittersweet", "frozen": True},
        "major_turning_points": [
            {"id": "T1", "stage": "inciting", "event": "姐姐归来", "state_change": "隐瞒", "frozen": True},
            {"id": "T2", "stage": "midpoint", "event": "发现非复活", "state_change": "怀疑", "frozen": True},
            {"id": "T3", "stage": "climax", "event": "公开身份", "state_change": "接受", "frozen": True},
        ],
        "adaptation_boundaries": {
            "frozen_facts": ["主角是归来者", "姐姐最终死亡", "归来不是复活"],
            "expandable_zones": ["其他归来者个案", "处理中心内部派系"],
            "prohibited_directions": ["不能鬼魂解释", "不能时间旅行撤销"],
            "unresolved_non_blocking": ["主角新身份名称"],
        },
        "quality": {"blocking_issues": [], "non_blocking_risks": ["中段可能重复"]},
    }


def write_inputs(tmp_path: Path, contract: dict) -> tuple[Path, Path]:
    contract_path = tmp_path / "contract.yaml"
    synopsis_path = tmp_path / "synopsis.md"
    contract_path.write_text(yaml.safe_dump(contract, allow_unicode=True), encoding="utf-8")
    synopsis_path.write_text(
        "# 活着的死者\n\n" + "完整故事梗概，包含因果、真相、反转与结局。" * 30,
        encoding="utf-8",
    )
    return contract_path, synopsis_path


class TestDeriveDesignId:
    def test_chinese_title_kept(self):
        module = load_emit_module()
        assert module.derive_design_id("活着的死者") == "活着的死者"

    def test_windows_illegal_chars_removed(self):
        module = load_emit_module()
        assert module.derive_design_id("A/B: C?") == "AB C"

    def test_trailing_dot_space_stripped(self):
        module = load_emit_module()
        assert module.derive_design_id("我的书. ") == "我的书"

    def test_empty_falls_back(self):
        module = load_emit_module()
        assert module.derive_design_id("...") == "untitled-story"


class TestEmitBuild:
    def test_build_writes_package_consumable_by_downstream(self, tmp_path):
        contract_path, synopsis_path = write_inputs(tmp_path, make_contract())
        design_root = tmp_path / "story-design" / "活着的死者"

        result = run_script(
            EMIT_SCRIPT, "build",
            "--design-root", str(design_root),
            "--synopsis", str(synopsis_path),
            "--contract", str(contract_path),
            "--json",
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["ready"] is True

        assert (design_root / "source" / "synopsis.md").exists()
        assert (design_root / "source" / "synopsis-contract.yaml").exists()

        pre = run_script(SERIAL_PREFLIGHT, "--design-root", str(design_root), "--json")
        assert pre.returncode == 0, pre.stdout
        assert json.loads(pre.stdout)["ready"] is True

    def test_check_passes_on_emitted_package(self, tmp_path):
        contract_path, synopsis_path = write_inputs(tmp_path, make_contract())
        design_root = tmp_path / "story-design" / "活着的死者"
        run_script(
            EMIT_SCRIPT, "build",
            "--design-root", str(design_root),
            "--synopsis", str(synopsis_path),
            "--contract", str(contract_path),
        )
        check = run_script(EMIT_SCRIPT, "check", "--design-root", str(design_root))
        assert check.returncode == 0, check.stderr

    def test_build_rejects_short_synopsis(self, tmp_path):
        contract_path, synopsis_path = write_inputs(tmp_path, make_contract())
        synopsis_path.write_text("太短。", encoding="utf-8")
        result = run_script(
            EMIT_SCRIPT, "build",
            "--design-root", str(tmp_path / "story-design" / "活着的死者"),
            "--synopsis", str(synopsis_path),
            "--contract", str(contract_path),
        )
        assert result.returncode == 2

    def test_build_rejects_unconfirmed_status(self, tmp_path):
        contract = make_contract()
        contract["status"]["handoff_ready"] = False
        contract_path, synopsis_path = write_inputs(tmp_path, contract)
        result = run_script(
            EMIT_SCRIPT, "build",
            "--design-root", str(tmp_path / "story-design" / "活着的死者"),
            "--synopsis", str(synopsis_path),
            "--contract", str(contract_path),
        )
        assert result.returncode == 2
        assert "handoff_ready" in result.stderr

    def test_build_rejects_too_few_turning_points(self, tmp_path):
        contract = make_contract()
        contract["major_turning_points"] = contract["major_turning_points"][:2]
        contract_path, synopsis_path = write_inputs(tmp_path, contract)
        result = run_script(
            EMIT_SCRIPT, "build",
            "--design-root", str(tmp_path / "story-design" / "活着的死者"),
            "--synopsis", str(synopsis_path),
            "--contract", str(contract_path),
        )
        assert result.returncode == 2
        assert "major_turning_points" in result.stderr

    def test_check_rejects_design_id_mismatch(self, tmp_path):
        contract = make_contract()
        contract["identity"]["design_id"] = "另一个故事"
        contract_path, synopsis_path = write_inputs(tmp_path, contract)
        design_root = tmp_path / "story-design" / "活着的死者"
        result = run_script(
            EMIT_SCRIPT, "build",
            "--design-root", str(design_root),
            "--synopsis", str(synopsis_path),
            "--contract", str(contract_path),
        )
        assert result.returncode == 2
        assert "design_id" in result.stderr

    def test_check_rejects_blocking_issue(self, tmp_path):
        contract_path, synopsis_path = write_inputs(tmp_path, make_contract())
        design_root = tmp_path / "story-design" / "活着的死者"
        run_script(
            EMIT_SCRIPT, "build",
            "--design-root", str(design_root),
            "--synopsis", str(synopsis_path),
            "--contract", str(contract_path),
        )
        contract_path_out = design_root / "source" / "synopsis-contract.yaml"
        data = yaml.safe_load(contract_path_out.read_text(encoding="utf-8"))
        data["quality"]["blocking_issues"] = ["核心冲突无法成立"]
        contract_path_out.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
        check = run_script(EMIT_SCRIPT, "check", "--design-root", str(design_root))
        assert check.returncode == 2
        assert "blocking_issues" in check.stderr
