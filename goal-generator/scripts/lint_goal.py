#!/usr/bin/env python3
"""Lightweight static validation for goal-generator outputs.

This is a STRUCTURAL checker, not a semantic judge. It validates a generated
/goal contract against the canonical label grammar shared by SKILL.md's
published templates and detects: missing sections (including Outcome),
placeholders, dangerous vague instructions, over-wide boundaries,
fact/hypothesis confusion, missing anti-gaming constraints, and thin blocked
reports.

Design notes:
- One canonical label grammar drives BOTH marker detection and section parsing,
  so every label form SKILL.md publishes (plain Chinese ``验证：``, bilingual
  ``Verification（验证）：``, and bracketed ``【验收证据】``) is accepted and no
  section bleeds into the next.
- Outcome is a REQUIRED structural field for both profiles; it is never
  inferred by falling back into Current Facts.
- There is NO baseline->threshold coercion. A baseline-only goal (metric in
  facts, no numeric target in verification) is valid and must not fail. Target
  provenance (user goal / SLO / proposed-pending-confirmation / measure-first)
  is a semantic property checked manually, not by regex.
- Findings are errors (structural failure), warnings (advisory; promoted to
  errors under --strict), or infos (heuristic hints; NEVER promoted).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

VERSION = "2.0.3"

# ---------------------------------------------------------------------------
# Canonical label grammar
# ---------------------------------------------------------------------------
# Each logical section maps to the label aliases SKILL.md accepts. Within a
# section, list the most specific alias first so longer labels win the
# alternation (e.g. "verification evidence" before "verification"). The stop /
# pause alias sets are deliberately shared with the Diagnostic combined
# 【阻塞与停止】 block; Standard presence is checked with stricter, separate
# regexes further down.
SECTION_ALIASES: dict[str, list[str]] = {
    "outcome": ["期望结果", "outcome"],
    "current_facts": ["current facts", "当前事实"],
    "hypotheses": ["hypotheses", "待验证假设"],
    "verification": ["verification evidence", "verification", "验收证据", "验证"],
    "constraints": [
        "invariants / anti-gaming",
        "invariants",
        "anti-gaming",
        "constraints",
        "必须保持",
        "约束",
    ],
    "boundaries": ["work boundaries", "boundaries", "工作边界", "边界"],
    "iteration": ["experiment strategy", "iteration policy", "iteration", "实验策略", "迭代策略"],
    # 【阻塞与停止】 covers both stop and pause semantics for Diagnostic goals.
    "stop": ["blocked report", "stop when", "stop", "阻塞与停止", "完成条件", "停止条件"],
    "pause": ["pause if", "pause", "暂停条件", "阻塞与停止", "blocked report"],
}


def _build_section_pattern(aliases: list[str]) -> re.Pattern[str]:
    """Build one anchored pattern that matches any label form for a section.

    Accepts (optionally under a markdown heading):
      - bracket form:  【验收证据】 ...
      - label form:    Verification（验证）： ...   /   验证： ...
    Captures the inline remainder after the closing 】 or the colon.
    """
    escaped = sorted({re.escape(a) for a in aliases}, key=len, reverse=True)
    alts = "|".join(escaped)
    label = rf"(?:{alts})\s*(?:[（(][^）)]*[）)])?\s*[:：]"
    bracket = rf"【\s*(?:{alts})[^】]*】"
    return re.compile(
        rf"^\s*(?:#{{1,6}}\s*)?(?:{bracket}|{label})\s*(.*)$",
        re.IGNORECASE | re.MULTILINE,
    )


SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    key: _build_section_pattern(aliases) for key, aliases in SECTION_ALIASES.items()
}

# A line is a section start if it opens ANY known section (or is a markdown
# heading). This is what stops one section's block from bleeding into the next.
_ALL_ALIASES = sorted(
    {a for aliases in SECTION_ALIASES.values() for a in aliases},
    key=len,
    reverse=True,
)
_ALL_ALTS = "|".join(re.escape(a) for a in _ALL_ALIASES)
SECTION_START = re.compile(
    rf"^\s*(?:#{{1,6}}\s+|【\s*(?:{_ALL_ALTS})[^】]*】|(?:{_ALL_ALTS})\s*(?:[（(][^）)]*[）)])?\s*[:：])",
    re.IGNORECASE,
)

COMMAND_PATTERNS = [r"(?m)^\s*/goal\b"]
BAD_COMMAND_PATTERNS = [r"(?m)^\s*/目标\b"]

# Sections every goal must carry. Outcome is checked separately (it may be
# inline on the /goal line or a standalone section); stop/pause are checked
# with profile-specific rules.
STANDARD_REQUIRED = ["verification", "constraints", "boundaries", "iteration"]
DIAGNOSTIC_REQUIRED = STANDARD_REQUIRED + ["current_facts", "hypotheses"]

# Standard goals must name Stop and Pause with their OWN labels; a single
# "Blocked report" line must not silently satisfy both.
STD_STOP_PRESENT = re.compile(
    r"(?m)^\s*(?:#{1,6}\s*)?(?:stop when|完成条件|停止条件)\s*(?:[（(][^）)]*[）)])?\s*[:：]",
    re.IGNORECASE,
)
STD_PAUSE_PRESENT = re.compile(
    r"(?m)^\s*(?:#{1,6}\s*)?(?:pause if|暂停条件)\s*(?:[（(][^）)]*[）)])?\s*[:：]",
    re.IGNORECASE,
)

# Narrow placeholder detection: only template-style fill-ins, not markdown
# links ([x](y)), array indices (items[0]), or regex classes ([0-9]).
PLACEHOLDER_PATTERNS = [
    (
        r"\[(?:XXX|TBD|TODO[^\]]*|待[^\]]{0,6}|路径|模块[^\]]{0,4}|文件[^\]]{0,4}|"
        r"范围|数值|阈值|命令[^\]]*|内容|说明|描述|Outcome|outcome|"
        r"具体[^\]]*|哪些[^\]]*|需要[^\]]*|不能[^\]]*)\]",
        "bracket placeholder [XXX]",
    ),
    (r"\bTBD\b", "TBD"),
    (r"\bTODO\b", "TODO"),
    (r"<[^>]+>", "angle-bracket placeholder <XXX>"),
    (r"待补充", "待补充"),
    (r"待定", "待定"),
    (r"某某", "vague '某某'"),
    (r"某模块", "'某模块' is a placeholder"),
    (r"某路径", "'某路径' is a placeholder"),
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

# A constraint counts as anti-gaming only when it forbids a *speculative way of
# faking the metric*, not when it merely states an invariant. Plain "不修改公共
# API" is an invariant, not anti-gaming.
ANTI_GAMING_PATTERN = (
    r"不通过|不得通过|不得.*规避|不得.*屏蔽|不得.*删除.*测试|禁止.*规避|禁止.*屏蔽|"
    r"不.*虚标|不.*虚假|不.*硬编码|不.*截断|不.*跳过.*用例|不.*降低采样|anti-gaming|投机"
)

# Anti-gaming is only mandatory when the goal has something a speculator could
# game. Destructive operations require an explicit object so a plain invariant
# like "不删除现有功能" does not mark the whole goal gameable.
GAMEABLE_SIGNAL = re.compile(
    r"性能|延迟|延时|吞吐|响应时间|覆盖率|可靠性|成功率|错误率|召回|相关性|指标|配额|"
    r"删除数据|清理数据|清空|批量移除|删库|迁移生产|迁移数据|数据迁移|"
    r"\bmetric\b|\bcoverage\b|\blatency\b|\bthroughput\b|\breliability\b|"
    r"P\d{2}\b|\bfps\b|\bQPS\b|\bTPS\b|\d+\s*(?:ms|毫秒|秒|fps|例/|次/)",
    re.IGNORECASE,
)

# Keywords signalling a Diagnostic blocked report carries real blocking
# conditions and report content (used to reject one-liner stop conditions).
BLOCKED_REPORT_KEYWORDS = (
    "环境", "权限", "授权", "缺少", "缺失", "无法", "不可用", "冲突",
    "必须修改", "证据", "已尝试", "风险", "所需", "输入", "置信度", "报告", "路径",
)

_PUNCT_ONLY = {"", "，", "：", ":", "。", "."}


def has_section(text: str, key: str) -> bool:
    return SECTION_PATTERNS[key].search(text) is not None


def classify_profile(text: str) -> str:
    if (
        has_section(text, "current_facts")
        or has_section(text, "hypotheses")
        or re.search(r"待验证假设|当前事实|Current facts|Hypotheses", text)
    ):
        return "diagnostic"
    return "standard"


def get_section_block(text: str, key: str) -> str:
    """Return the text under a section header, up to the next section header.

    Because every canonical label is recognised as a section start, a Standard
    goal's ``验证：`` block no longer swallows Constraints/Boundaries/Stop/Pause.
    """
    pat = SECTION_PATTERNS[key]
    lines = text.splitlines()
    block: list[str] = []
    in_section = False
    for line in lines:
        if in_section:
            if SECTION_START.match(line):
                break
            block.append(line)
            continue
        m = pat.match(line)
        if m:
            remainder = m.group(1).strip()
            if remainder:
                block.append(remainder)
            in_section = True
    return "\n".join(block).strip()


def find_outcome(text: str) -> str | None:
    """Return the Outcome: inline text after /goal, else the Outcome section.

    Deliberately does NOT fall back into Current Facts: an empty 【期望结果】
    header yields no outcome rather than borrowing the first fact.
    """
    for line in text.splitlines():
        if "/goal" in line:
            after = line[line.find("/goal") + 5 :].strip()
            if after and after not in _PUNCT_ONLY:
                return after
            break
    block = get_section_block(text, "outcome").strip()
    return block or None


def _emit(strict: bool, errors: list[str], warnings: list[str], msg: str) -> None:
    """Route an advisory finding; strict mode promotes it to an error."""
    if strict:
        errors.append(msg)
    else:
        warnings.append(msg)


def _gameable_scope(text: str) -> str:
    """Text searched for gameable signals: outcome + verification + facts only.

    Constraints/Boundaries/Stop are excluded so a negated invariant such as
    "不删除现有功能" cannot mark the whole goal gameable.
    """
    parts = []
    outcome = find_outcome(text)
    if outcome:
        parts.append(outcome)
    parts.append(get_section_block(text, "verification"))
    parts.append(get_section_block(text, "current_facts"))
    return "\n".join(parts)


def lint_text(
    text: str, source: str, strict: bool = False
) -> tuple[list[str], list[str], list[str]]:
    """Returns (errors, warnings, infos). Infos are never promoted by --strict."""
    errors: list[str] = []
    warnings: list[str] = []
    infos: list[str] = []

    profile = classify_profile(text)

    if any(re.search(p, text) for p in BAD_COMMAND_PATTERNS):
        errors.append(f"{source}: E01 - use /goal, not /目标, as the executable command")
    elif not any(re.search(p, text) for p in COMMAND_PATTERNS):
        errors.append(f"{source}: E02 - missing /goal command marker")

    # --- Outcome is required and must not be empty ---
    outcome_text = find_outcome(text)
    if not outcome_text:
        errors.append(
            f"{source}: E07 - missing or empty Outcome "
            f"(inline after /goal, or an Outcome（期望结果） / 【期望结果】 section)"
        )
    elif len(outcome_text) < 15:
        infos.append(f"{source}: I01 - /goal outcome is very short ({len(outcome_text)} chars)")

    # --- Required section markers ---
    required = DIAGNOSTIC_REQUIRED if profile == "diagnostic" else STANDARD_REQUIRED
    for name in required:
        if not has_section(text, name):
            examples = " / ".join(SECTION_ALIASES[name][:3])
            errors.append(f"{source}: E03 - missing required section `{name}` (e.g., {examples}：)")

    # --- Stop and Pause: profile-specific presence ---
    if profile == "standard":
        if not STD_STOP_PRESENT.search(text):
            errors.append(f"{source}: E05 - Standard goal needs a stop condition (完成条件 / Stop when)")
        if not STD_PAUSE_PRESENT.search(text):
            errors.append(f"{source}: E06 - Standard goal needs a pause condition (暂停条件 / Pause if)")
    else:
        if not has_section(text, "stop"):
            errors.append(f"{source}: E05 - missing stop condition (完成条件 / Stop when / 【阻塞与停止】)")
        if not has_section(text, "pause"):
            errors.append(f"{source}: E06 - missing pause condition (暂停条件 / Pause if / 【阻塞与停止】)")

    # --- Placeholders ---
    for pattern, desc in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            _emit(strict, errors, warnings, f"{source}: W01 - unresolved placeholder: {desc}")

    # --- Dangerous vague instructions ---
    for pattern, desc in DANGEROUS_VAGUE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            _emit(strict, errors, warnings, f"{source}: W02 - dangerous vague instruction: '{desc}'")

    # --- Verification names concrete evidence (section-isolated) ---
    verification_block = get_section_block(text, "verification")
    if verification_block and not any(
        re.search(p, verification_block, flags=re.IGNORECASE) for p in VERIFICATION_EVIDENCE_PATTERNS
    ):
        _emit(strict, errors, warnings, f"{source}: W04 - verification section should name concrete evidence")

    # --- Over-wide boundaries (section-isolated) ---
    boundary_block = get_section_block(text, "boundaries")
    if boundary_block:
        for pattern, desc in OVERWIDE_BOUNDARY_PATTERNS:
            if re.search(pattern, boundary_block):
                _emit(strict, errors, warnings, f"{source}: W05 - over-wide boundary: {desc}")

    # NOTE: there is intentionally NO baseline->threshold check. A baseline-only
    # goal is valid; fabricating a numeric target to satisfy a checker is exactly
    # the failure mode this skill forbids. Target provenance is a manual gate.

    # --- Diagnostic-only checks ---
    if profile == "diagnostic":
        facts_block = get_section_block(text, "current_facts")
        if facts_block and re.search(r"可能|待验证|猜测|假设", facts_block):
            _emit(strict, errors, warnings, f"{source}: W07 - current facts contains hypothesis language")

        iteration_block = get_section_block(text, "iteration")
        if iteration_block and not re.search(
            r"复现|重现|reproduce|先.*观察|先.*测量|先.*建立", iteration_block
        ):
            _emit(
                strict,
                errors,
                warnings,
                f"{source}: W08 - Diagnostic iteration strategy should start with reproduction/measurement",
            )

        # Blocked report must carry real blocking conditions + report content,
        # not a one-liner like "遇到问题时停止".
        blocked_block = get_section_block(text, "stop")
        if blocked_block:
            list_items = len(re.findall(r"(?m)^\s*(?:-\s+|\*\s+|\d+\s*[.)、])", blocked_block))
            keyword_hits = sum(1 for kw in BLOCKED_REPORT_KEYWORDS if kw in blocked_block)
            if list_items < 3 and keyword_hits < 3:
                _emit(
                    strict,
                    errors,
                    warnings,
                    f"{source}: W10 - Diagnostic blocked report is too thin "
                    f"(list >=3 blocking conditions or report fields)",
                )

    # --- Anti-gaming constraint (distinct from plain invariants) ---
    # Only mandatory when the gameable scope (outcome/verification/facts) has a
    # gameable metric or destructive op.
    constraints_block = get_section_block(text, "constraints")
    if (
        constraints_block
        and GAMEABLE_SIGNAL.search(_gameable_scope(text))
        and not re.search(ANTI_GAMING_PATTERN, constraints_block)
    ):
        _emit(
            strict,
            errors,
            warnings,
            f"{source}: W09 - gameable goal should forbid a speculative way of faking the metric (anti-gaming), not only state invariants",
        )

    # --- Stop condition must not be "continue until done" ---
    stop_block = get_section_block(text, "stop")
    if stop_block and re.search(r"继续直到完成|不要停下来|keep going|until done", stop_block, flags=re.IGNORECASE):
        errors.append(f"{source}: E04 - stop condition must not be 'continue until done'")

    return errors, warnings, infos


def print_usage() -> None:
    print(f"""goal-generator linter v{VERSION}

