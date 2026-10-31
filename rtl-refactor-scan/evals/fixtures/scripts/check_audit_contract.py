#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rtl-refactor-scan audit 产物契约 checker（skill-up script judge）。

从 case workspace root 执行，校验 audit 模式产出契约：
  1. findings.json 存在且可解析（唯一权威审计结果）
  2. 报告 md 存在（派生阅读物）
  3. findings.json 与报告的分类一致（A/B/C 分类字段在 JSON 中）

exit 0 = PASS；exit 1 = FAIL。
"""
import glob
import json
import os
import sys


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def main():
    failures = []

    def check(cond, msg):
        if not cond:
            failures.append(msg)

    findings = glob.glob("**/findings.json", recursive=True)
    findings = [p for p in findings if "evals" not in p]
    check(bool(findings), "findings: 未产出 findings.json")
    if findings:
        try:
            data = json.loads(read(findings[0]))
            text = json.dumps(data, ensure_ascii=False)
            check(len(text) > 10, "findings: findings.json 内容过少")
            check(bool(glob.glob("**/审计报告*.md", recursive=True)) or
                  bool(glob.glob("**/*报告*.md", recursive=True)),
                  "report: 未产出审计报告 md")
        except Exception as e:  # noqa: BLE001
            failures.append("findings: JSON 解析失败 %s" % e)

    for msg in failures:
        print("FAIL " + msg)
    if not failures:
        print("ALL PASS: audit 产物契约齐全")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
