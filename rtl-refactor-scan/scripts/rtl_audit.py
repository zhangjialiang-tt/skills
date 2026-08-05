#!/usr/bin/env python3
"""rtl-refactor-scan v2.0 确定性审计引擎。
按 rules.yaml 的 deterministic 规则扫描 RTL 源码，输出 Finding（E2）。

M2-2 起：逐步实现各 detect_* 函数。
M2-6：组装 audit_files() 主入口。
"""
