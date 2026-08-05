module cdc_synced (
    input clk_a, input clk_b,
    input din, output reg dout
);
    reg sync_a, sync_b;
    always @(posedge clk_b) begin
        sync_a <= din;
        sync_b <= sync_a;  // 2-stage synchronizer
        dout   <= sync_b;
    end
endmodule
