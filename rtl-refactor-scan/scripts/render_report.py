#!/usr/bin/env python3
"""从 findings.json 渲染 Markdown 审计报告。A/B/C 由 severity 派生（提案 §5.3）。"""
import json
from pathlib import Path

ABC_MAP = {"critical": "A", "high": "A", "medium": "B", "low": "C", "info": "C"}
ABC_ICON = {"A": "⚠️", "B": "🔶", "C": "🟢"}


def severity_to_abc(severity):
    return ABC_MAP.get(severity, "C")


def render_report(findings_data):
    findings = findings_data.get("findings", [])
    # 按 A/B/C 分组
    groups = {"A": [], "B": [], "C": []}
    for f in findings:
        abc = severity_to_abc(f["severity"])
        groups[abc].append(f)

    lines = ["# RTL 成熟度审计报告（由 findings.json 渲染）", ""]

    for abc in ["A", "B", "C"]:
        icon = ABC_ICON[abc]
        lines.append(f"## {icon} {abc} 类（severity 派生）")
        if not groups[abc]:
            lines.append("（无）")
            lines.append("")
            continue
        lines.append("")
        lines.append("| ID | 标题 | 位置 | severity | confidence | actionability |")
        lines.append("|----|------|------|----------|------------|---------------|")
        for f in groups[abc]:
            loc = f["locations"][0]
            pos = f"L{loc['start_line']}" if loc["start_line"] == loc["end_line"] else f"L{loc['start_line']}-L{loc['end_line']}"
            lines.append(
                f"| {f['finding_id']} | {f['title']} | {loc['file']}:{pos} | "
                f"{f['severity']} | {f['confidence']} | {f['actionability']} |"
            )
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(render_report(data))
