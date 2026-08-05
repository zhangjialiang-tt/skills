#!/usr/bin/env python3
"""rtl-refactor-scan v2.0 确定性审计引擎。
按 rules.yaml 的 deterministic 规则扫描 RTL 源码，输出 Finding（E2）。"""
import re


def _make_finding(rule_id, category, title, file_path, start_line, end_line,
                  severity, confidence, actionability, change_policy, description):
    return {
        "finding_id": None,  # 由调用方按序赋 id
        "rule_id": rule_id,
        "category": category,
        "title": title,
        "locations": [{"file": file_path, "start_line": start_line, "end_line": end_line}],
        "severity": severity,
        "confidence": confidence,
        "evidence_level": "E2",
        "evidence": [{"type": "deterministic_static", "description": description}],
        "actionability": actionability,
        "change_policy": change_policy,
    }


def detect_mixed_blocking(text, file_path):
    """SYN-MIXED-BLOCKING-001: 同一 posedge always 块内混用 = 和 <=。"""
    findings = []
    # 用 begin/end 深度配平提取完整的 always 块（处理嵌套 begin/end）
    always_starts = list(re.finditer(r"always\s*@\(\s*posedge\s+\w+\s*\)\s*begin", text))
    for start_match in always_starts:
        depth = 1
        i = start_match.end()
        block_start = i
        while i < len(text) and depth > 0:
            next_begin = text.find("begin", i)
            next_end = text.find("end", i)
            if next_end == -1:
                break
            if next_begin != -1 and next_begin < next_end:
                depth += 1
                i = next_begin + len("begin")
            else:
                depth -= 1
                i = next_end + len("end")
        block = text[block_start:i]
        has_blocking = bool(re.search(r"(\w+)\s*=[^=<>]", block))  # = 但非 == <= <=
        has_nonblocking = bool(re.search(r"<=", block))
        if has_blocking and has_nonblocking:
            start_line = text[:start_match.start()].count("\n") + 1
            end_line = text[:i].count("\n") + 1
            findings.append(_make_finding(
                "SYN-MIXED-BLOCKING-001", "synthesis",
                "同一 always @(posedge clk) 内混合 blocking/non-blocking",
                file_path, start_line, end_line,
                "critical", "confirmed", "plan_required", "requires_approval",
                f"always 块 L{start_line}-L{end_line} 内同时存在 = 和 <="
            ))
    return findings
