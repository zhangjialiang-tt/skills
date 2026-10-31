#!/usr/bin/env python3
"""成片 QC 采样工具（hyperframes-video skill）

出处：hyperframes-agent-video 项目 QC 流程固化（2026-10-30）。
一次完成四块证据采集：
  1. ffprobe 参数核验（codec/分辨率/帧率/时长/音轨；--expect-duration 按 ±0.1s 比对）
  2. 关键帧抽取（--frames 指定时刻，落 --outdir）
  3. 音量窗口采样（speech 窗口 mean 应 -25~0dB；gap 窗口应 <=-60dB，数字静音约 -91dB；
     max_volume 一并输出作削波证据，>=0dB 记削波嫌疑；gap 阈值仅适用于无背景音乐版本；
     无音轨视频自动跳过并登记 skipped_no_audio_track）
  4. blackdetect 黑帧事件（d=1.0，事件必须抽帧定性：深色主题/转场节拍常为误报）

退出码语义（供门禁/Agent 判定，不再"失败也返回 0"）：
  0 = 全部检查执行完毕且未发现异常
  2 = 用法/环境错误（文件不存在、ffmpeg 缺失、窗口/时刻参数畸形）
  3 = 采样失败（请求的证据未取到：抽帧未成功、ffmpeg 子进程非零返回、ffprobe 失败）
  4 = 发现异常待人工定性（音频窗口 mean 越界、削波嫌疑、blackdetect 事件、时长不符）

输出：不带 --json 时人类可读报告走 stdout；带 --json 时 stdout 只输出纯 JSON，
报告走 stderr（json.loads(stdout) 可直接解析）。

工具级单测：python scripts/qc_sample_test.py（ffmpeg 合成视频，不需要渲染管线）。
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def ffprobe_info(path):
    r = run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate",
        "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
        "-of", "json", str(path),
    ])
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe 失败：{r.stderr.strip()}")
    data = json.loads(r.stdout)
    streams = {s.get("codec_type"): s for s in data.get("streams", [])}
    fmt = data.get("format", {})
    return {
        "duration_sec": float(fmt.get("duration", 0) or 0),
        "size_bytes": int(fmt.get("size", 0) or 0),
        "bit_rate_bps": int(fmt.get("bit_rate", 0) or 0),
        "video": streams.get("video"),
        "audio": streams.get("audio"),
    }


def extract_frames(path, times, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    saved = []
    for t in times:
        out = outdir / f"frame-{t}s.png"
        r = run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1", str(out)])
        if r.returncode == 0 and out.exists():
            saved.append(str(out))
        else:
            saved.append(None)
    return saved


def mean_volume(path, start, dur):
    r = run(["ffmpeg", "-ss", str(start), "-t", str(dur), "-i", str(path), "-af", "volumedetect", "-f", "null", "-"])
    if r.returncode != 0:
        # ffmpeg 失败时子进程返回码才可靠；读数为空 -> 调用方记采样失败
        return {"start": start, "dur": dur, "mean_db": None, "max_db": None,
                "error": r.stderr.strip()[-200:]}
    mean = maxv = None
    for line in r.stderr.splitlines():
        if "mean_volume" in line:
            mean = float(line.split(":")[1].replace("dB", "").strip())
        if "max_volume" in line:
            maxv = float(line.split(":")[1].replace("dB", "").strip())
    return {"start": start, "dur": dur, "mean_db": mean, "max_db": maxv}


def parse_windows(spec):
    out = []
    for item in filter(None, (spec or "").split(",")):
        parts = item.split(":")
        if len(parts) != 2:
            raise ValueError(f"窗口参数格式错误：{item!r}（应为 start:dur）")
        try:
            start, dur = float(parts[0]), float(parts[1])
        except ValueError:
            raise ValueError(f"窗口参数不是数字：{item!r}（应为 start:dur）")
        if dur <= 0:
            raise ValueError(f"窗口时长必须为正：{item!r}")
        out.append((start, dur))
    return out


def parse_times(spec):
    out = []
    for item in filter(None, (spec or "").split(",")):
        try:
            out.append(float(item.strip()))
        except ValueError:
            raise ValueError(f"--frames 含非数字时刻：{item.strip()!r}")
    return out


def blackdetect(path, min_dur=1.0):
    r = run(["ffmpeg", "-i", str(path), "-vf", f"blackdetect=d={min_dur}:pix_th=0.10", "-an", "-f", "null", "-"])
    if r.returncode != 0:
        return None  # 子进程失败：无法区分"无事件"与"没测成"，由调用方记采样失败
    events = []
    for line in r.stderr.splitlines():
        if "black_start" in line:
            seg = line.split("blackdetect")[1]
            parts = dict(p.split(":") for p in seg.strip().split(" ") if ":" in p)
            events.append({
                "start": float(parts["black_start"]),
                "end": float(parts["black_end"]),
                "duration": float(parts["black_duration"]),
            })
    return events


def main():
    ap = argparse.ArgumentParser(description="成片 QC 采样：ffprobe + 抽帧 + 音量窗口 + blackdetect")
    ap.add_argument("video", help="MP4 路径")
    ap.add_argument("--frames", default="", help="逗号分隔的抽帧时刻（秒），如 0.5,3,20")
    ap.add_argument("--speech-windows", default="", help="有声窗口 start:dur 逗号分隔，如 1.0:0.5,8.0:0.5")
    ap.add_argument("--gap-windows", default="", help="静音间隙窗口 start:dur 逗号分隔（阈值仅适用无 BGM 版本）")
    ap.add_argument("--expect-duration", type=float, default=None, help="成片期望时长（秒），偏差 >0.1s 记异常")
    ap.add_argument("--outdir", default="reports/frames", help="抽帧输出目录")
    ap.add_argument("--json", action="store_true", help="stdout 输出纯 JSON（报告走 stderr）")
    args = ap.parse_args()

    video = Path(args.video)
    if not video.exists():
        print(f"[FAIL] 文件不存在：{video}", file=sys.stderr)
        sys.exit(2)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("[FAIL] ffmpeg/ffprobe 不在 PATH", file=sys.stderr)
        sys.exit(2)

    try:
        times = parse_times(args.frames)
        sw = parse_windows(args.speech_windows)
        gw = parse_windows(args.gap_windows)
    except ValueError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        sys.exit(2)

    out = sys.stderr if args.json else sys.stdout

    def say(msg=""):
        print(msg, file=out)

    result = {"video": str(video)}
    sampling_failed = False   # 退出码 3
    anomalies = []            # 退出码 4

    try:
        info = ffprobe_info(video)
    except RuntimeError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        sys.exit(3)
    result["probe"] = info
    v = info["video"] or {}
    say("== 1. ffprobe 参数 ==")
    say(f"  duration={info['duration_sec']:.3f}s size={info['size_bytes']}B bitrate={info['bit_rate_bps']}")
    say(f"  video: {v.get('codec_name')} {v.get('width')}x{v.get('height')} @{v.get('r_frame_rate')}")
    a = info["audio"]
    say(f"  audio: {a.get('codec_name') if a else '无音轨'} " + (f"{a.get('sample_rate')}Hz {a.get('channels')}ch" if a else ""))

    if args.expect_duration is not None:
        dev = abs(info["duration_sec"] - args.expect_duration)
        ok = dev <= 0.1
        result["duration_check"] = {"expect_sec": args.expect_duration,
                                    "actual_sec": round(info["duration_sec"], 3),
                                    "abs_dev_sec": round(dev, 3), "pass": ok}
        say(f"  时长比对：期望 {args.expect_duration}s 实测 {info['duration_sec']:.3f}s 偏差 {dev:.3f}s "
            f"({'符合 ±0.1s' if ok else '超出 ±0.1s，记异常'})")
        if not ok:
            anomalies.append(f"时长偏差 {dev:.3f}s 超出 ±0.1s")

    if times:
        say(f"== 2. 关键帧抽取（{len(times)} 帧）-> {args.outdir} ==")
        frames = extract_frames(video, times, Path(args.outdir))
        ok = sum(1 for f in frames if f)
        say(f"  成功 {ok}/{len(times)}")
        result["frames"] = frames
        if ok < len(times):
            sampling_failed = True
            say(f"  [FAIL] {len(times) - ok} 帧未取到（seek 超出片长或 ffmpeg 失败），记采样失败")

    if sw or gw:
        say("== 3. 音量窗口采样 ==")
        if info["audio"] is None:
            say("  无音轨：跳过音频窗口采样（静音版本属预期，登记即可）")
            result["audio_windows_verdict"] = "skipped_no_audio_track"
        else:
            speech = [mean_volume(video, s, d) for s, d in sw]
            gaps = [mean_volume(video, s, d) for s, d in gw]
            result["speech_windows"], result["gap_windows"] = speech, gaps
            for w in speech:
                say(f"  speech t={w['start']} d={w['dur']}: mean={w['mean_db']}dB max={w['max_db']}dB")
            for w in gaps:
                say(f"  gap    t={w['start']} d={w['dur']}: mean={w['mean_db']}dB max={w['max_db']}dB")
            win_err = [w for w in speech + gaps if w["mean_db"] is None]
            if win_err:
                sampling_failed = True
                say(f"  [FAIL] {len(win_err)} 个窗口 volumedetect 未返回读数，记采样失败")
            # mean 越界 = 异常；max >= 0dB = 削波嫌疑（audio-captions.md 判据：max≈-3dB 无削波）
            bad = [w for w in speech if w["mean_db"] is not None and (w["mean_db"] < -25 or w["mean_db"] > 0)]
            bad += [w for w in gaps if w["mean_db"] is not None and w["mean_db"] > -60]
            clipped = [w for w in speech if w["max_db"] is not None and w["max_db"] >= 0]
            if bad or clipped:
                if bad:
                    anomalies.append(f"{len(bad)} 个窗口 mean 越界（speech 应 -25~0dB / gap 应 <=-60dB）")
                if clipped:
                    anomalies.append(f"{len(clipped)} 个语音窗口 max>=0dB，削波嫌疑")
                say("  判定：存在异常窗口，逐个核对")
                result["audio_windows_verdict"] = "suspect"
            elif not win_err:
                say("  判定：指定窗口 mean 读数符合预期（speech -25~0dB / gap <=-60dB）")
                say("        口径：mean 仅证明窗口有声/近静音；音画同步需试听+画面对照，削波看 max 读数")
                result["audio_windows_verdict"] = "ok"

    say("== 4. blackdetect（>=1s）==")
    events = blackdetect(video)
    if events is None:
        sampling_failed = True
        result["blackdetect"] = None
        say("  [FAIL] blackdetect 执行失败（ffmpeg 非零返回），记采样失败")
    else:
        result["blackdetect"] = events
        if not events:
            say("  无事件")
        else:
            for e in events:
                say(f"  black {e['start']:.2f}-{e['end']:.2f} ({e['duration']:.2f}s)  <- 需抽帧定性（深色主题/转场节拍可能为误报）")
            say("  提示：对每段事件用 ffmpeg -ss <start+0.3> 抽帧目检定性，结论写入 quality_report.md")
            anomalies.append(f"blackdetect {len(events)} 段事件待抽帧定性")

    result["sampling_failed"] = sampling_failed
    result["anomalies"] = anomalies

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    if sampling_failed:
        say("[FAIL] 采样失败：请求的证据未全部取到（退出码 3）")
        sys.exit(3)
    if anomalies:
        say(f"[WARN] 发现 {len(anomalies)} 项异常待人工定性（退出码 4）：")
        for x in anomalies:
            say(f"  - {x}")
        sys.exit(4)
    say("[OK] 全部检查执行完毕，未发现异常（退出码 0）")
    sys.exit(0)


if __name__ == "__main__":
    main()
