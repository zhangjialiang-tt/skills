# -*- coding: utf-8 -*-
"""rtl-readability readability_model.py (v2.2.0-rebuilt, per v2.1 design records).

Subcommands: check / compare / render / rank.
Three states: answered / implicit / undocumented.
exit 0=ok, 1=check failed, 2=usage error.
"""
import argparse
import json
import os
import re
import sys

PROBES = [
    ("HANDSHAKE", 1, "valid/ready 的来源与目的地"),
    ("HANDSHAKE", 2, "data_hold：输出在无新数据时是否保持"),
    ("HANDSHAKE", 3, "握手协议类型"),
    ("PROTOCOL", 4, "帧边界如何标定"),
    ("PROTOCOL", 5, "反压传播路径"),
    ("PROTOCOL", 6, "常量（超时/计数上限）"),
    ("TIMING", 7, "跨时钟域信号清单与同步方式"),
    ("TIMING", 8, "输出采样点"),
    ("FSM", 9, "状态机状态清单与转移条件"),
    ("FSM", 10, "异常态处理"),
    ("NAME", 11, "关键信号命名与含义"),
    ("NAME", 12, "缩写映射声明"),
    ("PARAM", 13, "参数默认值与约束范围"),
    ("ADDRESS_MAP", 14, "RO/RW/触发/位图门控/读覆盖/地址别名（寄存器文件类）"),
]


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def probe_state(source, dim):
    comments = "\n".join(re.findall(r"//[^\n]*", source))
    has_logic = bool(re.search(r"always|assign|module", source))
    kw = {
        "HANDSHAKE": r"valid|ready|握手",
        "PROTOCOL": r"帧|协议|包",
        "TIMING": r"时钟域|CDC|采样",
        "FSM": r"状态|state",
        "NAME": r"命名|含义",
        "PARAM": r"参数|parameter",
        "ADDRESS_MAP": r"寄存器|RO|RW|地址映射",
    }
    pattern = kw.get(dim) or r"$^"
    if re.search(pattern, comments, re.I):
        return "answered"
    if has_logic:
        return "implicit"
    return "undocumented"


def cmd_check(args):
    src = read_text(args.verilog)
    sheet = {"file": os.path.basename(args.verilog), "probes": []}
    seen = set()
    for dim, no, question in PROBES:
        if no in seen:
            continue
        seen.add(no)
        sheet["probes"].append({
            "no": no, "dim": dim, "question": question,
            "status": probe_state(src, dim),
            "default": "", "signals": [], "UNKNOWNS": [],
        })
    sheet["score"] = {
        "answered": sum(1 for p in sheet["probes"] if p["status"] == "answered"),
        "implicit": sum(1 for p in sheet["probes"] if p["status"] == "implicit"),
        "undocumented": sum(1 for p in sheet["probes"] if p["status"] == "undocumented"),
        "total": 14,
    }
    with open(args.sheet, "w", encoding="utf-8") as f:
        json.dump(sheet, f, ensure_ascii=False, indent=2)
    print("check: %s" % args.sheet)
    return 0


def cmd_compare(before, after):
    b = json.loads(read_text(before))
    a = json.loads(read_text(after))
    diff = []
    for pb, pa in zip(b.get("probes", []), a.get("probes", [])):
        for k in ("status", "default", "signals", "UNKNOWNS"):
            if pb.get(k) != pa.get(k):
                diff.append({"no": pb["no"], "field": k,
                             "before": pb.get(k), "after": pa.get(k)})
    print(json.dumps({"changed": len(diff), "diff": diff}, ensure_ascii=False, indent=2))
    return 0


def cmd_render(findings_path, out_path):
    data = json.loads(read_text(findings_path))
    lines = ["# 可读性报告_%s" % data.get("module", "?"), "", "## 1 速览",
             "verdict: %s" % data.get("verdict", "N/A"), "", "## 2 发现"]
    for f in data.get("findings", []):
        lines.append("- [%s] %s:%s %s" % (f.get("risk", "?"), f.get("file", "?"),
                                          f.get("line", "?"), f.get("msg", "")))
    lines.append("")
    lines.append("## 3 测卷")
    for p in data.get("probes", []):
        lines.append("- #%s %s: %s" % (p.get("no"), p.get("dim"), p.get("status")))
    g = data.get("gates", {})
    lines.append("")
    lines.append("## 4 门禁")
    lines.append("L0: %s / L1: %s / L2: %s" % (g.get("L0", "N/A"), g.get("L1", "N/A"), g.get("L2", "N/A")))
    lines.append("")
    lines.append("## 5 修复复验")
    lines.append(str(data.get("reverify", "（未记录修复复验）")))
    lines.append("")
    lines.append("## 6 遗留")
    lines.append(str(data.get("leftover", "（无）")))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("render: %s" % out_path)
    return 0


def cmd_rank(args):
    rows = []
    for p in args.sheets:
        s = json.loads(read_text(p))
        sc = s.get("score", {})
        rows.append((p, sc.get("answered", 0), sc.get("implicit", 0), sc.get("undocumented", 0)))
    for p, a, i, u in sorted(rows, key=lambda r: -r[1]):
        print("%-50s answered=%d implicit=%d undocumented=%d" % (p, a, i, u))
    return 0


def main():
    ap = argparse.ArgumentParser(description="readability_model rebuilt")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("check")
    p1.add_argument("verilog")
    p1.add_argument("--sheet", required=True)
    p1.set_defaults(func=cmd_check)
    p2 = sub.add_parser("compare")
    p2.add_argument("--facts", nargs=2, required=True, metavar=("BEFORE", "AFTER"))
    p2.set_defaults(func=lambda a: cmd_compare(a.facts[0], a.facts[1]))
    p3 = sub.add_parser("render")
    p3.add_argument("findings")
    p3.add_argument("--out", required=True)
    p3.set_defaults(func=lambda a: cmd_render(a.findings, a.out))
    p4 = sub.add_parser("rank")
    p4.add_argument("sheets", nargs="+")
    p4.set_defaults(func=cmd_rank)
    args = ap.parse_args()
    try:
        return args.func(args)
    except (OSError, json.JSONDecodeError) as e:
        print("ERROR: %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
