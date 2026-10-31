#!/usr/bin/env python3
"""分镜时长闭合校验器（ai-drama-pilot skill）

出处：源流程《明天的来电》试播集生产包（2026-10-29）的时长校验脚本通用化。
检查四件事：
  1) 每行 end - start == duration（行内一致）
  2) 区间首尾相接（无重叠、无缝隙），且首镜起点为 0
  3) 总时长 == 目标总长（--total；缺省不检查总和，只报数值并打印 WARNING）
  4) shot_id 不重复

用法：
  python verify_timeline.py shot_list.csv
  python verify_timeline.py shot_list.csv --total 75.0
  python verify_timeline.py shot_list.csv --start-col s --end-col e --duration-col dur

退出码：0=通过，1=失败，2=用法/文件错误。
"""
import argparse
import csv
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description="分镜时长闭合校验")
    ap.add_argument("csv_path", help="分镜 CSV 路径")
    ap.add_argument("--start-col", default="start_s", help="起始秒列名（默认 start_s）")
    ap.add_argument("--end-col", default="end_s", help="结束秒列名（默认 end_s）")
    ap.add_argument("--duration-col", default="duration_s", help="时长列名（默认 duration_s）")
    ap.add_argument("--id-col", default="shot_id", help="镜头编号列名（默认 shot_id）")
    ap.add_argument("--total", type=float, default=None, help="目标总时长（秒），不给则只报数值并打印 WARNING")
    ap.add_argument("--tolerance", type=float, default=1e-6, help="浮点容差（默认 1e-6）")
    args = ap.parse_args()

    try:
        with open(args.csv_path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        print(f"ERROR: 无法读取 {args.csv_path}: {e}")
        return 2

    required = [args.id_col, args.start_col, args.end_col, args.duration_col]
    if not rows:
        print("ERROR: CSV 无数据行")
        return 2
    missing_cols = [c for c in required if c not in rows[0]]
    if missing_cols:
        print(f"ERROR: 缺少列 {missing_cols}，现有列: {list(rows[0].keys())}")
        return 2

    failures = []
    total = 0.0
    prev_end = None
    first_start = None
    seen_ids = set()
    for r in rows:
        sid = r[args.id_col]
        if sid in seen_ids:
            failures.append(f"{sid}: shot_id 重复")
        seen_ids.add(sid)
        try:
            s, e, d = (float(r[args.start_col]), float(r[args.end_col]), float(r[args.duration_col]))
        except (ValueError, TypeError):
            failures.append(f"{sid}: start/end/duration 存在非数值或缺失: {r[args.start_col]!r}/{r[args.end_col]!r}/{r[args.duration_col]!r}")
            continue
        if first_start is None:
            first_start = s
        if abs((e - s) - d) > args.tolerance:
            failures.append(f"{sid}: end-start={e - s:.3f} != duration={d:.3f}")
        if prev_end is not None and abs(s - prev_end) > args.tolerance:
            failures.append(f"{sid}: 起点{s:.3f}与上一镜终点{prev_end:.3f}之间存在重叠或缝隙")
        prev_end = e
        total += d

    print(f"镜头数: {len(rows)}  总时长: {total:.1f}s")
    if first_start is not None and abs(first_start) > args.tolerance:
        failures.append(f"首镜起点 {first_start:.3f} 应为 0（时间码原点）")
    if args.total is not None:
        if abs(total - args.total) > args.tolerance:
            failures.append(f"总时长 {total:.1f}s != 目标 {args.total:.1f}s")
        else:
            print(f"总时长闭合: OK (= {args.total:.1f}s)")
    else:
        print("WARNING: 未提供 --total，未校验目标总时长（门禁用法必须带 --total）", file=sys.stderr)
    if prev_end is not None and total > 0 and abs(prev_end - total) > args.tolerance:
        failures.append("末镜终点与总时长不一致（存在未计入的区间）")

    if failures:
        print("--- FAIL ---")
        for msg in failures:
            print(" ", msg)
        return 1
    print("closure/continuity: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