Usage: lint_goal.py [--strict] <file> [<file> ...]

Validates generated /goal contracts against the canonical label grammar.
Auto-detects Standard vs Diagnostic profile. Accepts plain Chinese labels
(验证：), bilingual labels (Verification（验证）：), and bracket labels (【验收证据】).
Outcome is required for both profiles.

Options:
  --strict    Treat warnings (Wxx) as errors. Infos (Ixx) are never promoted.
  -h, --help  Show this help and exit

Exit codes:
  0 = passed (no errors; warnings/infos OK in default mode) or help shown
  1 = at least one error
  2 = usage error (no input files)

Output format:
  <file>: EXX - <error message>     (structural failure)
  <file>: WXX - <warning message>    (advisory; promoted to error under --strict)
  <file>: IXX - <info message>       (heuristic hint; never promoted)

Limitations:
- STRUCTURAL checker, not a semantic judge.
- Does not coerce a baseline into a target threshold; target provenance
  (user goal / SLO / proposed-pending-confirmation) is a manual review gate.
""")


def main(argv: list[str]) -> int:
    args = list(argv[1:])
    strict = False
    if "--strict" in args:
        strict = True
        args.remove("--strict")

    if "-h" in args or "--help" in args:
        print_usage()
        return 0

    if not args:
        print_usage()
        return 2

    all_errors: list[str] = []
    all_warnings: list[str] = []
    all_infos: list[str] = []

    for raw_path in args:
        path = Path(raw_path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            all_errors.append(f"{path}: cannot read file: {exc}")
            continue
        errors, warnings, infos = lint_text(text, str(path), strict=strict)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
        all_infos.extend(infos)

    for info in all_infos:
        print(info, file=sys.stderr)
    for warning in all_warnings:
        print(warning, file=sys.stderr)
    for error in all_errors:
        print(error, file=sys.stderr)

    if all_errors:
        print(
            f"\nFAILED: {len(all_errors)} error(s), {len(all_warnings)} warning(s), {len(all_infos)} info(s)",
            file=sys.stderr,
        )
        return 1

    if all_warnings:
        print(f"PASSED with {len(all_warnings)} warning(s), {len(all_infos)} info(s).")
    else:
        print(f"PASSED: Goal contract lint passed ({len(all_infos)} info(s)).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
