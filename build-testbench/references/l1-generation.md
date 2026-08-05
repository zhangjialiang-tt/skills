# L1 生成参考

L1 目标是可运行骨架：依赖闭包可解析、路径正确、ModelSim 能完成编译 + elaboration + `run -all`、TB 打印 `[SIM_RESULT] L1 PASS`。L1 **不证明**算法、时序、边界条件或与 golden 一致。

## 端口提取

脚本：`scripts/tb_extract_ports.py`

```powershell
python .pi\skills\build-testbench\scripts\tb_extract_ports.py `
  --rtl-root $WorkspaceRoot `
  --top <top_module_name> `
  --json | Out-File -Encoding utf8 "$SimDir\ports.json"
```

常量表达式宽度归一化：`[8 - 1 : 0]` → `8`；符号宽度归一化为 `DW-1:0`。

### 支持的端口声明风格

- **ANSI 风格**（推荐）：方向在端口列表中声明，如 `input wire [7:0] foo`
- **Verilog-2001 风格**：端口名在 header，方向在 body 声明，如 `module foo(clk); input clk;`

### Fallback：脚本返回空数组 `[]`

说明 RTL 写法超出正则识别范围（interface、packed struct、宏生成实例等）。此时**手动创建** `ports.json`：

```json
[
  {"name": "clk", "direction": "input", "width": 1, "signed": false, "type": "wire"},
  {"name": "data", "direction": "output", "width": 8, "signed": false, "type": "wire"}
]
```

| 字段 | 说明 |
|------|------|
| `name` | 端口名 |
| `direction` | `input` / `output` / `inout` |
| `width` | 位宽（整数）；符号宽度用字符串如 `DW-1:0` |
| `signed` | 可选，布尔 |
| `type` | `wire` / `reg` 等，可选 |

## L1 testbench 生成

脚本：`scripts/tb_generator.py`

```powershell
python .pi\skills\build-testbench\scripts\tb_generator.py `
  --ports-file "$SimDir\ports.json" `
  --top <top_module_name> `
  --param DW=16 `
  --output "$SimDir\tb\tb_<top>_l1.v"
```

生成器行为：
- 自动检测时钟/复位信号名（子串匹配 `clk`/`clock`、`rst`/`reset`，含 `i_Sys_clk`、`i_Rst_n` 等变体）
- 复位极性按命名推断：`*_n` / `rstn` / `resetn` 为低有效，否则高有效
- 符号参数必须通过 `--param NAME=VALUE` 提供，不要把未定义的 `DW` 留给编译器
- 生成最小结构：DUT 例化 + 默认输入 + 时钟/复位 + VCD + `[SIM_RESULT] L1 PASS`

## 已知限制

- 端口提取基于正则，不解析完整 HDL 语法
- `interface`、`packed struct`、宏生成实例等复杂写法可能漏检 → 用 Fallback 手动创建
