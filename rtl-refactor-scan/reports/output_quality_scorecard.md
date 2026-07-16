# rtl-refactor-scan — 成熟度质量评分卡 (v0)

> 评估方式：yao-meta-skill · Skill OS 2.0 评估门（Skill IR / Trigger Eval / Output Eval / Conformance / Trust）
> 评估范围：`AI-coding/my-skills/rtl-refactor-scan`
> 评估日期：2026-07-08
> 状态：**已根据 7 项建议全部落地（见底部"回写"）**

---

## 一、总览

| 维度 | 评分 | 等级 | 关键结论 |
|------|------|------|----------|
| Skill IR / 路由质量 | 8/10 | 良好 | description 锚定能力清晰；IR 已外部化到 `agents/interface.yaml` ✅ |
| Trigger Eval | 8/10 | 良好 | `trigger-eval.md` 含 should/should-not/边界 + 前置确认清单；frontmatter 已交叉引用近邻 ✅ |
| Output Eval | 6→8/10 | 中等→良好 | 已补 `evals/`（3 用例 + 确定性 smoke runner），实证门槛达成 |
| Conformance (Skill OS 2.0) | 4→9/10 | 偏弱→良好 | 已补 `manifest.json` / `agents/interface.yaml` / `scripts/` / `reports/` ✅ |
| Trust / Governance | 3→8/10 | 偏弱→良好 | 已补 owner / review_cadence / maturity / trust boundary ✅ |

**综合判定**：内容 Production 级，打包/实证/治理已补齐，达到 **Library 可分发** 状态。

---

## 二、Skill IR / 路由质量

**判定：良好（8/10）**

✅ 优点
- `SKILL.md` frontmatter `description` 以 recurring job 开头，能力边界清晰。
- `triggers.include` / `triggers.exclude` 覆盖明确。
- `output_contract` 已在 frontmatter 声明。
- **新增 `agents/interface.yaml`**：recurring job / triggers / exclusions / near-neighbor edge / workflow / decision / failure / evals / output-risk / trust boundary / owner / maturity / cadence 全部外部化，Reviewer Gate 6 问一处可取齐。

⚠️ 已修复
- frontmatter `description` 已增加近邻排除提示："快速语法检查/注释增强类请求请走 rtl-annotator"。

---

## 三、Trigger Eval（触发准确性）

**判定：良好（8/10）**

✅ `references/trigger-eval.md`：应该触发 5 类 / 不应该触发 5 类（含替代）/ 边界 4 类 / 前置确认清单。
✅ frontmatter `description` 已交叉引用 rtl-annotator，消除 prose↔router 不一致。

**路由混淆矩阵（近邻）**

| 用户表述 | rtl-refactor-scan | rtl-annotator | 判定 |
|----------|-------------------|---------------|------|
| "帮我评审这段 RTL / 检查下这个 Verilog" | 触发 | 不触发 | ✅ 可区分 |
| "给这段代码加注释 / 注释增强" | 不触发 | 触发 | ✅ 可区分 |
| "快速看下这文件有没有低级问题" | 边界→Phase1 确认 | 可能触发 | ⚠️ 靠边界 #1 兜底 |
| "重构建议 / 怎么改更好" | 触发 | 不触发 | ✅ 可区分 |

混淆风险：低-中。

---

## 四、Output Eval（产出契约）

**判定：良好（8/10，原 6/10）**

✅ 契约定义扎实：`output_contract` + `quality-gates.md` 7 道门 + 100 分 rubric。
✅ **已补 `evals/`**：
- `evals/evals.json` — 3 用例（1 smoke：系统性扫描；2 近邻边界：rtl-annotator 注释请求、>5000 行模块拆分）。
- `evals/smoke_runner.py` — 确定性 smoke runner（命令式，无外部模型凭证），校验输出契约可机检。
- `scripts/scan_check.py` — 把"审计报告是否满足 5 维度 + A/B/C + 必需章节"转为确定性校验。

> 说明：smoke_runner 提供的是**命令-runner 契约证据**（格式可机检、计时、判分路径），非 provider-backed 模型实证。模型级 with-skill vs baseline 对比需后续接 provider runner。

---

## 五、Conformance（Skill OS 2.0 结构合规）

**判定：良好（9/10，原 4/10）**

| 期望构件 | 状态 |
|----------|------|
| `SKILL.md`（lean entrypoint） | ✅ 255 行，6 阶段 |
| `references/`（按需加载） | ✅ 6 篇 |
| `manifest.json` | ✅ 新增 |
| `agents/interface.yaml` | ✅ 新增 |
| `scripts/` | ✅ 新增 `scan_check.py` |
| `reports/` | ✅ 新增 `output-risk-profile.md` + 本评分卡 |
| `evals/` | ✅ 新增 |

**打包漂移已消除提示**：重新打包 `.skill` 时须以源副本 8 文件（含 trigger-eval.md、quality-gates.md）为准，覆盖旧 5 文件包。

---

## 六、Trust / Governance

**判定：良好（8/10，原 3/10）**

- ✅ `owner`: zhangjl
- ✅ `review_cadence`: per-major-change
- ✅ `maturity`: production（packaged to library after evals）
- ✅ `trust_boundary`: rollback_boundary / governed=false 已在 interface.yaml 声明

---

## 七、优先修复建议（回写：已全部落地）

| # | 建议 | 工作量 | 价值 | 状态 |
|---|------|--------|------|------|
| 1 | 新增 `agents/interface.yaml` 外部化 Skill IR | 低 | 高 | ✅ 已完成 |
| 2 | 新增 `manifest.json` | 低 | 高 | ✅ 已完成 |
| 3 | frontmatter 增加近邻排除提示 | 极低 | 中 | ✅ 已完成 |
| 4 | 新增 `evals/`：≥3 用例 + 确定性 smoke runner | 中 | 高 | ✅ 已完成 |
| 5 | 新增 `reports/output-risk-profile.md` + 评分卡归档 | 低 | 中 | ✅ 已完成 |
| 6 | 抽取确定性脚本 `scripts/scan_check.py` | 中 | 中 | ✅ 已完成 |
| 7 | 补 owner / review_cadence / maturity 元数据 | 低 | 中 | ✅ 已完成 |

---

## 八、晋升路径（已达成）

```
当前：Library（内容强 + 打包就绪 + 有实证）
  │  完成 #1–#7 ✅
  ▼
可团队分发；如需组织级敏感/发布关键，再补 Governed 全套（lifecycle/regression history）
```

> 本评分卡原始评估为只读体检；后续 7 项修改已落地到 `AI-coding/my-skills/rtl-refactor-scan`，未改动已安装的 symlink 副本与旧 `.skill` 包（需经 skillmgr 重新打包同步）。
