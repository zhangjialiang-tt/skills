#!/usr/bin/env python3
"""Generate a cocotb (cocotb_tools.runner + pytest) test skeleton for one RTL top.

Inputs (produced by sibling scripts):
  --fileset-json : JSON emitted by `build_fileset.py --json`
                   (keys used: status, top{name,kind,path}, fileset[])
  --ports-json   : JSON array emitted by `tb_extract_ports.py --json`
                   (items: {name, direction, width, signed, type})
                   For VHDL toplevels the agent authors this file by hand
                   from the entity declaration, same schema.

Outputs (written under --out, default `sim/<top>/`):
  design.json                 build/run configuration record (agent may edit)
  tb_runner.py                shared pytest<->runner plumbing
  conftest.py                 pytest marker registration
  test_<top>_smoke.py         L1-equivalent: build/elab + clock/reset/settle smoke
  test_<top>_functional.py    L2-equivalent: golden-first or characterization stubs
  .gitignore                  sim_build/ and result artifacts

Refuses to overwrite existing files unless --force. Exit 0 on success.

Templates are grounded in cocotb 2.x stable APIs:
  - `from cocotb_tools.runner import get_runner`
  - `Clock(...).start(start_high=False)` (2.x clock start)
  - `dut.<sig>.value = ...` assignment form
  - `.integer` raises ValueError on unresolved X/Z (used for resolve checks)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from string import Template

GENERATOR_TAG = "generated-by: cocotb-testbench/scripts/gen_cocotb_skeleton.py v1"

CLK_RE = re.compile(r"(^|_)(clk|clock|pclk|fclk|sclk|mclk|aclk|sysclk)(_|$)", re.IGNORECASE)
RST_RE = re.compile(r"(^|_)(rst|reset|clr|clear|areset)(_|$)|^n(rst|reset|clr)", re.IGNORECASE)
ACTIVE_LOW_RE = re.compile(r"(_n$|^n(rst|reset|clr))", re.IGNORECASE)

MARKS = ("smoke", "functional", "characterization")


# ---------------------------------------------------------------- templates

TBRUNNER_T = Template('''"""Shared pytest <-> cocotb_tools.runner plumbing for `$top`.

One pytest control function per test module builds the design and launches the
simulator; cocotb coroutine tests inside the same modules do the driving.
Run from this directory (pytest inserts it into sys.path and the runner
forwards sys.path to the simulator process as PYTHONPATH):

    pytest -m smoke                # build/elab + basic drive
    pytest -m functional           # feature checks
    SIM=questa pytest -m smoke     # pick simulator (default: $sim)
    WAVES=1 pytest                 # request waveforms
    GUI=1 pytest                   # open waveform/sim GUI after run
"""
$gen_tag

from __future__ import annotations

import json
import os
from pathlib import Path

from cocotb_tools.runner import get_runner

HERE = Path(__file__).resolve().parent
DESIGN = json.loads((HERE / "design.json").read_text(encoding="utf-8"))


def build_runner():
    sim = os.getenv("SIM", DESIGN["simulator_default"])
    return get_runner(sim)


def build_design(runner):
    runner.build(
        sources=DESIGN["sources"],
        hdl_toplevel=DESIGN["top"],
        always=DESIGN.get("always_build", True),
        includes=DESIGN.get("includes", []),
        defines=DESIGN.get("defines", {}),
        parameters=DESIGN.get("parameters", {}),
        timescale=(tuple(DESIGN["timescale"]) if DESIGN.get("timescale") else None),
        build_dir=HERE / "sim_build",
        verbose=True,
    )


def run_test(runner, test_module, testcase=None):
    return runner.test(
        hdl_toplevel=DESIGN["top"],
        hdl_toplevel_lang=DESIGN.get("toplevel_lang"),
        test_module=test_module,
        testcase=testcase,
        build_dir=HERE / "sim_build",
        waves=bool(os.getenv("WAVES")),
        gui=bool(os.getenv("GUI")),
        verbose=True,
    )
''')

CONFTEST_T = Template('''"""pytest configuration for $top (cocotb-testbench generated)."""
$gen_tag

MARKS = ("smoke", "functional", "characterization")


def pytest_configure(config):
    for mark in MARKS:
        config.addinivalue_line("markers", f"{mark}: cocotb-testbench generated marker")
''')

SMOKE_T = Template('''"""Smoke (L1-equivalent) for `$top`.

Proves ONLY: design compiles + elaborates, clock toggles, reset sequence
applies, outputs resolve (no X/Z) after settling. A smoke PASS is NEVER
functional correctness.

