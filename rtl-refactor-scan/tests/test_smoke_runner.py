"""验证 smoke_runner 跑通 Finding 全链路。"""
import json
import subprocess
import sys
from pathlib import Path

RUNNER = Path(__file__).resolve().parent.parent / "evals" / "smoke_runner.py"
FIXTURE = Path(__file__).resolve().parent.parent / "evals" / "fixtures" / "sample_fixt_known_defects.v"


def test_smoke_runner_returns_ok():
    result = subprocess.run(
        [sys.executable, str(RUNNER), str(FIXTURE), "--json"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["ok"] is True
    assert out["finding_count"] >= 4
    assert out["validation_passed"] is True


def test_smoke_runner_renders_report():
    result = subprocess.run(
        [sys.executable, str(RUNNER), str(FIXTURE), "--json"],
        capture_output=True, text=True
    )
    out = json.loads(result.stdout)
    assert "report_md" in out
    assert "RTL-" in out["report_md"]  # finding_id 出现在报告里
