// ============================================================================
// L2 Testbench Template — {MODULE_NAME}
// ============================================================================
// 结构：clock/reset → DUT → driver → monitor → checker → testcase controller
//
// 使用方式：
// 1. 根据 simulation_plan.md 中的测试用例，填充 task drive_tc01/task drive_tc02/...
// 2. 根据 Checker 策略，填充 task check_tc01/task check_tc02/...
// 3. 如需数据重建，使用 frame/memory 模型部分
// 4. 参数值从 plan 中的参数表读取
// ============================================================================

`timescale 1ns / 1ps

module tb_{MODULE_NAME}_l2;

    // -------------------------------------------------------------------------
    // Parameters — 从 simulation_plan.md 的参数表读取
    // -------------------------------------------------------------------------
    localparam integer FRAME_WIDTH        = 640;
    localparam integer FRAME_HEIGHT       = 512;
    localparam integer PIXEL_WIDTH        = 16;
    localparam integer BLOCK_W            = 8;
    localparam integer BLOCK_H            = 4;
    localparam integer BLOCK_X_W          = 8;
    localparam integer BLOCK_Y_W          = 8;
    localparam integer AXI_DATA_WIDTH     = 32;
    localparam integer ADDR_WIDTH         = 32;
    localparam integer LEN_WIDTH          = 20;
    localparam integer TAG_WIDTH          = 8;

    // 时序参数
    localparam integer CLK_PERIOD = 10;  // 100MHz
    localparam integer RESET_CYCLES = 20;
    localparam integer TIMEOUT = 100000;  // 全局超时

    // -------------------------------------------------------------------------
    // Clock / Reset
    // -------------------------------------------------------------------------
    reg clk;
    reg rst;

    initial clk = 0;
    always #(CLK_PERIOD / 2) clk = ~clk;

    initial begin
        rst = 1;
        repeat(RESET_CYCLES) @(posedge clk);
        rst = 0;
    end

    // -------------------------------------------------------------------------
    // DUT Interface Signals — 从 ports.json 生成
    // -------------------------------------------------------------------------
    // 控制流
    reg                   i_frame_start;
    wire                  o_frame_start_ready;
    reg  [ADDR_WIDTH-1:0] i_frame_base;
    reg  [15:0]           i_parah;
    reg  [15:0]           i_paratype;
    reg  [15:0]           i_frame_id;
    reg                   i_error_clear;

    // 数据输入 (result stream)
    reg                                       s_result_valid;
    wire                                      s_result_ready;
    reg  [7:0]                                s_ibits;
    reg  signed [PIXEL_WIDTH-1:0]             s_min_value;
    reg  [BLOCK_W*BLOCK_H*PIXEL_WIDTH-1:0]    s_payload_data;
    reg  [6:0]                                s_payload_bytes;
    reg  [BLOCK_X_W-1:0]                      s_block_x;
    reg  [BLOCK_Y_W-1:0]                      s_block_y;
    reg                                       s_result_last;

    // 数据输入 (param stream)
    reg         s_param_valid;
    wire        s_param_ready;
    reg  [15:0] s_param_data;
    reg         s_param_last;

    // DMA 写描述符 (DUT 输出)
    wire [ADDR_WIDTH-1:0] m_axis_write_desc_addr;
    wire [LEN_WIDTH-1:0]  m_axis_write_desc_len;
    wire [TAG_WIDTH-1:0]  m_axis_write_desc_tag;
    wire                  m_axis_write_desc_valid;
    reg                   m_axis_write_desc_ready;

    // DMA 写数据 (DUT 输出)
    wire [AXI_DATA_WIDTH-1:0]     m_axis_write_data_tdata;
    wire [AXI_DATA_WIDTH/8-1:0]   m_axis_write_data_tkeep;
    wire                          m_axis_write_data_tvalid;
    reg                           m_axis_write_data_tready;
    wire                          m_axis_write_data_tlast;
    wire [7:0]                    m_axis_write_data_tid;
    wire [7:0]                    m_axis_write_data_tdest;
    wire                          m_axis_write_data_tuser;

    // DMA 写状态 (DUT 输入，模拟 DMA 控制器响应)
    reg  [LEN_WIDTH-1:0] s_axis_write_desc_status_len;
    reg  [TAG_WIDTH-1:0] s_axis_write_desc_status_tag;
    reg  [7:0]           s_axis_write_desc_status_id;
    reg  [7:0]           s_axis_write_desc_status_dest;
    reg                  s_axis_write_desc_status_user;
    reg  [3:0]           s_axis_write_desc_status_error;
    reg                  s_axis_write_desc_status_valid;

    // 帧状态输出
    wire                  o_frame_ready;
    wire [ADDR_WIDTH-1:0] o_frame_base;
    wire [LEN_WIDTH-1:0]  o_frame_size;
    wire [LEN_WIDTH-1:0]  o_payload_size;
    wire [15:0]           o_frame_id;
    wire                  o_busy;
    wire                  o_error;
    wire [7:0]            o_error_code;

    // Debug 输出
    wire [31:0] o_dbg_word0;
    wire [31:0] o_dbg_word1;
    // ... (根据需要展开)

    // -------------------------------------------------------------------------
    // DUT Instance
    // -------------------------------------------------------------------------
    {MODULE_NAME} #(
        .FRAME_WIDTH        (FRAME_WIDTH),
        .FRAME_HEIGHT       (FRAME_HEIGHT),
        .PIXEL_WIDTH        (PIXEL_WIDTH),
        .BLOCK_W            (BLOCK_W),
        .BLOCK_H            (BLOCK_H),
        .BLOCK_X_W          (BLOCK_X_W),
        .BLOCK_Y_W          (BLOCK_Y_W),
        .AXI_DATA_WIDTH     (AXI_DATA_WIDTH),
        .ADDR_WIDTH         (ADDR_WIDTH),
        .LEN_WIDTH          (LEN_WIDTH),
        .TAG_WIDTH          (TAG_WIDTH)
    ) dut (
        .clk(clk),
        .rst(rst),
        .i_frame_start(i_frame_start),
        .o_frame_start_ready(o_frame_start_ready),
        .i_frame_base(i_frame_base),
        .i_parah(i_parah),
        .i_paratype(i_paratype),
        .i_frame_id(i_frame_id),
        .i_error_clear(i_error_clear),
        .s_result_valid(s_result_valid),
        .s_result_ready(s_result_ready),
        .s_ibits(s_ibits),
        .s_min_value(s_min_value),
        .s_payload_data(s_payload_data),
        .s_payload_bytes(s_payload_bytes),
        .s_block_x(s_block_x),
        .s_block_y(s_block_y),
        .s_result_last(s_result_last),
        .s_param_valid(s_param_valid),
        .s_param_ready(s_param_ready),
        .s_param_data(s_param_data),
        .s_param_last(s_param_last),
        .m_axis_write_desc_addr(m_axis_write_desc_addr),
        .m_axis_write_desc_len(m_axis_write_desc_len),
        .m_axis_write_desc_tag(m_axis_write_desc_tag),
        .m_axis_write_desc_valid(m_axis_write_desc_valid),
        .m_axis_write_desc_ready(m_axis_write_desc_ready),
        .m_axis_write_data_tdata(m_axis_write_data_tdata),
        .m_axis_write_data_tkeep(m_axis_write_data_tkeep),
        .m_axis_write_data_tvalid(m_axis_write_data_tvalid),
        .m_axis_write_data_tready(m_axis_write_data_tready),
        .m_axis_write_data_tlast(m_axis_write_data_tlast),
        .m_axis_write_data_tid(m_axis_write_data_tid),
        .m_axis_write_data_tdest(m_axis_write_data_tdest),
        .m_axis_write_data_tuser(m_axis_write_data_tuser),
        .s_axis_write_desc_status_len(s_axis_write_desc_status_len),
        .s_axis_write_desc_status_tag(s_axis_write_desc_status_tag),
        .s_axis_write_desc_status_id(s_axis_write_desc_status_id),
        .s_axis_write_desc_status_dest(s_axis_write_desc_status_dest),
        .s_axis_write_desc_status_user(s_axis_write_desc_status_user),
        .s_axis_write_desc_status_error(s_axis_write_desc_status_error),
        .s_axis_write_desc_status_valid(s_axis_write_desc_status_valid),
        .o_frame_ready(o_frame_ready),
        .o_frame_base(o_frame_base),
        .o_frame_size(o_frame_size),
        .o_payload_size(o_payload_size),
        .o_frame_id(o_frame_id),
        .o_busy(o_busy),
        .o_error(o_error),
        .o_error_code(o_error_code),
        .o_dbg_word0(o_dbg_word0),
        .o_dbg_word1(o_dbg_word1)
        // ... (根据需要展开)
    );

    // -------------------------------------------------------------------------
    // Memory / Frame Model — 用于 DMA 写数据重建（如 Checker 需要）
    // -------------------------------------------------------------------------
    // 模拟 DUT 下游的内存，DMA 写入时记录数据
    reg [7:0] mem_model [0:4095];  // 4KB frame buffer
    integer mem_write_count;
    integer dma_desc_count;
    integer dma_data_byte_count;

    initial begin
        mem_write_count = 0;
        dma_desc_count = 0;
        dma_data_byte_count = 0;
    end

    // 抓取 DMA 写描述符
    always @(posedge clk) begin
        if (m_axis_write_desc_valid && m_axis_write_desc_ready) begin
            dma_desc_count = dma_desc_count + 1;
            $display("[MON] DMA_DESC #%0d: addr=0x%08x len=%0d tag=%0d",
                     dma_desc_count,
                     m_axis_write_desc_addr,
                     m_axis_write_desc_len,
                     m_axis_write_desc_tag);
        end
    end

    // 抓取 DMA 写数据到 mem_model
    always @(posedge clk) begin
        if (m_axis_write_data_tvalid && m_axis_write_data_tready) begin
            // 根据 m_axis_write_desc_addr 偏移写入 mem_model
            // 简化版：顺序记录，实际应根据 desc_addr 计算偏移
            mem_model[dma_data_byte_count + 0] = m_axis_write_data_tdata[7:0];
            mem_model[dma_data_byte_count + 1] = m_axis_write_data_tdata[15:8];
            mem_model[dma_data_byte_count + 2] = m_axis_write_data_tdata[23:16];
            mem_model[dma_data_byte_count + 3] = m_axis_write_data_tdata[31:24];
            dma_data_byte_count = dma_data_byte_count + 4;
        end
    end

    // -------------------------------------------------------------------------
    // DMA 响应模型 — 模拟 DMA 控制器返回写状态
    // -------------------------------------------------------------------------
    // 在 DUT 发出 desc 后，延迟若干周期返回 status
    initial begin
        s_axis_write_desc_status_valid = 0;
        s_axis_write_desc_status_error = 0;
        // 可添加自动响应逻辑
    end

    // 简易自动响应：desc valid 后 5 周期返回 status
    reg [TAG_WIDTH-1:0] pending_tag;
    reg [2:0]           status_delay;
    reg                 status_pending;

    always @(posedge clk) begin
        if (rst) begin
            status_pending <= 0;
            s_axis_write_desc_status_valid <= 0;
        end else begin
            s_axis_write_desc_status_valid <= 0;

            if (m_axis_write_desc_valid && m_axis_write_desc_ready) begin
                pending_tag <= m_axis_write_desc_tag;
                status_delay <= 3'd5;
                status_pending <= 1;
            end else if (status_pending && status_delay > 0) begin
                status_delay <= status_delay - 1;
            end else if (status_pending) begin
                s_axis_write_desc_status_valid <= 1;
                s_axis_write_desc_status_tag <= pending_tag;
                s_axis_write_desc_status_error <= 4'd0;
                status_pending <= 0;
            end
        end
    end

    // -------------------------------------------------------------------------
    // Testcase Driver Tasks — 每个 TC 一个 task
    // -------------------------------------------------------------------------

    // TC01: 典型主路径
    task drive_tc01;
        integer i;
        begin
            @(posedge clk);
            // 帧配置
            i_frame_base = 32'h1000;
            i_parah = 16'd0;
            i_paratype = 16'd0;
            i_frame_id = 16'd1;

            // 启动帧
            wait(o_frame_start_ready);
            @(posedge clk);
            i_frame_start = 1;
            @(posedge clk);
            i_frame_start = 0;

            // 输入 block result 流
            // (根据 plan 中的描述，展开具体激励)
            // ...

            // 等待帧完成
            wait(o_frame_ready);
            @(posedge clk);
        end
    endtask

    // TC02: 变体场景
    task drive_tc02;
        begin
            @(posedge clk);
            // ...
        end
    endtask

    // TC03: 错误注入
    task drive_tc03;
        begin
            @(posedge clk);
            // 注入非法 payload_bytes 触发 ERR_BAD_PAYLOAD
            // ...
        end
    endtask

    // -------------------------------------------------------------------------
    // Checker Tasks — 每个 TC 一个 checker
    // -------------------------------------------------------------------------

    integer pass_count;
    integer fail_count;

    task check_tc01;
        begin
            $display("[CHK] TC01: Checking frame output...");
            if (o_frame_size == EXPECTED_FRAME_SIZE) begin
                $display("[CHK] TC01 PASS: o_frame_size=%0d (expected %0d)", o_frame_size, EXPECTED_FRAME_SIZE);
                pass_count = pass_count + 1;
            end else begin
                $display("[CHK] TC01 FAIL: o_frame_size=%0d (expected %0d)", o_frame_size, EXPECTED_FRAME_SIZE);
                fail_count = fail_count + 1;
            end
        end
    endtask

    task check_tc02;
        begin
            // ...
        end
    endtask

    task check_tc03;
        begin
            $display("[CHK] TC03: Checking error code...");
            if (o_error == 1 && o_error_code == 8'd1) begin  // ERR_BAD_PAYLOAD = 1
                $display("[CHK] TC03 PASS: o_error=1, o_error_code=%0d (ERR_BAD_PAYLOAD)", o_error_code);
                pass_count = pass_count + 1;
            end else begin
                $display("[CHK] TC03 FAIL: o_error=%0d, o_error_code=%0d (expect error=1, code=1)", o_error, o_error_code);
                fail_count = fail_count + 1;
            end
        end
    endtask

    // -------------------------------------------------------------------------
    // 期望值定义 — 从 simulation_plan.md 的期望输出列读取
    // -------------------------------------------------------------------------
    localparam integer EXPECTED_FRAME_SIZE = 1234;  // 根据 plan 修改
    // ...

    // -------------------------------------------------------------------------
    // Testcase Controller — 顺序执行所有 TC，打印汇总
    // -------------------------------------------------------------------------
    initial begin
        // 初始化
        i_frame_start = 0;
        i_frame_base = 0;
        i_parah = 0;
        i_paratype = 0;
        i_frame_id = 0;
        i_error_clear = 0;
        s_result_valid = 0;
        s_ibits = 0;
        s_min_value = 0;
        s_payload_data = 0;
        s_payload_bytes = 0;
        s_block_x = 0;
        s_block_y = 0;
        s_result_last = 0;
        s_param_valid = 0;
        s_param_data = 0;
        s_param_last = 0;
        m_axis_write_desc_ready = 1;
        m_axis_write_data_tready = 1;

        pass_count = 0;
        fail_count = 0;

        wait(!rst);
        repeat(10) @(posedge clk);

        // --- TC01 ---
        $display("========== TC01: 典型主路径 ==========");
        drive_tc01;
        check_tc01;

        // --- TC02 ---
        $display("========== TC02: 变体场景 ==========");
        drive_tc02;
        check_tc02;

        // --- TC03 ---
        $display("========== TC03: 错误注入 ==========");
        drive_tc03;
        check_tc03;

        // (根据 plan 添加更多 TC)

        // --- 汇总 ---
        $display("=====================================");
        $display("[SIM_RESULT] L2 %0s (%0d/%0d passed)",
                 (fail_count == 0) ? "PASS" : "FAIL",
                 pass_count, pass_count + fail_count);
        $display("=====================================");

        $finish;
    end

    // -------------------------------------------------------------------------
    // 超时保护
    // -------------------------------------------------------------------------
    initial begin
        #TIMEOUT;
        $display("[ERROR] Simulation timeout after %0d cycles!", TIMEOUT);
        $display("[SIM_RESULT] L2 FAIL (timeout)");
        $finish;
    end

    // -------------------------------------------------------------------------
    // VCD dump
    // -------------------------------------------------------------------------
    initial begin
        $dumpfile("log/{MODULE_NAME}_l2.vcd");
        $dumpvars(0, tb_{MODULE_NAME}_l2);
    end

endmodule
