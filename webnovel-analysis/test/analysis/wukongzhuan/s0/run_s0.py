# -*- coding: utf-8 -*-
"""S0 文本预处理：悟空传（BK20260801-001 / BK001）
转码 GBK->UTF-8，清洗站点广告，按章节切分，输出标准信封。
"""
import re
import csv
from pathlib import Path

SRC = Path(r"C:\Users\zhangjl\workspace-novel-analyse\docs\《悟空传》（校对版全本）作者：今何在.txt")
OUT = Path(r"C:\Users\zhangjl\workspace-novel-analyse\analysis\wukongzhuan\s0")
OUT.mkdir(parents=True, exist_ok=True)

raw_bytes = SRC.read_bytes()
raw_text = raw_bytes.decode("gbk", errors="replace")
raw_character_count = len(re.sub(r"\s", "", raw_text))

lines = raw_text.splitlines()

# ---- 清洗：移除站点广告横幅（头 3 行 + 尾 3 行）----
removed_types = []
if lines[0].startswith("=" * 20):
    removed_types.append("站点广告横幅(头部)")
    lines = lines[3:]
if lines[-1].startswith("=" * 20):
    removed_types.append("站点广告横幅(尾部)")
    lines = lines[:-3]

# 保留书名/作者/简介为元信息（前置块）
meta_lines = []
while lines and lines[0].strip() == "":
    lines.pop(0)
for i, ln in enumerate(lines[:6]):
    if ln.strip().startswith(("悟空传", "作者", "内容简介", "怎能忘了")):
        meta_lines.append(ln.strip())
        if ln.strip().startswith("怎能忘了"):
            break
# 元信息块结束于简介后第一个空行或第一章前
body_start = 0
for i, ln in enumerate(lines):
    if ln.strip() == "第一章" or re.match(r"^第[一二三四五六七八九十百千零〇0-9]+[章节回卷部]", ln.strip()):
        body_start = i
        break

cleaned = "\n".join(lines[body_start:])
clean_character_count = len(re.sub(r"\s", "", cleaned))

# ---- 章节识别 ----
chapter_title_re = re.compile(r"^(第[一二三四五六七八九十百千零〇0-9]+[章节回卷部]|篇外[:：].*)$")
chapters = []
cur = None
for idx, ln in enumerate(lines, start=body_start + 1):
    stripped = ln.strip()
    if chapter_title_re.match(stripped):
        if cur:
            chapters.append(cur)
        cur = {"no": stripped, "title": stripped, "lines": [], "start": idx, "text": []}
    elif cur is not None:
        cur["lines"].append(idx)
        cur["text"].append(ln)

if cur:
    chapters.append(cur)

# 统一编号（第X章 -> 数字，篇外 -> 附加）
def cn2num(s):
    if "篇外" in s:
        return None
    m = re.match(r"^第(.+)[章节回卷部]$", s)
    if not m:
        return None
    s = m.group(1)
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "百": 100, "零": 0, "〇": 0}
    if set(s) <= set("0123456789"):
        return int(s)
    total = 0
    if "十" in s:
        parts = s.split("十")
        a = digits.get(parts[0], 1) if parts[0] else 1
        b = digits.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
        return a * 10 + b
    return digits.get(s, 0)

numbered = []
extra_idx = 0
for ch in chapters:
    n = cn2num(ch["no"])
    if n is None:
        extra_idx += 1
        ch["chapter_no"] = 20 + extra_idx
        ch["is_extra"] = True
    else:
        ch["chapter_no"] = n
        ch["is_extra"] = False
    numbered.append(ch)
numbered.sort(key=lambda c: c["chapter_no"])

# ---- 生成输出 ----
chapter_index = []
std_parts = ["# 悟空传（标准化文本）", "", "## 元信息", ""]
for ml in meta_lines:
    std_parts.append("- " + ml)
std_parts += ["", "---", ""]

