#!/usr/bin/env python3
"""qc_sample.py 工具级单测（hyperframes-video skill）

不需要 HyperFrames 渲染管线：用 ffmpeg 临时合成视频，验证退出码语义与输出纯度。
覆盖对抗性评审修订的 P0/P1 项：
  - 采样失败（3）/ 发现异常（4）/ 成功（0）/ 用法错误（2）四态退出码
  - --json 时 stdout 为纯 JSON、报告走 stderr
  - ffmpeg 子进程失败与 seek 越界不再静默通过
  - 无音轨视频跳过音频窗口采样（不误报异常）
  - max_db 削波证据进入判定
  - --expect-duration ±0.1s 比对
  - blackdetect 事件记异常待定性
  - ffprobe 失败干净退出（无 traceback）

运行：python scripts/qc_sample_test.py
依赖：ffmpeg / ffprobe 在 PATH；退出码非 0 表示有用例失败。
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "qc_sample.py"
PY = sys.executable

passed = failed = 0


def run_qc(args, cwd):
    return subprocess.run([PY, str(SCRIPT)] + [str(a) for a in args],
                          capture_output=True, text=True, cwd=str(cwd))


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def make_video(path, dur=3.0, audio="silent", size="320x240", rate=10):
    """audio: silent=静音轨 / loud=响铃(mean≈-9dB) / clipped=削波(max=0dB) / none=无音轨 / black=黑帧无音轨

    注意：本机 ffmpeg 的 sine 源峰值仅约 -18dB，需 volume=10 才削到 0dB；
    削波用例用 PCM(mkv) 而非 AAC——AAC 解码会把削波峰值抹到约 -0.3dB，
    那是编解码 artifact，不应靠放宽工具的 max>=0dB 阈值来迁就。
    """
    if audio == "black":
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
               "-i", f"color=c=black:s={size}:r={rate}:d={dur}",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error",
               "-f", "lavfi", "-i", f"testsrc=size={size}:rate={rate}:duration={dur}"]
        if audio == "silent":
            cmd += ["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono", "-t", str(dur),
                    "-c:a", "aac"]
        elif audio == "loud":
            cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={dur}",
                    "-af", "volume=4", "-t", str(dur), "-c:a", "aac"]
        elif audio == "clipped":
            cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={dur}",
                    "-af", "volume=10", "-t", str(dur), "-c:a", "pcm_s16le"]
        # audio == "none"：不加音频流
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-shortest", str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"生成测试视频失败：{r.stderr}")
    return path


def main():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        silent = make_video(td / "silent.mp4", audio="silent")
        loud = make_video(td / "loud.mp4", audio="loud")
        clipped = make_video(td / "clipped.mkv", audio="clipped")
        noaudio = make_video(td / "noaudio.mp4", audio="none")
        black = make_video(td / "black.mp4", dur=2.0, audio="black")
        (td / "notavideo.txt").write_text("this is not a video", encoding="utf-8")

        print("== A. 抽帧部分失败 -> 退出码 3，且 --json 仍为纯 JSON ==")
        r = run_qc([silent, "--frames", "0.5,99", "--json", "--outdir", td / "fA"], td)
        check("退出码为 3", r.returncode == 3, f"rc={r.returncode} stderr={r.stderr[-200:]}")
        try:
            data = json.loads(r.stdout)
            pure = True
        except Exception:
            data, pure = {}, False
        check("stdout 可 json.loads（报告在 stderr）", pure)
        check("frames[1] 为 null", data.get("frames") == [str(td / "fA" / "frame-0.5s.png"), None]
              or (isinstance(data.get("frames"), list) and len(data["frames"]) == 2 and data["frames"][1] is None),
              f"frames={data.get('frames')}")
        check("sampling_failed 置位", data.get("sampling_failed") is True)
        check("stderr 含采样失败提示", "采样失败" in r.stderr)

        print("== B. 全部成功 -> 退出码 0，stdout 纯 JSON ==")
        r = run_qc([silent, "--frames", "0.5", "--json", "--outdir", td / "fB"], td)
        check("退出码为 0", r.returncode == 0, f"rc={r.returncode}")
        try:
            data = json.loads(r.stdout)
            pure = True
        except Exception:
            data, pure = {}, False
        check("stdout 可 json.loads", pure)
        check("报告不在 stdout", "ffprobe 参数" in r.stderr and "ffprobe 参数" not in r.stdout)

        print("== C. 无音轨 + 音频窗口 -> 跳过而非误报 ==")
        r = run_qc([noaudio, "--speech-windows", "0.5:0.5", "--gap-windows", "2.0:0.5", "--json"], td)
        check("退出码为 0", r.returncode == 0, f"rc={r.returncode} stderr={r.stderr[-200:]}")
        try:
            data = json.loads(r.stdout)
        except Exception:
            data = {}
        check("verdict=skipped_no_audio_track", data.get("audio_windows_verdict") == "skipped_no_audio_track",
              f"verdict={data.get('audio_windows_verdict')}")
        check("stderr 说明跳过原因", "无音轨" in r.stderr)

        print("== D. 响铃窗口 + 时长相符 -> 退出码 0 ==")
        r = run_qc([loud, "--speech-windows", "0.5:0.5", "--expect-duration", "3", "--json"], td)
        check("退出码为 0", r.returncode == 0, f"rc={r.returncode} stderr={r.stderr[-200:]}")
        try:
            data = json.loads(r.stdout)
        except Exception:
            data = {}
        check("verdict=ok", data.get("audio_windows_verdict") == "ok", f"verdict={data.get('audio_windows_verdict')}")
        check("duration_check.pass 为真", data.get("duration_check", {}).get("pass") is True)
        check("max_db 已输出", data.get("speech_windows", [{}])[0].get("max_db") is not None)

        print("== E. gap 窗口有声 -> 退出码 4 ==")
        r = run_qc([loud, "--gap-windows", "2.0:0.5", "--json"], td)
        check("退出码为 4", r.returncode == 4, f"rc={r.returncode}")
        try:
            data = json.loads(r.stdout)
        except Exception:
            data = {}
        check("verdict=suspect", data.get("audio_windows_verdict") == "suspect")
        check("anomalies 非空", bool(data.get("anomalies")))

        print("== F. 削波（max>=0dB）-> 退出码 4 且提示削波 ==")
        r = run_qc([clipped, "--speech-windows", "0.5:0.5", "--json"], td)
        check("退出码为 4", r.returncode == 4, f"rc={r.returncode} stderr={r.stderr[-200:]}")
        try:
            data = json.loads(r.stdout)
        except Exception:
            data = {}
        check("anomalies 含削波嫌疑", any("削波" in a for a in data.get("anomalies", [])),
              f"anomalies={data.get('anomalies')}")

        print("== G. 畸形窗口参数 -> 退出码 2 ==")
        r = run_qc([silent, "--speech-windows", "1.0"], td)
        check("退出码为 2", r.returncode == 2, f"rc={r.returncode}")
        check("stderr 有格式错误提示", "格式错误" in r.stderr)

        print("== H. 文件不存在 -> 退出码 2 ==")
        r = run_qc([td / "nope.mp4"], td)
        check("退出码为 2", r.returncode == 2, f"rc={r.returncode}")

        print("== I. 时长不符 -> 退出码 4 ==")
        r = run_qc([silent, "--expect-duration", "10", "--json"], td)
        check("退出码为 4", r.returncode == 4, f"rc={r.returncode}")
        try:
            data = json.loads(r.stdout)
        except Exception:
            data = {}
        check("duration_check.pass 为假", data.get("duration_check", {}).get("pass") is False)

        print("== J. blackdetect 事件 -> 退出码 4 待定性 ==")
        r = run_qc([black, "--json"], td)
        check("退出码为 4", r.returncode == 4, f"rc={r.returncode}")
        try:
            data = json.loads(r.stdout)
        except Exception:
            data = {}
        check("blackdetect 有事件", len(data.get("blackdetect") or []) >= 1)
        check("anomalies 含 blackdetect", any("blackdetect" in a for a in data.get("anomalies", [])))

        print("== K. 非视频文件 -> ffprobe 失败干净退出码 3 ==")
        r = run_qc([td / "notavideo.txt"], td)
        check("退出码为 3", r.returncode == 3, f"rc={r.returncode}")
        check("无 traceback", "Traceback" not in r.stderr, r.stderr[-200:])

    print(f"\n合计：{passed} PASS / {failed} FAIL")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
