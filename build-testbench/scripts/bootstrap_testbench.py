#!/usr/bin/env python3
"""Bootstrap a simulation framework directory in one transactional step.

Resolves the P0-01 circular dependency (output path needed SimSubDir, SimSubDir
needed resolve first) and P0-04 top-identity loss (port extraction used to
re-search the whole workspace, possibly picking a wrong historical version).

Flow:
  1. resolve_fileset() — parse only, write nothing
  2. read authoritative top.name / top.path
  3. allocate the next sim/ index
  4. create sim/sub{x}-{name}/ subtree
  5. write fileset.f atomically (reuse _write_fileset)
  6. extract ports from the SAME top file the resolver picked
     (reuse _extract_ports_from_file, bypassing find_module_file)
  7. write ports.json
  8. emit a bootstrap result JSON

On any resolution failure, NO directory is created (transactional: a failed
parse produces no side effects). This script does NOT generate testbenches or
Makefiles — those remain the Agent's template-instantiation job, keeping the
orchestrator responsibilities separated.

Dependencies on sibling modules (private functions, same package):
  - build_fileset.resolve_fileset, _write_fileset
  - tb_extract_ports._extract_ports_from_file
If those modules are refactored, update the imports here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Allow direct execution: add this script's dir to sys.path so the sibling
# imports work both as a package and as standalone CLI.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from build_fileset import resolve_fileset, _write_fileset  # noqa: E402
from tb_extract_ports import _extract_ports_from_file  # noqa: E402


_SUBDIR_RE = re.compile(r"^sub(\d+)-")
_SIM_SUBDIRS = ("tb", "data", "scripts", "log")


def _next_index(sim_root: Path) -> int:
    """Return the next global sub{x} index by scanning existing sim/ dirs."""
    max_index = 0
    if not sim_root.is_dir():
        return 1
    for entry in sim_root.iterdir():
        if not entry.is_dir():
            continue
        match = _SUBDIR_RE.match(entry.name)
        if match:
            idx = int(match.group(1))
            if idx > max_index:
                max_index = idx
    return max_index + 1


def bootstrap(
    workspace_root: Path,
    top_arg: str,
    level: str = "l1",
) -> dict:
    """Bootstrap a sim framework dir. Returns a result dict.

    On failure, status == "FAILED" and no directory is created.
    """
    roots = [workspace_root]
    # Step 1-2: resolve only, no writes. top.path/name is the authoritative identity.
    resolved = resolve_fileset(roots, top_arg, output="")
    if resolved["status"] != "SUCCESS":
        return {
            "schema_version": "1.0",
            "status": "FAILED",
            "workspace_root": workspace_root.as_posix(),
            "top_arg": top_arg,
            "sim_dir": None,
            "diagnostics": resolved.get("diagnostics", []),
            "summary": {"unresolved_dependencies": resolved.get("summary", {}).get(
                "unresolved_dependencies", 0)},
        }

    top = resolved["top"]
    module_name = top["name"]
    top_rel_path = top["path"]  # workspace-relative

    # Step 3: allocate index now that we know the module name.
    sim_root = workspace_root / "sim"
    next_index = _next_index(sim_root)
    sim_dir_name = f"sub{next_index}-{module_name}"
    sim_dir = sim_root / sim_dir_name

    # Step 4: create the subtree.
    for sub in _SIM_SUBDIRS:
        (sim_dir / sub).mkdir(parents=True, exist_ok=True)

    # Step 5: write fileset.f atomically (reuse helper).
    fileset_path = sim_dir / "fileset.f"
    _write_fileset(fileset_path, resolved["fileset"])

    # Step 6: extract ports from the SAME file the resolver picked.
    # This bypasses find_module_file's whole-workspace search (P0-04 fix).
    abs_top_path = workspace_root / top_rel_path
    ports = _extract_ports_from_file(abs_top_path, module_name)

    # Step 7: write ports.json.
    ports_path = sim_dir / "ports.json"
    ports_path.write_text(
        json.dumps(ports, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Step 8: emit result.
    return {
        "schema_version": "1.0",
        "status": "SUCCESS",
        "workspace_root": workspace_root.as_posix(),
        "top_arg": top_arg,
        "sim_dir": sim_dir.relative_to(workspace_root).as_posix(),
        "sim_dir_name": sim_dir_name,
        "module_name": module_name,
        "level": level,
        "dut": {
            "path": top_rel_path,
            "name": module_name,
            "kind": top.get("kind"),
        },
        "fileset_path": fileset_path.relative_to(workspace_root).as_posix(),
        "ports_path": ports_path.relative_to(workspace_root).as_posix(),
        "fileset": resolved["fileset"],
        "dependencies": resolved.get("dependencies", []),
        "ports": ports,
        "diagnostics": resolved.get("diagnostics", []),
        "summary": {
            "modules_in_closure": resolved["summary"]["modules_in_closure"],
            "files_in_closure": resolved["summary"]["files_in_closure"],
            "port_count": len(ports),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Bootstrap a sim/sub{x}-{module}/ framework dir in one step. "
            "Resolves dependencies, allocates the index, writes fileset.f and "
            "ports.json. Does not generate testbenches or Makefiles."
        )
    )
    parser.add_argument(
        "--workspace", required=True,
        help="Workspace root (the dir containing .git and sim/)",
    )
    parser.add_argument(
        "--top", required=True,
        help="Top module/entity name or workspace-relative RTL file path",
    )
    parser.add_argument(
        "--level", default="l1", choices=["l1", "l2"],
        help="Requested verification level (recorded in output, default l1)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args(argv)

    result = bootstrap(Path(args.workspace).resolve(), args.top, args.level)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["status"] != "SUCCESS":
            for d in result.get("diagnostics", []):
                print(f"ERROR: {d}", file=sys.stderr)
            print(f"FAILED: bootstrap for top '{args.top}'", file=sys.stderr)
        else:
            print(f"Module:  {result['module_name']}")
            print(f"Sim dir: {result['sim_dir']}")
            print(f"Fileset: {result['fileset_path']}")
            print(f"Ports:   {result['ports_path']} ({result['summary']['port_count']} ports)")
            for d in result.get("diagnostics", []):
                print(f"WARNING: {d}")
    return 0 if result["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
