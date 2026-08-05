#!/usr/bin/env python3
"""rtl-refactor-scan v2.0 smoke runner：Finding 全链路确定性证据。
collect_context → rtl_audit → validate_findings → render_report。
仍非 provider-backed 模型实证；证明的是确定性脚本能从 RTL 产出合法 findings。"""
import json
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from collect_context import collect_context
from rtl_audit import audit_files
from render_report import render_report
import validate_findings


def run(verilog_files):
    ctx = collect_context(verilog_files)
    findings_data = audit_files(verilog_files, ctx)

    # 写临时 findings.json 并校验
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(findings_data, f, ensure_ascii=False)
        tmp = f.name
    validation = validate_findings.validate_findings(tmp)

    report_md = render_report(findings_data)

    return {
        "ok": validation["passed"] and len(findings_data["findings"]) >= 1,
        "finding_count": len(findings_data["findings"]),
        "validation_passed": validation["passed"],
        "validation_errors": validation["errors"],
        "report_md": report_md,
        "execution_kind": "deterministic_pipeline",
    }


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    files = [f for f in args if f != "--json"]
    if not files:
        print("usage: smoke_runner.py <file.v> [...] [--json]", file=sys.stderr)
        return 2
    result = run(files)
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        verdict = "PASS" if result["ok"] else "FAIL"
        print(f"[{verdict}] findings={result['finding_count']} validation={result['validation_passed']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
