// fixture for rtl-refactor-scan smoke eval
// 故意植入多种已知缺陷，用于验证扫描器能否识别并分级。

module sample_fixt (
    input  wire        clk_a,
    input  wire        clk_b,
    input  wire        rst_n_async,
    input  wire        din_valid,
    input  wire [31:0] din_data,
    input  wire        din_last,
    output wire        dout_valid,
    output wire [31:0] dout_data,
    output wire        dout_last
);

    // ---- 缺陷 1：混合 blocking/non-blocking 赋值 ----
    reg [31:0] mixed_reg;
    always @(posedge clk_a) begin
        if (!rst_n_async) begin
            mixed_reg <= 32'h0;            // non-blocking
        end else begin
            mixed_reg = din_data;          // 行 N1：混用 blocking
        end
    end

    // ---- 缺陷 2：缺少复位（仿真默认值在 FPGA 上可能 X） ----
    reg [31:0] no_rst_reg;
    always @(posedge clk_a) begin
        no_rst_reg <= din_data;            // 行 N2：缺复位
    end

    // ---- 缺陷 3：variable part-select ----
    reg [127:0] wide_bus;
    reg [31:0]  part_out;
    always @(*) begin
        part_out = wide_bus[din_data[1:0]*32 +: 32];  // 行 N3：variable part-select
    end

    // ---- 缺陷 4：unpacked array（规模较小但 EDA debug 不稳） ----
    reg [7:0] history [0:15];
    integer i;
    always @(posedge clk_a) begin
        history[0] <= din_data[7:0];       // 行 N4：unpacked array 直接探测
        for (i = 1; i < 16; i = i + 1) begin
            history[i] <= history[i-1];
        end
    end

    // ---- 缺陷 5：单 bit 跨时钟未同步 ----
    reg cdc_pulse;
    always @(posedge clk_a) cdc_pulse <= din_valid;
    always @(posedge clk_b) dout_valid <= cdc_pulse;  // 行 N5：单 bit 跨时钟无同步器

    // ---- 缺陷 6：多 bit 总线直接打拍跨时钟 ----
    reg [31:0] cdc_bus;
    always @(posedge clk_a) cdc_bus <= mixed_reg;
    always @(posedge clk_b) dout_data <= cdc_bus;     // 行 N6：多 bit 直接打拍跨时钟

    assign dout_last = din_last;

endmodule
