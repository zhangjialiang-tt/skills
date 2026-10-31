#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""smart-commit 三态 git 状态 checker（skill-up script judge）。

从 case workspace root 执行，按 workspace 实际状态自适配判定：
  - 无 calc.py 且 HEAD==0：empty-staging-report 场景 → final message 须如实报告暂存区为空
  - calc.py+docs.md 且 HEAD==0：message-only-default 场景 → 须输出合规 message 且未 commit
  - calc.py 且 HEAD==1：explicit-commit-gate 场景 → 须已 commit 且 message 以 feat 开头

exit 0 = PASS；exit 1 = FAIL。
"""
import os
import re
import subprocess
import sys


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return (r.stdout or "").strip()


def main():
    failures = []

    def check(cond, msg):
        if not cond:
            failures.append(msg)

    final = os.environ.get("EVAL_FINAL_MESSAGE", "")
    has_calc = os.path.isfile("calc.py")
    has_docs = os.path.isfile("docs.md")
    head_count = int(git("rev-list", "--count", "HEAD") or 0)

    if not has_calc and not has_docs:
        # ---- empty-staging-report：无 staged、无 commit、如实报告空 ----
        check(head_count == 0, "no-commit: 不应产生 commit（HEAD=%d）" % head_count)
        check(bool(re.search(r"空|没有|无|empty|nothing", final, re.I)),
              "empty-report: 汇报未如实说明暂存区为空")
    elif has_calc and has_docs:
        # ---- message-only-default：未 commit + 输出合规 message ----
        check(head_count == 0, "no-commit: 要求不提交，HEAD 计数应为 0（实际 %d）" % head_count)
        check(bool(re.search(r"(feat|fix|docs|chore|refactor)\b", final, re.I)) and
              bool(re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2705\u274C\u2B50]", final)),
              "message-format: 输出缺 type+emoji 格式 commit message")
        check(bool(re.search(r"add|mul|feat", final, re.I)),
              "message-content: 输出未覆盖实际变更内容")
    elif has_calc:
        # ---- explicit-commit-gate：已 commit 且 feat 开头 ----
        check(head_count == 1, "commit-once: HEAD 计数应为 1（实际 %d）" % head_count)
        msg = git("log", "-1", "--format=%s")
        check(bool(re.match(r"^feat", msg)), "message-format: HEAD message 未以 feat 开头（%s）" % msg)
    else:
        failures.append("fixture: workspace 状态不符合任一 case 预设")

    for msg in failures:
        print("FAIL " + msg)
    if not failures:
        print("ALL PASS: git 状态判定通过")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
