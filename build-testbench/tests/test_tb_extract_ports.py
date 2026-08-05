import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "tb_extract_ports.py"


def test_constant_expression_widths_are_normalized(tmp_path):
    source = tmp_path / "dut.v"
    source.write_text(
        "module dut(input wire [1 - 1 : 0] clk,"
        "input wire [8 - 1 : 0] data,"
        "input wire [DW - 1 : 0] param_data); endmodule\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--rtl-root", str(tmp_path),
         "--top", "dut", "--json"],
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0
    ports = json.loads(completed.stdout)
    assert [port["width"] for port in ports] == [1, 8, "DW-1:0"]
