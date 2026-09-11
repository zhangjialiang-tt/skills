#!/usr/bin/env python3
"""Extract top-level module port declarations from RTL files."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path


# Matches a Verilog-2001 style port in a module header:
#   input wire [7:0] foo,
#   output reg bar,
#   input logic [3:0] baz
VERILOG_PORT_RE = re.compile(
    r"(?P<direction>input|output|inout)\s+"
    r"(?P<type>wire|reg|logic|bit|byte|int|integer|longint|shortint)?\s*"
    r"(?P<signed>signed)?\s*"
    r"(?:\[(?P<msb>[^:\]]+)\s*:\s*(?P<lsb>[^:\]]+)\])?\s*"
    r"(?P<name>[a-zA-Z_][a-zA-Z0-9_$]*)",
    re.MULTILINE,
)

# Matches VHDL port declaration:
#   port_name : in  std_logic;
#   port_name : out std_logic_vector(7 downto 0);
VHDL_PORT_RE = re.compile(
    r"(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*"
    r"(?P<direction>in|out|inout|buffer)\s+"
    r"(?P<type>[a-zA-Z_][a-zA-Z0-9_\s\(\)]*)",
    re.MULTILINE,
)

VERILOG_MODULE_RE = re.compile(
    r"\bmodule\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_$]*)\s*\("
)


def _eval_constant(expression: str) -> int | None:
    """Evaluate the small arithmetic expressions common in packed widths."""
    cleaned = re.sub(r"\s+", "", expression)
    if not re.fullmatch(r"[0-9()+*/-]+", cleaned):
        return None
    try:
        tree = ast.parse(cleaned, mode="eval")
    except SyntaxError:
        return None
    allowed = (ast.Expression, ast.Constant, ast.UnaryOp, ast.BinOp,
               ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
               ast.USub, ast.UAdd, ast.Load)
    if any(not isinstance(node, allowed) for node in ast.walk(tree)):
        return None
    try:
        value = eval(compile(tree, "<packed-width>", "eval"),
                     {"__builtins__": {}}, {})
    except (ArithmeticError, TypeError, ValueError):
        return None
    return value if isinstance(value, int) else int(value)


def _mask_comments(text: str) -> str:
    """Strip // and /* */ comments while preserving newlines."""
    result = []
    i = 0
    while i < len(text):
        if i + 1 < len(text) and text[i] == "/" and text[i + 1] == "/":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        if i + 1 < len(text) and text[i] == "/" and text[i + 1] == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                if text[i] == "\n":
                    result.append("\n")
                i += 1
            i += 2
            continue
        result.append(text[i])
        i += 1
    return "".join(result)


def _find_module_range(source: str, module_name: str) -> tuple[int, int] | None:
    """Find the start (module declaration) and end (endmatch) of a module."""
    name_pattern = re.compile(rf"\bmodule\s+{re.escape(module_name)}\b")
    name_match = name_pattern.search(source)
    if not name_match:
        return None
    # Find matching endmodule
    # Simple approach: find the next "endmodule" after the declaration
    end_match = re.search(r'\bendmodule\b', source[name_match.start():])
    if not end_match:
        return None
    end_pos = name_match.start() + end_match.end()
    return name_match.start(), end_pos


