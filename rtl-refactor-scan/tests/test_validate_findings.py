"""验证 validate_findings.py：schema 合法、行号必填、E0 不能 confirmed。"""
import json
import subprocess
import sys
from pathlib import Path

VALIDATOR = Path(__file__).resolve().parent.parent / "scripts" / "validate_findings.py"


def run_validator(findings_dict, tmp_path):
    f = tmp_path / "findings.json"
    f.write_text(json.dumps(findings_dict, ensure_ascii=False), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(f), "--json"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout) if result.stdout.strip() else {"_raw": result.stderr}


def test_valid_findings_pass(tmp_path):
    findings = {
        "findings": [{
            "finding_id": "RTL-CDC-001",
            "rule_id": "CDC-MULTIBIT-DIRECT-001",
            "category": "cdc",
            "title": "test",
            "locations": [{"file": "a.v", "start_line": 1, "end_line": 2}],
            "severity": "critical",
            "confidence": "confirmed",
            "evidence_level": "E2",
            "evidence": [{"type": "source", "description": "d"}],
            "actionability": "manual_design_required",
            "change_policy": "do_not_auto_fix"
        }]
    }
    result = run_validator(findings, tmp_path)
    assert result["passed"] is True


def test_e0_confirmed_rejected(tmp_path):
    findings = {
        "findings": [{
            "finding_id": "RTL-SYN-001", "rule_id": "SYN-LATCH-001", "category": "synthesis",
            "title": "t", "locations": [{"file": "a.v", "start_line": 1, "end_line": 2}],
            "severity": "high", "confidence": "confirmed", "evidence_level": "E0",
            "evidence": [{"type": "x", "description": "d"}],
            "actionability": "plan_required", "change_policy": "requires_approval"
        }]
    }
    result = run_validator(findings, tmp_path)
    assert result["passed"] is False
