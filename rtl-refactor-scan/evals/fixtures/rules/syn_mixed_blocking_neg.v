module neg (
    input clk, input rst_n, input [31:0] din,
    output reg [31:0] dout
);
    always @(posedge clk) begin
        if (!rst_n) dout <= 32'h0;
        else        dout <= din;
    end
endmodule
