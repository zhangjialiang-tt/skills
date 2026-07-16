#!/usr/bin/env python3
"""rtl-refactor-scan: deterministic audit-report checker (read-only).

Validates a generated 审计报告_<module>.md against the output contract that
SKILL.md Phase 3 and references/output-format.md define:

  * the five scan dimensions are present
  * A/B/C risk tiers are used
  * every finding records a line-number position
  * required report sections exist

It never writes or modifies anything. Exit code 0 = analysis ran; the
pass/fail verdict is in the printed JSON so the agent (or the eval runner)
can decide, not an error.

Usage:
    python scripts/scan_check.py <report.md> [--json]
"""
import json
import re
import sys

# Five dimensions from SKILL.md Phase 2 / scan-checklist.md.
# A valid audit report must explicitly declare full 5-dimension coverage
# (e.g. "按五大维度扫描：可综合性、可实现性、时序优化、仿真上板一致性、EDA LA 友好性").
DIMENSIONS = [
    "可综合性",
    "可实现性",
    "时序优化",
    "仿真上板一致性",
    "EDA LA 友好性",
]

# Required sections from references/output-format.md §1 template.
REQUIRED_SECTIONS = [
    "模块功能概述",
    "时钟",
    "复位",
    "数据流",
    "反压",
    "pipeline",
    "RAM",
    "FIFO",
    "风险列表",
    "A 类",
    "B 类",
    "C 类",
    "上板不一致",
    "EDA",
    "建议修改项",
    "最小修改集合",
    "是否建议进入修改阶段",
]

RISK_TIERS = ["A 类", "B 类", "C 类"]


def check(text):
    missing_dimensions = [d for d in DIMENSIONS if d not in text]

    missing_sections = [s for s in REQUIRED_SECTIONS if s not in text]

    # Every risk finding should carry a line-number position like "行 123" / "L123" / ":123".
    risk_block = text
    line_ref_pattern = re.compile(r"(行\s*\d+|L\d+|:\s*\d+|line\s*\d+)", re.IGNORECASE)
    has_any_position = bool(line_ref_pattern.search(risk_block))

    tiers_present = [t for t in RISK_TIERS if t in text]

    covered = (not missing_dimensions) and (not missing_sections)
    has_tiers = len(tiers_present) >= 2  # at least two tiers actually used
    passed = covered and has_tiers and has_any_position

    return {
        "passed": passed,
        "missing_dimensions": missing_dimensions,
        "missing_sections": missing_sections,
        "risk_tiers_present": tiers_present,
        "has_line_position": has_any_position,
        "score": (
            (100 if not missing_dimensions else 100 - 10 * len(missing_dimensions))
            + (0 if not missing_sections else -5 * len(missing_sections))
            + (0 if has_tiers else -10)
            + (0 if has_any_position else -10)
        ),
    }


def main():
    if len(sys.argv) < 2:
        print("usage: scan_check.py <report.md> [--json]", file=sys.stderr)
        return 2
    path = sys.argv[1]
    as_json = "--json" in sys.argv[2:]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        return 2

    result = check(text)
    if as_json:
        print(json.dumps({"file": path, **result}, ensure_ascii=False, indent=2))
    else:
        verdict = "PASS" if result["passed"] else "FAIL"
        print(f"[{verdict}] {path}  score={result['score']}")
        if result["missing_dimensions"]:
            print("  missing dimensions:", ", ".join(result["missing_dimensions"]))
        if result["missing_sections"]:
            print("  missing sections:", ", ".join(result["missing_sections"]))
        if not result["has_line_position"]:
            print("  warning: no line-number position found in risk list")
    return 0


if __name__ == "__main__":
    sys.exit(main())
