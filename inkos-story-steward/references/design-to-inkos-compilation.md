# 创意设计到 InkOS 构件编译

> 本文件定义 `story-design/` 到 `story-design/inkos/` 的唯一编译 seam。
> 在 PREBUILD 阶段 10-11 和 FOUNDATION_ALIGNMENT 编译损失检查时加载。

## 编译不变量

1. 每项已确认设计必须映射到至少一个 InkOS 构件，或在 Readiness 中标记为“仅设计层保留”并说明原因。
2. 编译只转换表达形式，不得补造源设计中不存在的事实、规则、角色关系或伏笔。
3. InkOS 构件只保存生产所需的最小信息；完整推演和判断依据继续保留在 `story-design/00-10`。
4. `book_rules.md` 只接收可执行的“条件 → 结果”规则，百科描述不得伪装成规则。
5. 编译完成不等于 InkOS 二次转换无损；建书后必须通过 FOUNDATION_ALIGNMENT 复核。

## 唯一映射表

| 设计源 | InkOS 构件 | 必须保留 |
|--------|------------|----------|
| `00-project-brief.md`、`01-story-promise.md` | `book-brief.md`、`author_intent.md` | 题材、目标读者、作品承诺、冻结方向、禁止方向 |
| `02-world-system.md`、`04-conflict-engine.md` | `story_frame.md`、`book_rules.md` | 世界压力、硬规则、代价、核心冲突和升级路径 |
| `03-character-system.md`、`04-conflict-engine.md` | `roles/**` | 欲望、利益、价值观、能力边界、关系债务、秘密、知识边界和独立目标 |
| `05-plot-architecture.md`、`08-volume-outline.md`、`09-story-outline.md` | `story_frame.md`、`volume_map.md` | 故事发动机、卷间因果、不可逆状态变化、关键转折和结局前置条件 |
| `06-payoff-system.md` | `volume_map.md` | 各卷的期待、兑现类型、见证、状态变化、升级和下一轮期待 |
| `07-foreshadowing-and-mystery.md` | `pending_hooks.md`、`book_rules.md` | 前台问题、预期回收、公平线索、回收条件、信息边界；完整误导与知识矩阵留在设计层 |
| `10-readiness-review.md` | 不直接生成运行构件 | 编译覆盖、仅设计层保留项、冲突和损失结论 |

## 编译步骤

1. 从 `00-10` 提取作者已确认的设计决定，建立逐项清单。
2. 按唯一映射表写入目标构件，不跨过映射关系随意分发。
3. 对每项记录：源位置、目标位置、保留方式、是否压缩、压缩理由。
4. 对无法进入 InkOS 格式的完整推演标记“仅设计层保留”，并确认生产所需的最小约束已经进入构件。
5. 反向读取编译包，逐项回答“仅看 InkOS 构件，生产流程是否仍能遵守该决定”。
6. 将缺失、冲突或新增事实写入 `10-readiness-review.md`；存在阻塞项时不得建书。

## 编译覆盖记录

```markdown
| 设计决定 | 设计源 | InkOS 目标 | 保留方式 | 结论 |
|----------|--------|------------|----------|------|
| ... | 02-world-system.md | book_rules.md | 条件 → 结果 | mapped |
| ... | 07-foreshadowing-and-mystery.md | 仅设计层 | 完整知识矩阵 | design-only |
```

`结论` 只能是：

- `mapped`：生产所需信息已进入 InkOS 构件；
- `design-only`：完整信息留在设计层，原因已记录，且生产最小约束已映射；
- `blocked`：存在丢失、冲突或无来源新增事实，禁止进入建书。

## FOUNDATION_ALIGNMENT 复核

建书后将精确编译包与 InkOS 生成文件逐项反向比对：

- `mapped` 项在 InkOS 文件中缺失或含义变化 → 对齐失败；
- `design-only` 项被 InkOS 擅自扩写成新事实 → 对齐失败；
- InkOS 文件出现无法追溯到设计源的规则、关系或伏笔 → 对齐失败。

修正仍受红黄绿分区、写锁、版本预检和 `verify_diff.py` 约束。
