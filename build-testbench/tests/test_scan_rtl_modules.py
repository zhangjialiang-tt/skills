import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from scan_rtl_modules import scan_rtl


SCRIPT = Path(__file__).parents[1] / "scripts" / "scan_rtl_modules.py"


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_recursively_finds_verilog_systemverilog_and_vhdl(tmp_path):
    write_file(
        tmp_path,
        "zeta/multi.v",
        "// module fake;\nmodule real_a;\nendmodule\nmodule real_b;\nendmodule\n",
    )
    write_file(tmp_path, "alpha/unit.sv", "module sv_unit;\nendmodule\n")
    write_file(
        tmp_path,
        "beta/entity.vhd",
        "-- entity fake is\nentity vhdl_unit is\nend entity vhdl_unit;\n",
    )
    write_file(
        tmp_path,
        "beta/multiple.vhdl",
        "entity second_unit is\nend entity second_unit;\n"
        "entity third_unit is\nend entity third_unit;\n",
    )
    write_file(tmp_path, "README.txt", "module not_rtl;\n")
    write_file(tmp_path, "empty.v", "assign signal_a = signal_b;\n")

    result = scan_rtl(tmp_path)

    assert result["status"] == "SUCCESS"
    assert result["summary"] == {
        "files_scanned": 6,
        "rtl_files": 5,
        "files_with_modules": 4,
        "modules_found": 6,
    }
    assert [file["path"] for file in result["files"]] == [
        "alpha/unit.sv",
        "beta/entity.vhd",
        "beta/multiple.vhdl",
        "empty.v",
        "zeta/multi.v",
    ]
    assert result["files"][0]["language"] == "systemverilog"
    assert result["files"][1]["modules"] == [
        {"name": "vhdl_unit", "kind": "entity", "line": 2}
    ]
    assert result["files"][2]["modules"] == [
        {"name": "second_unit", "kind": "entity", "line": 1},
        {"name": "third_unit", "kind": "entity", "line": 3},
    ]
    assert result["files"][4]["modules"] == [
        {"name": "real_a", "kind": "module", "line": 2},
        {"name": "real_b", "kind": "module", "line": 4},
    ]


def test_comments_and_strings_do_not_create_declarations(tmp_path):
    write_file(
        tmp_path,
        "comments.v",
        "/* module block_fake; */\n"
        'initial $display("module string_fake;");\n'
        "// module line_fake;\n"
        "module actual;\nendmodule\n",
    )
    write_file(
        tmp_path,
        "comments.vhd",
        "-- entity line_fake is\n"
        'constant message : string := "entity string_fake is";\n'
        "entity actual_entity is\nend entity actual_entity;\n",
    )

    result = scan_rtl(tmp_path)

    assert result["files"][0]["modules"] == [
        {"name": "actual", "kind": "module", "line": 4}
    ]
    assert result["files"][1]["modules"] == [
        {"name": "actual_entity", "kind": "entity", "line": 3}
    ]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_json_cli_is_machine_readable_and_contains_no_diagnostics(tmp_path):
    write_file(tmp_path, "counter.v", "module counter;\nendmodule\n")

    completed = run_cli(str(tmp_path), "--json")

    assert completed.returncode == 0
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    assert payload["status"] == "SUCCESS"
    assert payload["files"][0]["modules"][0]["name"] == "counter"


def test_json_cli_reports_missing_root_without_fake_success(tmp_path):
    missing = tmp_path / "missing"

    completed = run_cli(str(missing), "--json")

    assert completed.returncode != 0
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    assert payload["status"] == "FAILED"
    assert payload["files"] == []
    assert payload["diagnostics"]


def test_json_cli_rejects_file_as_root(tmp_path):
    root_file = tmp_path / "not-a-directory.v"
    root_file.write_text("module not_a_root;\nendmodule\n", encoding="utf-8")

    completed = run_cli(str(root_file), "--json")

    assert completed.returncode != 0
    payload = json.loads(completed.stdout)
    assert payload["status"] == "FAILED"
    assert "directory" in payload["diagnostics"][0].lower()


def test_text_cli_reports_failure_on_stderr(tmp_path):
    completed = run_cli(str(tmp_path / "missing"))

    assert completed.returncode != 0
    assert completed.stdout == ""
    assert "ERROR" in completed.stderr
