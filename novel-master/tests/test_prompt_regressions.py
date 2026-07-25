"""Prompt 回归集与确定性对比器测试。"""

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
EVALS_PATH = ROOT / "evals" / "evals.json"
FIXTURE_PATH = ROOT / "evals" / "fixtures" / "results-valid.json"
sys.path.insert(0, str(SCRIPTS_DIR))

from check_prompt_regressions import (  # noqa: E402
    compare_results,
    load_json,
    render_markdown_report,
    validate_suite,
)


EXPECTED_CASE_IDS = [f"NM-REG-{index:03d}" for index in range(1, 18)]


def test_fixed_regression_suite_covers_all_required_cases():
    suite = load_json(EVALS_PATH)

    assert [case["id"] for case in suite["evals"]] == EXPECTED_CASE_IDS
    assert validate_suite(suite) == []


def test_suite_rejects_missing_required_case():
    suite = load_json(EVALS_PATH)
    broken = deepcopy(suite)
    broken["evals"].pop()

    issues = validate_suite(broken)

    assert any("NM-REG-017" in issue for issue in issues)


def test_suite_rejects_duplicate_case_id():
    suite = load_json(EVALS_PATH)
    broken = deepcopy(suite)
    broken["evals"][1]["id"] = broken["evals"][0]["id"]

    issues = validate_suite(broken)

    assert any("重复" in issue for issue in issues)


def test_known_good_results_pass_all_assertions():
    suite = load_json(EVALS_PATH)
    results = load_json(FIXTURE_PATH)

    comparison = compare_results(suite, results)

    assert comparison["summary"] == {
        "total": 17,
        "passed": 17,
        "failed": 0,
        "missing": 0,
    }


def test_comparison_exposes_forbidden_mutation():
    suite = load_json(EVALS_PATH)
    results = load_json(FIXTURE_PATH)
    broken = deepcopy(results)
    broken["results"][0]["actual"]["actions"].append("rewrite_source")

    comparison = compare_results(suite, broken)

    first_case = comparison["cases"][0]
    assert first_case["passed"] is False
    assert any(
        failure["path"] == "actions"
        and failure["operator"] == "not_contains"
        for failure in first_case["failures"]
    )


def test_markdown_report_is_human_reviewable():
    comparison = compare_results(
        load_json(EVALS_PATH),
        load_json(FIXTURE_PATH),
    )

    report = render_markdown_report(comparison)

    assert "# novel-master Prompt 回归对比报告" in report
    assert "| NM-REG-001 |" in report
    assert "17/17" in report
    assert "人工复核项" in report


def test_cli_validates_suite_and_emits_markdown_report(tmp_path):
    report_path = tmp_path / "comparison.md"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "check_prompt_regressions.py"),
            str(EVALS_PATH),
            "--actual",
            str(FIXTURE_PATH),
            "--report",
            str(report_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary["suite_valid"] is True
    assert summary["comparison"]["failed"] == 0
    assert report_path.is_file()