Generated assumptions (verify before trusting results):
  * clock : $clk_note
  * reset : $rst_note
"""
$gen_tag

import random

import cocotb
import pytest
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

import tb_runner as tb

CLK = $clk_literal
RESET = $reset_literal  # {"name": ..., "active_low": bool} or None
SETTLE_CYCLES = 10  # TODO raise for pipelines deeper than this
INPUTS = $inputs_literal
OUTPUTS = $outputs_literal
# TODO ports with undetermined or bidirectional direction are NOT driven here:
$skipped_todo_lines


@pytest.mark.smoke
def test_${top}_smoke():
    """Build the design and run the cocotb smoke tests."""
    runner = tb.build_runner()
    tb.build_design(runner)
    tb.run_test(runner, "test_${top}_smoke")

async def _apply_reset(dut):
$reset_apply_body


def _assert_resolved(dut, name):
    try:
        dut.__getattr__(name).value.integer
    except ValueError:
        raise AssertionError(
            f"dut.{name} contains unresolved X/Z: {dut.__getattr__(name).value!s}"
        )


@cocotb.test()
async def test_${top}_clock_reset(dut):
    """$clock_reset_doc"""
$clock_start_lines
    for p in INPUTS:
        dut.__getattr__(p["name"]).value = 0
    await _apply_reset(dut)
$clk_waits5
$resolve_check_lines

@cocotb.test()
async def test_${top}_outputs_settle(dut):
    """Random inputs, then settle: every output must resolve to a valid value."""
$clock_start_lines
    for p in INPUTS:
        dut.__getattr__(p["name"]).value = 0
    await _apply_reset(dut)
    for _ in range(SETTLE_CYCLES):
        for p in INPUTS:
            v = (
                random.getrandbits(p["width"])
                if p["width"] and p["width"] > 1
                else random.randint(0, 1)
                if p["width"] == 1
                else 0  # symbolic width: drive constant, raise TODO below
            )
            dut.__getattr__(p["name"]).value = v
$clk_wait1
    for p in OUTPUTS:
        _assert_resolved(dut, p["name"])
''')

FUNC_T = Template('''"""Functional (L2-equivalent) tests for `$top`.

Verification basis at generation time: $basis_doc
$truth_warning

Marker policy:
  - golden-backed comparisons      -> `functional`
  - RTL-derived expectations only  -> keep the `characterization` label in the
    docstring and report them as behavior characterization, never as proof.
