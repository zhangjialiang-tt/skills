"""全 fixture 矩阵回归：验证每类 fixture 的预期检出/不检出行为。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from rtl_audit import audit_files
from collect_context import collect_context

FX = Path(__file__).resolve().parent.parent / "evals" / "fixtures"


def _audit(rel):
    f = str(FX / rel)
    ctx = collect_context([f])
    return audit_files([f], ctx)["findings"]


def test_sample_fixt_finds_at_least_4():
    findings = _audit("sample_fixt_known_defects.v")
    assert len(findings) >= 4


def test_clean_module_zero():
    assert _audit("clean_module.v") == []


def test_pos_fixtures_detected():
    """所有 _pos.v 正例至少检出 1 个 finding。"""
    for pos in (FX / "rules").glob("*_pos.v"):
        findings = _audit(f"rules/{pos.name}")
        assert len(findings) >= 1, f"{pos.name} should trigger findings"


def test_neg_fixtures_target_rule_absent():
    """cdc_synced_neg.v 不应检出 CDC 规则。"""
    findings = _audit("rules/cdc_synced_neg.v")
    cdc_findings = [f for f in findings if f["rule_id"].startswith("CDC-")]
    assert cdc_findings == [], f"synced fixture should not trigger CDC: {[f['rule_id'] for f in cdc_findings]}"
