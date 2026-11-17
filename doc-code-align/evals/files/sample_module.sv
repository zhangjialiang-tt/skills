// sample_module.sv — doc-code-align eval fixture
// 单文件自洽：FSM/参数/常量/数据通路真值全部以此文件为准。
`timescale 1ns/1ps

module sample_module #(
    parameter int unsigned DEPTH      = 16, // 聚合深度（字节）
    parameter int unsigned RESET_WAIT = 4   // 复位后稳定等待拍数
)(
    input  logic       clk,
    input  logic       rst_n,
    input  logic       in_valid,
    input  logic [7:0] in_byte,
    output logic       out_valid,
    output logic [7:0] out_byte,
    input  logic       flush    // 流刷新：清聚合缓冲并回 IDLE
);

    typedef enum logic [1:0] {
        M_IDLE = 2'd0,
        M_RUN  = 2'd1,
        M_DONE = 2'd2
    } state_t;

    state_t             st_q;
    logic [31:0]        wait_q;
    logic [DEPTH*8-1:0] agg_q;

    // 预留常量：当前无任何消费点
    localparam int unsigned STALL_WARN_CYCLES = 128;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            st_q   <= M_IDLE;
            wait_q <= '0;
            agg_q  <= '0;
        end else begin
            if (wait_q < RESET_WAIT) wait_q <= wait_q + 1;
            unique case (st_q)
                M_IDLE: if (wait_q == RESET_WAIT-1 && in_valid) st_q <= M_RUN;
                M_RUN: begin
                    // 新字节从低位移入；旧内容向高位滚动
                    if (in_valid) agg_q <= {agg_q[DEPTH*8-9:0], in_byte};
                    if (flush) begin
                        agg_q <= '0;
                        st_q  <= M_IDLE;
                    end
                end
                M_DONE: st_q <= M_IDLE;
                default: st_q <= M_IDLE;
            endcase
        end
    end

    assign out_valid = (st_q == M_RUN) && in_valid;
    assign out_byte  = agg_q[7:0];

endmodule
