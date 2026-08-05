"""Tests for bootstrap_testbench — P0-01 (circular dep) and P0-04 (top identity)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from bootstrap_testbench import bootstrap, _next_index  # noqa: E402


def _make_workspace(tmp_path: Path) -> Path:
    """Create a minimal workspace with .git and sim/ markers."""
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".git").mkdir()
    (ws / "sim").mkdir()
    return ws


def test_bootstrap_normal_flow_creates_dir_and_artifacts(tmp_path):
    ws = _make_workspace(tmp_path)
    rtl_dir = ws / "rtl"
    rtl_dir.mkdir()
    (rtl_dir / "foo.v").write_text(
        "module foo(input clk, input rst_n, input [7:0] a, output [7:0] b);\n"
        "assign b = a;\nendmodule\n",
        encoding="utf-8",
    )

    result = bootstrap(ws, "rtl/foo.v")

    assert result["status"] == "SUCCESS"
    assert result["module_name"] == "foo"
    assert result["sim_dir"] == "sim/sub1-foo"
    assert result["dut"]["path"] == "rtl/foo.v"
    # Artifacts written.
    sim_dir = ws / result["sim_dir"]
    assert (sim_dir / "fileset.f").is_file()
    assert (sim_dir / "ports.json").is_file()
    for sub in ("tb", "data", "scripts", "log"):
        assert (sim_dir / sub).is_dir()
    # Ports extracted from the resolved top file.
    ports = json.loads((sim_dir / "ports.json").read_text(encoding="utf-8"))
    names = [p["name"] for p in ports]
    assert "clk" in names and "a" in names and "b" in names


def test_top_name_taken_from_module_declaration_not_filename(tmp_path):
    """Multi-module file: top.name must follow the module declaration matched
    by the resolver, not a raw filename guess. This guards the invariant that
    module_name comes from build_fileset's resolved declaration."""
    ws = _make_workspace(tmp_path)
    rtl_dir = ws / "rtl"
    rtl_dir.mkdir()
    # File wrapper.v contains two modules; the one matching the filename stem
    # is 'wrapper' (the primary). 'helper' must NOT be picked.
    (rtl_dir / "wrapper.v").write_text(
        "module helper(input a); endmodule\n"
        "module wrapper(input clk, input [7:0] d, output [7:0] q);\n"
        "assign q = d;\nendmodule\n",
        encoding="utf-8",
    )

    result = bootstrap(ws, "rtl/wrapper.v")

    assert result["status"] == "SUCCESS"
    # module_name is the resolved declaration, never a Path.stem guess.
    assert result["module_name"] == "wrapper"
    assert result["module_name"] == result["dut"]["name"]
    # Ports belong to 'wrapper', proving the right declaration was used.
    port_names = [p["name"] for p in result["ports"]]
    assert "d" in port_names and "q" in port_names


def test_top_identity_carried_to_port_extraction(tmp_path):
    """P0-04 regression: when two files define the same module name in
    different historical version dirs, ports must be extracted from the SAME
    file the resolver picked, not from the first workspace-wide match."""
    ws = _make_workspace(tmp_path)
    # Two versioned dirs each with a module named dup — different port widths
    # so we can tell which file was read.
    v3 = ws / "ghe_v3" / "rtl"
    v3.mkdir(parents=True)
    (v3 / "dup.v").write_text(
        "module dup(input clk, input [3:0] a); endmodule\n", encoding="utf-8"
    )
    v4 = ws / "ghe_v4" / "rtl"
    v4.mkdir(parents=True)
    (v4 / "dup.v").write_text(
        "module dup(input clk, input [15:0] a); endmodule\n", encoding="utf-8"
    )

    # Explicitly target the v4 file via workspace-relative path.
    result = bootstrap(ws, "ghe_v4/rtl/dup.v")

    assert result["status"] == "SUCCESS"
    assert result["dut"]["path"] == "ghe_v4/rtl/dup.v"
    # Port 'a' width must be 16 (v4), proving port extraction read the resolved
    # file rather than re-searching and finding v3 first.
    a_port = next(p for p in result["ports"] if p["name"] == "a")
    assert a_port["width"] == 16


def test_resolve_failure_creates_no_directory(tmp_path):
    """Transactionality: when resolution fails, no sim/sub* dir is created."""
    ws = _make_workspace(tmp_path)
    rtl_dir = ws / "rtl"
    rtl_dir.mkdir()
    (rtl_dir / "foo.v").write_text(
        "module foo(input clk); endmodule\n", encoding="utf-8",
    )

    result = bootstrap(ws, "rtl/does_not_exist.v")

    assert result["status"] == "FAILED"
    # No sub* dir should have been created.
    sim_root = ws / "sim"
    sub_dirs = [p.name for p in sim_root.iterdir() if p.is_dir()]
    assert not any(name.startswith("sub") for name in sub_dirs)


def test_next_index_increments_over_existing(tmp_path):
    ws = _make_workspace(tmp_path)
    (ws / "sim" / "sub2-foo").mkdir()
    (ws / "sim" / "sub5-bar").mkdir()
    assert _next_index(ws / "sim") == 6
