#!/usr/bin/env python3
"""Resolve RTL module/entity dependencies and write a simulator fileset."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Iterable

try:
    from .scan_rtl_modules import (
        _mask_comments_and_strings,
        scan_multi_roots,
        scan_rtl,
    )
except ImportError:  # Direct execution: tools/rtl is on sys.path.
    from scan_rtl_modules import _mask_comments_and_strings, scan_multi_roots, scan_rtl


VERILOG_DECL_RE = re.compile(
    r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)", re.MULTILINE
)
VHDL_DECL_RE = re.compile(
    r"\bentity\s+([A-Za-z_][A-Za-z0-9_]*)\s+is\b",
    re.IGNORECASE | re.MULTILINE,
)

IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")
VHDL_ENTITY_RE = re.compile(
    r"\bentity\s+(?:(?:[A-Za-z_][A-Za-z0-9_]*)\s*\.\s*)?"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
VHDL_COMPONENT_RE = re.compile(
    r":\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+port\s+map\b",
    re.IGNORECASE,
)

VERILOG_KEYWORDS = {
    "always",
    "always_comb",
    "always_ff",
    "always_latch",
    "and",
    "assign",
    "automatic",
    "begin",
    "buf",
    "case",
    "casez",
    "casex",
    "checker",
    "class",
    "default",
    "disable",
    "else",
    "end",
    "endcase",
    "endgenerate",
    "endfunction",
    "endmodule",
    "endtask",
    "for",
    "forever",
    "fork",
    "function",
    "generate",
    "genvar",
    "ifdef",
    "ifndef",
    "elsif",
    "endif",
    "define",
    "undef",
    "include",
    "timescale",
    "default_nettype",
    "resetall",
    "if",
    "initial",
    "inout",
    "input",
    "interface",
    "join",
    "join_any",
    "join_none",
    "localparam",
    "logic",
    "macromodule",
    "module",
    "nand",
    "negedge",
    "nor",
    "not",
    "or",
    "output",
    "parameter",
    "posedge",
    "program",
    "property",
    "reg",
    "repeat",
    "return",
    "sequence",
    "signed",
    "task",
    "tri",
    "typedef",
    "uwire",
    "wait",
    "wire",
    "while",
    "xnor",
    "xor",
}


def _get_file_root_dir(scan_result: dict, file_result: dict) -> Path:
    """Return the root directory for a file entry in a scan result."""
    root_index = file_result.get("root_index")
    if root_index is not None:
        roots = scan_result.get("roots", [])
        if 0 <= root_index < len(roots):
            return Path(roots[root_index])
    return Path(scan_result.get("root", "."))


def _normalize_name(name: str) -> str:
    return name.casefold()


def _normalize_relative_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _skip_whitespace(text: str, position: int) -> int:
    while position < len(text) and text[position].isspace():
        position += 1
    return position


def _consume_parentheses(text: str, position: int) -> int | None:
    if position >= len(text) or text[position] != "(":
        return None

    depth = 0
    for index in range(position, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    return None


def _collect_generate_labels(masked: str) -> set[str]:
    """Collect label names from generate blocks to filter false-positive candidates."""
    labels: set[str] = set()
    # begin : label (including inside generate / for)
    for m in re.finditer(r"\bbegin\s*:\s*(\w+)", masked):
        labels.add(m.group(1))
    # for (...) begin : label
    for m in re.finditer(r"\bfor\s*\([^)]*\)\s*begin\s*:\s*(\w+)", masked):
        labels.add(m.group(1))
    return labels


def _consume_delay(text: str, position: int) -> int:
    """Consume a Verilog delay like #1, #0.5 after '#' was already consumed."""
    while position < len(text) and (text[position].isdigit() or text[position] == "."):
        position += 1
    return position


def _extract_verilog_candidates(source: str) -> set[str]:
    masked = _mask_comments_and_strings(source, "systemverilog")
    candidates: set[str] = set()
    generate_labels = _collect_generate_labels(masked)

    for match in IDENTIFIER_RE.finditer(masked):
        type_name = match.group(0)
        if type_name.casefold() in VERILOG_KEYWORDS:
            continue
        # F1: filter generate block labels (e.g. "begin : g_data_array_gen")
        if type_name in generate_labels:
            continue

        position = _skip_whitespace(masked, match.end())
        if position < len(masked) and masked[position] == "#":
            position = _skip_whitespace(masked, position + 1)
            if position < len(masked) and masked[position] == "(":
                # F2: parameter override #(...)
                consumed = _consume_parentheses(masked, position)
                if consumed is None:
                    continue
                position = _skip_whitespace(masked, consumed)
            else:
                # F2: delay #1 / #0.5
                position = _consume_delay(masked, position)
                position = _skip_whitespace(masked, position)

        instance = IDENTIFIER_RE.match(masked, position)
        if instance is None:
            continue
        position = _skip_whitespace(masked, instance.end())
        if position < len(masked) and masked[position] == "(":
            candidates.add(type_name)

    return candidates


