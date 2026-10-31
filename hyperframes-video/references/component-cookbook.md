# 组件菜谱（component-cookbook）

> 出处：hyperframes-agent-video 项目实战（2026-10-30，10 场景全部过 check + 抽帧目检）。
> 每个组件给出：用途 / 结构 / 关键值 / 动画 / 专属坑。色板与字号一律引用
> `design-system-starter.md` 的 token，本文件不重复。完整可运行场景见 `assets/examples/`。

## 0. 所有组件共用的结构约定（违背任何一条都会在 check 返工）

```html
<template id="xxx-template">
  <div data-composition-id="xxx" data-width="1920" data-height="1080" data-duration="8">
    <div class="stage"> …组件 DOM… </div>
    <style> /* 作用域样式，选择器一律 [data-composition-id="xxx"] 前缀限定 */ </style>
    <script src="assets/gsap.min.js"></script>
    <script> /* paused timeline + window.__timelines["xxx"] 注册 */ </script>
  </div>
</template>
```

1. `<style>`/`<script>` 放在**合成根 div 内部**，选择器用 `[data-composition-id="xxx"]` 前缀限定作用域；
2. **每个嵌套合成文件都要写 `@font-face`**（独立样式作用域，lint 逐文件检查——本项目第一轮就踩过）；
3. 首尾淡变对：`fromTo(stage, opacity 0→1, 0.4s, 0)` + `to(stage, opacity→0, 0.4s, duration−0.4)`
   （**开场场景例外**：只有尾淡变，首帧必须有内容）；
4. 动画一律 `fromTo` + 显式位置参数；先建完全部 tween，最后才注册 timeline；
5. 宿主挂载：`data-composition-src` 指向文件，宿主 id 与子文件内部 id、注册键三方一致。

## 1. 编辑器窗 + 代码块（代码展示场景）

用途：展示 HTML/代码片段，配右侧"结果预览"形成因果对照。

- 结构：`.editor`（标题栏 56px + `.code` 区）→ 每行一个 `.ln`；语法着色用 class：
  `.tag`（标签，accent）/ `.attr`（属性名，code-purple）/ `.str`（字符串，code-green）；
- 关键值：code-bg 底、圆角 16px、Consolas 34px、行高 1.7、padding 40px 44px；
- 动画：窗口 `y:48→0` 升入（0.7s power3.out）→ 代码行逐条 `opacity+y` 进场（0.35s/条，间隔 0.36s）
  → 右侧预览框延后 1.5s 左右进入，形成"先写后渲"的因果节奏；
- 专属坑：
  - 代码行必须逐条动画或逐条着色，**整块静态代码会被判 `dead_stretch`**，且观感廉价；
  - HTML 实体在代码块里要转义（`&lt;div&gt;`），否则解析错误；
  - 行长短预演：超长行会换行破版，代码字号 34px 下单行 ≤ 30 字符。

## 2. 流程管线（步骤流/ pipeline 场景）

用途：多步骤流程依次推进，最后可收敛为一个符号或结论。

- 结构：`.flow-row`（flex，`justify-content: space-between`）→ 若干 `.node`（图标+标签）
  + 节点间 `.link`（2px 线，内部 `.fill` 子元素做生长）；
- 动画：节点依次 `scale 0.92→1 + borderColor 点亮`（0.45s/个，间隔 0.45s）；
  连线 `scaleX 0→1`（0.4s）错峰生长；结局符号 `back.out(1.4)` 弹入；
- 专属坑：
  - **连线生长不能用伪元素**（GSAP 不能动画 `::after`）——用真实子元素 `.fill` + `scaleX`；
  - 节点"点亮"直接动画 `borderColor/opacity/scale`，**不要用 className 切换**（随机 seek 残留状态）；
  - 流动箭头类循环写成固定次数有限循环（如 3 轮），禁止 `repeat: -1`。

## 3. 多轨时间轴（排期/编排类内容）

用途：展示"片段/字幕/音频/转场"多轨排布，播放头扫描。

- 结构：`.panel`（圆角 16px）→ `.ruler`（刻度 tick）+ 若干 `.lane`（名称 160px + `.bars` 轨道区）
  → `.bar` 绝对定位（`left/width` 百分比）→ `.playhead`（3px 竖线）；
