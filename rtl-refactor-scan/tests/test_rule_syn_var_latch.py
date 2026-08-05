import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from rtl_audit import detect_variable_part_select, detect_latch

FX = Path(__file__).resolve().parent.parent / "evals" / "fixtures" / "rules"


def test_var_part_select_detected_as_medium():
    text = (FX / "var_part_select_pos.v").read_text(encoding="utf-8")
    findings = detect_variable_part_select(text, "v.v")
    assert len(findings) == 1
    assert findings[0]["rule_id"] == "SYN-VARIABLE-PART-SELECT-001"
    assert findings[0]["severity"] == "medium"
    assert findings[0]["actionability"] == "plan_required"


def test_fixed_part_select_not_flagged():
    text = (FX / "var_part_select_neg.v").read_text(encoding="utf-8")
    assert detect_variable_part_select(text, "v.v") == []


def test_latch_detected():
    text = (FX / "latch_pos.v").read_text(encoding="utf-8")
    findings = detect_latch(text, "l.v")
    assert len(findings) == 1
    assert findings[0]["rule_id"] == "SYN-LATCH-001"
