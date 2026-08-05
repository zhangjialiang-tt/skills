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


def _extract_always_blocks(text, clk_pattern):
    """提取匹配 clk_pattern 的所有 always 块（支持 begin/end 块和无 begin 的单行语句）。
    返回 [(block_text, start_line, end_line)]。"""
    blocks = []
    # 形式 1：always @(posedge CLK) begin ... end
    for start_match in re.finditer(
        r"always\s*@\(\s*posedge\s+" + clk_pattern + r"\s*\)\s*begin", text
    ):
        depth = 1
        i = start_match.end()
        while i < len(text) and depth > 0:
            nb = text.find("begin", i)
            ne = text.find("end", i)
            if ne == -1:
                break
            if nb != -1 and nb < ne:
                depth += 1
                i = nb + len("begin")
            else:
                depth -= 1
                i = ne + len("end")
        start_line = text[:start_match.start()].count("\n") + 1
        end_line = text[:i].count("\n") + 1
        blocks.append((text[start_match.end():i], start_line, end_line))
    # 形式 2：always @(posedge CLK) stmt; （无 begin，单行）
    for m in re.finditer(
        r"always\s*@\(\s*posedge\s+" + clk_pattern + r"\s*\)\s*([^\n]*?;)", text
    ):
        # 排除已被 begin 形式覆盖的
        if "begin" in m.group(0):
            continue
        start_line = text[:m.start()].count("\n") + 1
        end_line = text[:m.end()].count("\n") + 1
        blocks.append((m.group(1), start_line, end_line))
    return blocks


def detect_cdc_direct(text, file_path, context):
    """CDC-SINGLEBIT-DIRECT-001 / CDC-MULTIBIT-DIRECT-001。"""
    findings = []
    clocks = context.get("clocks", [])
    if len(clocks) < 2:
        return findings  # 单时钟域无 CDC

    clk_names = [c["name"] for c in clocks]

    # 先扫描所有 reg/wire 声明，建立信号位宽映射
    sig_widths = {}
    for decl in re.finditer(r"\b(?:reg|wire)\s*(?:\[(\d+):(\d+)\])?\s*(\w+(?:\s*,\s*\w+)*)", text):
        hi, lo = decl.group(1), decl.group(2)
        width = abs(int(hi) - int(lo)) + 1 if hi is not None else 1
        for name in decl.group(3).split(","):
            name = name.strip()
            if name and name not in sig_widths:
                sig_widths[name] = width

    # 对每个时钟域，提取该域 always 块中赋值的信号
    domain_assigns = {}  # clk -> {signal: {"line": int, "width": int}}
    for clk in clk_names:
        clk_pat = re.escape(clk)
        for block_text, block_start, _ in _extract_always_blocks(text, clk_pat):
            for am in re.finditer(r"(\w+(?:\s*\[[^\]]+\])?)\s*<=\s*([^;]+);", block_text):
                sig_full = am.group(1).strip()
                line = block_start + block_text[:am.start()].count("\n")
                base = re.sub(r"\s*\[.*?\]", "", sig_full).strip()
                # 位宽优先从声明查，其次从赋值处推断
                width_m = re.search(r"\[(\d+):0\]", sig_full)
                if width_m:
                    width = int(width_m.group(1)) + 1
                else:
                    width = sig_widths.get(base, 1)
                domain_assigns.setdefault(clk, {})[base] = {"line": line, "width": width}

    # 对每对时钟域，检查跨域读取
    for i, src_clk in enumerate(clk_names):
        for dst_clk in clk_names[i + 1:]:
            src_sigs = domain_assigns.get(src_clk, {})
            dst_blocks = _extract_always_blocks(text, re.escape(dst_clk))
            for block_text, block_start, _ in dst_blocks:
                for sig, info in src_sigs.items():
                    if sig in block_text:
                        # 检查是否有 2 级同步器（sync_a <= sig; sync_b <= sync_a）
                        if _has_synchronizer(block_text, sig):
                            continue
                        line = block_start + block_text.find(sig)
                        line = block_start + block_text[:block_text.find(sig)].count("\n")
                        width = info["width"]
                        rule_id = "CDC-MULTIBIT-DIRECT-001" if width > 1 else "CDC-SINGLEBIT-DIRECT-001"
                        desc = f"{'多 bit' if width > 1 else '单 bit'} 信号 {sig} 在 {src_clk} 赋值(L{info['line']})，在 {dst_clk} 域直接使用(L{line})，无同步器"
                        findings.append(_make_finding(
                            rule_id, "cdc",
                            f"{'多 bit' if width > 1 else '单 bit'} 信号 {sig} 直接跨时钟域 ({src_clk}→{dst_clk})",
                            file_path, line, line,
                            "critical", "confirmed", "manual_design_required", "do_not_auto_fix",
                            desc
                        ))
    return findings


def _has_synchronizer(block_text, signal):
    """简化判断：块内是否有 sync_a/sync_b 两级链引用该 signal。"""
    sync_chain = re.search(
        r"(\w+)\s*<=\s*" + re.escape(signal) + r"\s*;.*?\1\w*\s*<=\s*\1\s*;",
        block_text, re.DOTALL
    )
    return bool(sync_chain)


