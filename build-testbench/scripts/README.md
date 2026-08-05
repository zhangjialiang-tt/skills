# build-testbench/scripts — RTL Fileset 构建工具

递归扫描 Verilog / SystemVerilog / VHDL 源文件，提取 module/entity 声明与实例化依赖，输出拓扑排序后的 simulator fileset。

## 文件结构

| 文件 | 功能 |
|------|------|
| `scan_rtl_modules.py` | 扫描 RTL 文件，提取 module/entity 声明（名称、类型、行号） |
| `build_fileset.py` | 解析依赖闭包，拓扑排序后写出 fileset 文件 |
| `workspace_root.py` | 从 RTL 文件或目录向上定位最近的 `.git` workspace 根 |

两个脚本既可独立使用（作为 CLI），也可作为模块导入（`scan_rtl` / `build_fileset`）。

---

## 快速开始

### 扫描目录，列出所有 module

```bash
# workspace 根目录扫描（推荐）
python .pi/skills/build-testbench/scripts/scan_rtl_modules.py path/to/rtl

# 多 root
python .pi/skills/build-testbench/scripts/scan_rtl_modules.py path/to/rtl path/to/ip_lib
```

输出示例：
```
path/to/rtl/foo.v:10 module foo
path/to/rtl/bar.v:23 module bar
path/to/ip_lib/baz.v:5 module baz
Scanned 3 RTL file(s), found 3 module/entity declaration(s).
```

### 构建 fileset（含依赖解析）

```bash
# workspace 根作为 root，top 使用 workspace-relative 文件路径
python .pi/skills/build-testbench/scripts/build_fileset.py \
  --root path/to/workspace \
  --top project/rtl/my_top_module.v \
  --output fileset.f

# 多 root（跨项目 + IP 库）
python .pi/skills/build-testbench/scripts/build_fileset.py \
  --root path/to/project/rtl \
   --root path/to/ip_lib \
  --root path/to/basic_modules \
  --top my_top_module \
  --output fileset.f
```

输出示例：
```
WARNING: resolved ambiguous dependency 'fifo' by language (verilog): chose 'ip_lib/fifo.v' over ['ip_lib/fifo.vhd']
Top: my_top_module (my_top_module.v)
Fileset: fileset.f
Resolved 8 module/entity declaration(s) in 8 file(s).
```

---

## CLI 参数

### `scan_rtl_modules.py`

```
positional arguments:
  root        Directory to scan recursively (one or more)

options:
  -h, --help  show this help message and exit
  --json      Emit one JSON result object
```

### `build_fileset.py`

```
options:
  -h, --help       show this help message and exit
  --root ROOT      RTL root directory (repeat to add multiple)
  --top TOP        Top module/entity name or RTL file
  --output OUTPUT  Output fileset path
  --json           Emit one JSON result object
```

**多 root 优先级规则**：`--root` 出现越早优先级越高。同名 module 在多个 root 中存在时，取先声明的 root。

---

## JSON 输出格式

### `scan_rtl_modules.py`

单 root（schema 1.0）：

```json
{
  "schema_version": "1.0",
  "root": "/abs/path/to/rtl",
  "status": "SUCCESS",
  "files": [
    {
      "path": "sub/module_a.v",
      "language": "verilog",
      "modules": [
        {"name": "module_a", "kind": "module", "line": 10}
      ]
    }
  ],
  "diagnostics": [],
  "summary": {
    "files_scanned": 42,
    "rtl_files": 15,
    "files_with_modules": 12,
    "modules_found": 18
  }
}
```

多 root（schema 1.1）：

```json
{
  "schema_version": "1.1",
  "roots": ["/abs/path/rtl", "/abs/path/ip_lib"],
  "status": "SUCCESS",
  "files": [
    {
      "path": "module_a.v",
      "language": "verilog",
      "root_index": 0,
      "modules": [{"name": "module_a", "kind": "module", "line": 10}]
    }
  ],
  "diagnostics": [],
  "summary": { "..." : "..." }
}
```

### `build_fileset.py`

