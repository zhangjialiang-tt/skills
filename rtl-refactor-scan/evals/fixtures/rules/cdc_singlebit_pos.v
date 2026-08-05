module cdc_single (
    input clk_a, input clk_b,
    input din, output reg dout
);
    reg pulse;
    always @(posedge clk_a) pulse <= din;
    always @(posedge clk_b) dout  <= pulse;  // 直接跨域
endmodule
