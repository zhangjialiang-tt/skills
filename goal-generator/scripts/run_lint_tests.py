#!/usr/bin/env python3
"""Contract-consistency test runner for goal-generator.

Encodes the v2.0.2 acceptance gates as executable checks:
  1. Both canonical SKILL.md templates (bilingual Standard + bracket Diagnostic)
     pass the linter under --strict.
  2. Every pass_* / *_pass fixture passes under --strict.
  3. Every fail_* fixture still fails (structural error in default mode).
  4. A baseline-only goal is NOT forced to fabricate a target threshold.
  5. Section parsing does not bleed one field into the next.
  6. All formal files declare the same version.

Exit 0 on full pass, 1 on any failure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import lint_goal  # noqa: E402

FIXTURES = SCRIPTS_DIR / "test_fixtures"

_results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    _results.append((ok, label))
    print(f"{'PASS' if ok else 'FAIL'}  {label}")


def lint_file(path: Path, strict: bool) -> tuple[list[str], list[str]]:
    return lint_goal.lint_text(path.read_text(encoding="utf-8"), path.name, strict=strict)


def test_canonical_templates_strict() -> None:
    cases = {
        "canonical_standard_template.txt": "standard",
        "canonical_diagnostic_template.txt": "diagnostic",
    }
    for name, expected_profile in cases.items():
        path = FIXTURES / name
        errors, warnings = lint_file(path, strict=True)
        profile = lint_goal.classify_profile(path.read_text(encoding="utf-8"))
        check(
            not errors and profile == expected_profile,
            f"canonical template strict PASS + profile={expected_profile}: {name}"
            + (f"  [errors={errors}, profile={profile}]" if errors or profile != expected_profile else ""),
        )


def test_pass_fixtures_strict() -> None:
    names = sorted(p.name for p in FIXTURES.glob("*.txt") if "fail" not in p.name)
    for name in names:
        errors, warnings = lint_file(FIXTURES / name, strict=True)
        check(not errors, f"pass fixture strict PASS: {name}" + (f"  [errors={errors}]" if errors else ""))


def test_fail_fixtures_fail() -> None:
    for path in sorted(FIXTURES.glob("fail_*.txt")):
        errors, _ = lint_file(path, strict=False)
        check(bool(errors), f"fail fixture fails (structural error): {path.name}")


def test_baseline_only_not_coerced() -> None:
    path = FIXTURES / "pass_baseline_only.txt"
    errors, warnings = lint_file(path, strict=True)
    coerced = any("threshold" in e.lower() for e in errors + warnings)
    check(
        not errors and not coerced,
        "baseline-only goal passes strict without a fabricated threshold",
    )


def test_section_isolation() -> None:
    # Verification has NO evidence keyword; a later Stop section does. If sections
    # bled, the Stop section's "测试通过" would mask the missing evidence.
    bleed_verification = (
        "/goal 创建一个本地数据整理工具，实现核心流程。\n"
        "验证：确认结果符合预期。\n"
        "约束：不加入无关功能。\n"
        "边界：只修改 src/ 目录。\n"
        "迭代策略：一次一个聚焦改动，重跑检查。\n"
        "完成条件：测试通过后即可视为完成。\n"
        "暂停条件：需要凭证或付费时暂停。\n"
    )
    errors, warnings = lint_goal.lint_text(bleed_verification, "inline", strict=False)
    check(
        any("W04" in w for w in warnings) and not errors,
        "verification isolation: missing evidence flagged even when a later section has evidence words",
    )

    # Over-wide phrase lives ONLY in the Stop section, not Boundaries: W05 must NOT fire.
    overwide_elsewhere = bleed_verification.replace("边界：只修改 src/ 目录。", "边界：只修改 src/ 目录。").replace(
        "完成条件：测试通过后即可视为完成。", "完成条件：整个项目的测试全部通过即完成。"
    )
    _, warnings2 = lint_goal.lint_text(overwide_elsewhere, "inline", strict=False)
    check(
        not any("W05" in w for w in warnings2),
        "boundary isolation: over-wide phrase outside Boundaries does not trigger W05",
    )

    # Over-wide phrase inside Boundaries: W05 MUST fire.
    overwide_boundary = bleed_verification.replace("边界：只修改 src/ 目录。", "边界：整个项目都可以修改。")
    _, warnings3 = lint_goal.lint_text(overwide_boundary, "inline", strict=False)
    check(
        any("W05" in w for w in warnings3),
        "boundary isolation: over-wide phrase inside Boundaries triggers W05",
    )


def _read_version(path: Path, pattern: str) -> str | None:
    if path.suffix == ".json":
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("version")
        except (OSError, json.JSONDecodeError):
            return None
    m = re.search(pattern, path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    return m.group(1) if m else None


def test_version_consistency() -> None:
    sources = {
        "SKILL.md": (ROOT / "SKILL.md", r'^version:\s*"([^"]+)"'),
        "manifest.json": (ROOT / "manifest.json", None),
        "agents/interface.yaml": (ROOT / "agents" / "interface.yaml", r'^version:\s*"([^"]+)"'),
        "scripts/lint_goal.py": (SCRIPTS_DIR / "lint_goal.py", r'VERSION\s*=\s*"([^"]+)"'),
        "evals/evals.json": (ROOT / "evals" / "evals.json", None),
        "evals/output_evals.json": (ROOT / "evals" / "output_evals.json", None),
        "reports/trust-report.md": (ROOT / "reports" / "trust-report.md", r"\*\*Version:\*\*\s*([0-9][\w.\-]*)"),
        "reports/portability-report.md": (ROOT / "reports" / "portability-report.md", r"\*\*Version:\*\*\s*([0-9][\w.\-]*)"),
        "reports/output-risk-profile.md": (ROOT / "reports" / "output-risk-profile.md", r"goal-generator\s+v([0-9][\w.\-]*)"),
    }
    versions: dict[str, str | None] = {}
    for label, (path, pattern) in sources.items():
        versions[label] = _read_version(path, pattern) if pattern else _read_version(path, "")
    unique = set(versions.values())
    detail = ", ".join(f"{k}={v}" for k, v in versions.items())
    check(len(unique) == 1 and None not in unique, f"all formal files share one version ({detail})")


def main() -> int:
    print(f"goal-generator contract-consistency tests (linter v{lint_goal.VERSION})\n")
    test_canonical_templates_strict()
    test_pass_fixtures_strict()
    test_fail_fixtures_fail()
    test_baseline_only_not_coerced()
    test_section_isolation()
    test_version_consistency()

    failed = [label for ok, label in _results if not ok]
    print(f"\n{'=' * 60}\n{len(_results) - len(failed)}/{len(_results)} checks passed.")
    if failed:
        print("FAILURES:")
        for label in failed:
            print(f"  - {label}")
        return 1
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
