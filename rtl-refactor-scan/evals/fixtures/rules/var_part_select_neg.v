module vps_neg (input [127:0] bus, output [31:0] out);
    assign out = bus[31:0];  // fixed
endmodule
