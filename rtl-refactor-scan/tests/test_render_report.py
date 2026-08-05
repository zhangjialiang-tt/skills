"""验证 render_report.py：从 findings 生成 Markdown，A/B/C 由 severity 派生。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from render_report import render_report, severity_to_abc

FINDINGS = {
    "findings": [
        {
            "finding_id": "RTL-CDC-001", "rule_id": "CDC-MULTIBIT-DIRECT-001",
            "category": "cdc", "title": "多bit跨域",
            "locations": [{"file": "a.v", "start_line": 120, "end_line": 127}],
            "severity": "critical", "confidence": "confirmed", "evidence_level": "E2",
            "evidence": [{"type": "source", "description": "d"}],
            "actionability": "manual_design_required", "change_policy": "do_not_auto_fix"
        },
        {
            "finding_id": "RTL-SYN-001", "rule_id": "SYN-VARIABLE-PART-SELECT-001",
            "category": "synthesis", "title": "variable part-select",
            "locations": [{"file": "a.v", "start_line": 34, "end_line": 34}],
            "severity": "medium", "confidence": "probable", "evidence_level": "E1",
            "evidence": [{"type": "source", "description": "d"}],
            "actionability": "plan_required", "change_policy": "requires_approval"
        }
    ]
}


def test_severity_to_abc_mapping():
    assert severity_to_abc("critical") == "A"
    assert severity_to_abc("high") == "A"
    assert severity_to_abc("medium") == "B"
    assert severity_to_abc("low") == "C"
    assert severity_to_abc("info") == "C"


def test_report_contains_abc_sections():
    md = render_report(FINDINGS)
    assert "A 类" in md or "⚠️" in md
    assert "B 类" in md or "🔶" in md


def test_report_contains_finding_ids_and_lines():
    md = render_report(FINDINGS)
    assert "RTL-CDC-001" in md
    assert "L120" in md or "120" in md
    assert "RTL-SYN-001" in md
    assert "L34" in md or "34" in md


def test_report_contains_actionability():
    md = render_report(FINDINGS)
    assert "manual_design_required" in md
    assert "plan_required" in md
