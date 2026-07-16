# RTL 重构模式参考

## §1 数组标量化

**目标**: 将小规模 unpacked array 转为标量寄存器，提升 EDA 调试可见性。

### 适用条件
- N ≤ 16（小规模寄存器组 / slice buffer / block row buffer）
- 不希望 EDA debug 解析 unpacked array 的内部调试路径

### 改前
```verilog
reg [W-1:0] arr [0:N-1];

always @(posedge clk) begin
    if (wr_en) begin
        arr[wr_idx] <= wr_data;
    end
end

assign out = arr[rd_idx];
```

### 改后
```verilog
reg [W-1:0] arr0;
reg [W-1:0] arr1;
reg [W-1:0] arr2;
// ... （N 个标量 reg）

always @(posedge clk) begin
    if (wr_en) begin
        case (wr_idx)
            0: arr0 <= wr_data;
            1: arr1 <= wr_data;
            2: arr2 <= wr_data;
            // ...
        endcase
    end
end

always @(*) begin
    case (rd_idx)
        0: out = arr0;
        1: out = arr1;
        2: out = arr2;
        // ...
        default: out = {W{1'bx}};
    endcase
end
```

### 不适用场景
- 大容量 RAM（>64 entries）
- line buffer / frame buffer
- FIFO memory
- 需要 BRAM 推断的结构

---

## §2 RAM 子模块化

**目标**: 将主模块内部 RAM-like array 拆成独立子模块，避免 EDA LA 直接探测内部 array。

### 适用条件
- history buffer / line buffer / frame buffer / cache buffer
- 深度 < 64k，宽度任意

### 改前
```verilog
// 在主模块内部
reg [DATA_W-1:0] mem [0:DEPTH-1];
```

### 改后

独立子模块 `xxx_ram.v`：
```verilog
module xxx_ram #(
    parameter ADDR_W = 8,
    parameter DATA_W = 16
) (
    input  wire               clk,
    input  wire               wr_en,
    input  wire [ADDR_W-1:0]  wr_addr,
    input  wire [DATA_W-1:0]  wr_data,
    input  wire               rd_en,
    input  wire [ADDR_W-1:0]  rd_addr,
    output reg  [DATA_W-1:0]  rd_data
);

reg [DATA_W-1:0] mem [0:(1<<ADDR_W)-1];

always @(posedge clk) begin
    if (wr_en) mem[wr_addr] <= wr_data;
    if (rd_en) rd_data <= mem[rd_addr];
end

endmodule
```

主模块只保留接口信号：
```verilog
wire [DATA_W-1:0] ram_rd_data;
reg  [ADDR_W-1:0] ram_wr_addr;
reg  [ADDR_W-1:0] ram_rd_addr;
reg               ram_wr_en;
reg               ram_rd_en;

xxx_ram #(
    .ADDR_W(ADDR_W),
    .DATA_W(DATA_W)
) u_ram (
    .clk     (clk),
    .wr_en   (ram_wr_en),
    .wr_addr (ram_wr_addr),
    .wr_data (ram_wr_data),
    .rd_en   (ram_rd_en),
    .rd_addr (ram_rd_addr),
    .rd_data (ram_rd_data)
);
```

---

## §3 Function 去综合路径化

**目标**: 将关键路径上的复杂 function 替换为等效的树形/流水/滚动结构。

### 滚动 min/max（推荐）
```verilog
// 滚动结构：每拍更新，无需尾部扫描
always @(posedge clk) begin
    if (reset || frame_start) begin
        run_min <= {PIXEL_W{1'b1}};
        run_max <= 0;
        first   <= 1'b1;
    end else if (pixel_valid) begin
        run_min <= first ? pixel : ((pixel < run_min) ? pixel : run_min);
        run_max <= first ? pixel : ((pixel > run_max) ? pixel : run_max);
        first   <= 1'b0;
    end
end
```

### 树形 sum/checksum
```verilog
// 两级树：将宽总线求和拆为并行加法器，改善时序
// 示例：16 个 8-bit 输入 → 4 个部分和 → 最终 sum
wire [7:0] data [0:15];  // 16 个 8-bit 输入（示例接口）
wire [10:0] sum_l0 [0:3]; // 4 个部分和（位宽扩展防溢出）
wire [11:0] sum_l1 [0:1];
wire [12:0] sum_final;

genvar gi;
generate
    for (gi = 0; gi < 4; gi = gi + 1) begin : sum_l0_gen
        // 每 4 个 8-bit 输入相加，得到部分和
        assign sum_l0[gi] = data[gi*4] + data[gi*4+1] + data[gi*4+2] + data[gi*4+3];
    end
endgenerate

// 第二级：2 个部分和相加
assign sum_l1[0] = sum_l0[0] + sum_l0[1];
assign sum_l1[1] = sum_l0[2] + sum_l0[3];

// 第三级：最终 sum
assign sum_final = sum_l1[0] + sum_l1[1];

// 注：实际项目中 data 可能是 128-bit 宽总线，需根据实际位宽调整
```

### 查表替换复杂计算
```verilog
// 复杂 if-else chain → case 查表
function [2:0] calc_ibits;
    input [16:0] range;
    begin
        casez (range)
            17'b0000_0000_0000_0000_1: calc_ibits = 3'd4;  // 1-1  → 2-bit
            17'b0000_0000_0000_0001_z: calc_ibits = 3'd4;  // 2-3  → 2-bit
            17'b0000_0000_0000_001z_z: calc_ibits = 3'd4;  // 4-7  → 4-bit
            17'b0000_0000_0000_01zz_zz: calc_ibits = 3'd4; // 8-15 → 4-bit
            17'b0000_0000_0000_1zzz_zz: calc_ibits = 3'd5; // 16-31 → 4-bit
            // ...
            default: calc_ibits = 3'd6; // ≥1024 → 16-bit
        endcase
    end
endfunction
```

