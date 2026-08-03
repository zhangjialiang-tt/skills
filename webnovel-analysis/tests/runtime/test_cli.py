import json
import os
from pathlib import Path
import subprocess
import sys

from helpers import ROOT


def run_cli(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["WEBNOVEL_ANALYSIS_RUNS"] = str(tmp_path / "runs")
    return subprocess.run(
        [sys.executable, str(ROOT / "runtime" / "cli.py"), *args],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_runs_valid_fixture_to_delivery(tmp_path) -> None:
    request = ROOT / "examples" / "mini-urban-rebirth" / "request.yaml"
    gate_c = ROOT / "tests" / "fixtures" / "runtime" / "gate-c-accepted.yaml"
    assert run_cli(tmp_path, "create", "--request", str(request)).returncode == 0
    assert run_cli(tmp_path, "run-batch", "--task", "TASK-0001", "--batch", "BATCH-001", "--adapter", "fixture", "--scenario", "valid").returncode == 0
    finalized = run_cli(tmp_path, "finalize", "--task", "TASK-0001", "--gate-c-decision", str(gate_c))
    assert finalized.returncode == 0
    assert json.loads(finalized.stdout)["status"] == "DELIVERABLE_READY"


def test_cli_returns_structured_nonzero_error_for_invalid_output(tmp_path) -> None:
    request = ROOT / "examples" / "mini-urban-rebirth" / "request.yaml"
    run_cli(tmp_path, "create", "--request", str(request))
    failed = run_cli(tmp_path, "run-batch", "--task", "TASK-0001", "--batch", "BATCH-001", "--scenario", "invalid_s2")
    assert failed.returncode != 0
    assert json.loads(failed.stderr)["error"]["code"] == "MODULE_OUTPUT_SCHEMA_INVALID"
