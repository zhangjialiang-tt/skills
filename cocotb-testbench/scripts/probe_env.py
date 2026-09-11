#!/usr/bin/env python3
"""Probe the local cocotb toolchain: Python packages + simulator executables.

Cross-platform (shutil.which only). Emits a JSON report; never installs
anything. Exit code: 0 = report produced (gaps included), 2 = cocotb absent
(hard prerequisite for this skill).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from importlib import metadata

SIM_EXECUTABLES = {
    "icarus": ["iverilog"],
    "verilator": ["verilator"],
    "ghdl": ["ghdl"],
    "modelsim": ["vsim"],
    "questa": ["vsim", "qrun"],
    "xcelium": ["xrun"],
    "vcs": ["vcs"],
    "riviera": ["asim"],
    "nvc": ["nvc"],
}


def probe() -> dict:
    report: dict = {
        "python": sys.version.split()[0],
        "packages": {},
        "simulators": {},
        "missing": [],
        "recommendations": [],
    }
    for pkg in ("cocotb", "pytest"):
        try:
            report["packages"][pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            report["packages"][pkg] = None
            report["missing"].append(pkg)

    cocotb_ver = report["packages"]["cocotb"]
    if cocotb_ver:
        major = int(cocotb_ver.split(".")[0])
        if major < 2:
            report["recommendations"].append(
                f"cocotb {cocotb_ver} is 1.x; generated templates target 2.x "
                "APIs (Clock(...).start(), runner.build(sources=)). Upgrade: pip install -U 'cocotb>=2,<3'"
            )

    for sim, exes in SIM_EXECUTABLES.items():
        found = {e: shutil.which(e) for e in exes}
        usable = [e for e, path in found.items() if path]
        if usable:
            report["simulators"][sim] = {"available": True, "executables": usable}
        else:
            report["simulators"][sim] = {"available": False, "executables": []}

    if not any(v["available"] for v in report["simulators"].values()):
        report["missing"].append("simulator")
        report["recommendations"].append(
            "No supported simulator on PATH. Cheapest option: install Icarus "
            "Verilog (https://bleyer.org/icarus/ on Windows, distro package elsewhere)."
        )
    if "pytest" in report["missing"]:
        report["recommendations"].append("pip install pytest")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args(argv)
    report = probe()
    print(json.dumps(report, indent=2))
    if report["packages"].get("cocotb") is None:
        print("ERROR: cocotb is required before this skill can run; "
              "propose the install command to the user and wait for confirmation.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
