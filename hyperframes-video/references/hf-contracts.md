# HyperFrames 硬契约与踩坑清单

> 出处：hyperframes-agent-video 项目生产实战核对，验证于 2026-10-29，CLI v0.8.216。
> **使用前必读**：框架版本演进快，本文件是"上次验证的基线"，不是永恒真理。
> 每次生产前先抓 `https://hyperframes.heygen.com/llms.txt` 定位当版本文档，
> 核对本文各节是否仍然成立；冲突时以官方为准并在执行日志记录差异。

## 1. HTML schema 契约

### 合成根元素（必需属性）

```html
<div id="root"
     data-composition-id="main"   <!-- 唯一 ID，须与 window.__timelines 注册键一致 -->
     data-start="0"               <!-- 顶层根必需 -->
     data-duration="90"           <!-- 总渲染时长（秒），编译器在脚本运行前读取，脚本改不动 -->
     data-width="1920" data-height="1080">
```

- `data-duration` 是输出窗口：省略时会从时间线与媒体推断，但含 Three.js/无限动画/无时间线的合成必须显式声明。
- 无时间轴的静态嵌套块加 `data-no-timeline`，否则渲染器等满 player-ready-timeout（默认 45s）。

### 定时 clip

- `id` 必需（计时/编辑/动画的稳定标识）。
- `data-start` 必需（秒数，或引用同合成内另一 clip 的 `clip-id ± seconds` 相对时间，不可成环）。
- `data-duration`：DOM/嵌套合成必需；图像可选（默认 3s）；**音视频建议一律显式声明**（原因见 §4）。
- `data-track-index` 只是编辑器显示轨道，渲染不读、不防重叠——层级用 CSS z-index。
- 定时 DOM 元素加 `class="clip"`（lint 依赖它给满幅盒子）。

### 媒体属性

- `<video>`/`<audio>` 源内偏移用 `data-media-start`；嵌套合成的播放偏移用 `data-playback-start`（两者不可混用——音频混音器只读 media-start）。
- `data-volume` 1 = 0dB，上限 3.98（+12dB）；`data-fade-in/out` 线性增益淡变。
- 每个定时视频必须二选一：`muted`（无声）或 `data-has-audio="true"`（lint: video_missing_muted）。
- **禁止**手动 `play()/pause()/currentTime`——媒体播控归渲染器；要动视频就动它的外层包装元素。

## 2. GSAP 动画契约（可 seek 的关键）

```js
const tl = gsap.timeline({ paused: true });
tl.fromTo("#title", { opacity: 0, y: 40 },
          { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, 0.2); // 位置参数显式
window.__timelines = window.__timelines || {};
window.__timelines["main"] = tl;   // 键 = data-composition-id
```

- 两端状态都重要时用 `fromTo()`（随机/回退 seek 后仍可靠）；`to()/from()` 慎用于关键帧。
- 只动画 `transform / opacity / clip-path`；`top/left/width/height` 会引发布局抖动。
- 字体测量前先 `document.fonts.load()`；**先建完全部 tween，最后才注册时间线**（过早注册空时间线会让嵌套合成被提前判定就绪）。
- clip 的出现/隐藏交给 data-start/data-duration，不要在时间线里重复管可见性。
- 异步就绪（字体等）完成后再注册；不要在渲染路径上等待网络。

## 3. 确定性三禁

渲染要求"同源码 + 同媒体 + 同设置 → 同帧同结果"：

1. 禁 `Date.now()` / 墙钟；
2. 禁未播种随机（`Math.random()`）；
3. 禁渲染期网络请求（GSAP 等依赖下载到本地 assets 引用）。

无限循环动画（`repeat: -1`）同样破坏 seek 语义——流动/循环效果写成固定次数的有限循环。

## 4. 音频轨（实战踩坑最多的一节）

- `<audio>` **必须显式 `data-duration`**。省略时检查器按"延伸到片尾"判定，多段旁白会被判
  `duplicate_audio_track`（全部叠播）。用 ffprobe 实测时长后逐段写死。
- 音频默认取源长度，但显式声明是唯一可靠口径。
- 音画对齐：`data-start` = 场景起点 + 0.4~0.5s（开场句留半秒呼吸）。

