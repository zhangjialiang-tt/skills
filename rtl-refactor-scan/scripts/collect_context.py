#!/usr/bin/env python3
"""从 Verilog 源码提取 RTL 上下文（模块名、clocks、resets、文件列表）。
纯源码启发式（E1），不调用 EDA 工具。"""
import re
from pathlib import Path


def collect_context(verilog_files):
    """verilog_files: list[str] 路径。返回 rtl_context dict。"""
    files = []
    clocks = []
    resets = []
    top_module = None

    clock_pattern = re.compile(r"\binput\s+(?:wire\s+)?(clk\w*|clock\w*)\b", re.IGNORECASE)
    reset_pattern = re.compile(r"\binput\s+(?:wire\s+)?(rst\w*|reset\w*)\b", re.IGNORECASE)
    module_pattern = re.compile(r"^\s*module\s+(\w+)\s*\(", re.MULTILINE)

    for vf in verilog_files:
        text = Path(vf).read_text(encoding="utf-8", errors="replace")
        lang = "systemverilog" if vf.endswith((".sv", ".svh")) else "verilog-2001"
        files.append({"path": vf, "language": lang})

        for m in clock_pattern.finditer(text):
            name = m.group(1)
            if not any(c["name"] == name for c in clocks):
                clocks.append({"name": name, "domain": name})

        for m in reset_pattern.finditer(text):
            name = m.group(1)
            rtype = "async-low" if "n" in name.lower() else "sync-high"
            if not any(r["name"] == name for r in resets):
                resets.append({"name": name, "type": rtype})

        if top_module is None:
            mm = module_pattern.search(text)
            if mm:
                top_module = mm.group(1)

    return {
        "top_module": top_module,
        "files": files,
        "clocks": clocks,
        "resets": resets,
        "ports": [],
        "parameters": [],
        "testbench": None,
        "regression_command": None,
        "tool_availability": {},
        "user_confirmed_facts": [],
    }


if __name__ == "__main__":
    import sys
    ctx = collect_context(sys.argv[1:])
    import json
    print(json.dumps(ctx, ensure_ascii=False, indent=2))
