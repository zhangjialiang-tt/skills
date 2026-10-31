# 起始设计系统（design-system-starter）

> 出处：hyperframes-agent-video 项目 design_system.md，验证于 2026-10-30（成片通过 `npm run check`
> 0 错 0 警、WCAG AA 对比度、12 帧抽帧目检）。本文件是**默认值来源**，不是永恒真理：
> Phase 3 产出 design_system.md 时从本文件套改，不从零发明色板与字阶；换风格时改 token 值，不动结构。

## 1. 使用方式

1. 整表复制到项目 `project/design_system.md`，按需替换主强调色与品牌字标；
2. 场景 CSS 一律引用这里的 token 值，**不在单个场景里发明新颜色/新字号**（跨场景一致性是"不廉价"的第一来源）；
3. 对比度要求与字号下限是 lint 硬门槛，不放宽；
4. 每部片只允许一套强调色组合；确需第二强调色时仅用于大字号 ≥44px 元素。

## 2. 画布与安全区

| 项 | 值 |
|---|---|
| 画布 | 1920×1080（成本敏感可 1280×720，全部 px 值按比例缩放） |
| 安全区 | 左右 ≥120px、上下 ≥90px（内容区 1680×900，起点 120,90） |
| 字幕带 | 底部 y=920–1010，居中，单行为主、至多两行 |
| 场景根 | `overflow: hidden`，禁止元素越出画布 |

## 3. 色板（默认深色科技风）

| 变量 | 值 | 用途 |
|---|---|---|
| `--ground` | `#0A0E14` | 全局背景 |
| `--panel` | `#121A26` | 面板 / 编辑器窗 |
| `--panel-edge` | `#1E2A3A` | 面板描边、连线静止态 |
| `--ink` | `#E8EDF4` | 主文字 |
| `--ink-dim` | `#9AA7B8` | 次级文字（仅 ≥32px 使用） |
| `--accent` | `#22D3EE` | 主强调（青） |
| `--accent-2` | `#818CF8` | 次强调（靛） |
| `--accent-warm` | `#F59E0B` | 少量点睛（仅印章/关键高亮） |
| `--code-bg` | `#0D1420` | 代码块底 |
| `--code-green` | `#7EE787` | 代码字符串/成功态 |
| `--code-purple` | `#C297FF` | 代码属性名 |

对比度要求（lint 硬门槛）：正文 `--ink` 对 `--ground` ≥12:1；字幕 ≥10:1；
`--ink-dim` 仅用于 ≥32px 文字；水印类低透明度元素实测 alpha 0.58/深底可达 3:1。

**暖色变体（未实测，首片必须跑 check 对比度项）**：`--ground` 保持深底不动，
`--accent` 换 `#F59E0B`、`--accent-2` 换 `#FB923C`，其余 token 不变。
该组合仅在项目印章元素（3px 描边、40px 字）上用过，**未做过正文/字幕的 AA 验证**，
换色后第一件事是跑 `npm run check` 看对比度报告。

## 4. 字体体系

- 显示字体：`"Microsoft YaHei", "微软雅黑", sans-serif`（**font-family 列表里每个名字都要有对应
  `@font-face` 声明**，最简做法是使用列表只留一个名字；本机 msyh.ttc 经 `local()` 引用渲染正常）；
- 代码字体：`Consolas, "Courier New", monospace`；
- 字号层级（1080p）：

| 层级 | px | 用途 |
|---|---|---|
| 巨标题 | 128 | 开场字标 |
| 场景主标题 | 84 | — |
| 内容标题 | 56 | 底部标语/结论句 |
| 正文 | 40 | — |
| 字幕 | 46 | 烧录字幕 |
| 代码 | 34 | — |
| 小注 | 28 | lint 下限，再小会被 `text_below_floor` 警告（纯装饰加 `data-layout-ignore`） |

