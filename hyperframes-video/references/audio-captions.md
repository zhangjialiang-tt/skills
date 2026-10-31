# 配音与字幕方法（TTS 速度系数 · 双轨字幕）

> 出处：hyperframes-agent-video 项目实战（2026-10-30，CLI v0.8.216）。命令形态以当版本 `--help` 为准。

## 1. TTS 基线

```bash
# 本地 Kokoro-82M，免费无外部服务；中文音色 zf_xiaobei；需 python + pip install kokoro-onnx soundfile
npx hyperframes tts --voice zf_xiaobei -l zh -s 1.22 -o assets/narration/n01.wav "$(cat n01.txt)"
```

- 旁白逐句落成 txt 文件（与冻结脚本逐字一致），逐句生成，文件名与场景编号对应。
- 首次运行会下载模型（约 310MB，`~/.cache/hyperframes/tts/`），下载期间转去做字幕/内容。
- 中文默认速度（-s 1.0）实测约 **3.7 字/秒，偏慢**；1.22 ≈ 4.5 字/秒是宣传片舒适区。

## 2. 速度系数反算（核心方法）

目标：每段旁白语音终点落入其场景窗口（场景 start + 0.4s 起、场景 end − 0.2s 止，
溢入淡出缓冲带 ≤0.25s 可接受）。

```
速度系数 = 实测时长 × 当前速度 / 预算窗口
```

流程：全部先按基准速度（1.22）生成 → ffprobe 实测 → 超窗段反算系数单独重生成。

- **连贯性约束**：相邻段系数差 ≤6%（听感一致）；个别句需要 >1.35 才能装下时，改脚本而不是硬提速。
- 实测时长 ≈ 语音终点：Kokoro 输出尾部静音极短，silencedetect 检出的多为句中停顿
  （有 silence_end 的不是尾静音），直接用文件时长即可，不必过度甄别。
- 音量核验：`ffmpeg -af volumedetect` —— max ≈ -3dB 无削波；各段 mean 电平差应 <2dB。
  （成片端的对应证据：qc_sample.py 的 max_db 输出，≥0dB 记削波嫌疑。）

## 3. 回填时间轴

- index.html 音频轨：`<audio id="nXX" src="assets/narration/nXX.wav" data-start="…" data-duration="实测时长">`
  ——**data-duration 必须显式**（省略会被判多轨叠播，见 hf-contracts.md §4）。
- timeline.json 同步回填 narration_duration / narration_end，保持机读口径一致。

## 4. 字幕：双轨制

**画面内字幕**（烧进成片）：

- 独立 captions 合成（0 → 总时长），每条字幕一个独立元素 + fromTo 进出场，时刻写绝对时间。
- 样式：底部居中、深色圆角底板、46px（1080p）、关键词强调色加粗；最多两行。
- 长句切分：按**内容字符数占比**分配时长（标点不计权重），条间留 0.2–0.3s 空隙。
  精度预期 ±0.4s；如需逐词级，用 `npx hyperframes transcribe <wav> --language zh` 取词级时间戳重排。
- **与大字同文的条目画面内隐藏**（SRT 保留）——同屏重复是最常见的廉价感来源。

**外挂 SRT**（subtitles/captions.srt）：完整 21→N 条版本，供外挂播放与无障碍；
时间与画面内字幕同源（同一张时刻表生成两份产物，避免漂移）。

## 5. 混音检查清单（有音乐/音效时）

1. 有声看一遍、静音看一遍、只听不看一遍；
2. 最响音乐段里语音仍清晰（说话处压音乐，不是整体降音量）；
3. 每个音效与画面动作对齐；
4. 音乐有目的地结束，不是戛然而止。

无音乐/音效是合法选择（版权规避），报告中登记即可，不视为缺陷。