"""
$gen_tag

import logging

import cocotb
import pytest

import tb_runner as tb

CLK = $clk_literal
RESET = $reset_literal
GOLDEN_MODEL = $golden_literal  # "python_module.function" from design.json or None
INPUTS = $inputs_literal
OUTPUTS = $outputs_literal

SETTLE_CYCLES = 10  # TODO raise for deep pipelines; see smoke module


@pytest.mark.functional
def test_${top}_functional():
    """Build the design and run the cocotb functional tests."""
    runner = tb.build_runner()
    tb.build_design(runner)
    tb.run_test(runner, "test_${top}_functional")


async def _setup(dut):
$setup_body


@cocotb.test()
async def test_${top}_golden_equivalence(dut):
    """Bit-accurate comparison against the golden model (no-op without one)."""
    if GOLDEN_MODEL is None:
        logging.getLogger("cocotb.test").warning(
            "golden model not wired: set design.json['golden_model'] "
            "to 'python_module.function'; this test self-skips"
        )
        return
    import importlib

    mod_name, fn_name = GOLDEN_MODEL.rsplit(".", 1)
    golden = getattr(importlib.import_module(mod_name), fn_name)
    await _setup(dut)
    # TODO: stream real stimulus vectors (data/ dir or file); per sample/frame:
    #   1. drive inputs           dut.<sig>.value = ...
    #   2. await settling         await RisingEdge(dut.<clk>) * latency
    #   3. compare bit-accurate   assert dut.<out>.value.integer == golden(...)
    # Keep comparisons exact; do NOT loosen asserts to obtain a PASS.


@cocotb.test()
async def test_${top}_behavior_characterization(dut):
    """characterization: fill expected values from spec/golden/measured vectors.

    Expected values derived only from reading the RTL are behavioral records,
    not independent proof. Keep this test labeled `characterization` unless an
    independent source backs the expectations.
    """
    await _setup(dut)
    # TODO per-feature stimulus + assertions.
$charter_stub_lines
''')

GITIGNORE_T = Template('''# $gen_tag
sim_build/
results.xml
__pycache__/
*.vcd
*.fst
*.ghw
''')


# ---------------------------------------------------------------- helpers


def _load_json(path: Path, label: str):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        sys.exit(f"ERROR: cannot read {label} file {path}: {exc}")
    except json.JSONDecodeError as exc:
        sys.exit(f"ERROR: {label} file {path} is not valid JSON: {exc}")
    return data


def classify_ports(ports: list) -> dict:
    clocks, resets, inputs, outputs, inouts, unknowns = [], [], [], [], [], []
    for p in ports:
        if not isinstance(p, dict) or "name" not in p:
            sys.exit(f"ERROR: ports entry missing name: {p!r}")
        name = p["name"]
        direction = p.get("direction", "unknown")
        raw_w = p.get("width", 1)
        width_bits = raw_w if isinstance(raw_w, int) and raw_w >= 1 else None
        entry = {
            "name": name,
            "width": width_bits,
            "width_expr": str(raw_w) if width_bits is None else None,
            "signed": bool(p.get("signed", False)),
        }
        if direction == "input":
            if width_bits == 1 and CLK_RE.search(name):
                clocks.append(entry)
            elif width_bits == 1 and RST_RE.search(name):
                entry["active_low"] = bool(ACTIVE_LOW_RE.search(name))
                resets.append(entry)
            else:
                inputs.append(entry)
        elif direction == "output":
            outputs.append(entry)
        elif direction == "inout":
            inouts.append(entry)
        else:
            unknowns.append(entry)
    return {
        "clocks": clocks,
        "resets": resets,
        "inputs": inputs,
        "outputs": outputs,
        "inouts": inouts,
        "unknown": unknowns,
    }


def wait_lines(count: int, clk: str | None, indent: str) -> str:
    if clk:
        return "\n".join(f"{indent}await RisingEdge(dut.{clk})" for _ in range(count)) + "\n"
    return f"{indent}await Timer({10 * count}, unit='ns')  # no clock port detected\n"


def render_reset_apply(reset, clk: str | None) -> str:
    if reset is None:
        return (
            "    # no reset-like port detected; delete this helper or wire a "
            "manual init sequence if the DUT needs one\n"
            "    await Timer(100, unit='ns')\n"
        )
    active = 0 if reset["active_low"] else 1
    idle = 1 - active
    lines = [
        f"    dut.{reset['name']}.value = {active}",
    ]
    lines.append(wait_lines(2, clk, "    ").rstrip("\n"))
    lines.append(f"    dut.{reset['name']}.value = {idle}")
    lines.append(wait_lines(1, clk, "    ").rstrip("\n"))
    return "\n".join(lines) + "\n"


def py_literal(obj) -> str:
    return repr(obj)


# ---------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fileset-json", required=True, help="build_fileset.py --json output file")
    ap.add_argument("--ports-json", required=True, help="tb_extract_ports.py --json output file")
    ap.add_argument("--out", help="output dir (default: sim/<top>)")
    ap.add_argument("--sim", default="icarus", help="default runner simulator name")
    ap.add_argument("--toplevel-lang", choices=["verilog", "vhdl"], help="override auto detection")
    ap.add_argument("--golden", help='golden model entry "python_module.function"')
    ap.add_argument("--force", action="store_true", help="overwrite existing generated files")
    args = ap.parse_args(argv)

    design = _load_json(Path(args.fileset_json), "fileset")
    if design.get("status") != "SUCCESS":
        diags = "\n  ".join(design.get("diagnostics", []))
        sys.exit(f"ERROR: fileset resolution failed:\n  {diags}")
    top = design["top"]["name"]
    ports = _load_json(Path(args.ports_json), "ports")
    if not isinstance(ports, list):
        sys.exit("ERROR: ports JSON must be a list of port objects")

    # build_fileset reports sources relative to each scan root; the runner
    # resolves against pytest's cwd, so absolutize here.
    roots = [Path(r) for r in design.get("roots", [design.get("root", ".")])]
    missing = []
    abs_sources = []
    for s in design["fileset"]:
        p = Path(s)
        if p.is_absolute():
            abs_sources.append(p.as_posix())
            continue
        for r in roots:
            cand = (r / p)
            if cand.exists():
                abs_sources.append(cand.resolve().as_posix())
                break
        else:
            missing.append(s)
            abs_sources.append((Path.cwd() / p).resolve().as_posix())
    if missing:
        print(
            "WARNING: sources not found under scan roots (build may fail): "
            + ", ".join(missing),
            file=sys.stderr,
        )

    kind = design["top"].get("kind", "module")
    lang = args.toplevel_lang or ("vhdl" if kind == "entity" else "verilog")
    out = Path(args.out) if args.out else Path("sim") / top

    cls = classify_ports(ports)
    clk = cls["clocks"][0]["name"] if cls["clocks"] else None
    reset = cls["resets"][0] if cls["resets"] else None
    gen_tag = f"# {GENERATOR_TAG}"

    skipped = cls["inouts"] + cls["unknown"]
    skipped_lines = "\n".join(
        [f"#   {p['name']} (inout)" for p in cls["inouts"]]
        + [f"#   {p['name']} (unknown direction)" for p in cls["unknown"]]
    ) or "#   (none)"

    files: dict[str, str] = {}

    files["design.json"] = json.dumps(
        {
            "top": top,
            "toplevel_lang": lang,
            "sources": abs_sources,
            "includes": [],
            "defines": {},
            "parameters": {},
            "simulator_default": args.sim,
            "always_build": True,
            "golden_model": args.golden,
            "timescale": ["1ns", "1ps"],
        },
        indent=2,
    ) + "\n"

    files["tb_runner.py"] = TBRUNNER_T.substitute(
        gen_tag=gen_tag, top=top, sim=args.sim
    )
    files["conftest.py"] = CONFTEST_T.substitute(gen_tag=gen_tag, top=top)

    inputs_lit = py_literal(cls["inputs"])
    outputs_lit = py_literal(cls["outputs"])
    files[f"test_{top}_smoke.py"] = SMOKE_T.substitute(
        gen_tag=gen_tag,
        top=top,
        clk_literal=py_literal(clk),
        reset_literal=py_literal(reset),
        inputs_literal=inputs_lit,
        outputs_literal=outputs_lit,
        skipped_todo_lines=skipped_lines,
        clk_note=(f"{clk} (driven 10 ns period)" if clk else "no clock-like port found; combinational-only"),
        rst_note=(
            f"{reset['name']} assumed active-{'low' if reset['active_low'] else 'high'} (name heuristic)"
            if reset
            else "no reset-like port found (Timer-based settle)"
        ),
        reset_apply_body=render_reset_apply(reset, clk),
        clock_start_lines=(
            f"    Clock(dut.{clk}, 10, unit='ns').start(start_high=False)"
            if clk
            else "    # no clock port: nothing to start"
        ),
        clk_waits5=wait_lines(5, clk, "    "),
        clk_wait1=wait_lines(1, clk, "        "),
        resolve_check_lines=(
            "    for p in OUTPUTS:\n        _assert_resolved(dut, p[\"name\"])"
            if reset or not clk
            else "    # no reset detected: outputs may legitimately hold X at boot; settle test covers resolve checks"
        ),
        clock_reset_doc=(
            "clock starts, reset applies, 5 cycles run without incident"
            if clk
            else "no clock detected: static input drive only"
        ),
    )

    files[f"test_{top}_functional.py"] = FUNC_T.substitute(
        gen_tag=gen_tag,
        top=top,
        clk_literal=py_literal(clk),
        reset_literal=py_literal(reset),
        inputs_literal=inputs_lit,
        outputs_literal=outputs_lit,
        golden_literal=py_literal(args.golden),
        basis_doc=(f"golden model `{args.golden}`" if args.golden else "RTL analysis only (no independent source wired)"),
        truth_warning=(
            "Golden model present: keep comparisons bit-accurate; never loosen asserts to pass."
            if args.golden
            else "NOTICE: with no golden/spec source, generated expectations are behavior records, not proof."
        ),
        setup_body=(
            "    from cocotb.clock import Clock\n"
            "    from cocotb.triggers import RisingEdge, Timer\n"
            + (f"    Clock(dut.{clk}, 10, unit='ns').start(start_high=False)\n" if clk else "")
            + render_reset_apply(reset, clk)
        ),
        charter_stub_lines="\n".join(
            f"    # - output {p['name']} (width {p['width']})" for p in cls["outputs"]
        ) or "    # (no outputs detected - fill manually)",
    )

    files[".gitignore"] = GITIGNORE_T.substitute(gen_tag=GENERATOR_TAG)

    existing = [name for name in files if (out / name).exists()]
    if existing and not args.force:
        sys.exit(
            f"ERROR: files already exist in {out}: {sorted(existing)}; "
            "back them up or re-run with --force (overwrites generated set only)"
        )

    out.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (out / name).write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "OK", "top": top, "out": out.as_posix(), "files": sorted(files)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
