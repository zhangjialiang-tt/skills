#!/usr/bin/env python3
"""校验 novel-master Prompt 回归集并对比规范化实际结果。

用法：
    python scripts/check_prompt_regressions.py evals/evals.json
    python scripts/check_prompt_regressions.py evals/evals.json \
        --actual evals/fixtures/results-valid.json \
        --report comparison.md

实际结果格式：
    {"results": [{"id": "NM-REG-001", "actual": {...}}]}

脚本只对声明式自动断言作确定性判断。文风、证据充分性等人工复核项
会进入 Markdown 报告，但不会被伪装成自动 PASS。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_CASE_IDS = [f"NM-REG-{index:03d}" for index in range(1, 11)]
ALLOWED_OPERATORS = {
    "equals",
    "contains",
    "not_contains",
    "is_empty",
    "is_not_empty",
}
MISSING = object()


def load_json(path: Path | str) -> dict[str, Any]:
    """以 UTF-8 读取 JSON 对象。"""
    with Path(path).open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"{path} 的根节点必须是对象")
    return data


def validate_suite(suite: dict[str, Any]) -> list[str]:
    """验证固定回归集的结构和 10 条必需场景。"""
    issues: list[str] = []
    if suite.get("skill_name") != "novel-master":
        issues.append("skill_name 必须是 novel-master")

    cases = suite.get("evals")
    if not isinstance(cases, list):
        return issues + ["evals 必须是数组"]

    ids: list[str] = []
    for index, case in enumerate(cases):
        location = f"evals[{index}]"
        if not isinstance(case, dict):
            issues.append(f"{location} 必须是对象")
            continue

        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            issues.append(f"{location}.id 必须是非空字符串")
        else:
            ids.append(case_id)

        for field in ("title", "prompt"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                issues.append(f"{location}.{field} 必须是非空字符串")

        assertions = case.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            issues.append(f"{location}.assertions 必须是非空数组")
        else:
            for assertion_index, assertion in enumerate(assertions):
                assertion_location = (
                    f"{location}.assertions[{assertion_index}]"
                )
                if not isinstance(assertion, dict):
                    issues.append(f"{assertion_location} 必须是对象")
                    continue
                if not isinstance(assertion.get("path"), str):
                    issues.append(f"{assertion_location}.path 必须是字符串")
                operator = assertion.get("operator")
                if operator not in ALLOWED_OPERATORS:
                    issues.append(
                        f"{assertion_location}.operator 非法: {operator}"
                    )
                if (
                    operator in {"equals", "contains", "not_contains"}
                    and "expected" not in assertion
                ):
                    issues.append(
                        f"{assertion_location} 缺少 expected"
                    )

        manual_checks = case.get("manual_checks")
        if (
            not isinstance(manual_checks, list)
            or not manual_checks
            or not all(
                isinstance(item, str) and item.strip()
                for item in manual_checks
            )
        ):
            issues.append(f"{location}.manual_checks 必须是非空字符串数组")

    duplicate_ids = sorted(
        case_id for case_id in set(ids) if ids.count(case_id) > 1
    )
    for case_id in duplicate_ids:
        issues.append(f"回归编号重复: {case_id}")

    missing_ids = [
        case_id for case_id in REQUIRED_CASE_IDS if case_id not in ids
    ]
    for case_id in missing_ids:
        issues.append(f"缺少必需回归场景: {case_id}")

    extra_ids = [
        case_id for case_id in ids if case_id not in REQUIRED_CASE_IDS
    ]
    for case_id in extra_ids:
        issues.append(f"存在未登记回归编号: {case_id}")

    if ids and ids != REQUIRED_CASE_IDS:
        issues.append("回归场景必须按 NM-REG-001 至 NM-REG-010 排序")

    return issues


def _resolve_path(data: Any, dotted_path: str) -> Any:
    current = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return MISSING
        current = current[part]
    return current


def _assertion_passes(actual: Any, assertion: dict[str, Any]) -> bool:
    operator = assertion["operator"]
    expected = assertion.get("expected")

    if actual is MISSING:
        return False
    if operator == "equals":
        return actual == expected
    if operator == "contains":
        return (
            isinstance(actual, (list, str))
            and expected in actual
        )
    if operator == "not_contains":
        return (
            isinstance(actual, (list, str))
            and expected not in actual
        )
    if operator == "is_empty":
        return actual in (None, "", [], {})
    if operator == "is_not_empty":
        return actual not in (None, "", [], {})
    return False


def compare_results(
    suite: dict[str, Any],
    results: dict[str, Any],
) -> dict[str, Any]:
    """将规范化实际结果与声明式断言逐项对比。"""
    raw_results = results.get("results", [])
    result_map = {
        item.get("id"): item.get("actual")
        for item in raw_results
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    case_results: list[dict[str, Any]] = []
    missing = 0
    for case in suite["evals"]:
        case_id = case["id"]
        actual = result_map.get(case_id, MISSING)
        if actual is MISSING:
            missing += 1
            case_results.append(
                {
                    "id": case_id,
                    "title": case["title"],
                    "passed": False,
                    "missing": True,
                    "failures": [
                        {
                            "path": "$",
                            "operator": "exists",
                            "expected": "actual result",
                            "actual": "<MISSING>",
                        }
                    ],
                    "manual_checks": case["manual_checks"],
                }
            )
            continue

        failures: list[dict[str, Any]] = []
        for assertion in case["assertions"]:
            observed = _resolve_path(actual, assertion["path"])
            if not _assertion_passes(observed, assertion):
                failures.append(
                    {
                        "path": assertion["path"],
                        "operator": assertion["operator"],
                        "expected": assertion.get("expected"),
                        "actual": (
                            "<MISSING>" if observed is MISSING else observed
                        ),
                    }
                )

        case_results.append(
            {
                "id": case_id,
                "title": case["title"],
                "passed": not failures,
                "missing": False,
                "failures": failures,
                "manual_checks": case["manual_checks"],
            }
        )

    passed = sum(case["passed"] for case in case_results)
    total = len(case_results)
    return {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "missing": missing,
        },
        "cases": case_results,
    }


def render_markdown_report(comparison: dict[str, Any]) -> str:
    """生成可供人工复核的 Markdown 对比报告。"""
    summary = comparison["summary"]
    lines = [
        "# novel-master Prompt 回归对比报告",
        "",
        (
            f"- 自动断言：{summary['passed']}/{summary['total']} 通过"
            f"，失败 {summary['failed']}，缺失 {summary['missing']}"
        ),
        "- 说明：自动断言只检查结构化行为；人工复核项不计入自动通过率。",
        "",
        "| 编号 | 场景 | 自动结果 | 失败断言 |",
        "| --- | --- | --- | --- |",
    ]

    for case in comparison["cases"]:
        verdict = "PASS" if case["passed"] else "FAIL"
        failure_text = "<br>".join(
            (
                f"`{failure['path']}` {failure['operator']} "
                f"`{failure['expected']}`，实际 "
                f"`{failure['actual']}`"
            )
            for failure in case["failures"]
        ) or "-"
        lines.append(
            f"| {case['id']} | {case['title']} | {verdict} | "
            f"{failure_text} |"
        )

    lines.extend(["", "## 人工复核项", ""])
    for case in comparison["cases"]:
        lines.append(f"### {case['id']} {case['title']}")
        lines.append("")
        for item in case["manual_checks"]:
            lines.append(f"- [ ] {item}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="校验 Prompt 回归集并对比规范化实际结果。"
    )
    parser.add_argument("suite", type=Path, help="evals.json 路径")
    parser.add_argument(
        "--actual",
        type=Path,
        help="规范化实际结果 JSON；省略时仅校验回归集",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="将对比结果写为 Markdown；必须同时提供 --actual",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.report and not args.actual:
        print("--report 必须与 --actual 同时使用", file=sys.stderr)
        return 2

    try:
        suite = load_json(args.suite)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2

    suite_issues = validate_suite(suite)
    output: dict[str, Any] = {
        "suite_valid": not suite_issues,
        "suite_issues": suite_issues,
        "case_count": len(suite.get("evals", [])),
    }
    if suite_issues:
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 1

    if args.actual:
        try:
            results = load_json(args.actual)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(str(error), file=sys.stderr)
            return 2
        comparison = compare_results(suite, results)
        output["comparison"] = comparison["summary"]
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(
                render_markdown_report(comparison),
                encoding="utf-8",
            )
        exit_code = 0 if comparison["summary"]["failed"] == 0 else 1
    else:
        exit_code = 0

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
