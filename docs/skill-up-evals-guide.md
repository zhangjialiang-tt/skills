# skill-up 评测套件使用指南（docs/skill-up-evals-guide.md）

> 面向对象：未来在本仓库工作的新会话/新 agent。读这一篇即可上手运行 15 个技能的评测套件，
> 不需要了解 2026-10-31 那轮优化的全过程。历史背景见 `reports/optimization-summary.md`。

## 1. 这是什么

本仓库 15 个技能每个都有一套 **skill-up 原生评测套件**（`<skill>/evals/eval.yaml` + `evals/cases/*.yaml`），
共 49 个用例。`evals/evals.json`（Anthropic/自造格式）是**更早的基线，原样保留、禁止删改**；skill-up 套件
是并存的自动化回归层。

用例分两层：

- **低成本行为用例**（每技能 2–4 个）：触发正/负、边界转介、单点行为确认，判定全为
  `rule_based`（`output_contains` + `expect` 门控）；
- **端到端用例**（6 个技能各 1 个）：真实产出物 + `script` judge
  （checker 脚本位于 `<skill>/evals/fixtures/scripts/*.cmd`，单文件 polyglot，见 §4）。

## 2. 前置条件

| 依赖 | 位置 | 说明 |
|---|---|---|
| skill-up CLI | `~/.local/bin/skill-up.exe`（v0.14.0，Windows amd64） | `skill-up --version` 验证 |
| claude CLI | PATH 中（claude_code 引擎用本机登录态） | `claude -p "reply OK"` 冒烟 |
| Python | PATH（3.11+） | checker 脚本运行时 |
| 判定模型 | 引擎默认模型 | 无需 ANTHROPIC_API_KEY；agent_judge 用 `judge.model: claude-sonnet-4-6` |

## 3. 标准运行流程

**永远在沙箱里跑，不要直接在仓库跑**（评测 agent 会在 case workspace 写文件；上轮出现过 agent
越界写行为迹象，沙箱保证源目录隔离）：

```bash
# 1) 建沙箱并复制完整技能（必须含 SKILL.md 本体，否则 skill-up 拒装）
SB=$(mktemp -d)
cp -r <仓库根>/<skill> "$SB/"
find "$SB/<skill>" -name __pycache__ -type d -exec rm -rf {} +

# 2) 快速配置校验（不烧 token）
cd "$SB/<skill>" && skill-up validate evals/eval.yaml

# 3) 跑评测（单用例调试用 --include-case-name；全量直接 run）
cd "$SB/<skill>" && skill-up run evals/eval.yaml

# 4) 证据回填仓库（原生报告是唯一证据锚点）
cp -r "$SB/<skill>-workspace/iteration-N" <仓库根>/<skill>-workspace/
```

全量 validate 循环（验证 1 原文命令）：

```bash
for d in ai-drama-pilot ai-plat-bridge build-testbench cocotb-testbench goal-generator \
         hyperframes-video no-gui-debug openviking-agent-onboarding openviking-memory-governance \
         requirement-alignment rtl-readability rtl-refactor-scan smart-commit zcode-idle-task \
         zg-agent-setup; do
  skill-up validate $d/evals/eval.yaml || echo FAIL:$d
done
```

## 4. script judge 的 polyglot 机制（重要）

skill-up 的 Windows script judge **只把 script_path 指向的单个文件复制到临时目录执行**：
- 同目录的 `.py` 拿不到（`%~dp0` 指向 judge 临时目录）；
- 技能的安装副本（case workspace 的 `.claude/skills/<skill>/`）**不含 evals/**；
- `python script.py` / shebang 均不被识别。

因此 checker 写成 **cmd/python polyglot 单文件**（`*.cmd`）：

```
@echo off & python -x "%~f0" %* & exit /b %ERRORLEVEL%
# -*- coding: utf-8 -*-
<完整 Python 判定逻辑>
```

`python -x` 跳过第一行 cmd 头，从第二行起按 Python 执行——**单文件自包含、零路径依赖、可移植**。
`.py` 同名文件保留仅作可读参考，judge 实际跑的是 `.cmd`。修改判定逻辑时**只改 `.cmd`**（或改 .py 后
重新拼接，参考 `reports/optimization-summary.md` §2 的生成方式）。

## 5. 判定与成本预期

| 用例类型 | 单次耗时 | 成本来源 |
|---|---|---|
| rule_based（触发/边界/行为） | 3–10 分钟 | agent 会话 |
| script（端到端产出） | 15–40 分钟 | agent 会话（生产包/框架/渲染） |

调参经验：

- 引擎默认 300s 超时偏紧，多数套件 defaults 已提到 600s，重用例 900–1800s（在 case 的
  `constraints.timeout_seconds` 或 eval.yaml `cases.defaults`）；
- 超时（`context deadline exceeded`）→ 先提 timeout 重跑一次，再考虑把 prompt 聚焦到"说明方案
  不要执行"（见 §6.3）。

## 6. 常见失败模式与处置（上轮实测沉淀）

1. **否定性提及误伤**：`expect.must_not_contain`/checker 词面断言会把 agent 引用契约原文的解释
   （"不能宣称功能正确"）误判为违规。处置：词面检查只保留在"宣告式"模式（如 `"任务合同如下"`、
   `已验证功能正确`），或把精确判定放进 checker（查 log 文件而非 final message）。
2. **agent 输出变体**：同一用例 PASS/FAIL 漂移（如 /goal 前缀偶发遗漏）。处置：先重跑一次再定性；
   连续漂移则在报告记输出稳定性备注，不要为单次变体改断言。
3. **agent 真的去执行了**：端到端/重场景用例若只想测路由/方案层，prompt 显式写"说明归属与理由
   即可，先不要实际执行"，否则 agent（尤其面对可执行小任务）会直接开工导致超时。
4. **转介类用例需要双技能挂载**：转介目标技能要在 eval.yaml 的 `skills[]` 里同时挂载
   （仓库内用 `path: ../<skill>`，仓库外用绝对路径如 `C:/Users/zhangjl/.workbuddy/skills/openviking-server-ops`），
   否则 agent 无法转介而自行处理。
5. **双套件并存纪律**：`evals.json` 原件禁止删改（回归基线）；skill-up 套件增补不删改。技能行为契约
   （触发词/边界/输出格式）变更必须在 `reports/optimization-summary.md` 显式登记影响面。

## 7. 证据与豁免记录

- 每次运行的唯一证据锚点：`<skill>-workspace/iteration-N/result.json`（含 `case_results[].status`、
  token 用量）；grading 明细在 `<case>/with_skill/grading.json`。
- 已知豁免（5 项，含原因与影响评估）与逐技能闭环结论：`reports/optimization-summary.md` §3。
- evals.json 回归（原件零改动的转译副本执行）证据：`reports/evidence/evals-json-regression/`。

## 8. 快速自检清单（新会话开场 2 分钟）

```bash
skill-up --version                       # 0.14.0
claude -p "reply with exactly: OK"       # 引擎凭据
for d in <15 技能>; do skill-up validate $d/evals/eval.yaml || echo FAIL:$d; done   # 应 15 行 ✓
python -I <仓库>/rtl-readability/evals/self_check.py   # 应 11/11（该技能自带回归）
```
