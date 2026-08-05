import json
from pathlib import Path
import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "rtl-context.schema.json"


def test_valid_context():
    ctx = {
        "top_module": "sample_fixt",
        "files": [{"path": "rtl/foo.v", "language": "verilog-2001"}],
        "clocks": [{"name": "clk_a", "domain": "A"}, {"name": "clk_b", "domain": "B"}],
        "resets": [{"name": "rst_n", "type": "async-low"}],
        "ports": [],
        "parameters": [],
        "testbench": None,
        "regression_command": None,
        "tool_availability": {"verilator": False},
        "user_confirmed_facts": []
    }
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(ctx, schema)


def test_multi_clock_detected():
    """多时钟域必须能被 context 表达（CDC 检测前置）。"""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert "clocks" in schema["properties"]
    assert schema["properties"]["clocks"]["type"] == "array"
