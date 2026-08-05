module cdc_multi (
    input clk_a, input clk_b,
    input [31:0] din, output reg [31:0] dout
);
    reg [31:0] bus;
    always @(posedge clk_a) bus  <= din;
    always @(posedge clk_b) dout <= bus;  // 多bit直接跨域
endmodule
