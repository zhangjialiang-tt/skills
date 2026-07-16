#!/usr/bin/env python3
"""rtl-refactor-scan: deterministic smoke-runner for output-eval.

Local release-gate smoke evidence WITHOUT external model credentials.

Per yao-meta-skill output-eval-method, this proves the command-runner
contract (format machine-checkable, timing captured, grading path works,
failure handled). It must NOT be described as provider-backed model evidence.

The runner receives a JSON request on stdin and returns JSON with:
  - output            : the scan_check.py verdict for the fixture report
  - execution_kind    : "command"
  - provider / model  : omitted (no model involved)

Usage:
    echo '{"report":"evals/fixtures/sample_audit_report.md"}' | python evals/smoke_runner.py
"""
import json
import os
import subprocess
import sys

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKER = os.path.join(SKILL_ROOT, "scripts", "scan_check.py")


def main():
    raw = sys.stdin.read().strip()
    try:
        req = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        req = {}

    report = req.get("report") or os.path.join(
        SKILL_ROOT, "evals", "fixtures", "sample_audit_report.md"
    )
    if not os.path.isabs(report):
        report = os.path.join(SKILL_ROOT, report)

    if not os.path.exists(report):
        return _emit({"error": f"fixture not found: {report}"}, ok=False)
    if not os.path.exists(CHECKER):
        return _emit({"error": f"checker not found: {CHECKER}"}, ok=False)

    proc = subprocess.run(
        [sys.executable, CHECKER, report, "--json"],
        capture_output=True, text=True, cwd=SKILL_ROOT,
    )
    if proc.returncode != 0:
        return _emit({"error": proc.stderr.strip() or "checker failed"}, ok=False)

    try:
        verdict = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return _emit({"error": "invalid checker output"}, ok=False)

    return _emit({
        "output": verdict,
        "execution_kind": "command",
        "checked_report": report,
    }, ok=verdict.get("passed", False))


def _emit(payload, ok):
    payload["ok"] = ok
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    # 0 = ran successfully; the agent/eval decides pass/fail from `ok`.
    return 0


if __name__ == "__main__":
    sys.exit(main())
