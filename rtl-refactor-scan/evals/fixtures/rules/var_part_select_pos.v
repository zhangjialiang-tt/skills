module vps (input [127:0] bus, input [1:0] idx, output [31:0] out);
    assign out = bus[idx*32 +: 32];  // variable part-select
endmodule
