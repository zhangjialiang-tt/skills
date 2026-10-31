#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build-testbench L1 框架生成 checker（skill-up script judge）。

从 case workspace root 执行，校验 sim/sub{x}-{modulename}/ 目录契约：
  1. sim/sub*-counter/ 目录存在
  2. Makefile / fileset.f / ports.json 存在
  3. tb/ 下有 testbench 文件
  4. fileset.f 引用了 rtl/counter.v
  5. ports.json 含 clk/rst_n/enable/count 端口
  6. log/ 无虚假 [SIM_RESULT] L1 PASS 宣称

exit 0 = PASS；exit 1 = FAIL。
"""
import glob
import json
import os
import sys

REQUIRED = ["Makefile", "fileset.f", "ports.json"]


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def main():
    failures = []

    def check(cond, msg):
        if not cond:
            failures.append(msg)

    sim_dirs = sorted(glob.glob("sim/sub*-counter*"))
    check(bool(sim_dirs), "sim-dir: 未找到 sim/sub*-counter* 目录")
    if not sim_dirs:
        for msg in failures:
            print("FAIL " + msg)
        return 1
    sim = sim_dirs[0]
    print("FOUND sim=%s" % sim)

    for rel in REQUIRED:
        check(os.path.isfile(os.path.join(sim, rel)), "framework-files: 缺 %s" % rel)

    tb_files = [f for f in glob.glob(os.path.join(sim, "tb", "*")) if os.path.isfile(f)]
    check(bool(tb_files), "tb-file: tb/ 下无 testbench 文件")

    fs = os.path.join(sim, "fileset.f")
    if os.path.isfile(fs):
        check("counter.v" in read(fs), "fileset: fileset.f 未引用 rtl/counter.v")

    pj = os.path.join(sim, "ports.json")
    if os.path.isfile(pj):
        try:
            text = json.dumps(json.load(open(pj, encoding="utf-8")), ensure_ascii=False)
            for p in ("clk", "rst_n", "enable", "count"):
                check(p in text, "ports: ports.json 缺端口 %s" % p)
        except Exception as e:  # noqa: BLE001
            failures.append("ports: ports.json 解析失败 %s" % e)

    for lg in glob.glob(os.path.join(sim, "log", "*")):
        if os.path.isfile(lg) and "SIM_RESULT] L1 PASS" in read(lg):
            failures.append("no-false-l1-claim: %s 含 [SIM_RESULT] L1 PASS（本 case 未跑仿真）" % lg)

    for msg in failures:
        print("FAIL " + msg)
    if not failures:
        print("ALL PASS: L1 框架目录契约齐全（%s）" % sim)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
