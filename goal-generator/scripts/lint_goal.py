#!/usr/bin/env python3
"""Lightweight static validation for goal-generator outputs.

Checks generated /goal contracts against the selected profile contract.
Detects missing markers, placeholders, dangerous vague instructions,
over-wide boundaries, fact-hypothesis confusion (Diagnostic), and
missing metric thresholds.

Limitations (read carefully):
- This is a STRUCTURAL checker, not a semantic judge.
- It cannot reliably determine if an Outcome truly describes an
  observable state vs. an action; it only flags a short outcome.
- It cannot determine if anti-gaming constraints are truly domain-specific.
- It cannot determine if a hypothesis is correctly separated from facts.
- Warnings (W-) are advisory; errors (E-) are structural failures.

Exit codes:
  0 = passed (no errors, warnings OK)
  1 = at least one error
  2 = usage error
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

VERSION = "2.0.0"

# ---------------------------------------------------------------------------
# Pattern groups
# ---------------------------------------------------------------------------

COMMAND_PATTERNS = [r"(?m)^\s*/goal\b"]
BAD_COMMAND_PATTERNS = [r"(?m)^\s*/目标\b"]

COMMON_MARKERS = {
    "command": [r"(?m)/goal"],
    "verification": [r"验证[:：]", r"Verification[:：]", r"验收证据", r"【验证】", r"【验收证据】"],
    "constraints": [r"约束[:：]", r"Constraints[:：]", r"必须保持", r"【约束】", r"【必须保持】"],
    "boundaries": [r"边界[:：]", r"Boundaries[:：]", r"工作边界", r"【边界】", r"【工作边界】"],
    "iteration": [r"迭代策略[:：]", r"Iteration policy[:：]", r"迭代", r"【迭代策略】"],
    "stop": [r"完成条件[:：]", r"Stop when[:：]", r"停止条件[:：]", r"阻塞与停止", r"【完成条件】", r"【阻塞与停止】", r"暂停条件[:：]", r"Pause if[:：]", r"【暂停条件】"],
}

DIAGNOSTIC_MARKERS = {
    "current_facts": [r"当前事实[:：]", r"Current facts[:：]", r"【当前事实】"],
    "hypotheses": [r"待验证假设[:：]", r"Hypotheses[:：]", r"【待验证假设】"],
    "blocked_report": [r"阻塞与停止", r"Blocked report[:：]", r"暂停条件", r"【阻塞与停止】", r"【暂停条件】"],
}

PLACEHOLDER_PATTERNS = [
    (r"\[[^\]]+\]", "bracket placeholder [XXX]"),
    (r"\bTBD\b", "TBD"),
    (r"\bTODO\b", "TODO"),
    (r"<[^>]+>", "angle-bracket placeholder <XXX>"),
    (r"待补充", "待补充"),
    (r"待定", "待定"),
    (r"某", "vague '某'"),
]

DANGEROUS_VAGUE_PATTERNS = [
    (r"make sure it works", "make sure it works"),
    (r"edit anything", "edit anything"),
    (r"change whatever", "change whatever"),
    (r"keep trying", "keep trying"),
    (r"until it (looks|seems|feels) good", "until it looks/seems/feels good"),
    (r"随便改", "随便改"),
    (r"随意修改", "随意修改"),
    (r"一直尝试", "一直尝试"),
    (r"直到满意", "直到满意"),
    (r"看起来不错就行", "看起来不错就行"),
    (r"感觉可以", "感觉可以"),
    (r"尽可能", "vague '尽可能'"),
]

VERIFICATION_EVIDENCE_PATTERNS = [
    r"\b(run|start|open|test|build|lint|typecheck|verify|inspect|capture|screenshot|log|artifact|file|url|api|simulator|browser|local)\b",
    r"(运行|启动|打开|测试|构建|检查|验证|读取|截图|日志|产物|文件|链接|接口|API|模拟器|浏览器|本地|证据|PASS|通过|失败|阈值|ms|秒|fps|例|百分比|%|≥|≤|<|>|==)",
]

OVERWIDE_BOUNDARY_PATTERNS = [
    (r"所有文件", "'所有文件' is over-wide"),
    (r"整个项目", "'整个项目' is over-wide"),
    (r"整个仓库", "'整个仓库' is over-wide"),
    (r"全部代码", "'全部代码' is over-wide"),
    (r"不限制", "'不限制' is over-wide"),
    (r"anywhere", "'anywhere' is over-wide"),
    (r"everywhere", "'everywhere' is over-wide"),
]

METRIC_PATTERNS = [
    r"(\d+\.?\d*)\s*(ms|毫秒|秒|分钟|小时|fps|帧|GB|MB|KB|TB|%|百分比|例|次|人|个)",
    r"(每周|每天|每小时|每月|每年)\s*(\d+\.?\d*)\s*",
]

THRESHOLD_PATTERNS = [
    r"[<>≤≥]=?\s*\d+\.?\d*",
    r"(低于|小于|大于|不超过|至少|≥|≤|>|<|==|降低|提高)\s*\d+\.?\d*",
    r"P\d+\s*[<>≤≥]=?\s*\d+\.?\d*",
]


def classify_profile(text: str) -> str:
    diag_score = 0
    for name, patterns in DIAGNOSTIC_MARKERS.items():
        if any(re.search(p, text) for p in patterns):
            diag_score += 1
    if diag_score >= 2:
        return "diagnostic"
    if re.search(r"待验证假设|Current facts|Hypotheses|当前事实", text):
        return "diagnostic"
    return "standard"


def extract_outcome(text: str) -> str | None:
    """Extract outcome text after /goal, handling both inline and block formats."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if '/goal' in line:
            idx = line.find('/goal') + 5
            after = line[idx:].strip()
            # If there's meaningful content after /goal on the same line
            if after and after not in ('', '，', '：', ':', '。', '.'):
                return after
            # Look at subsequent non-empty lines
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if not next_line:
                    continue
                # Skip section headers like 【期望结果】
                if next_line.startswith('【') and next_line.endswith('】'):
                    continue
                # Skip section headers with content: 【期望结果】some text
                if '【' in next_line and '】' in next_line:
                    after_header = next_line[next_line.index('】') + 1:].strip()
                    if after_header:
                        return after_header
                    continue
                return next_line
            break
    return None


