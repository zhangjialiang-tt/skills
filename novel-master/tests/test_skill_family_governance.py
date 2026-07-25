import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHILDREN = (
    "novel-brief",
    "story-architect",
    "chapter-planner",
    "chapter-writer",
    "novel-reviewer",
    "continuity-keeper",
)
FROZEN_HASHES = {
    "docs/novel-master-architecture-v1.0.1-frozen.md": "8b276013c5c7e1f9d07de92f0eb86e345e2a29029e8ae546aa6e456b0ee35d16",
    "docs/novel-master-contracts-v1.0.1-frozen.md": "27571f0e48b6457ee93dbfb2d0b94aade514642ef00331b09e76976ba9dc3cce",
}
GOVERNED_LABELS = {
    "input_files",
    "output contract",
    "rollback boundary",
    "trust report",
    "reports/output_quality_scorecard.md",
    "missing evidence",
}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_manifest_declares_production_candidate_and_two_targets():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["version"] == "1.1.0"
    assert manifest["owner"] == "zhangjl"
    assert manifest["maturity_tier"] == "production"
    assert manifest["lifecycle_stage"] == "production"
    assert manifest["review_cadence"] == "per-release"
    assert manifest["target_platforms"] == ["openai", "generic"]


def test_root_is_implicit_and_children_are_manual():
    root_interface = load_yaml(ROOT / "agents" / "interface.yaml")
    assert root_interface["compatibility"]["activation"]["mode"] == "implicit"

    for child in CHILDREN:
        interface = load_yaml(ROOT / child / "agents" / "interface.yaml")
        assert interface["compatibility"]["activation"]["mode"] == "manual"
        assert interface["compatibility"]["adapter_targets"] == ["openai", "generic"]
        assert interface["compatibility"]["trust"]["remote_inline_execution"] == "forbid"


def test_openai_implicit_policy_matches_family_boundary():
    root_openai = load_yaml(ROOT / "agents" / "openai.yaml")
    assert root_openai["policy"]["allow_implicit_invocation"] is True

    for child in CHILDREN:
        openai = load_yaml(ROOT / child / "agents" / "openai.yaml")
        assert openai["policy"]["allow_implicit_invocation"] is False


def test_child_trigger_descriptions_require_explicit_invocation():
    for child in CHILDREN:
        skill = (ROOT / child / "SKILL.md").read_text(encoding="utf-8")
        assert f"${child}" in skill
        assert "$novel-master" in skill
        assert "显式调用" in skill


def test_output_eval_cases_are_file_backed_and_disclose_missing_evidence():
    cases = [
        json.loads(line)
        for line in (ROOT / "evals" / "output" / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(cases) >= 6
    for case in cases:
        assert case["input_files"]
        assert case["metadata"]["case_type"] == "file-backed fixture"
        for relative_path in case["input_files"]:
            assert (ROOT / "evals" / "output" / relative_path).is_file()
        assert GOVERNED_LABELS.issubset(set().union(*(set(check.get("required", [])) for check in case["assertions"])))


def test_frozen_documents_keep_stage_4_baseline_hashes():
    for relative_path, expected_hash in FROZEN_HASHES.items():
        actual_hash = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        assert actual_hash == expected_hash