def _extract_vhdl_candidates(source: str) -> set[str]:
    masked = _mask_comments_and_strings(source, "vhdl")
    candidates: set[str] = set()

    for match in VHDL_ENTITY_RE.finditer(masked):
        name = match.group("name")
        after_name = _skip_whitespace(masked, match.end())
        if masked[after_name : after_name + 2].casefold() == "is":
            continue
        candidates.add(name)

    for match in VHDL_COMPONENT_RE.finditer(masked):
        candidates.add(match.group("name"))

    return candidates


def _failure_result(root: Path, output: str, diagnostics: Iterable[str]) -> dict:
    return {
        "schema_version": "1.0",
        "status": "FAILED",
        "root": root.as_posix(),
        "top": None,
        "dependencies": [],
        "fileset": [],
        "output": output,
        "diagnostics": list(diagnostics),
        "summary": {
            "modules_in_closure": 0,
            "files_in_closure": 0,
            "unresolved_dependencies": 0,
        },
    }


def _build_indexes(scan_result: dict) -> tuple[dict, dict]:
    by_name: dict[str, list[dict]] = {}
    by_path: dict[str, dict] = {}

    for file_result in scan_result.get("files", []):
        path = file_result["path"]
        by_path[_normalize_relative_path(path)] = file_result
        root_index = file_result.get("root_index")
        for declaration in file_result.get("modules", []):
            record = {
                "name": declaration["name"],
                "kind": declaration["kind"],
                "path": path,
                "language": file_result["language"],
            }
            if root_index is not None:
                record["root_index"] = root_index
            by_name.setdefault(_normalize_name(record["name"]), []).append(record)

    return by_name, by_path


def _filter_matches_by_root_priority(
    matches: list[dict],
) -> list[dict]:
    """Prefer matches from the lowest root_index (highest-priority root)."""
    min_root_index = None
    for m in matches:
        ri = m.get("root_index", 0)
        if min_root_index is None or ri < min_root_index:
            min_root_index = ri
    if min_root_index is None:
        return matches
    filtered = [m for m in matches if m.get("root_index", 0) == min_root_index]
    return filtered if filtered else matches


_PATH_PRIORITY_KEYWORDS = (
    "efinity_basic_lib/",
    "guideir_ptic/",
    "basicmodule/",
    "ip/",
    "lib/",
    "/rtl/",
    "common/",
    "basic_module/",
)
_PATH_DEPRIORITIZE_KEYWORDS = (
    "/archive/",
    "/debug/",
    "/temp/",
    "/sim/",
    "/test/",
    "/backup/",
    "/.worktrees/",
)


def _filter_matches_by_path_priority(matches: list[dict]) -> list[dict]:
    """Prefer production code paths (ip/, lib/, rtl/) over debug/temp paths."""
    def path_score(m: dict) -> int:
        path = m.get("path", "").lower()
        for kw in _PATH_DEPRIORITIZE_KEYWORDS:
            if kw in path:
                return 1
        for index, kw in enumerate(_PATH_PRIORITY_KEYWORDS):
            if kw in path:
                return len(_PATH_PRIORITY_KEYWORDS) - index + 3
        return 2

    max_score = max((path_score(m) for m in matches), default=0)
    if max_score <= 1:
        return matches
    filtered = [m for m in matches if path_score(m) == max_score]
    if not filtered:
        return matches
    # 同分平局时优先最短相对路径：规范 IP 布局 ip/<name>/<name>.v 优于
    # 其 devkit/Testbench 变体（位于更深子目录）
    min_len = min(len(m.get("path", "")) for m in filtered)
    shortest = [m for m in filtered if len(m.get("path", "")) == min_len]
    return shortest if shortest else filtered


def _language_group_suffixes(language: str) -> tuple[str, ...]:
    """Return file suffixes that belong to a given HDL language."""
    if language == "vhdl":
        return (".vhd", ".vhdl")
    if language in ("verilog", "systemverilog"):
        return (".v", ".sv")
    return ()


def _filter_matches_by_language(
    matches: list[dict], language: str
) -> list[dict]:
    """Prefer matches whose file suffix matches the source language."""
    suffixes = _language_group_suffixes(language)
    if not suffixes:
        return matches
    same_lang = [m for m in matches if m["path"].lower().endswith(suffixes)]
    return same_lang if same_lang else matches


