#!/usr/bin/env python3
"""Recursively scan Verilog/SystemVerilog and VHDL RTL declarations."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable


SUPPORTED_EXTENSIONS = {
    ".v": "verilog",
    ".sv": "systemverilog",
    ".vhd": "vhdl",
    ".vhdl": "vhdl",
}

VERILOG_MODULE_RE = re.compile(
    r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)", re.MULTILINE
)
VHDL_ENTITY_RE = re.compile(
    r"\bentity\s+([A-Za-z_][A-Za-z0-9_]*)\s+is\b",
    re.IGNORECASE | re.MULTILINE,
)


def _normalize_relative_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _failure_result(root: Path, diagnostic: str) -> dict:
    return {
        "schema_version": "1.0",
        "root": root.as_posix(),
        "status": "FAILED",
        "files": [],
        "diagnostics": [diagnostic],
        "summary": {
            "files_scanned": 0,
            "rtl_files": 0,
            "files_with_modules": 0,
            "modules_found": 0,
        },
    }


def _mask_comments_and_strings(text: str, language: str) -> str:
    """Mask comments and quoted strings while preserving newline positions."""
    masked = list(text)
    verilog = language in {"verilog", "systemverilog"}
    state = "normal"
    index = 0

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if state == "normal":
            if verilog and char == "/" and next_char == "/":
                masked[index] = " "
                masked[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if verilog and char == "/" and next_char == "*":
                masked[index] = " "
                masked[index + 1] = " "
                index += 2
                state = "block_comment"
                continue
            if not verilog and char == "-" and next_char == "-":
                masked[index] = " "
                masked[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if char == '"':
                masked[index] = " "
                index += 1
                state = "string"
                continue
            index += 1
            continue

        if state == "line_comment":
            if char == "\n":
                state = "normal"
            else:
                masked[index] = " "
            index += 1
            continue

        if state == "block_comment":
            if char == "*" and next_char == "/":
                masked[index] = " "
                masked[index + 1] = " "
                index += 2
                state = "normal"
            else:
                if char != "\n":
                    masked[index] = " "
                index += 1
            continue

        # Quoted string. Newlines are retained for stable source locations.
        if char == "\n":
            index += 1
            continue
        if verilog and char == "\\" and index + 1 < len(text):
            masked[index] = " "
            if text[index + 1] != "\n":
                masked[index + 1] = " "
            index += 2
            continue
        if not verilog and char == '"' and next_char == '"':
            masked[index] = " "
            masked[index + 1] = " "
            index += 2
            continue
        masked[index] = " "
        index += 1
        if char == '"':
            state = "normal"

    return "".join(masked)


def _extract_declarations(text: str, language: str) -> list[dict]:
    masked = _mask_comments_and_strings(text, language)
    pattern = VHDL_ENTITY_RE if language == "vhdl" else VERILOG_MODULE_RE
    kind = "entity" if language == "vhdl" else "module"
    declarations = []

    for match in pattern.finditer(masked):
        declarations.append(
            {
                "name": match.group(1),
                "kind": kind,
                "line": masked.count("\n", 0, match.start()) + 1,
            }
        )

    return declarations


def _iter_files(root: Path) -> Iterable[Path]:
    return sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )


def _scan_single_root(root: Path) -> dict:
    """Scan one root directory and return per-root scan result."""
    root = Path(root).resolve()
    if not root.exists():
        return _failure_result(root, f"root path does not exist: {root}")
    if not root.is_dir():
        return _failure_result(root, f"root path is not a directory: {root}")

    try:
        all_files = list(_iter_files(root))
    except OSError as exc:
        return _failure_result(root, f"failed to scan root directory {root}: {exc}")

    rtl_files = [path for path in all_files if path.suffix.lower() in SUPPORTED_EXTENSIONS]
    files = []

    for path in rtl_files:
        language = SUPPORTED_EXTENSIONS[path.suffix.lower()]
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeError) as exc:
            result = _failure_result(root, f"failed to read RTL file {path}: {exc}")
            result["files"] = files
            result["summary"] = {
                "files_scanned": len(all_files),
                "rtl_files": len(rtl_files),
                "files_with_modules": sum(bool(item["modules"]) for item in files),
                "modules_found": sum(len(item["modules"]) for item in files),
            }
            return result

        relative_path = path.relative_to(root).as_posix()
        files.append(
            {
                "path": relative_path,
                "language": language,
                "modules": _extract_declarations(source, language),
            }
        )

    modules_found = sum(len(item["modules"]) for item in files)
    return {
        "status": "SUCCESS",
        "root": root.as_posix(),
        "files": files,
        "diagnostics": [],
        "summary": {
            "files_scanned": len(all_files),
            "rtl_files": len(rtl_files),
            "files_with_modules": sum(bool(item["modules"]) for item in files),
            "modules_found": modules_found,
        },
    }


def scan_rtl(root: Path) -> dict:
    """Scan a directory recursively and return structured RTL declarations."""
    result = _scan_single_root(root)
    result["schema_version"] = "1.0"
    return result


def scan_multi_roots(roots: list[Path]) -> dict:
    """Scan multiple root directories, merge results with per-file root_index."""
    if not roots:
        return _failure_result(Path("."), "no root directories provided")

    resolved_roots = [Path(r).resolve() for r in roots]
    all_files: list[dict] = []
    all_diagnostics: list[str] = []
    seen_paths: set[str] = set()
    total_scanned = 0
    total_rtl = 0
    total_modules = 0
    has_success = False

    for root_index, root in enumerate(resolved_roots):
        per_root = _scan_single_root(root)
        all_diagnostics.extend(per_root.get("diagnostics", []))
        summary = per_root.get("summary", {})
        total_scanned += summary.get("files_scanned", 0)
        total_rtl += summary.get("rtl_files", 0)
        total_modules += summary.get("modules_found", 0)

        if per_root["status"] == "SUCCESS":
            has_success = True

        for file_result in per_root.get("files", []):
            path = _normalize_relative_path(file_result["path"])
            # First-match-wins: skip duplicates from later roots.
            if path in seen_paths:
                continue
            seen_paths.add(path)
            merged = dict(file_result)
            merged["root_index"] = root_index
            all_files.append(merged)

    if not has_success:
        result = _failure_result(resolved_roots[0], "all root directories failed to scan")
        result["roots"] = [str(r) for r in resolved_roots]
        result["diagnostics"] = all_diagnostics
        return result

    return {
        "schema_version": "1.1",
        "roots": [str(r) for r in resolved_roots],
        "status": "SUCCESS",
        "files": all_files,
        "diagnostics": all_diagnostics,
        "summary": {
            "files_scanned": total_scanned,
            "rtl_files": total_rtl,
            "files_with_modules": sum(bool(item["modules"]) for item in all_files),
            "modules_found": total_modules,
        },
    }


def _print_text(result: dict) -> None:
    if result["status"] == "FAILED":
        for diagnostic in result["diagnostics"]:
            print(f"ERROR: {diagnostic}", file=sys.stderr)
        return

    for file_result in result["files"]:
        for declaration in file_result["modules"]:
            print(
                f"{file_result['path']}:{declaration['line']} "
                f"{declaration['kind']} {declaration['name']}"
            )
    summary = result["summary"]
    print(
        "Scanned "
        f"{summary['rtl_files']} RTL file(s), "
        f"found {summary['modules_found']} module/entity declaration(s)."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recursively scan RTL files and report module/entity names."
    )
    parser.add_argument(
        "root", nargs="+", help="Directory to scan recursively (one or more)"
    )
    parser.add_argument("--json", action="store_true", help="Emit one JSON result object")
    args = parser.parse_args(argv)

    if len(args.root) == 1:
        result = scan_rtl(Path(args.root[0]))
    else:
        result = scan_multi_roots([Path(r) for r in args.root])
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)

    return 0 if result["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
