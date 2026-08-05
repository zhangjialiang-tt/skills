import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from rtl_audit import detect_cdc_direct

FX = Path(__file__).resolve().parent.parent / "evals" / "fixtures" / "rules"


def test_singlebit_detected():
    text = (FX / "cdc_singlebit_pos.v").read_text(encoding="utf-8")
    ctx = {"clocks": [{"name": "clk_a", "domain": "A"}, {"name": "clk_b", "domain": "B"}]}
    findings = detect_cdc_direct(text, "s.v", ctx)
    assert any(f["rule_id"] == "CDC-SINGLEBIT-DIRECT-001" for f in findings)


def test_multibit_detected():
    text = (FX / "cdc_multibit_pos.v").read_text(encoding="utf-8")
    ctx = {"clocks": [{"name": "clk_a", "domain": "A"}, {"name": "clk_b", "domain": "B"}]}
    findings = detect_cdc_direct(text, "m.v", ctx)
    assert any(f["rule_id"] == "CDC-MULTIBIT-DIRECT-001" for f in findings)
    f = [x for x in findings if x["rule_id"] == "CDC-MULTIBIT-DIRECT-001"][0]
    assert f["actionability"] == "manual_design_required"


def test_synced_not_flagged():
    text = (FX / "cdc_synced_neg.v").read_text(encoding="utf-8")
    ctx = {"clocks": [{"name": "clk_a"}, {"name": "clk_b"}]}
    findings = detect_cdc_direct(text, "sync.v", ctx)
    assert findings == []
