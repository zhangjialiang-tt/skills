module pos (
    input clk, input rst_n, input [31:0] din,
    output reg [31:0] dout
);
    reg [31:0] tmp;
    always @(posedge clk) begin
        if (!rst_n) begin
            tmp <= 32'h0;
            dout <= 32'h0;
        end else begin
            tmp = din;          // blocking
            dout <= tmp + din;  // non-blocking
        end
    end
endmodule
