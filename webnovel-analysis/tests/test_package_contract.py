from pathlib import Path

import json
import yaml


ROOT = Path(__file__).parents[1]
MODULE_IDS = ["O0", "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "Q0"]


def test_root_is_the_only_installable_skill() -> None:
    skill_files = list(ROOT.rglob("SKILL.md"))
    assert skill_files == [ROOT / "SKILL.md"]
    assert (ROOT / "agents" / "interface.yaml").is_file()
    assert list(ROOT.rglob("interface.yaml")) == [ROOT / "agents" / "interface.yaml"]


def test_internal_modules_are_registered_but_not_routeable() -> None:
    registry = yaml.safe_load((ROOT / "references" / "internal-module-registry.yaml").read_text(encoding="utf-8"))
    modules = registry["modules"]
    assert [module["id"] for module in modules] == MODULE_IDS
    for module in modules:
        module_file = ROOT / module["entry"]
        assert module_file.is_file()
        assert module_file.name == "MODULE.md"
        assert not module_file.read_text(encoding="utf-8").startswith("---")
        assert module["external_routeable"] is False


def test_manifest_describes_the_root_package() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "webnovel-analysis"
    assert manifest["status"] == "active"
    assert "agents" in manifest["factory_components"]
    assert "references" in manifest["factory_components"]
    assert "schemas" in manifest["factory_components"]


def test_each_prompt_declares_its_normative_module_schema() -> None:
    registry = yaml.safe_load((ROOT / "references" / "internal-module-registry.yaml").read_text(encoding="utf-8"))
    for module in registry["modules"]:
        module_dir = (ROOT / module["entry"]).parent
        prompt = (module_dir / "references" / "prompt-template.md").read_text(encoding="utf-8")
        assert "model-output-contract.md" in prompt
        assert f"schemas/modules/{module['id']}.schema.json" in prompt
        assert "## 输出 Schema" not in prompt