def detect_variable_part_select(text, file_path):
    """SYN-VARIABLE-PART-SELECT-001: data[idx*W +: W] 模式。"""
    findings = []
    # 匹配 variable part-select: name[expr +: width] 或 name[expr -: width]，其中 expr 含变量
    pattern = re.compile(r"(\w+)\s*\[(\s*\w+[^:\]]*\s*\+\s*:\s*\w+\s*)\]")
    for m in pattern.finditer(text):
        line = text[:m.start()].count("\n") + 1
        findings.append(_make_finding(
            "SYN-VARIABLE-PART-SELECT-001", "synthesis",
            "variable part-select 导致 EDA debug 不稳定",
            file_path, line, line,
            "medium", "probable", "plan_required", "requires_approval",
            f"L{line}: {m.group(0)}"
        ))
    return findings


def detect_latch(text, file_path):
    """SYN-LATCH-001: always @(*) 中 if 无 else。"""
    findings = []
    # 匹配 always @(*) begin ... end（组合块）
    for start_match in re.finditer(r"always\s*@\(\s*\*\s*\)\s*begin", text):
        depth = 1
        i = start_match.end()
        while i < len(text) and depth > 0:
            nb = text.find("begin", i)
            ne = text.find("end", i)
            if ne == -1:
                break
            if nb != -1 and nb < ne:
                depth += 1
                i = nb + len("begin")
            else:
                depth -= 1
                i = ne + len("end")
        block_text = text[start_match.end():ne] if ne != -1 else text[start_match.end():]
        start_line = text[:start_match.start()].count("\n") + 1
        end_line = text[:i].count("\n") + 1
        # 排除注释后检测 if/else
        code = re.sub(r"//[^\n]*", "", block_text)  # 去行注释
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)  # 去块注释
        has_if = bool(re.search(r"\bif\b", code))
        has_else = bool(re.search(r"\belse\b", code))
        if has_if and not has_else:
            findings.append(_make_finding(
                "SYN-LATCH-001", "synthesis",
                "always @(*) 分支不完整推断 latch",
                file_path, start_line, end_line,
                "high", "confirmed", "plan_required", "requires_approval",
                "combinational block has if without else"
            ))
    return findings


def detect_missing_reset(text, file_path):
    """RST-MISSING-001: posedge always 块无 if(!reset) 分支。"""
    findings = []
    # 用 _extract_always_blocks 匹配任意时钟的 posedge 块
    for block_text, start_line, end_line in _extract_always_blocks(text, r"\w+"):
        if "rst" not in block_text.lower() and "reset" not in block_text.lower():
            findings.append(_make_finding(
                "RST-MISSING-001", "reset", "关键路径寄存器缺复位",
                file_path, start_line, end_line,
                "high", "probable", "plan_required", "requires_approval",
                "sequential block has no reset branch"
            ))
    return findings


def detect_multi_driver(text, file_path):
    """SYN-MULTI-DRIVER-001: 同一 reg 被多个 always 块赋值。"""
    findings = []
    drivers = {}  # signal -> list of line
    # 用通用 always 提取（匹配所有 clock/comb 块）
    for block_text, block_start, _ in _extract_all_always_blocks(text):
        for am in re.finditer(r"(\w+)\s*<=?\s*", block_text):
            sig = am.group(1)
            # 跳过关键字和常见非赋值左值
            if sig in ("if", "else", "begin", "end", "for", "while", "case", "endcase"):
                continue
            line = block_start + block_text[:am.start()].count("\n")
            drivers.setdefault(sig, []).append(line)
    for sig, lines in drivers.items():
        if len(lines) > 1:
            findings.append(_make_finding(
                "SYN-MULTI-DRIVER-001", "synthesis", f"多 always 块驱动同一变量 {sig}",
                file_path, lines[0], lines[-1],
                "critical", "confirmed", "plan_required", "requires_approval",
                f"{sig} driven at lines {lines}"
            ))
    return findings


def _extract_all_always_blocks(text):
    """提取所有 always 块（begin/end 和单行），返回 [(block_text, start_line, end_line)]。"""
    blocks = []
    # 形式 1：always @(...) begin ... end
    for start_match in re.finditer(r"always\s*@\([^)]+\)\s*begin", text):
        depth = 1
        i = start_match.end()
        while i < len(text) and depth > 0:
            nb = text.find("begin", i)
            ne = text.find("end", i)
            if ne == -1:
                break
            if nb != -1 and nb < ne:
                depth += 1
                i = nb + len("begin")
            else:
                depth -= 1
                i = ne + len("end")
        start_line = text[:start_match.start()].count("\n") + 1
        end_line = text[:i].count("\n") + 1
        blocks.append((text[start_match.end():i], start_line, end_line))
    # 形式 2：always @(*) stmt; （无 begin，单行）
    for m in re.finditer(r"always\s*@\([^)]+\)\s*([^\n]*?;)", text):
        if "begin" in m.group(0):
            continue
        start_line = text[:m.start()].count("\n") + 1
        end_line = text[:m.end()].count("\n") + 1
        blocks.append((m.group(1), start_line, end_line))
    return blocks


def detect_unsupported_construct(text, file_path):
    """SYN-UNSUPPORTED-CONSTRUCT-001: initial / #delay / fork-join。"""
    findings = []
    for pat in [r"\binitial\b\s", r"#\d+\s", r"\bfork\b", r"\bjoin\b"]:
        for m in re.finditer(pat, text):
            line = text[:m.start()].count("\n") + 1
            findings.append(_make_finding(
                "SYN-UNSUPPORTED-CONSTRUCT-001", "synthesis",
                "不适合综合的写法",
                file_path, line, line,
                "high", "confirmed", "plan_required", "requires_approval",
                f"L{line}: {m.group(0).strip()}"
            ))
    return findings