---

## §4 Variable Part-Select 显式化

**目标**: 将固定结构的 variable part-select 写成显式位段，提升 EDA 调试稳定性。

### 适用条件
- 固定宽度和固定分段个数已知（如 32×16-bit → 32 个显式段）
- 关键大总线拆分/拼接（如 payload 打包/解包）

### 改前
```verilog
for (i = 0; i < 32; i = i + 1) begin
    out_data[i*16 +: 16] <= in_data[i*16 +: 16];
end
```

### 改后
当 32 个分段过多写出时，选择以下方案之一：
1. 显式写出小规模分段（≤8）
2. 用 `generate for` 配合 genvar（综合器展开层级名更好预测）
```verilog
genvar gi;
generate
    for (gi = 0; gi < 32; gi = gi + 1) begin : unpack
        wire [15:0] slice = in_data[gi*16 +: 16];
        // 每个 gi 生成独立层级 unpack[0].slice, unpack[1].slice...
    end
endgenerate
```
3. 对 ≤8 分段的固定总线直接显式位段
```verilog
assign out_data[127:112] = in_data[127:112];  // byte[7]
assign out_data[111:96]  = in_data[111:96];   // byte[6]
// ...
```

---

## §5 Debug Bus 标准化

**目标**: 为上板调试提供标准化的 64-bit debug bus，寄存输出、宏控制。

### 框架代码
```verilog
`ifdef DEBUG_XXX
// 输出声明（在端口列表中）
output wire [63:0] dbg_xxx_bus64,
output wire [63:0] dbg_xxx_event64,
`endif

// 内部寄存器（用 keep 防止被综合优化）
`ifdef DEBUG_XXX
(* keep = "true" *) reg [63:0] dbg_xxx_bus64_r;
(* keep = "true" *) reg [63:0] dbg_xxx_event64_r;

assign dbg_xxx_bus64   = dbg_xxx_bus64_r;
assign dbg_xxx_event64 = dbg_xxx_event64_r;

// debug bus 赋值（每个 cycle 持续反映状态）
always @(posedge clk) begin
    dbg_xxx_bus64_r[7:0]   <= pipe_state;
    dbg_xxx_bus64_r[15:8]  <= block_count;
    dbg_xxx_bus64_r[23:16] <= error_code;
    dbg_xxx_bus64_r[31:24] <= frame_id;
    dbg_xxx_bus64_r[39:32] <= block_ready;
    dbg_xxx_bus64_r[47:40] <= result_valid;
    dbg_xxx_bus64_r[63:48] <= 16'b0;  // reserved
end

// 事件现场锁存（第一次 fire 后锁住现场，不被覆盖）
always @(posedge clk) begin
    if (error_fire && dbg_xxx_event64_r[63:56] == 8'd0) begin
        dbg_xxx_event64_r <= {
            8'(error_code),        // [63:56] error type
            8'(block_cnt),         // [55:48] block count
            16'(pipeline_state),   // [47:32] pipeline dump
            32'(error_data)        // [31:0]  error data snapshot
        };
    end
end
`endif
```

---

## §6 混合赋值分离

**目标**: 将 `always @(posedge clk)` 中混合使用的 blocking(=) 和 non-blocking(<=) 赋值分离，消除综合-仿真一致风险。

### 改前
```verilog
integer i;
reg [15:0] tmp_val;

always @(posedge clk) begin
    if (valid) begin
        for (i = 0; i < N; i = i + 1) begin
            tmp_val = data[i*16 +: 16];       // blocking, intermediate
            deltas[i*16 +: 16] <= tmp_val;    // non-blocking, registered
        end
    end
end
```

### 改后（方案 A：分离组合块）
```verilog
// --- S2组合计算块 ---
reg [15:0] tmp_val_c [0:N-1];  // combinational array
integer i_c;

always @(*) begin
    for (i_c = 0; i_c < N; i_c = i_c + 1) begin
        tmp_val_c[i_c] = data[i_c*16 +: 16];
    end
end

// --- S2寄存器块 ---
always @(posedge clk) begin
    if (valid) begin
        for (i = 0; i < N; i = i + 1) begin
            deltas[i*16 +: 16] <= tmp_val_c[i];  // only non-blocking
        end
    end
end
```

### 改后（方案 B：直接展开为组合 wire）
```verilog
// 如果 N 很小，也可以直接使用 generate
genvar gi;
generate
    for (gi = 0; gi < N; gi = gi + 1) begin : delta_gen
        wire [15:0] slice_w = data[gi*16 +: 16];
        always @(posedge clk) begin
            if (valid) deltas[gi*16 +: 16] <= slice_w;
        end
    end
endgenerate
```

---

## §7 寄存器化 Ready

**目标**: 将纯组合的 ready 条件改为寄存器输出，改善时序并消除潜在组合环。

### 改前
```verilog
assign block_ready = !s1_valid && !s2_valid && !s3_valid
                  && (!s4_valid || (result_ready && !skid_valid));
```

### 改后
```verilog
reg block_ready_r;

always @(posedge clk) begin
    block_ready_r <= !s1_valid && !s2_valid && !s3_valid
                  && (!s4_valid || (result_ready && !skid_valid));
end

assign block_ready = block_ready_r;
```

**注意**: 改后 ready 输出延迟 1 cycle。对 drain-first pipeline 模型，只要上游不依赖 ready 的零延迟响应，此改动安全。需在回归中验证时间行为。