def find_section_content(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(rf"{pattern}\s*(.+)", text)
        if match:
            return match.group(1).strip()
    return None


def get_section_block(text: str, header_patterns: list[str]) -> str:
    lines = text.splitlines()
    in_section = False
    block_lines = []
    all_section_starters = [
        r"^【.+】",
        r"^###\s",
        r"^#{1,3}\s",
    ]

    for line in lines:
        if in_section:
            starter_match = any(re.match(p, line.strip()) for p in all_section_starters)
            if starter_match:
                break
            block_lines.append(line)
            continue

        for pattern in header_patterns:
            m = re.search(pattern, line)
            if m:
                remainder = line[m.end():].strip()
                if remainder:
                    block_lines.append(remainder)
                in_section = True
                break

    return "\n".join(block_lines)


def lint_text(text: str, source: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    profile = classify_profile(text)

    if any(re.search(p, text) for p in BAD_COMMAND_PATTERNS):
        errors.append(f"{source}: E01 - use /goal, not /目标, as the executable command")
    elif not any(re.search(p, text) for p in COMMAND_PATTERNS):
        errors.append(f"{source}: E02 - missing /goal command marker")

    all_markers = {**COMMON_MARKERS}
    if profile == "diagnostic":
        all_markers.update(DIAGNOSTIC_MARKERS)

    for name, patterns in all_markers.items():
        if not any(re.search(p, text) for p in patterns):
            readable = " / ".join(p.replace(r"[:：]", ":").replace(r"(?m)", "") for p in patterns[:3])
            errors.append(f"{source}: E03 - missing required marker for `{name}` (e.g., {readable})")

    for pattern, desc in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            warnings.append(f"{source}: W01 - unresolved placeholder: {desc}")

    for pattern, desc in DANGEROUS_VAGUE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            warnings.append(f"{source}: W02 - dangerous vague instruction: '{desc}'")

    outcome_text = extract_outcome(text)
    if outcome_text and len(outcome_text) < 15:
        warnings.append(f"{source}: W03 - /goal outcome is very short ({len(outcome_text)} chars); consider whether it describes an observable state")

    verification_content = find_section_content(text, COMMON_MARKERS["verification"])
    if verification_content:
        if not any(re.search(p, verification_content, flags=re.IGNORECASE) for p in VERIFICATION_EVIDENCE_PATTERNS):
            warnings.append(f"{source}: W04 - verification section should name concrete evidence")

    boundary_block = get_section_block(text, COMMON_MARKERS["boundaries"])
    if boundary_block:
        for pattern, desc in OVERWIDE_BOUNDARY_PATTERNS:
            if re.search(pattern, boundary_block):
                warnings.append(f"{source}: W05 - over-wide boundary: {desc}")

    user_metrics = []
    for pattern in METRIC_PATTERNS:
        for match in re.finditer(pattern, text):
            user_metrics.append(match.group(0))

    if user_metrics:
        has_threshold = any(re.search(p, text) for p in THRESHOLD_PATTERNS)
        if not has_threshold:
            warnings.append(f"{source}: W06 - user provided metrics ({', '.join(user_metrics[:3])}) but no target threshold found in verification")

    if profile == "diagnostic":
        facts_block = get_section_block(text, DIAGNOSTIC_MARKERS["current_facts"])
        hypotheses_block = get_section_block(text, DIAGNOSTIC_MARKERS["hypotheses"])
        if facts_block and hypotheses_block:
            if re.search(r"可能|待验证|猜测|假设", facts_block):
                warnings.append(f"{source}: W07 - current facts contains hypothesis language")

        iteration_block = get_section_block(text, COMMON_MARKERS["iteration"])
        if iteration_block:
            if not re.search(r"复现|重现|reproduce|先.*观察|先.*测量|先.*建立", iteration_block):
                warnings.append(f"{source}: W08 - Diagnostic Goal iteration strategy should start with reproduction/measurement")

    constraints_block = get_section_block(text, COMMON_MARKERS["constraints"])
    if constraints_block:
        if not re.search(r"不通过|不得|禁止|不.*规避|不.*屏蔽|不.*删除.*测试|不.*硬编码|anti-gaming|投机", constraints_block):
            warnings.append(f"{source}: W09 - constraints should include at least one anti-gaming prohibition")

    stop_block = get_section_block(text, COMMON_MARKERS["stop"])
    if stop_block:
        if re.search(r"继续直到完成|不要停下来|keep going|until done", stop_block, flags=re.IGNORECASE):
            errors.append(f"{source}: E04 - stop condition must not be 'continue until done'")

    return errors, warnings


def print_usage() -> None:
    print(f"""goal-generator linter v{VERSION}

Usage: lint_goal.py <file> [<file> ...]

Validates generated /goal contracts against the selected profile.
Auto-detects Standard vs Diagnostic profile.

Exit codes:
  0 = passed (no errors, warnings OK)
  1 = at least one error
  2 = usage error

Output format:
  <file>: EXX - <error message>     (structural failure)
  <file>: WXX - <warning message>    (advisory)

Limitations:
- STRUCTURAL checker, not a semantic judge.
- Warnings are advisory; errors are structural failures.
""")


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print_usage()
        return 2

    all_errors: list[str] = []
    all_warnings: list[str] = []

    for raw_path in argv[1:]:
        path = Path(raw_path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            all_errors.append(f"{path}: cannot read file: {exc}")
            continue
        errors, warnings = lint_text(text, str(path))
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    for warning in all_warnings:
        print(warning, file=sys.stderr)

    for error in all_errors:
        print(error, file=sys.stderr)

    if all_errors:
        print(f"\nFAILED: {len(all_errors)} error(s), {len(all_warnings)} warning(s)", file=sys.stderr)
        return 1

    if all_warnings:
        print(f"PASSED with {len(all_warnings)} warning(s).")
    else:
        print("PASSED: Goal contract lint passed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