```json
{
  "schema_version": "1.0",
  "status": "SUCCESS",
  "root": "/abs/path/to/rtl",
  "roots": ["/abs/path/to/rtl", "/abs/path/to/ip_lib"],
  "top": { "name": "my_top", "kind": "module", "path": "my_top.v" },
  "dependencies": [
    {"name": "fifo", "kind": "module", "path": "ip_lib/fifo.v"},
    {"name": "uart", "kind": "module", "path": "rtl/uart.v"}
  ],
  "fileset": [
    "ip_lib/fifo.v",
    "rtl/uart.v",
    "my_top.v"
  ],
  "output": "fileset.f",
  "diagnostics": [
    "WARNING: resolved ambiguous dependency 'clock_gen' by language..."
  ],
  "summary": {
    "modules_in_closure": 3,
    "files_in_closure": 3,
    "unresolved_dependencies": 0
  }
}
```

**字段说明**：

| 字段 | 说明 |
|------|------|
| `status` | `SUCCESS` 或 `FAILED` |
| `roots` | 多 root 模式下的所有根目录列表（仅 schema 1.1 / 多 root） |
| `top` | 顶层模块信息（name / kind / path） |
| `dependencies` | 顶层依赖列表（不含顶层自身） |
| `fileset` | **拓扑排序**后的文件列表（依赖在前，顶层在后） |
| `diagnostics` | 警告信息（歧义解决记录） |
| `summary` | 统计信息（模块数 / 文件数 / 未解析数） |

---

## 依赖消歧策略

当一个 module 名对应多个文件时，按以下顺序依次尝试消歧：

1. **Language 匹配** — Verilog 文件中的实例化优先匹配 `.v/.sv`，VHDL 优先匹配 `.vhd/.vhdl`
2. **Root priority** — 多 root 时按 `--root` 出现顺序，取最早声明的 root 中的文件
3. **Path priority** — 路径优先级：`ip/`、`lib/`、`rtl/`、`common/` > 普通路径 > `debug/`、`temp/`、`sim/`
4. **FAIL** — 上述规则仍无法唯一确定时，报错 `ambiguous dependency`

消歧成功时会输出 `WARNING` 级别的 diagnostics，方便审计。

---

## 作为模块导入

```python
import sys
sys.path.insert(0, ".pi/skills/build-testbench/scripts")

from scan_rtl_modules import scan_rtl, scan_multi_roots
from build_fileset import build_fileset, resolve_fileset

# 单 root 扫描
result = scan_rtl(Path("/path/to/rtl"))

# 多 root 扫描
result = scan_multi_roots([Path("/path/rtl"), Path("/path/ip")])

# 构建 fileset（返回 JSON 结果，不写文件）
result = resolve_fileset([Path("/path/rtl"), Path("/path/ip")], "my_top", "fileset.f")

# 构建 fileset（写入文件）
result = build_fileset([Path("/path/rtl"), Path("/path/ip")], "my_top", Path("fileset.f"))
```

---

## 支持的扩展名

| 扩展名 | 语言 |
|--------|------|
| `.v` | Verilog |
| `.sv` | SystemVerilog |
| `.vhd` | VHDL |
| `.vhdl` | VHDL |

---

## 已知限制

1. **依赖解析基于正则，非完整语法分析** — 不解析 `` `include `` / `` `define `` / 预处理条件
2. **实例化检测不覆盖所有 Verilog 语法** — 不支持位置关联（`mod_inst (.a, .b)`）和 `.*` 隐式端口（SystemVerilog）
3. **跨语言边界 IP** — Verilog 调用 VHDL 模块时需确保双方都在扫描路径内
4. **路径去重 first-match-wins** — 多 root 中相同相对路径的文件只保留第一个
5. **fileset 不包含 include 文件** — 需要单独用 `-incdir` 或类似机制告知 EDA 工具

---

## 返回值

| 状态码 | 含义 |
|--------|------|
| 0 | SUCCESS — 依赖完全解析，fileset 已生成 |
| 1 | FAILED — 有未解决的依赖、歧义或文件错误 |

---

## 设计原则

- **零外部依赖** — 仅 Python 3.8+ 标准库
- **不改变 RTL 源码** — 只扫描和分析，不修改任何文件
- **确定性输出** — 同输入同输出（fileset 顺序稳定）
- **渐进式降级** — 优先 warning，无法解决时才 FAIL
