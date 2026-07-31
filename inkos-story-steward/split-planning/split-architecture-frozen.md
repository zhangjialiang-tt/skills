# Skill 拆分架构冻结文档

> 基线 commit: e0d6736 (feature/novel-master)
> 冻结日期: 2026-07-30
> 状态: FROZEN — 本文档定义的架构边界在 Phase 1-7 实施期间不得静默修改

---

## 一、拆分动机

`inkos-story-steward` 同时承担三种性质不同的工作：
1. 创意生产（从模糊创意到完整设计）
2. 格式编译（设计到 InkOS 机器包）
3. 生产项目治理（建书后安全维护）

这三者具有相反的行为原则（探索 vs fail-closed）、不同的写入权限和不同的失败模型。

---

## 二、目标架构

```
story-synopsis          → 完整、媒介无关的故事梗概
webnovel-serial-designer → 长篇网文连载设计包
inkos-brief-compiler    → InkOS 建书机器包
inkos-project-steward   → 建书对齐与持续维护
novel-coach             → 只读质量评审（本轮不改）
```

### 主链

```
创意碎片
  → story-synopsis → StorySynopsisPackage
  → webnovel-serial-designer → SerialDesignPackage
  → inkos-brief-compiler → InkOSBuildPackage
  → inkos book create
  → inkos-project-steward → 持续维护
```

### 废弃路径

`novel-master/` 及其子 skill（story-architect、chapter-writer 等）不属于当前生产链，仅保留为架构参考。

---

## 三、职责矩阵

| 能力 | story-synopsis | serial-designer | brief-compiler | project-steward | novel-coach |
|------|:-:|:-:|:-:|:-:|:-:|
| 模糊创意发展 | Owner | 禁止 | 禁止 | 禁止 | Reviewer |
| 完整故事梗概 | Owner | 只读输入 | 只读 | 禁止 | Reviewer |
| 连载发动机/分卷/爽点 | 禁止 | Owner | 只读映射 | 后续维护 | Reviewer |
| 作者 Gate | 拥有定稿确认 | Gate A + B | 验证 frozen | 读取 | 提供评审 |
| 生成 book-brief.md | 禁止 | 禁止 | Owner | 只读 | 禁止 |
| InkOS 格式映射 | 禁止 | 禁止 | Owner | 验证 | 禁止 |
| FOUNDATION_ALIGNMENT | 禁止 | 禁止 | 提供基线 | Owner | 质量复核 |
| 绿黄红区 | 不关心 | 不关心 | 不关心 | Owner | 不关心 |
| sync/rewrite | 禁止 | 禁止 | 禁止 | Owner | 只读建议 |

---

## 四、包结构

```
story-design/<design-id>/
├── manifest.yaml                    # 包级身份（不含阶段状态）
├── source/
│   ├── synopsis.md                  # story-synopsis 拥有
│   └── synopsis-contract.yaml       # story-synopsis 拥有
├── serial/
│   ├── serial-contract.yaml         # serial-designer 拥有
│   ├── design/                      # serial-designer 拥有
│   │   ├── 00-serialization-brief.md
│   │   ├── 01-serial-promise.md
│   │   ├── 02-story-engine.md
│   │   ├── 03-character-serialization.md
│   │   ├── 04-world-pressure-system.md
│   │   ├── 05-volume-architecture.md
│   │   ├── 06-payoff-and-rhythm.md
│   │   ├── 07-mystery-and-information.md
│   │   ├── 08-launch-plan.md
│   │   ├── 09-endgame-convergence.md
│   │   └── 10-readiness-review.md
│   └── reviews/
│       ├── gate-a-architecture.yaml
│       ├── readiness-review.yaml
│       └── gate-b-freeze.yaml
└── compile/
    └── inkos/                       # brief-compiler 拥有
        ├── book-brief.md
        ├── author_intent.md
        ├── story_frame.md
        ├── volume_map.md
        ├── book_rules.md
        ├── pending_hooks.md
        ├── roles/
        ├── mapping-plan.yaml
        └── compilation-report.yaml
```

---

## 五、design-id 规则

1. 从作品标题派生
2. 去除 Windows 非法路径字符（\ / : * ? " < > |）
3. 去除尾部句点和空格
4. 内部空白折叠为连字符
5. 空结果回退到 `untitled-story`
6. 中文保留
7. 同名冲突不静默覆盖

---

## 六、模式路由（inkos-project-steward）

| 模式 | 条件 |
|------|------|
| PREBUILD_STANDALONE | 无 inkos.json |
| PREBUILD_IN_PROJECT | inkos.json 存在，目标书不存在或未绑定 |
| FOUNDATION_ALIGNMENT | manifest 绑定 book_id，书存在，无章节 |
| ACTIVE_MAINTENANCE | manifest 绑定，书存在，有章节 |
| AMBIGUOUS_BINDING | 多 manifest 绑同一 book / book 不存在 / 多书无指定 |

---

## 七、实施顺序（绞杀者迁移）

```
Phase 0: 冻结基线 + 三份文档（本文档）
Phase 1: 冻结三个包契约
Phase 2: 增强 story-synopsis（输出 StorySynopsisPackage）
Phase 3: 新建 webnovel-serial-designer
Phase 4: 新建 inkos-brief-compiler
Phase 5: 新旧链路影子验证
Phase 6: 提取 inkos-project-steward
Phase 7: 旧 inkos-story-steward 退化为兼容入口/归档
```

---

## 八、Serial Designer 交互模型

- 2 个固定 Gate：A（连载架构）+ B（冻结确认）
- 5 类事件触发升级（修改上游/体量不可行/多种宏观架构/改变 Gate A/阻塞性风险）
- 4 级决策权限：L0 执行细节 / L1 局部设计 / L2 宏观架构 / L3 上游事实
- Readiness Review 由 designer 自身完成，Coach 为可选外部评审

---

## 九、编译模型

三层所有权：
- serial designer：定义 assertion 语义（id/type/statement/status/importance/source_ref/invariants）
- compiler policy：静态类型策略表（requirement/compression/omission/default_targets）
- 作者：只审批编译异常

Compiler 定位：受约束的语义编译器——理解语义但无创意决策权。

---

## 十、不变量

1. 建书前设计包不写 `books/<book-id>/`
2. 设计包按 design-id 隔离，多书互不覆盖
3. 绑定优先于猜测（manifest 显式 bookId）
4. 建书失败不推进生命周期
5. EPERM staging rename 是 InkOS/Windows 问题，不是 brief 路径问题
6. 只有 confirmed assertion 进入正式编译
7. Compiler 不创造、不修改、不补完设计事实
8. diagnostic 模式成功不等于 completion_proof
