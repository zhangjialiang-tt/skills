module edge_m (
    input clk, input [31:0] din, output reg [31:0] comb
);
    always @(*) begin
        comb = din + 1;  // blocking in combinational, OK
    end
endmodule