def _filter_matches_by_path_proximity(
    matches: list[dict], anchor_path: str
) -> list[dict]:
    """Prefer candidates under the same project/version path as the caller."""
    anchor_parts = _normalize_relative_path(anchor_path).split("/")

    def common_prefix_length(match: dict) -> int:
        candidate_parts = _normalize_relative_path(match.get("path", "")).split("/")
        length = 0
        for left, right in zip(anchor_parts, candidate_parts):
            if left.casefold() != right.casefold():
                break
            length += 1
        return length

    scores = {id(match): common_prefix_length(match) for match in matches}
    max_score = max(scores.values(), default=0)
    # One shared component (for example AlgorithmModule/) is too weak: broad
    # workspace scans commonly contain several sibling projects. Require at
    # least a project/version-level match before selecting by proximity.
    if max_score < 2:
        return matches
    filtered = [match for match in matches if scores[id(match)] == max_score]
    return filtered if filtered else matches


def _filter_byte_identical_matches(
    matches: list[dict], sources: dict[str, str]
) -> list[dict]:
    """Collapse duplicate declarations whose complete source files are identical."""
    if len(matches) < 2:
        return matches
    fingerprints = {
        hashlib.sha256(sources[match["path"]].encode("utf-8")).hexdigest()
        for match in matches
        if match["path"] in sources
    }
    available_matches = [match for match in matches if match["path"] in sources]
    if len(fingerprints) != 1 or len(available_matches) != len(matches):
        return matches
    return [sorted(matches, key=lambda match: match["path"])[0]]


def _resolve_top(
    scan_result: dict, top_arg: str, by_name: dict, by_path: dict
) -> tuple[dict | None, str | None]:
    normalized_arg = _normalize_relative_path(top_arg)
    file_result = by_path.get(normalized_arg)

    if file_result is None:
        candidate = Path(top_arg)
        roots = scan_result.get("roots")
        if roots is not None:
            # Try each root to resolve an absolute or relative path.
            resolved_relatives: list[str] = []
            for root_str in roots:
                root = Path(root_str)
                if candidate.is_absolute():
                    try:
                        resolved_relatives.append(
                            candidate.resolve().relative_to(root.resolve()).as_posix()
                        )
                    except ValueError:
                        pass
                else:
                    try:
                        resolved_relatives.append(
                            (root / candidate).resolve().relative_to(root.resolve()).as_posix()
                        )
                    except ValueError:
                        pass
            for relative in resolved_relatives:
                file_result = by_path.get(_normalize_relative_path(relative))
                if file_result is not None:
                    break
        else:
            root = Path(scan_result.get("root", "."))
            if candidate.is_absolute():
                try:
                    relative = candidate.resolve().relative_to(root.resolve()).as_posix()
                except ValueError:
                    relative = ""
            else:
                try:
                    relative = (root / candidate).resolve().relative_to(root.resolve()).as_posix()
                except ValueError:
                    relative = ""
            file_result = by_path.get(_normalize_relative_path(relative))

    if file_result is not None:
        declarations = file_result.get("modules", [])
        if len(declarations) == 1:
            declaration = declarations[0]
        else:
            # Multi-module file: try to match the primary module by filename.
            # Convention: the primary/top module name matches the filename (without extension).
            file_stem = Path(file_result["path"]).stem.lower()
            matched = [
                d for d in declarations if d["name"].lower() == file_stem
            ]
            if len(matched) == 1:
                declaration = matched[0]
            elif len(matched) > 1:
                return None, (
                    f"top file '{top_arg}' contains multiple modules matching "
                    f"filename stem '{file_stem}'; specify module name explicitly"
                )
            else:
                return None, (
                    f"top file '{top_arg}' contains {len(declarations)} modules "
                    f"but none matches filename stem '{file_stem}'. "
                    f"Found: {', '.join(d['name'] for d in declarations)}. "
                    f"Specify module name explicitly as top argument."
                )
        return {
            "name": declaration["name"],
            "kind": declaration["kind"],
            "path": file_result["path"],
            "language": file_result["language"],
        }, None

    matches = by_name.get(_normalize_name(top_arg), [])
    if not matches:
        return None, f"top module/entity '{top_arg}' was not found"
    if len(matches) > 1:
        paths = ", ".join(sorted(record["path"] for record in matches))
        return None, f"ambiguous top module/entity '{top_arg}': {paths}"
    return matches[0], None


