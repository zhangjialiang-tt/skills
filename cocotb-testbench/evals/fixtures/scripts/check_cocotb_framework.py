#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cocotb-testbench 框架生成 checker（skill-up script judge）。

从 case workspace root 执行，校验 sim/<top>/ 框架契约与措辞纪律：
  1. sim/ 下有测试目录
  2. Python test 文件含 cocotb import 与 smoke/functional 分级
  3. runner 配置（Makefile 或 runner 脚本/pyproject）存在
  4. 产出文档无"功能验证通过/功能正确"宣称（无 golden 场景）

exit 0 = PASS；exit 1 = FAIL。
"""
import glob
import os
import re
import sys


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def main():
    failures = []

    def check(cond, msg):
        if not cond:
            failures.append(msg)

    sim_subdirs = [d for d in glob.glob("sim/*") if os.path.isdir(d)]
    check(bool(sim_subdirs), "sim-dir: sim/ 下无测试目录")
    if not sim_subdirs:
        for msg in failures:
            print("FAIL " + msg)
        return 1
    sim = sim_subdirs[0]
    print("FOUND sim=%s" % sim)

    py_tests = [f for f in glob.glob(os.path.join(sim, "**", "test_*.py"), recursive=True) + \
        glob.glob(os.path.join(sim, "tb", "*.py")) + \
        glob.glob("test_*.py") if os.path.isfile(f)]
    check(bool(py_tests), "py-test: 无 cocotb Python 测试文件（test_*.py）")
    if py_tests:
        t = read(py_tests[0])
        check("cocotb" in t, "py-test: %s 缺 cocotb import" % py_tests[0])
        check(bool(re.search(r"smoke|functional", t)),
              "py-test: 未体现 smoke/functional 分级")

    py_all = [f for f in glob.glob(os.path.join(sim, "**", "*.py"), recursive=True) if os.path.isfile(f)]
    runners = [f for f in glob.glob(os.path.join(sim, "**", "Makefile"), recursive=True) + \
        glob.glob(os.path.join(sim, "**", "runner*.py"), recursive=True) + \
        glob.glob(os.path.join(sim, "**", "pyproject.toml"), recursive=True) + \
        [f for f in py_all if "get_runner" in read(f) or "cocotb.runner" in read(f)] if os.path.isfile(f)]
    check(bool(runners), "runner: 缺 runner 配置（Makefile/runner.py/pyproject.toml/含 runner API 的 .py）")

    docs = glob.glob(os.path.join(sim, "**", "*.md"), recursive=True)
    for p in docs:
        if re.search(r"已验证功能正确|功能验证通过[。！]|功能验证：\s*PASS|✅\s*功能正确", read(p)):
            failures.append("wording: %s 含'功能验证通过/功能正确'宣称（无 golden 应 characterization 降级）" % p)

    for msg in failures:
        print("FAIL " + msg)
    if not failures:
        print("ALL PASS: cocotb 框架契约齐全（%s）" % sim)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
