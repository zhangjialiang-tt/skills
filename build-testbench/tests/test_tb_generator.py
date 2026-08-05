import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from tb_generator import generate_testbench


def test_symbolic_width_can_be_declared_for_generated_template():
    source = generate_testbench(
        "dut", [{"name": "data", "direction": "input", "width": "DW-1:0"}],
        {"DW": "16"},
    )
    assert "localparam integer DW = 16;" in source
    assert "reg [DW-1:0] data;" in source
    assert "module tb_dut_l1;" in source
    assert "[SIM_RESULT] L1 PASS" in source
    assert ".DW (DW)" in source


def test_l1_uses_active_high_reset_and_valid_integer_width_syntax():
    source = generate_testbench(
        "dut",
        [
            {"name": "clk", "direction": "input", "width": 1},
            {"name": "rst", "direction": "input", "width": 1},
            {"name": "data", "direction": "input", "width": 16},
        ],
    )
    assert "reg [15:0] data;" in source
    assert "rst = 1;" in source
    assert "rst = 0;" in source
    assert "data = 0;" in source