def _declaration_source(record: dict, source: str) -> str:
    """Return the source region belonging to one module/entity declaration."""
    language = record["language"]
    masked = _mask_comments_and_strings(source, language)
    if language == "vhdl":
        matches = [
            match
            for match in VHDL_DECL_RE.finditer(masked)
            if _normalize_name(match.group(1)) == _normalize_name(record["name"])
        ]
        if not matches:
            return source
        start_match = matches[0]
        next_match = VHDL_DECL_RE.search(masked, start_match.end())
        end = next_match.start() if next_match else len(source)
        return source[start_match.start() : end]

    matches = [
        match
        for match in VERILOG_DECL_RE.finditer(masked)
        if match.group(1) == record["name"]
    ]
    if not matches:
        return source
    start_match = matches[0]
    end_match = re.search(r"\bendmodule\b", masked[start_match.end() :])
    end = start_match.end() + end_match.end() if end_match else len(source)
    return source[start_match.start() : end]


def _extract_candidates(record: dict, source: str) -> set[str]:
    declaration_source = _declaration_source(record, source)
    if record["language"] == "vhdl":
        return _extract_vhdl_candidates(declaration_source)
    return _extract_verilog_candidates(declaration_source)


def _read_sources(scan_result: dict) -> tuple[dict[str, str], str | None]:
    sources: dict[str, str] = {}
    for file_result in scan_result.get("files", []):
        root_dir = _get_file_root_dir(scan_result, file_result)
        path = root_dir / Path(file_result["path"])
        try:
            sources[file_result["path"]] = path.read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError as exc:
            return {}, f"failed to read RTL file {path}: {exc}"
    return sources, None


def resolve_fileset(
    roots: list[Path], top_arg: str, output: str = ""
) -> dict:
    """Resolve a top module/entity to a dependency-first fileset result."""
    if len(roots) == 1:
        scan_result = scan_rtl(roots[0])
    else:
        scan_result = scan_multi_roots(roots)
    if scan_result["status"] != "SUCCESS":
        primary = Path(scan_result.get("root", roots[0].as_posix()))
        return _failure_result(primary, output, scan_result.get("diagnostics", []))

    by_name, by_path = _build_indexes(scan_result)
    top, top_error = _resolve_top(scan_result, top_arg, by_name, by_path)
    if top_error:
        primary = Path(scan_result.get("root", roots[0].as_posix()))
        return _failure_result(primary, output, [top_error])

    sources, source_error = _read_sources(scan_result)
    if source_error:
        primary = Path(scan_result.get("root", roots[0].as_posix()))
        return _failure_result(primary, output, [source_error])

    visited: set[str] = set()
    visiting: set[str] = set()
    ordered_records: list[dict] = []
    ordered_files: list[str] = []
    unresolved = 0
    warnings: list[str] = []

    def visit(record: dict) -> str | None:
        nonlocal unresolved
        key = _normalize_name(record["name"])
        if key in visited or key in visiting:
            return None
        visiting.add(key)

        candidate_names = sorted(
            _extract_candidates(record, sources[record["path"]]),
            key=lambda name: (name.casefold(), name),
        )
        for candidate_name in candidate_names:
            candidate_key = _normalize_name(candidate_name)
            matches = by_name.get(candidate_key, [])
            if not matches:
                unresolved += 1
                return (
                    f"unresolved dependency '{candidate_name}' referenced by "
                    f"{record['path']}"
                )
            # F3: prefer the same project/version path as the current caller.
            if len(matches) > 1:
                proximity_filtered = _filter_matches_by_path_proximity(
                    matches, record["path"]
                )
                if len(proximity_filtered) < len(matches):
                    warnings.append(
                        f"resolved ambiguous dependency '{candidate_name}' "
                        f"by path proximity: chose '{proximity_filtered[0]['path']}' "
                        f"over {[m['path'] for m in matches if m not in proximity_filtered]}"
                    )
                    matches = proximity_filtered
            # F4: identical mirrored IP files are equivalent; keep one deterministically.
            if len(matches) > 1:
                identical_filtered = _filter_byte_identical_matches(matches, sources)
                if len(identical_filtered) < len(matches):
                    warnings.append(
                        f"resolved duplicate dependency '{candidate_name}' by identical source: "
                        f"chose '{identical_filtered[0]['path']}' over "
                        f"{[m['path'] for m in matches if m not in identical_filtered]}"
                    )
                    matches = identical_filtered
            # F5: prefer known shared-IP/production paths before language.
            if len(matches) > 1:
                path_filtered = _filter_matches_by_path_priority(matches)
                if len(path_filtered) < len(matches):
                    warnings.append(
                        f"resolved ambiguous dependency '{candidate_name}' "
                        f"by path priority: chose '{path_filtered[0]['path']}' over "
                        f"{[m['path'] for m in matches if m not in path_filtered]}"
                    )
                    matches = path_filtered
            # F6: use HDL language when candidates remain equivalent by path.
            if len(matches) > 1:
                language_filtered = _filter_matches_by_language(
                    matches, record["language"]
                )
                if len(language_filtered) < len(matches):
                    warnings.append(
                        f"resolved ambiguous dependency '{candidate_name}' "
                        f"by language ({record['language']}): "
                        f"chose '{language_filtered[0]['path']}' over "
                        f"{[m['path'] for m in matches if m not in language_filtered]}"
                    )
                    matches = language_filtered
            # F7: root priority is the final tie-breaker for multi-root scans.
            if len(matches) > 1:
                root_filtered = _filter_matches_by_root_priority(matches)
                if len(root_filtered) < len(matches):
                    warnings.append(
                        f"resolved ambiguous dependency '{candidate_name}' "
                        f"by root priority: chose '{root_filtered[0]['path']}' over "
                        f"{[m['path'] for m in matches if m not in root_filtered]}"
                    )
                    matches = root_filtered
            if len(matches) > 1:
                paths = ", ".join(sorted(match["path"] for match in matches))
                return (
                    f"ambiguous dependency '{candidate_name}' referenced by "
                    f"{record['path']} ({record['language']}): {paths}"
                )
            error = visit(matches[0])
            if error:
                return error

        visiting.remove(key)
        visited.add(key)
        ordered_records.append(record)
        if record["path"] not in ordered_files:
            ordered_files.append(record["path"])
        return None

    error = visit(top)
    if error:
        primary = Path(scan_result.get("root", roots[0].as_posix()))
        result = _failure_result(primary, output, [error])
        result["summary"]["unresolved_dependencies"] = unresolved
        return result

    dependency_records = [
        record
        for record in ordered_records
        if _normalize_name(record["name"]) != _normalize_name(top["name"])
    ]
    success_result = {
        "schema_version": "1.0",
        "status": "SUCCESS",
        "top": {
            "name": top["name"],
            "kind": top["kind"],
            "path": top["path"],
        },
        "dependencies": [
            {"name": record["name"], "kind": record["kind"], "path": record["path"]}
            for record in dependency_records
        ],
        "fileset": ordered_files,
        "output": output,
        "diagnostics": list(warnings),
        "summary": {
            "modules_in_closure": len(ordered_records),
            "files_in_closure": len(ordered_files),
            "unresolved_dependencies": 0,
        },
    }
    roots_list = scan_result.get("roots")
    if roots_list is not None:
        success_result["roots"] = roots_list
    else:
        success_result["root"] = scan_result["root"]
    return success_result


