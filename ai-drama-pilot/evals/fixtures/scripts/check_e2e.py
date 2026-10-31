#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai-drama-pilot e2e checker（skill-up script judge）。

从 case workspace root 执行，校验 45s/≤10镜 端到端生产包（转译自 evals.json id2 断言）：
  1. core-files-exist            六阶段核心文件齐全
  2. timeline-closed-45s         shot_list.csv 通过 verify_timeline.py --total 45 且总时长 44–46s
  3. shot-count-within-10        镜头数 ≤ 10
  4. stills-majority             静帧后期镜 ≥50% 或有动态生成最小化的镜头级决策记录
  5. prompts-bilingual           每镜提示词含中英双语段落
  6. fallback-per-shot           每镜提示词含替代实现方案段落
  7. unverified-marked           生产包存在"待验证"标注
  8. review-with-priorities      存在审查文档且问题用 P0/P1/P2 分级
  9. no-premature-completion-claims  无宣告式"已生成/已测试视频"宣称

exit 0 = PASS；exit 1 = FAIL（逐项打印原因）。
"""
import csv
import glob
import os
import re
import subprocess
import sys

TOTAL = 45.0
MAX_SHOTS = 10


def find_root():
    """定位产出根目录：任意项目目录下的 pilot-01，或 workspace 根平铺。"""
    roots = sorted(d for d in glob.glob("*/pilot-01") if os.path.isdir(d))
    if roots:
        return roots[0]
    if os.path.isdir("01_script") and os.path.isdir("02_storyboard"):
        return "."
    return None


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def main():
    failures = []

    def check(cond, msg):
        if not cond:
            failures.append(msg)

    # ---- 1. core-files-exist ----
    root = find_root()
    if not root:
        print("FAIL core-files-exist: 未找到 */pilot-01 产出目录（也无 workspace 根平铺）")
        return 1
    print("FOUND root=%s" % root)

    core = [
        "README.md",
        "01_script/screenplay_final.md",
        "02_storyboard/storyboard.md",
        "02_storyboard/shot_list.csv",
        "03_visual/character_bible.md",
        "03_visual/visual_style.md",
        "04_prompts/generation_manifest.csv",
        "05_audio_editing/audio_plan.md",
        "05_audio_editing/editing_plan.md",
        "05_audio_editing/pilot_test_plan.md",
    ]
    for rel in core:
        check(os.path.isfile(os.path.join(root, rel)), "core-files-exist: 缺 %s" % rel)

    # ---- 2/3. shot_list.csv：镜头数与时长闭合 ----
    csv_path = os.path.join(root, "02_storyboard", "shot_list.csv")
    if not os.path.isfile(csv_path):
        failures.append("timeline-closed-45s: 找不到 shot_list.csv")
        for msg in failures:
            print("FAIL " + msg)
        return 1
    with open(csv_path, encoding="utf-8", errors="replace", newline="") as f:
        rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
    n_shots = max(0, len(rows) - 1)
    check(n_shots > 0, "timeline-closed-45s: shot_list.csv 无数据行")
    check(n_shots <= MAX_SHOTS, "shot-count-within-10: CSV 数据行 %d > 10" % n_shots)
    if n_shots == 0:
        for msg in failures:
            print("FAIL " + msg)
        return 1

    # skill 自带 verify_timeline.py 门禁：--total 45（skill root 由脚本自身位置推导）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
    vt = os.path.join(skill_root, "scripts", "verify_timeline.py")
    if os.path.isfile(vt):
        r = subprocess.run([sys.executable, vt, csv_path, "--total", str(TOTAL)],
                           capture_output=True, text=True)
        check(r.returncode == 0,
              "timeline-closed-45s: verify_timeline.py 退出码 %d；stdout=%s stderr=%s"
              % (r.returncode, (r.stdout or "")[-400:], (r.stderr or "")[-200:]))
    else:
        failures.append("timeline-closed-45s: 未找到 skill 校验脚本 %s" % vt)

    # 总时长区间复确认（44–46s）
    try:
        with open(csv_path, encoding="utf-8", errors="replace", newline="") as f:
            dict_rows = [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]
        if dict_rows:
            cols = list(dict_rows[0].keys())

            def col(*names):
                for n in names:
                    if n in cols:
                        return n
                return None

            sc, ec, dc = col("start", "start_s", "s"), col("end", "end_s", "e"), col("duration", "duration_s", "dur")
            total = 0.0
            if dc:
                total = sum(float(row[dc]) for row in dict_rows)
            elif sc and ec:
                total = sum(float(row[ec]) - float(row[sc]) for row in dict_rows)
            check(44.0 <= total <= 46.0,
                  "timeline-closed-45s: 总时长 %.1fs 不在 44–46s" % total)
    except Exception as e:  # noqa: BLE001
        failures.append("timeline-closed-45s: 总时长解析失败 %s" % e)

    # ---- 4. stills-majority ----
    sb = ""
    for cand in (os.path.join(root, "02_storyboard", "storyboard.md"),
                 os.path.join(root, "README.md")):
        if os.path.isfile(cand):
            sb += read(cand)
    stills_n = len(re.findall(r"静帧后期|静帧\s*/\s*后期|still frame", sb, re.I))
    check(stills_n >= n_shots * 0.5 or "最小化" in sb or "镜头级" in sb,
          "stills-majority: 静帧后期镜占比不足 50%% 且无动态生成最小化决策记录")
    check(("静帧" in sb) or ("动态生成" in sb) or ("动态镜头" in sb),
          "stills-majority: 分镜文档未区分静帧后期/动态生成镜头")

    # ---- 5/6. 逐镜提示词：数量、双语、替代方案 ----
    shots = sorted(glob.glob(os.path.join(root, "04_prompts", "SHOT_*.md")))
    check(len(shots) == n_shots,
          "prompts-bilingual: SHOT_*.md 数量 %d != CSV 镜头数 %d" % (len(shots), n_shots))
    for p in shots:
        t = read(p)
        name = os.path.basename(p)
        has_zh = bool(re.search(r"[\u4e00-\u9fff]", t))
        has_en = bool(re.search(r"[A-Za-z]{3,}", t))
        check(has_zh and has_en, "prompts-bilingual: %s 缺中/英文段落" % name)
        check(bool(re.search(r"替代|fallback|plan\s*b", t, re.I)),
              "fallback-per-shot: %s 缺替代方案段落" % name)

    # ---- 7. unverified-marked ----
    all_md = glob.glob(os.path.join(root, "**", "*.md"), recursive=True)
    joined = "".join(read(p) for p in all_md)
    check("待验证" in joined, "unverified-marked: 生产包无'待验证'标注")

    # ---- 8. review-with-priorities ----
    reviews = glob.glob(os.path.join(root, "06_review", "**", "*.md"), recursive=True)
    review_txt = "".join(read(p) for p in reviews)
    check(bool(reviews), "review-with-priorities: 06_review/ 无审查文档")
    check(bool(re.search(r"P0|P1|P2", review_txt)),
          "review-with-priorities: 审查文档无 P0/P1/P2 分级")

    # ---- 9. no-premature-completion-claims ----
    claim_re = re.compile(r"视频已渲染|视频文件已产出|\.mp4\s*已生成|已成功生成视频|已成功测试视频")
    for p in all_md:
        for m in claim_re.finditer(read(p)):
            failures.append("no-premature-completion-claims: %s 含宣告式完成宣称：%s"
                            % (os.path.relpath(p, root), m.group(0)))

    for msg in failures:
        print("FAIL " + msg)
    if not failures:
        print("ALL PASS: e2e 生产包校验通过（%d 镜）" % n_shots)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