def _extract_verilog_ports(source: str, module_name: str) -> list[dict]:
    """Extract ports for a specific Verilog module.

    Supports two styles:
    - ANSI style: direction declared in the port list (e.g. input wire [7:0] foo)
    - Verilog-2001 style: port names in header, direction/width declared in body
      (e.g. module foo(clk, clk); ... input clk; output [7:0] bar;)
    """
    ports = []

    # Find the module declaration — name on its own, not requiring "(" on same line
    name_pattern = re.compile(rf"\bmodule\s+{re.escape(module_name)}\b")
    name_match = name_pattern.search(source)
    if not name_match:
        return ports

    # Skip past #(...) parameter list if present, then find the port list "("
    pos = name_match.end()
    # Skip optional #(...) parameter block
    hash_match = re.search(r"\s*#\s*\(", source[pos:])
    if hash_match:
        # Found #(, find matching )
        depth = 1
        i = pos + hash_match.end()
        while i < len(source) and depth > 0:
            if source[i] == "(":
                depth += 1
            elif source[i] == ")":
                depth -= 1
            i += 1
        pos = i

    # Now find the port list opening "("
    paren_match = re.search(r"\s*\(", source[pos:])
    if not paren_match:
        return ports
    port_start = pos + paren_match.end()

    # Find the port list closing ");"
    depth = 1
    i = port_start
    while i < len(source) and depth > 0:
        if source[i] == "(":
            depth += 1
        elif source[i] == ")":
            depth -= 1
            if depth == 0:
                break
        i += 1
    port_end = i

    port_list = source[port_start:port_end]
    masked = _mask_comments(port_list)

    # First pass: try ANSI-style extraction (direction in port list)
    ansi_ports = []
    for match in VERILOG_PORT_RE.finditer(masked):
        msb = match.group("msb")
        lsb = match.group("lsb")
        if msb and lsb:
            msb_s = msb.strip()
            lsb_s = lsb.strip()
            msb_value = _eval_constant(msb_s)
            lsb_value = _eval_constant(lsb_s)
            if msb_value is not None and lsb_value is not None:
                width = abs(msb_value - lsb_value) + 1
            else:
                normalized_msb = re.sub(r"\s+", "", msb_s)
                normalized_lsb = re.sub(r"\s+", "", lsb_s)
                width = f"{normalized_msb}:{normalized_lsb}"
        else:
            width = 1

        ansi_ports.append({
            "name": match.group("name"),
            "direction": match.group("direction"),
            "width": width,
            "signed": match.group("signed") is not None,
            "type": match.group("type") or "wire",
        })

    if ansi_ports:
        return ansi_ports

    # Second pass: Verilog-2001 style — port names in header, direction in body
    # Extract port names from the header port list
    port_names = [p.strip() for p in masked.split(",") if p.strip()]
    # Clean up: remove comments and extra whitespace
    cleaned_names = []
    for name in port_names:
        # Remove inline comments
        name = re.split(r'//', name)[0].strip()
        if name and re.match(r'^[a-zA-Z_][a-zA-Z0-9_$]*$', name):
            cleaned_names.append(name)

    if not cleaned_names:
        return ports

    # Now find direction/width declarations in the module body
    # Extract module body (after port list)
    module_end_match = re.search(r'\bendmodule\b', source[port_end:])
    if not module_end_match:
        return ports
    body = source[port_end:port_end + module_end_match.start()]
    body_masked = _mask_comments(body)

    # Pattern for body-style port declarations:
    #   input [msb:lsb] name;
    #   output reg [msb:lsb] name;
    #   input name;
    body_port_re = re.compile(
        r"(?P<direction>input|output|inout)\s+"
        r"(?P<type>wire|reg|logic|bit|byte|int|integer|longint|shortint)?\s*"
        r"(?P<signed>signed)?\s*"
        r"(?:\[(?P<msb>[^:\]]+)\s*:\s*(?P<lsb>[^:\]]+)\])?\s*"
        r"(?P<names>[a-zA-Z_][a-zA-Z0-9_$]*"
        r"(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_$]*)*)\s*;",
        re.MULTILINE,
    )

    # Build a map from port name to declaration info
    port_info = {}
    for match in body_port_re.finditer(body_masked):
        direction = match.group("direction")
        ptype = match.group("type") or "wire"
        signed = match.group("signed") is not None
        msb = match.group("msb")
        lsb = match.group("lsb")
        names_str = match.group("names")

        if msb and lsb:
            msb_s = msb.strip()
            lsb_s = lsb.strip()
            msb_value = _eval_constant(msb_s)
            lsb_value = _eval_constant(lsb_s)
            if msb_value is not None and lsb_value is not None:
                width = abs(msb_value - lsb_value) + 1
            else:
                normalized_msb = re.sub(r"\s+", "", msb_s)
                normalized_lsb = re.sub(r"\s+", "", lsb_s)
                width = f"{normalized_msb}:{normalized_lsb}"
        else:
            width = 1

        # Parse comma-separated names
        for name in re.split(r'\s*,\s*', names_str):
            name = name.strip()
            if name:
                port_info[name] = {
                    "direction": direction,
                    "width": width,
                    "signed": signed,
                    "type": ptype,
                }

    # Build final ports list in header order
    for name in cleaned_names:
        if name in port_info:
            info = port_info[name]
            ports.append({
                "name": name,
                "direction": info["direction"],
                "width": info["width"],
                "signed": info["signed"],
                "type": info["type"],
            })
        else:
            # Port name found in header but not declared in body — still include it
            ports.append({
                "name": name,
                "direction": "unknown",
                "width": 1,
                "signed": False,
                "type": "wire",
            })

    return ports


def _extract_ports_from_file(path: Path, module_name: str) -> list[dict]:
    """Read a file and extract ports for the given module name."""
    source = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()

    if suffix in (".v", ".sv"):
        return _extract_verilog_ports(source, module_name)
    return []


def find_module_file(roots: list[Path], module_name: str) -> Path | None:
    """Find the file containing a module definition."""
    pattern = re.compile(rf"\bmodule\s+{re.escape(module_name)}\b")
    for root in roots:
        for path in root.rglob("*"):
            if path.suffix.lower() in (".v", ".sv"):
                try:
                    if pattern.search(path.read_text(encoding="utf-8", errors="replace")):
                        return path
                except OSError:
                    continue
    return None


def extract_ports(roots: list[Path], module_name: str) -> list[dict]:
    """Main entry point: find module file and extract its ports."""
    module_file = find_module_file(roots, module_name)
    if module_file is None:
        return []
    return _extract_ports_from_file(module_file, module_name)


def _format_port_line(p: dict) -> str:
    """Format a single port dict as human-readable line."""
    w = p.get("width", 1)
    width_str = "[{}:0] ".format(w - 1) if isinstance(w, int) and w > 1 else ""
    signed_str = " signed" if p.get("signed") else ""
    direction = p.get("direction", "")
    ptype = p.get("type", "")
    name = p.get("name", "")
    return "  {:6s} {}{}{} {}".format(direction, ptype, signed_str, width_str, name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract top-level module ports from RTL files."
    )
    parser.add_argument(
        "--rtl-root", action="append", required=True,
        help="RTL root directory (repeat for multiple)"
    )
    parser.add_argument("--top", required=True, help="Top module name")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args(argv)

    roots = [Path(r) for r in args.rtl_root]
    ports = extract_ports(roots, args.top)

    if args.json:
        print(json.dumps(ports, ensure_ascii=False, indent=2))
    else:
        for p in ports:
            print(_format_port_line(p))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