- 动画：面板升入 → 刻度 `stagger: 0.08` 淡入 → 轨道条 `scaleX 0→1` `stagger: 0.22` 依次生长
  → 播放头 `set(x:0)` 后 `to(x:内容区宽度, 5s, none)` 线性扫描；
- 专属坑：
  - 播放头 x 位移量 = 面板内容区实际宽度（面板宽 − padding − 名称列宽），**用常量算好写死**，
    用百分比 left 动画在随机 seek 下不可靠；
  - 轨道条初始态 `transform: scaleX(0)` + `transform-origin: left center`（CSS 初态与 fromTo 一致）；
  - 扫描过程点亮面板用 `filter: brightness` 脉冲即可，不要每轨单独高亮（过度设计）。

## 4. 柱状图/数据增长（数据展示场景）

用途：数值对比、增长叙事；同一组件换数据换配色复用。

- 结构：`.chart-card`（面板）→ `.chart`（flex，`align-items: flex-end`）→ 每个 `.col`
  （`.col-bar` + `.col-val` 数值标签）；
- 关键值：柱宽 96px、圆角顶 8px、渐变 `--accent-2 → --accent`；
- 动画：柱子 `scaleY 0→1`（0.55s power3.out，`transform-origin: bottom center`）依次生长；
  **数值标签延后 0.35s 再淡入**（先长后读数，符合认知顺序）；
- 专属坑：
  - **不动画 height**（引发布局抖动），一律 `scaleY`；
  - 柱高写死在 inline style（`height: 260px`），只改数值即可复用；
  - 两张卡片演示"同组件复用"时，第二张整体延后 2.5s 以上进入，避免同时运动抢注意力。

## 5. 宫格缩略墙（合集/回顾场景）

用途：多镜头回顾、封面合集；可整体收缩为"胶片带"。

- 结构：`.grid-wrap`（`display: grid; grid-template-columns: repeat(3, 320px); gap: 20px`）
  → 若干 `.cell`（编号+标签）；最后一格 `.hero` 用强调色渐变底；
- 动画：格子 `opacity + scale 0.88→1` `back.out(1.4)` 依次亮起（0.4s/个，间隔 0.27s）
  → 整体 `scale 0.62 + y 位移` 收缩为胶片带（1.1s power3.inOut）→ 印章弹入；
- 专属坑：
  - 格子内小字（编号 26px）加 `data-layout-ignore`，否则 `text_below_floor` 警告；
  - 收缩动画作用于**容器** `.grid-wrap`，不要逐格计算目标位置；
  - 印章 `back.out(1.8)` 从 `scale 1.7` 收入，旋转角在 from/to 两端都写（seek 可靠）。

## 6. 字幕条与 captions 合成（双轨字幕的画面内部分）

用途：烧录字幕；与旁白逐条对齐；与大字同文的条目隐藏。

- 结构：主合成内独立 captions 合成（0 → 总时长），每条字幕一个独立元素，`CAPS` 三元组
  `[id, 开始, 结束]` 驱动；样式：底部居中、`rgba(10,14,20,0.72)` 圆角底板、46px、最多两行；
- 动画：每条 `fromTo(opacity+y)` 进出场，绝对时间写死；完整方法见 `references/audio-captions.md`；
- 专属坑：
  - **与场景大字同文的条目画面内隐藏**（SRT 保留）——同屏重复是最常见的廉价感来源；
  - captions 合成的 `data-duration` = 全片总时长，不是单条时长；
  - 字幕时间必须用 TTS **实测时长**回填，禁用预算估算值（见 audio-captions.md 速度系数法）。

## 7. 反模式清单（做了就会廉价或返工）

- 大面积无意义发光、高频闪烁、粒子海、复杂背景纹理；
- 字幕对比度不足或字号过小（<46px 或底板透明度 >0.85）；
- 动画抢旁白的注意力（画面是释义不是伴奏）；
- 渲染路径上的 3D/着色器炫技——可靠性优先于复杂度；
- 单场景发明一次性样式（应在 design_system 里先定义再引用）；
- className 切换表达状态、伪元素动画、`repeat: -1`、墙钟与随机数（随机 seek 必翻车）。
