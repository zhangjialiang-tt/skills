import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_fileset.py"


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_verilog_dependency_closure_is_dependency_first(tmp_path):
    write_file(
        tmp_path,
        "top.sv",
        "module top;\n"
        "  mid #(.WIDTH(8)) u_mid (.clk(clk));\n"
        "endmodule\n",
    )
    write_file(
        tmp_path,
        "lib/mid.sv",
        "module mid;\n"
        "  leaf u_leaf (.clk(clk));\n"
        "  leaf u_leaf2 (.clk(clk));\n"
        "endmodule\n",
    )
    write_file(tmp_path, "lib/leaf.sv", "module leaf;\nendmodule\n")
    output = tmp_path / "out" / "fileset.f"

    completed = run_cli(
        "--root", str(tmp_path), "--top", "top", "--output", str(output), "--json"
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["status"] == "SUCCESS"
    assert payload["top"] == {"name": "top", "kind": "module", "path": "top.sv"}
    assert payload["fileset"] == ["lib/leaf.sv", "lib/mid.sv", "top.sv"]
    assert output.read_text(encoding="utf-8") == "lib/leaf.sv\nlib/mid.sv\ntop.sv\n"
    assert payload["summary"] == {
        "modules_in_closure": 3,
        "files_in_closure": 3,
        "unresolved_dependencies": 0,
    }


def test_vhdl_entity_references_and_cycles_terminate_deterministically(tmp_path):
    write_file(
        tmp_path,
        "top.vhd",
        "entity top is end entity top;\n"
        "architecture rtl of top is\n"
        "begin\n"
        "  u_child : entity work.child port map ();\n"
        "end architecture rtl;\n",
    )
    write_file(
        tmp_path,
        "child.vhd",
        "entity child is end entity child;\n"
        "architecture rtl of child is\n"
        "begin\n"
        "  u_cycle : cycle port map ();\n"
        "end architecture rtl;\n",
    )
    write_file(
        tmp_path,
        "cycle.vhd",
        "entity cycle is end entity cycle;\n"
        "architecture rtl of cycle is\n"
        "begin\n"
        "  u_child : entity work.child port map ();\n"
        "end architecture rtl;\n",
    )

    first_output = tmp_path / "first.f"
    second_output = tmp_path / "second.f"
    first = run_cli(
        "--root", str(tmp_path), "--top", "top", "--output", str(first_output), "--json"
    )
    second = run_cli(
        "--root", str(tmp_path), "--top", "top", "--output", str(second_output), "--json"
    )

    assert first.returncode == 0
    assert second.returncode == 0
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["fileset"] == ["cycle.vhd", "child.vhd", "top.vhd"]
    assert first_payload["fileset"] == second_payload["fileset"]
    assert first_output.read_text(encoding="utf-8") == second_output.read_text(encoding="utf-8")


def test_top_can_be_selected_by_file_path_and_comments_are_ignored(tmp_path):
    write_file(
        tmp_path,
        "top.sv",
        "module top;\n"
        "  // child fake_instance (clk);\n"
        '  initial $display("child string_instance (clk);");\n'
        "  child real_instance (.clk(clk));\n"
        "endmodule\n",
    )
    write_file(tmp_path, "child.sv", "module child;\nendmodule\n")
    output_by_name = tmp_path / "name.f"
    output_by_path = tmp_path / "path.f"

    by_name = run_cli(
        "--root", str(tmp_path), "--top", "top", "--output", str(output_by_name), "--json"
    )
    by_path = run_cli(
        "--root", str(tmp_path), "--top", "top.sv", "--output", str(output_by_path), "--json"
    )

    assert by_name.returncode == 0
    assert by_path.returncode == 0
    name_payload = json.loads(by_name.stdout)
    path_payload = json.loads(by_path.stdout)
    assert name_payload["top"] == path_payload["top"]
    assert name_payload["fileset"] == path_payload["fileset"] == ["child.sv", "top.sv"]


def test_missing_dependency_fails_without_overwriting_existing_fileset(tmp_path):
    write_file(
        tmp_path,
        "top.v",
        "module top;\n  missing u_missing (.clk(clk));\nendmodule\n",
    )
    output = tmp_path / "fileset.f"
    output.write_text("keep this content\n", encoding="utf-8")

    completed = run_cli(
        "--root", str(tmp_path), "--top", "top", "--output", str(output), "--json"
    )

    assert completed.returncode != 0
    payload = json.loads(completed.stdout)
    assert payload["status"] == "FAILED"
    assert payload["fileset"] == []
    assert any("missing" in diagnostic for diagnostic in payload["diagnostics"])
    assert output.read_text(encoding="utf-8") == "keep this content\n"


def test_ambiguous_top_and_invalid_root_fail_with_json(tmp_path):
    write_file(tmp_path, "a/top.v", "module top; endmodule\n")
    write_file(tmp_path, "b/top.v", "module top; endmodule\n")
    output = tmp_path / "fileset.f"

    ambiguous = run_cli(
        "--root", str(tmp_path), "--top", "top", "--output", str(output), "--json"
    )
    invalid_root = run_cli(
        "--root", str(tmp_path / "missing"), "--top", "top", "--output", str(output), "--json"
    )

    assert ambiguous.returncode != 0
    assert invalid_root.returncode != 0
    assert json.loads(ambiguous.stdout)["status"] == "FAILED"
    assert json.loads(invalid_root.stdout)["status"] == "FAILED"


def test_missing_top_fails_without_creating_output(tmp_path):
    write_file(tmp_path, "top.v", "module top; endmodule\n")
    output = tmp_path / "fileset.f"

    completed = run_cli(
        "--root", str(tmp_path), "--top", "unknown", "--output", str(output), "--json"
    )

    assert completed.returncode != 0
    assert not output.exists()
    payload = json.loads(completed.stdout)
    assert payload["status"] == "FAILED"
    assert payload["top"] is None

def test_same_file_declarations_are_scoped_to_selected_module(tmp_path):
    write_file(
        tmp_path,
        "bundle.v",
        "module top;\n"
        "  child u_child (.clk(clk));\n"
        "endmodule\n"
        "module child;\n"
        "endmodule\n"
        "module unrelated;\n"
        "  missing u_missing (.clk(clk));\n"
        "endmodule\n",
    )
    output = tmp_path / "fileset.f"

    completed = run_cli(
        "--root", str(tmp_path), "--top", "top", "--output", str(output), "--json"
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["summary"]["modules_in_closure"] == 2
    assert [dependency["name"] for dependency in payload["dependencies"]] == ["child"]
    assert payload["fileset"] == ["bundle.v"]


def test_workspace_root_uses_top_path_proximity_for_versioned_duplicates(tmp_path):
    write_file(
        tmp_path,
        "project/v4/rtl/top.v",
        "module top; cal_image_mean u_mean (.clk(clk)); endmodule\n",
    )
    write_file(tmp_path, "project/v2/rtl/cal_image_mean.v", "module cal_image_mean; endmodule\n")
    write_file(tmp_path, "project/v4/rtl/cal_image_mean.v", "module cal_image_mean; endmodule\n")
    output = tmp_path / "sim" / "fileset.f"

    completed = run_cli(
        "--root", str(tmp_path), "--top", "project/v4/rtl/top.v",
        "--output", str(output), "--json"
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["fileset"] == [
        "project/v4/rtl/cal_image_mean.v",
        "project/v4/rtl/top.v",
    ]
    assert any("path proximity" in item for item in payload["diagnostics"])


def test_identical_mirrored_dependencies_are_collapsed(tmp_path):
    write_file(
        tmp_path,
        "top.v",
        "module top; child u_child (.clk(clk)); endmodule\n",
    )
    child_source = "module child; endmodule\n"
    write_file(tmp_path, "src/lib-a/child.v", child_source)
    write_file(tmp_path, "src/lib-b/child.v", child_source)
    output = tmp_path / "fileset.f"

    completed = run_cli(
        "--root", str(tmp_path), "--top", "top.v",
        "--output", str(output), "--json"
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["fileset"] == ["src/lib-a/child.v", "top.v"]
    assert any("identical source" in item for item in payload["diagnostics"])