def _write_fileset(output: Path, fileset: list[str]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write("\n".join(fileset))
            temporary.write("\n")
        temporary_path.replace(output)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def build_fileset(roots: list[Path], top_arg: str, output: Path) -> dict:
    """Resolve dependencies and atomically write a fileset on success."""
    result = resolve_fileset(roots, top_arg, str(output))
    if result["status"] != "SUCCESS":
        return result

    try:
        _write_fileset(output, result["fileset"])
    except OSError as exc:
        primary = Path(result.get("root", roots[0].as_posix()))
        return _failure_result(primary, str(output), [f"failed to write fileset: {exc}"])
    return result


def _print_text(result: dict) -> None:
    if result["status"] == "FAILED":
        for diagnostic in result["diagnostics"]:
            print(f"ERROR: {diagnostic}", file=sys.stderr)
        return

    for diagnostic in result.get("diagnostics", []):
        print(f"WARNING: {diagnostic}")

    print(f"Top: {result['top']['name']} ({result['top']['path']})")
    print(f"Fileset: {result['output']}")
    print(
        f"Resolved {result['summary']['modules_in_closure']} module/entity "
        f"declaration(s) in {result['summary']['files_in_closure']} file(s)."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve RTL dependencies and write a simulator fileset."
    )
    parser.add_argument(
        "--root", action="append", required=True,
        help="RTL root directory (repeat to add multiple)"
    )
    parser.add_argument("--top", required=True, help="Top module/entity name or RTL file")
    parser.add_argument("--output", required=True, help="Output fileset path")
    parser.add_argument("--json", action="store_true", help="Emit one JSON result object")
    args = parser.parse_args(argv)

    roots = [Path(r) for r in args.root]
    result = build_fileset(roots, args.top, Path(args.output))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 0 if result["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
