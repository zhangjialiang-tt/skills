---
name: hyperframes-video
description: 用 HyperFrames 把一个主题从零制作为可播放的科技短片 MP4：环境勘察、官方契约核对、冒烟渲染验证、脚本与分镜（语速预算 + 事实核查 + 时间闭合）、HTML/CSS/GSAP 场景实现、本地 TTS 配音（实测时长驱动时间轴校准）、双轨字幕、渲染与自动化质量检查、模板化收口，全程确定性可复现。只要用户想"做一条视频/宣传片/产品介绍/科技短视频/动画短片"、"用 HTML 或代码做视频"、"提到 HyperFrames"，或想要一条不依赖 AI 视频生成模型、不需要真人出镜、可编程可复现的视频——即使没有点名框架——都应使用本 skill。不适用：AI 视频生成模型出画面、真人实拍/录屏剪辑、长片粗剪、外部平台发布（见 Non-goals）；只要离线前期生产包不要成片（走 ai-drama-pilot）。触发：做视频、宣传片、产品短片、片头、动画演示、HTML 视频、HyperFrames、MP4 产出。
---

# HyperFrames 视频生产（hyperframes-video）

本 skill 编排一条已验证的生产线：**主题 → 可播放 MP4**。核心思想是"HTML 就是视频"——画面由
HTML/CSS/GSAP 构成，HyperFrames 渲染器在无头 Chrome 中逐帧 seek 后交给 FFmpeg 编码，因此同一份
源码在相同框架版本/浏览器/字体环境下渲染出同一部片子（实际版本与依赖记入 execution_log），天然可编程、可版本管理、可复现。流程中每个阶段都有门禁与证据要求，
失败时按降级决策树走替代路径，不阻塞、不空转。

## Non-goals

- 不调用 AI 视频生成模型（本流程的全部动态画面来自代码动画）。
- 不为"AI 视频生成模型出画面"的短剧准备离线生产资料（剧本→分镜→逐镜提示词包）——那类需求走
  `ai-drama-pilot`。判断归属看用户要的结果：要成片 MP4 用本 skill，要"能拿去生成"的资料包用后者。
- 不替代 HyperFrames 官方 skill/plugin 与官方文档——框架契约以官方为准，本 skill 只固化生产编排与已验证的坑。
- 不做真人实拍、长片剪辑、外部平台发布，不调用任何付费服务。

## Inputs and defaults

| 参数 | 默认 | 说明 |
|---|---|---|
| 主题 | （必需） | 短片讲什么；受众与定位最好一并给出 |
| 时长 | 30s | 建议范围 10–90s；首次跑通建议 10–15s |
| 分辨率 / 比例 | 1920×1080 · 16:9 | 成本敏感时先用 1280×720 验证管线再上目标分辨率 |
| 帧率 | 30fps | HyperFrames 默认，稳定 |
| 视觉风格 | 深色科技、克制 | 高对比、少粒子、无频闪；详见 references/content-method.md |
| 配音 | 中文（本地 Kokoro TTS） | 可指定其他语言/音色；不可用时降级，见降级决策树 |
| 背景音乐 / 音效 | 无 | 只有用户提供合法授权素材时才加入 |

## 硬约束（每条都有原因，违反会导致返工或不可交付）

1. **先核对契约再写代码**。HyperFrames 版本演进快，动手前必须按 Phase 2 用官方 llms.txt 实时抓取
   当版本文档核对契约，不得凭训练记忆写 data 属性或时间轴 API。
2. **动画必须随机 seek 可靠**：显式初始状态 + 显式位置参数（入场 `fromTo()` 锚定两端状态；
   出场 `to()`/`set()` 仅用于已被 `fromTo()` 锚定的条目，模板即此用法），时间线 `{ paused: true }` 注册到
   `window.__timelines[合成ID]`；禁止无限循环（流动类动画用固定次数的有限循环）、禁止随机数与
   墙钟——渲染器会跳到任意帧，不满足这些的画面会跳变或渲染超时。
3. **音频实测驱动音频轴与字幕**：场景时长按语速预算在 Phase 3 定稿；TTS 实测时长驱动音频起点、
   字幕时间与速度系数回迁（相邻段系数差 ≤6%）；未拿到实测时长不得写死音频起点与字幕时间。
4. **门禁未过不进下一阶段**。每阶段的证据要求见"阶段门禁"表；跳门禁省下的时间会在渲染后加倍还回来。
5. **阻塞期必须并行**：模型/依赖下载、渲染进行时，转去做内容写作、字幕、文档等不被阻塞的阶段。
6. **每阶段成果立即落盘**（script.md、storyboard.md 等先于视频存在）；跨会话可恢复。
7. **无证据不称完成**：MP4 未 ffprobe 验证、有音轨而音频未采样、check 未通过，不得宣称交付
   （无音轨版本登记即可，qc_sample 会自动跳过音频窗口采样）。

## Workflow

### Phase 0 · 需求定位

与用户确认 Inputs 表中各项；未提供的按默认值执行并在最终报告中记录假设。确定叙事核心问题
（一条能勾住前 5 秒的问句或冲突）。

