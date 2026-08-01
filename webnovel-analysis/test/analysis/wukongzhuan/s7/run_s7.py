# -*- coding: utf-8 -*-
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

BASE = r"C:\Users\zhangjl\workspace-novel-analyse\analysis\wukongzhuan"
S6 = json.load(open(os.path.join(BASE, "s6", "S6_data_aggregation.json"), encoding="utf-8"))
rows = S6["master_records"]
chapters = [f"CH{r['chapter_no']:02d}" for r in rows]
emotion = [r["emotion_score"] for r in rows]
pressure = [r["pressure_score"] for r in rows]
release = [r["release_score"] for r in rows]
suppression = [r["suppression_level"] for r in rows]
payoff = [r["payoff_strength"] if r["payoff_present"] else 0 for r in rows]
break_strength = [r["chapter_break_strength"] for r in rows]
x = np.arange(len(chapters))
OUT = os.path.join(BASE, "s7")
os.makedirs(OUT, exist_ok=True)

# 1. EmotionCurve 折线图
fig, ax = plt.subplots(figsize=(14, 5.5))
ax.plot(x, emotion, "o-", color="#2E86AB", lw=2.2, label="情绪分")
ax.plot(x, pressure, "s--", color="#D1495B", lw=1.8, alpha=0.85, label="压抑分")
ax.plot(x, release, "^:", color="#2A9D8F", lw=1.8, alpha=0.85, label="释放分")
ax.fill_between(x, 0, emotion, color="#2E86AB", alpha=0.15)
ax.axhline(y=4.0, color="#888", ls=":", lw=1)
ax.axhline(y=5.2, color="#D1495B", ls=":", lw=1)
for xi, v in zip(x, emotion):
    if v >= 6:
        ax.annotate(str(v), (xi, v), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, color="#2E86AB", fontweight="bold")
    elif v <= 2:
        ax.annotate(str(v), (xi, v), textcoords="offset points", xytext=(0, -14), ha="center", fontsize=9, color="#D1495B", fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(chapters, rotation=45, fontsize=8)
ax.set_ylim(-1, 11)
ax.set_ylabel("分数")
ax.set_title("《悟空传》章节情绪-压抑-释放曲线（均值：情绪4.0/压抑5.2/释放1.5）")
ax.legend(loc="upper left", fontsize=9)
ax.grid(alpha=0.3, ls=":")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "emotion_curve.png"), dpi=150)
plt.close()

# 2. Heatmap 热力图
fig, ax = plt.subplots(figsize=(14, 3.2))
matrix = np.array([emotion, pressure, release, suppression, payoff, break_strength])
labels = ["情绪", "压抑", "释放", "压抑等级", "爽点强度", "断章强度"]
cmaps = ["RdYlGn_r", "Reds", "Greens", "YlOrBr", "Oranges", "Purples"]
for i, (row, lab, cmap) in enumerate(zip(matrix, labels, cmaps)):
    ax.imshow([row], aspect="auto", cmap=cmap, vmin=0, vmax=10 if i != 3 else 4, alpha=0.9)
ax.set_yticks(np.arange(len(labels)))
ax.set_yticklabels(labels, fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels(chapters, rotation=45, fontsize=8)
for i, row in enumerate(matrix):
    for j, v in enumerate(row):
        ax.text(j, i, str(v), ha="center", va="center", fontsize=7, color="black", alpha=0.85)
ax.set_title("《悟空传》章节热力图")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "heatmap.png"), dpi=150)
plt.close()

# 3. PayoffTimeline 爽点时间线
fig, ax = plt.subplots(figsize=(14, 4))
pe = json.load(open(os.path.join(BASE, "s4", "S4_payoff_engineering.json"), encoding="utf-8"))["payoff_events"]
for e in pe:
    cn = int(e["chapter_id"].split("CH")[-1])
    strength = e["payoff_strength"]
    color = "#2A9D8F" if e["release_mode"] != "反向释放" else "#D1495B"
    ax.bar(cn, strength, color=color, width=0.6, alpha=0.85)
    ax.annotate(e["payoff_type"], (cn, strength + 0.15), ha="center", fontsize=7, rotation=0, color="#333")
ax.set_xticks(x)
ax.set_xticklabels(chapters, rotation=45, fontsize=8)
ax.set_ylim(0, 10)
ax.set_ylabel("爽点强度")
ax.set_title("《悟空传》主要爽点时间线（红色=反向释放/文学性释放）")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "payoff_timeline.png"), dpi=150)
plt.close()

# 4. VolumeSummary 卷级曲线
fig, ax = plt.subplots(figsize=(12, 4))
vol_means = {v["volume_id"]: v for v in S6["volume_statistics"]}
vol_labels = ["V01\n迷途\nCH1-5", "V02\n前尘\nCH6-13", "V03\n轮回\nCH14-20", "V04\n篇外\nCH21"]
vx = np.arange(4)
ax.plot(vx, [vol_means["V01"]["mean_emotion"], vol_means["V02"]["mean_emotion"], vol_means["V03"]["mean_emotion"], vol_means["V04"]["mean_emotion"]], "o-", color="#2E86AB", lw=2, label="卷均情绪")
ax.plot(vx, [vol_means["V01"]["mean_pressure"], vol_means["V02"]["mean_pressure"], vol_means["V03"]["mean_pressure"], vol_means["V04"]["mean_pressure"]], "s--", color="#D1495B", lw=2, label="卷均压抑")
ax.plot(vx, [vol_means["V01"]["mean_release"], vol_means["V02"]["mean_release"], vol_means["V03"]["mean_release"], vol_means["V04"]["mean_release"]], "^:", color="#2A9D8F", lw=2, label="卷均释放")
ax.set_xticks(vx)
ax.set_xticklabels(vol_labels, fontsize=8)
ax.set_ylim(0, 10)
ax.set_ylabel("分数")
ax.set_title("《悟空传》卷级节奏对比（V03轮回压抑最高6.7）")
ax.legend(fontsize=9)
ax.grid(alpha=0.3, ls=":")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "volume_summary.png"), dpi=150)
plt.close()

print("S7 charts generated:", os.listdir(OUT))
