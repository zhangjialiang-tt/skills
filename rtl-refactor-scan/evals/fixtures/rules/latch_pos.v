module lat (input a, input b, output reg q);
    always @(*) begin
        if (a) q = b;
        // 缺 else -> latch
    end
endmodule
