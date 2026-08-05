// 干净模块：符合所有 deterministic 规则，用于验证误报基线。
module clean_fifo (
    input        clk,
    input        rst_n,
    input        valid_in,
    input [7:0]  data_in,
    output       ready_out,
    output       valid_out,
    output [7:0] data_out
);
    reg [7:0] mem [0:15];
    reg [3:0] wr_ptr, rd_ptr;
    reg       full, empty;

    always @(posedge clk) begin
        if (!rst_n) begin
            wr_ptr <= 4'h0;
            rd_ptr <= 4'h0;
            full   <= 1'b0;
            empty  <= 1'b1;
        end else begin
            if (valid_in && ready_out && !full) begin
                mem[wr_ptr] <= data_in;
                wr_ptr <= wr_ptr + 1'b1;
            end
            if (valid_out && !empty) begin
                rd_ptr <= rd_ptr + 1'b1;
            end
        end
    end

    assign ready_out = !full;
    assign valid_out = !empty;
    assign data_out  = mem[rd_ptr];
endmodule