### Phase 1 · 环境勘察

不假设平台，逐项实测并记录（写入 progress.md）：

| 检查项 | 命令（按平台替换） | 要求 |
|---|---|---|
| Node.js | `node --version` | ≥ 22（HyperFrames 要求） |
| FFmpeg | `ffmpeg -version` / `ffprobe -version` | 在 PATH |
| 浏览器 | Chrome 或 Edge 可执行文件存在 | 渲染器无头调用 |
| 中文字体 | 字体目录存在（如 Windows Fonts 下 msyh*） | 无则改用可用的中文字体并同步 @font-face |
| 磁盘 | `df -h` 或等效 | ≥ 5GB 余量 |

### Phase 2 · 官方契约核对 + 安装冒烟

1. 抓取 `https://hyperframes.heygen.com/llms.txt` 定位当版本文档；重点核对：HTML schema、
   GSAP 动画契约、音频属性、渲染命令与参数。完整契约清单与核对要点见
   `references/hf-contracts.md`（含本 skill 上次验证的版本号——若当前版本更新，以官方为准）。
2. 在工作目录初始化项目：`npx -y hyperframes init <name> --example blank --non-interactive --skip-skills`
3. **冒烟渲染**：给空白项目加一个带 GSAP 动画的标题，`npm run check` 通过后
   `npx hyperframes render --quality draft --output renders/smoke.mp4`，ffprobe 验证编码/分辨率/时长/帧率。
   冒烟不过，先修环境（`npx hyperframes doctor`），不带病进入内容阶段。

### Phase 3 · 内容三件套（渲染/下载等待期可提前完成）

产出三个文件到 `project/`，方法与模板见 `references/content-method.md`：

- `script.md`：逐场景旁白，每句标注字数与语速预算（不超预算才有自然节奏），附**事实核查表**
  （每条产品表述 → 官方依据；**用户明确声明为虚构/演示用的设定允许保留**，表中标注"虚构"并在
  README 事实声明登记；仅删除 agent 自行推测、无依据的表述，不写推测性功能）。
  钩子写法、句子节奏、删减纪律与 TTS 发音风险见 `references/narrative-craft.md`。
- `storyboard.md`：每场景的起止时间/画面/动画时刻/音频需求/验收标准；**各场景时长之和必须等于总时长**。
- `design_system.md`：从 `references/design-system-starter.md` 的起始值**套改**（不从零发明
  色板与字阶），再按本片定位调整：色板（含对比度要求）、字体层级、组件规范（编辑器窗/流程节点/
  时间轴条/字幕条等）、动画节奏规则（入场 0.4–0.6s power3.out、只动 transform/opacity）。

脚本冻结后进入 Phase 4；后续改动须同步 storyboard 与字幕。用户要求先审脚本/分镜时
（如"先给我脚本和分镜再动手"），在此暂停并提交审阅，确认后再进入 Phase 4。

### Phase 4 · 场景实现

- 主合成 `index.html` 挂载各场景（`data-composition-src` 嵌套合成）+ 字幕合成 + 音频轨；
  每个场景独立成文件、可单独渲染检查。骨架从 `assets/index-template.html` 与
  `assets/scene-template.html` 复制改写；含完整动画时序的范例场景（开场钩子 / 数据图表）见
  `assets/examples/`，六大组件模式（编辑器窗/流程管线/多轨时间轴/柱状图/宫格墙/字幕条）见
  `references/component-cookbook.md`；契约细节与踩坑清单见 `references/hf-contracts.md`。
- 优先复用统一视觉组件（设计系统里定义过的），不为单场景发明一次性样式。
- GSAP 下载到项目 `assets/gsap.min.js` 引用（渲染期不依赖外网；注意与 skill 自带的 `assets/` 模板目录区分）。

### Phase 5 · check 门禁循环

`npm run check`（= lint + 运行时 + 布局 + 动效 + 对比度）。报错时按
`references/qc-method.md` 的"修复模式表"定位处理（字体声明、音频 data-duration、首帧内容、
字号下限、对比度 3:1、重叠、停留时长等），修到 0 错误 0 警告再进 Phase 6。

### Phase 6 · 快照目检循环

check 通过 ≠ 好看。`npx hyperframes snapshot --at <关键时刻列表>` 抽帧逐张看：场景是否按
storyboard 出现、文字是否截断/重叠/与场景大字同文、组件是否对齐。发现问题回 Phase 4 修，
再 check、再抽帧，直到干净。

### Phase 7 · 配音（TTS 速度系数法）

1. 旁白逐句落成文本文件；`npx hyperframes tts`（本地 Kokoro）逐句生成 WAV，输出路径见
   `references/audio-captions.md`。
2. ffprobe 实测每段时长；超场景窗口的段落按 `时长 × 当前速度 / 预算` 反算速度系数重新生成
   （相邻段系数差控制在 6% 内，听感才连贯）。
3. 校验音量（volumedetect：无削波、响度一致）。
4. **降级**：TTS 不可用（依赖装不上/无网络）→ 直接做无配音版：屏幕字幕承担全部叙事，
   在报告中如实登记"无音频"，不得伪造音频生成成功。**用户明确要求过配音时，报告须标注
   "部分交付"**（原需求含配音、当前未完成），并说明原因与补齐路径（旁白脚本与生成接口保留）。