issue_rows = []
for ch in numbered:
    cid = f"BK001-CH{ch['chapter_no']:04d}"
    text = "\n".join(ch["text"]).strip()
    # 保留行内空行为自然分段（作者有意空行保留）
    word_count = len(re.sub(r"\s", "", text))
    flags = []
    if ch["is_extra"]:
        flags.append("非第X章格式标题(篇外)")
    if word_count > 5000:
        flags.append("超长章>5000")
    if word_count < 800:
        flags.append("异常短章")
    end = ch["lines"][-1] if ch["lines"] else ch["start"]
    chapter_index.append({
        "chapter_id": cid,
        "chapter_no": ch["chapter_no"],
        "original_title": ch["no"],
        "normalized_title": ch["no"],
        "word_count": word_count,
        "boundary_confidence": "确定" if not ch["is_extra"] else "推断",
        "source_location": f"novel.txt:{ch['start']}-{end}",
        "issue_flags": "|".join(flags),
    })
    std_parts.append(f"<chapter>")
    std_parts.append(f"chapter_id: {cid}")
    std_parts.append(f"chapter_no: {ch['chapter_no']}")
    std_parts.append(f"original_title: {ch['no']}")
    std_parts.append(f"normalized_title: {ch['no']}")
    std_parts.append(f"boundary_confidence: {'确定' if not ch['is_extra'] else '推断'}")
    std_parts.append("text:")
    std_parts.append(text)
    std_parts.append("</chapter>")
    std_parts.append("")
    for f in flags:
        issue_rows.append([cid, ch["no"], f])

# 检查缺章/重章/跳号
nos = [c["chapter_no"] for c in numbered if not c["is_extra"]]
expected = set(range(1, 21))
if set(nos) != expected:
    missing = sorted(expected - set(nos))
    dupes = sorted({n for n in nos if nos.count(n) > 1})
    if missing:
        issue_rows.append(["全书", "", f"缺章:{missing}"])
    if dupes:
        issue_rows.append(["全书", "", f"重章:{dupes}"])

# ---- 写文件 ----
(OUT / "standardized_chapters.md").write_text("\n".join(std_parts), encoding="utf-8")
with open(OUT / "chapter_index.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(chapter_index[0].keys()))
    w.writeheader()
    w.writerows(chapter_index)
with open(OUT / "preprocessing_issues.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["chapter_id", "chapter_title", "issue"])
    w.writerows(issue_rows)

# batch_manifest: 全书 20 章 + 1 篇外，按 2 批
batch1 = [f"BK001-CH{i:04d}" for i in range(1, 11)]
batch2 = [f"BK001-CH{i:04d}" for i in range(11, 21)] + ["BK001-CH0021"]
b1_chars = sum(c["word_count"] for c in chapter_index if c["chapter_no"] <= 10)
b2_chars = sum(c["word_count"] for c in chapter_index if c["chapter_no"] > 10)
batch_manifest = f"""task_id: BK20260801-001
skill_id: S0
batches:
  - batch_id: BATCH-01
    chapter_ids: {batch1}
    reason: 开篇-中段连续事件单元（ch01-10）
    estimated_characters: {b1_chars}
    boundary_confidence: 确定
  - batch_id: BATCH-02
    chapter_ids: {batch2}
    reason: 后段-结局与篇外（ch11-20 + 篇外花果山）
    estimated_characters: {b2_chars}
    boundary_confidence: 确定
"""
(OUT / "batch_manifest.yaml").write_text(batch_manifest, encoding="utf-8")

report = {
    "task_id": "BK20260801-001",
    "skill_id": "S0",
    "source_file": str(SRC),
    "preprocessing_report": {
        "raw_character_count": raw_character_count,
        "clean_character_count": clean_character_count,
        "chapter_count": len(numbered),
        "removed_content_types": removed_types,
        "text_modified_beyond_cleaning": False,
    },
    "chapter_count": len(numbered),
    "extra_chapter": 1,
}
import json
(OUT / "preprocessing_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(report, ensure_ascii=False, indent=2))
print("章节列表:")
for c in chapter_index:
    print(f"  {c['chapter_id']} {c['original_title']} {c['word_count']}字 {c['source_location']} flags=[{c['issue_flags']}]")
