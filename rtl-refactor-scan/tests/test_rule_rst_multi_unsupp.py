import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from rtl_audit import detect_missing_reset, detect_multi_driver, detect_unsupported_construct

RST_TEXT = """module m (input clk, input rst_n, input [31:0] din, output reg [31:0] q);
    always @(posedge clk) begin
        q <= din;
    end
endmodule
"""

MULTI_TEXT = """module m (input clk, output reg q);
    always @(posedge clk) q <= 1'b0;
    always @(posedge clk) q <= 1'b1;
endmodule
"""

UNSUPP_TEXT = """module m;
    initial begin
        $display("hi");
    end
endmodule
"""


def test_missing_reset():
    findings = detect_missing_reset(RST_TEXT, "r.v")
    assert any(f["rule_id"] == "RST-MISSING-001" for f in findings)


def test_multi_driver():
    findings = detect_multi_driver(MULTI_TEXT, "m.v")
    assert any(f["rule_id"] == "SYN-MULTI-DRIVER-001" for f in findings)


def test_unsupported_construct():
    findings = detect_unsupported_construct(UNSUPP_TEXT, "u.v")
    assert any(f["rule_id"] == "SYN-UNSUPPORTED-CONSTRUCT-001" for f in findings)
