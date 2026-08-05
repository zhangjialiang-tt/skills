"""验证 collect_context.py 能从 sample_fixt_known_defects.v 提取双时钟域。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from collect_context import collect_context

FIXTURE = Path(__file__).resolve().parent.parent / "evals" / "fixtures" / "sample_fixt_known_defects.v"


def test_extracts_module_name():
    ctx = collect_context([str(FIXTURE)])
    assert ctx["top_module"] == "sample_fixt"


def test_detects_two_clocks():
    ctx = collect_context([str(FIXTURE)])
    clock_names = [c["name"] for c in ctx["clocks"]]
    assert "clk_a" in clock_names
    assert "clk_b" in clock_names
    assert len(ctx["clocks"]) == 2


def test_detects_async_reset():
    ctx = collect_context([str(FIXTURE)])
    reset_names = [r["name"] for r in ctx["resets"]]
    assert "rst_n_async" in reset_names
