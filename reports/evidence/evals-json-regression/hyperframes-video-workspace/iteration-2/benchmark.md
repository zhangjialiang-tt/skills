# Skill Benchmark: hyperframes-video

**Date**: 2026-10-31T02:58:07Z
**Evals**: 12 秒配音字幕短片端到端（evals.json id3 断言转译） (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 100% ± 0% |

## Per-Case Results

### 12 秒配音字幕短片端到端（evals.json id3 断言转译） (with_skill)

- **Pass Rate**: 100% (4/4)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| 产出 MP4 或按 TTS 降级规则产出无配音版并如实登记'部分交付/无音频'，未伪造音频生成成功 | ✅ | TTS 真实执行：transcript 记录下载 kokoro-v1.0.onnx（325532387 字节）与 voices-v1.0.bin，冒烟生成中文 2.03s（zf_xiaobei @1.22），4 段旁白均实际生成（'Generated 2.2s/3.7s/2.6s/2.8s of speech → assets/narration/n0X.wav'）并有 ffprobe 实测时长（MEASURED n01=2.197333 等）; v1 旁白两句超窗后按 skill 纪律改脚本而非硬提速（n02 改为「HTML，就是视频。」并重新生成，实测 2.517s），与 final_message 登记的取舍一致，无伪造; 成片音频真实存在：qc_sample 输出 'audio: aac 48000Hz 2ch, duration=12.000s'，语音窗口 mean -16.0~-20.4dB（有声），间隙窗口 -91dB，blackdetect 无事件，退出码 0; final_message 如实声明'本地 Kokoro 实测可用，未触发降级'，未声称降级也未伪造音频，并登记了无背景音乐等已知限制 |
| script.md 含事实核查表，storyboard 场景时长闭合等于总时长 | ✅ | script.md 写入内容含'## 事实核查表'，6 行逐条列出表述/依据/结论（官方 docs compositions、gsap、rendering，v0.8.222 会话内抓取核对），全部 ✅ 且结尾声明'无虚构设定'; storyboard.md 开头明确'硬校验：3.0 + 3.0 + 3.0 + 3.0 = 12.0s ✅ 时间闭合'，四个场景 S01 0–3.0 / S02 3.0–6.0 / S03 6.0–9.0 / S04 9.0–12.0 闭合等于总时长 12.0s; 事实核查依据来自会话内真实抓取的官方文档（WebFetch hyperframes.heygen.com/llms.txt 与 _llms/docs.txt 记录在 transcript 中） |
| 字幕方案存在（画面内或 SRT） | ✅ | 画面内字幕方案存在：storyboard.md 含'字幕时刻表（全片基准，画面内与 SRT 同源）'4 条 cap，画面内列全部 ✅；index.html 含 captions 合成（README 结构说明）; 外挂 SRT 存在：transcript 记录 subtitles/captions.srt 文件创建成功，内容为 4 条带时间码的字幕（00:00:00,400-->00:00:02,850 等），文本与 v2 修订后旁白一致; final_message 交付物列表明确包含 'subtitles/captions.srt' 外挂字幕链接 |
| 质量检查有执行证据（check/抽帧/qc 记录） | ✅ | npm run check 多轮真实执行：初检发现 3 条警告（S03 代码越界）后定位修复，最终输出 '◇ 0 errors, 0 warnings / ◇ 32/32 text checks pass WCAG AA / ◇ Check passed'，全量日志落盘 reports/check_full.log; qc_sample.py 以具体参数实际运行（--frames/--speech-windows/--gap-windows/--expect-duration 12），输出完整：ffprobe 参数核对、6/6 关键帧抽取、8 个体积窗口采样、blackdetect 无事件，退出码 0; 抽帧目检有执行记录：'npx hyperframes snapshot --at 1.9,4.7,7.5,10.7' 及 qc 抽帧到 reports\frames，final_message 登记成片抽帧目检无截断、无重叠 |