## 5. 字体

- 中文系统字体（微软雅黑等）必须声明且 **font-family 使用列表里的每个名字都要有对应 @font-face**：

```css
@font-face { font-family: "Microsoft YaHei"; src: local("Microsoft YaHei"), local("微软雅黑"); }
```

（lint 报 `font_family_without_font_face` 的两种形态：缺声明、或用了未声明的别名——最简做法是
使用列表只留一个名字。）实测路径：Windows 本机 msyh.ttc 经 `local()` 引用渲染正常。

## 6. 嵌套合成的规范结构（官方示例形态）

子合成文件整体包在 `<template id="xxx-template">` 里，`<style>` 与 `<script>` 放在**合成根 div 内部**，
选择器用 `[data-composition-id="xxx"]` 前缀限定作用域：

```html
<template id="s01-template">
  <div data-composition-id="s01" data-width="1920" data-height="1080" data-duration="7">
    <div class="stage">…</div>
    <style> /* 作用域样式 */ </style>
    <script src="assets/gsap.min.js"></script>
    <script> /* 时间线注册，键 = s01 */ </script>
  </div>
</template>
```

宿主挂载：

```html
<div class="scene" data-composition-id="s01" data-composition-src="compositions/s01.html"
     data-start="0" data-duration="7" data-track-index="1" data-width="1920" data-height="1080"></div>
```

- 宿主的 composition-id 须与子文件内部 ID、时间线注册键三方一致。
- 不要把子时间线手动加进父时间线——渲染器独立 seek 子合成。

## 7. GSAP 的能力边界（踩过才知道）

- **不能动画伪元素**（`::after/::before`）——连线生长这类效果用真实子元素 + `transform: scaleX`。
- **不要用 className 切换表达状态**——直接动画 `borderColor/opacity/scale` 等属性，
  随机 seek 才不残留状态。
- `tl.set(el, { innerText: "..." })` 可用（官方示例在用），但逐条独立元素 + fromTo 更直观。

## 8. lint/check 修复模式速查（v0.8.216 实测）

| 规则/警告 | 修法 |
|---|---|
| font_family_without_font_face | 见 §5 |
| video_missing_muted | 定时视频加 `muted` 或 `data-has-audio="true"` |
| duplicate_audio_track | 音频显式 data-duration（§4） |
| first_frame_empty | 首帧（=社交封面）必须有内容：开场场景不要从 opacity 0 淡入，先让标题暗态可见 |
| text_below_floor | 阅读类文字 ≥28px（1080p 下 2.6% 短边）；纯装饰小字加 `data-layout-ignore` |
| line_unread | 文字停留 ≥ 0.5s + 0.3s/词；提前入场或缩短文案 |
| content_overlap | 给每块文字独立区域；刻意重叠在文本元素上加 `data-layout-allow-overlap`（场景根上标记无效） |
| dead_stretch | >3s 无画面变化：安排下一个动作，或对刻意停留的元素加 `data-hold` |
| 对比度 <3:1 | 大文字需 3:1、正文 4.5:1；低透明度水印调 alpha（实测 0.58/深底可达标） |
| container_overflow(info) | 装饰性溢出且 overflow:hidden 裁切住的可忽略 |
| film_silent(info) | 无音轨提示；无配音版本属预期，报告登记即可 |

## 9. 渲染命令备忘

```bash
npm run check                                     # lint+运行时+布局+动效+对比度
npx hyperframes snapshot --at 0.5,3,20            # 指定时刻抽帧（--range 起止亦可）
npx hyperframes render --quality draft --output renders/preview.mp4
npx hyperframes render --output renders/final.mp4 # 默认 looks（CRF16）、1920x1080、组合的 data-fps 或 30fps
npx hyperframes doctor                            # 环境诊断
npx hyperframes preview --background              # 后台 Studio 预览（agent 安全）；--status / --stop
```

- 渲染失败顺序：`doctor` → `lint` → `check`，抓住第一个确切错误再动手。
- 产物默认 `renders/`；帧数 = duration × fps，渲染日志里 totalFrames 可对账。
- `npx hyperframes tts --voice zf_xiaobei -l zh` 本地 Kokoro 配音（详见 references/audio-captions.md）。