5. 把实测时长回填 index.html 音频轨（必须显式 `data-duration`）与字幕时间。

### Phase 8 · 字幕双轨

- 画面内字幕：独立 captions 合成，时间与旁白逐条对齐；与大字同文的条目画面内隐藏。
- 外挂 SRT：完整版（含未上屏条目），导出到 `subtitles/captions.srt`。
- 方法：`references/audio-captions.md`。

### Phase 9 · 渲染与质量检查

0. **回填后终审门禁（render 之前必做）**：Phase 7–8 改过 index.html（音频 data-start/
   data-duration、字幕合成内容），字幕合成从未单独过 lint。对最终状态重跑 `npm run check`
   （0 错 0 警）+ `npx hyperframes snapshot --at <字幕关键时刻>`；不过不进 render——
   这一步的成本远低于渲染后返工。
1. `npx hyperframes render --output renders/final.mp4`（默认 looks 质量），产物复制到
   `output/<项目名>.mp4`。
2. 运行 `python <skill>/scripts/qc_sample.py output/<项目名>.mp4 --frames <关键时刻> --expect-duration <总时长> ...`
   （`<skill>` = 本 SKILL.md 所在目录，不是项目目录）
   一次完成：ffprobe 参数核验（含时长 ±0.1s 比对）、关键帧抽取、音量窗口采样、黑帧检测。
   退出码即门禁：0=无异常；2=用法/环境错误；3=采样失败；4=发现异常待定性。
   `--json` 时 stdout 为纯 JSON（报告走 stderr），可直接机读。
3. 抽帧逐张目检；blackdetect 事件必须抽帧定性（深色主题下大面积低亮度是常见误报，
   以人眼抽帧为准），结论写入 `reports/quality_report.md`。

### Phase 10 · 模板化收口

- 把本片**实际复用过的**组件写进 `project/template_guide.md`（哪些文件改什么就能换内容），
  不做过度抽象（组件模式库见 `references/component-cookbook.md`）。
- `README.md`：环境要求、快速重渲命令、结构说明、事实声明（含虚构设定登记）、已知限制。
- `progress.md` / `execution_log.md` 全程落盘；最终报告须含：实际完成项、MP4 路径与实测参数、
  是否有配音、真实验证过什么、未完成项与原因、已知缺陷、如何重跑。

## 阶段门禁

| 阶段 | 通过证据 |
|---|---|
| P1 环境 | progress.md 记录各项实测结果 |
| P2 冒烟 | smoke.mp4 存在且 ffprobe 参数正确 |
| P3 内容 | script.md 有事实核查表；storyboard 时长闭合；语速逐句 ≤ 预算 |
| P4 实现 | 文件齐备，场景均可独立定位 |
| P5 check | 0 错误 0 警告 |
| P6 目检 | 抽帧无截断/重叠/缺场 |
| P7 配音 | 每段实测时长落入场景窗口；或降级已登记 |
| P8 字幕 | SRT 与画面内字幕同源同时刻 |
| P9-0 终审（Phase 9 步骤 0） | 音频/字幕回填后 check 0 错 0 警 + 字幕时刻快照无截断/重叠 |
| P9 QC | ffprobe + 采样 + 目检三件齐，quality_report.md 落盘；qc_sample 退出码 0，或异常已逐条定性 |
| P10 收口 | template_guide + README + 最终报告 |

## 降级决策树

- **TTS 不可用** → 无配音 + 屏幕字幕版（叙事全部上屏），报告登记；保留旁白脚本与生成接口。
  用户明确要求过配音时登记为"部分交付"并给出补齐路径，不得表述为原需求完成。
- **官方文档不可达** → 以 `references/hf-contracts.md` 记录的契约继续，报告标注"契约基于
  <验证日期+版本>，未能当版本核对"。
- **渲染失败** → `doctor` → `lint` → `check` 阶梯定位，读首个确切错误再修；禁止原地无限重试同一命令。
- **渲染太慢/成本高** → 先 `--quality draft` + 低分辨率验证内容，锁定后再出正式规格成片。

## 输出契约

```
output/<项目名>.mp4          # 最终成片（唯一交付视频）
project/                     # script.md / storyboard.md / design_system.md / timeline.json / template_guide.md
subtitles/captions.srt       # 外挂字幕
subtitles/subtitle_plan.md   # 字幕方案
audio/audio_plan.md          # 音频方案与实测时长表
reports/quality_report.md    # 质量检查报告（含抽帧定性证据）
reports/script_review.md     # 脚本评审
README.md / progress.md / execution_log.md
```

机器可读产物（JSON/SRT/命令输出）保持原始格式；报告中的每个结论都要能指到文件或命令输出。

简单短片（≤15s、无配音）可裁剪产物：保留 script/storyboard（可合并为一份）、成片与必要验证；
事实核查深表、design_system、template_guide 按内容量与复用需要生成，裁剪项在最终报告中登记。
