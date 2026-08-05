"""验证干净模块不产生任何 deterministic finding（误报基线）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from rtl_audit import audit_files
from collect_context import collect_context

CLEAN = str(Path(__file__).resolve().parent.parent / "evals" / "fixtures" / "clean_module.v")


def test_clean_module_zero_findings():
    ctx = collect_context([CLEAN])
    result = audit_files([CLEAN], ctx)
    findings = result["findings"]
    assert findings == [], f"false positives on clean module: {[f['rule_id'] for f in findings]}"
