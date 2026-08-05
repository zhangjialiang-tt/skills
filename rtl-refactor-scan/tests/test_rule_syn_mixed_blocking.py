import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from rtl_audit import detect_mixed_blocking

FX = Path(__file__).resolve().parent.parent / "evals" / "fixtures" / "rules"


def test_positive_detected():
    text = (FX / "syn_mixed_blocking_pos.v").read_text(encoding="utf-8")
    findings = detect_mixed_blocking(text, "pos.v")
    assert len(findings) == 1
    f = findings[0]
    assert f["rule_id"] == "SYN-MIXED-BLOCKING-001"
    assert f["severity"] == "critical"
    assert f["evidence_level"] == "E2"
    assert f["locations"][0]["start_line"] >= 1


def test_negative_not_detected():
    text = (FX / "syn_mixed_blocking_neg.v").read_text(encoding="utf-8")
    assert detect_mixed_blocking(text, "neg.v") == []


def test_edge_combinational_not_flagged():
    text = (FX / "syn_mixed_blocking_edge.v").read_text(encoding="utf-8")
    assert detect_mixed_blocking(text, "edge.v") == []
