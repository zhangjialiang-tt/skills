#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hyperframes-video 内容三件套 checker（skill-up script judge）。

从 case workspace root 执行，校验 Phase 3 内容三件套契约：
  1. project/script.md：含语速预算与事实核查表
  2. project/storyboard.md：场景时长闭合（之和 == 总时长）
  3. project/design_system.md：色板/字体/动画节奏

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

    # ---- 1. script.md ----
    scripts = [p for p in glob.glob("project/script.md") if os.path.isfile(p)]
    check(bool(scripts), "script: 未找到 project/script.md")
    if scripts:
        t = read(scripts[0])
        check(bool(re.search(r"语速|字数|budget|每分钟|字/秒", t, re.I)),
              "script-speed: script.md 无语速/字数预算标注")
        check(bool(re.search(r"事实核查|核查表|官方依据|来源", t)),
              "script-factcheck: script.md 无事实核查表/依据标注")

    # ---- 2. storyboard.md 时长闭合 ----
    sbs = [p for p in glob.glob("project/storyboard.md") if os.path.isfile(p)]
    check(bool(sbs), "storyboard: 未找到 project/storyboard.md")
    if sbs:
        t = read(sbs[0])
        nums = re.findall(r"(\d+(?:\.\d+)?)\s*s(?:ec|econd)?\s*[|｜]", t, re.I)
        total_line = re.search(r"总时长[^0-9]{0,6}(\d+(?:\.\d+)?)", t)
        if nums and total_line:
            per_scene = [float(n) for n in nums if float(n) <= 30.0]
            if per_scene:
                diff = abs(sum(per_scene) - float(total_line.group(1)))
                check(diff <= 0.2,
                      "storyboard-closed: 场景时长之和 %.1fs 与总时长 %ss 相差 %.1fs"
                      % (sum(per_scene), total_line.group(1), diff))
        check(bool(re.search(r"起止|开始|时间轴|场景", t)), "storyboard: 缺场景结构")

    # ---- 3. design_system.md ----
    ds = [p for p in glob.glob("project/design_system.md") if os.path.isfile(p)]
    check(bool(ds), "design-system: 未找到 project/design_system.md")
    if ds:
        t = read(ds[0])
        check(bool(re.search(r"色板|配色|颜色|palette|#[0-9a-fA-F]{3,6}", t)),
              "design-palette: design_system.md 无色板")
        check(bool(re.search(r"字体|字阶|font", t, re.I)), "design-font: 无字体层级")
        check(bool(re.search(r"动画|节奏|power|easing", t, re.I)), "design-anim: 无动画节奏规则")

    for msg in failures:
        print("FAIL " + msg)
    if not failures:
        print("ALL PASS: 内容三件套契约齐全")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