- 字重：标题 700、正文 400、代码 400；中文行高 1.5、标题 1.2；
  `letter-spacing`：中文 0.01em，Logo 字标 −0.03em。

## 5. 组件规格（跨场景复用，动画写法见 component-cookbook.md）

1. **编辑器窗**：panel 底、1px panel-edge 描边、圆角 16px、标题栏高 56px；
   标题栏三点用单色系 `#2A394B`（不要用 macOS 三原色，破坏深色克制感）。
2. **代码块**：code-bg 底、Consolas 34px、行高 1.7、内边距 32px；
   标签 `--accent`、属性名 `--code-purple`、字符串 `--code-green`。
3. **流程节点**：胶囊/圆角 20px，panel 底 + 2px panel-edge 描边；
   点亮态描边 `--accent`、文字 `--ink`；连线 2px panel-edge，生长态 `--accent`。
4. **时间轴轨道**：高 72px、圆角 10px；画面轨 `--accent-2`、字幕轨 `--accent`、
   音频轨 `--code-green`、转场轨 `--ink-dim`；刻度线 1px `rgba(232,237,244,0.12)`。
5. **字幕条**：底 `rgba(10,14,20,0.72)`、圆角 12px、内边距 20px 40px、文字 46px `--ink`，
   最多两行；关键词用 `--accent`。
6. **图表柱**：宽 96px、圆角顶 8px、`--accent-2` 渐变至 `--accent`；数值标签 32px。
7. **印章**：3px 描边 `--accent-warm`、圆角 12px、旋转 −8°、内文 40px。

## 6. 动画节奏规则

| 动作 | 时长 | 缓动 | 说明 |
|---|---|---|---|
| 入场 | 0.4–0.6s | `power3.out` | 位移 32–48px |
| 出场/淡出 | 0.3–0.4s | `power2.in` 或 opacity 直落 | — |
| 强调高亮 | 0.2s | `power2.out` | 亮起 0.2s → 退暗 0.35s 脉冲 |
| 场景转场 | 首/尾各 0.4s | `none`（opacity） | 各合成自身 timeline 控制 stage opacity |

- 只动 `transform / opacity / clip-path`；不动画 `top/left/width/height`（柱状图用 `scaleY`）；
- 时间基准：全部动画写入各自嵌套合成的 paused GSAP timeline，位置参数显式；主合成只管场景进出；
- 禁止：无限循环（箭头/帧流动为固定次数有限循环）、随机数、墙钟、渲染期网络请求。

## 7. 背景纹理与装饰

- 全局：径向渐变 vignette（中心透明 → 边缘 `rgba(0,0,0,0.35)`）+ 顶部强调色 4–10% 光晕，**静态不动画**；
- 网格：40px 网格线 `rgba(232,237,244,0.03)`，仅开场/结尾场景使用，静态；
- 光标闪烁：2 次/秒方波（`set` 打点，不用 CSS animation），仅开场场景；
- 场景编号水印：右上 28px `--ink-dim`、alpha 0.58，便于审查定位；
- 不使用粒子、噪点视频、频闪、大面积无意义发光。

## 8. lint 安全值速查（这套值为什么能过 check）

| 检查项 | 本系统的安全值 |
|---|---|
| `text_below_floor` | 阅读类文字 ≥28px；装饰小字加 `data-layout-ignore` |
| `line_unread` | 文字停留 ≥0.5s + 0.3s/词；最长字幕条预演不越界 |
| `content_overlap` | 每块文字独立区域；刻意重叠在**文本元素上**加 `data-layout-allow-overlap` |
| `first_frame_empty` | 开场场景标题"暗态可见"（opacity ≥0.3），不从 0 淡入 |
| `dead_stretch` | >3s 无画面变化要安排下一个动作，或对刻意停留加 `data-hold` |
| 对比度 <3:1 | 大文字 3:1、正文 4.5:1；水印 alpha 调到 0.58 |
| `film_silent` | 无音轨提示；无配音版本属预期，报告登记即可 |
