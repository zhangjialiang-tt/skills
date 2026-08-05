"""端到端：对 sample_fixt_known_defects.v 审计，验证至少检出 4 个已知缺陷。"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from rtl_audit import audit_files
from collect_context import collect_context

FIXTURE = str(Path(__file__).resolve().parent.parent / "evals" / "fixtures" / "sample_fixt_known_defects.v")


def test_e2e_finds_known_defects():
    ctx = collect_context([FIXTURE])
    result = audit_files([FIXTURE], ctx)
    findings = result["findings"]
    rule_ids = {f["rule_id"] for f in findings}
    # 至少 4 个已知缺陷对应规则
    assert "SYN-MIXED-BLOCKING-001" in rule_ids
    assert "CDC-MULTIBIT-DIRECT-001" in rule_ids or "CDC-SINGLEBIT-DIRECT-001" in rule_ids
    assert "SYN-VARIABLE-PART-SELECT-001" in rule_ids


def test_e2e_findings_have_unique_ids():
    ctx = collect_context([FIXTURE])
    result = audit_files([FIXTURE], ctx)
    ids = [f["finding_id"] for f in result["findings"]]
    assert len(ids) == len(set(ids)), "finding_ids must be unique"


def test_e2e_output_passes_validate():
    ctx = collect_context([FIXTURE])
    result = audit_files([FIXTURE], ctx)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
        tmp = f.name
    r = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent.parent / "scripts" / "validate_findings.py"), tmp, "--json"],
        capture_output=True, text=True
    )
    out = json.loads(r.stdout)
    assert out["passed"], f"validation failed: {out.get('errors')}"
