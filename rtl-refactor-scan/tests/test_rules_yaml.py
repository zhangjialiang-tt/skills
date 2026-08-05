"""验证 rules.yaml：每条规则有三轴、有 rule_id、有 detection、variable part-select 不再是 A 类。"""
import yaml
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "rules.yaml"


def load_rules():
    return yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))


def test_every_rule_has_required_fields():
    rules = load_rules()
    for r in rules["rules"]:
        assert "rule_id" in r, f"missing rule_id: {r}"
        assert "category" in r
        assert "default_severity" in r
        assert "default_actionability" in r
        assert "detection" in r
        assert "method" in r["detection"]


def test_variable_part_select_not_critical():
    """冲突裁决：variable part-select 冻结为 medium（旧 B 类语义），不再 critical/A 类。"""
    rules = load_rules()
    vps = [r for r in rules["rules"] if "VARIABLE" in r["rule_id"] or "PART_SELECT" in r["rule_id"]]
    assert len(vps) == 1, "exactly one variable part-select rule"
    assert vps[0]["default_severity"] == "medium"
    assert vps[0]["default_actionability"] == "plan_required"


def test_cdc_rules_actionability_manual():
    """冲突裁决：CDC 规则 severity=critical 但 actionability=manual_design_required（不再 C 类只读）。"""
    rules = load_rules()
    cdc_rules = [r for r in rules["rules"] if r["category"] == "cdc"]
    assert len(cdc_rules) >= 2, "at least 2 CDC rules (single-bit + multi-bit)"
    for r in cdc_rules:
        assert r["default_severity"] == "critical"
        assert r["default_actionability"] == "manual_design_required"


def test_mux_threshold_unified():
    """冲突裁决：mux 阈值统一为 >32:1 触发 plan_required。"""
    rules = load_rules()
    mux_rules = [r for r in rules["rules"] if "MUX" in r["rule_id"]]
    assert len(mux_rules) >= 1
    high_mux = [r for r in mux_rules if "32" in r.get("detection", {}).get("threshold", "")]
    assert len(high_mux) >= 1
