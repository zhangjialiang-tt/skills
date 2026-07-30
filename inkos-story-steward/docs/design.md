这个方向是成立的，而且比“只做一个 InkOS 写作 Skill”更完整。

建议把它定义为：

> **面向 InkOS 的故事架构与创作构件维护 Skill：建书前完成高质量故事研发，建书后安全维护 InkOS 的创作控制面。**

它不是一个单纯的提示词，也不是 InkOS Core 的替代品，而是一层：

```text
故事创意研发
→ 构件化设计
→ InkOS 格式编译
→ 建书后持续维护
→ 变更影响分析
→ 安全同步
```

你整理的目录和红黄绿区域已经足以作为这个 Skill 的文件契约基础。

---

# 一、建议的 Skill 定位

可以暂定名称：

```text
inkos-story-steward
```

中文名：

> **InkOS 故事架构与设定管家**

核心目标：

> 帮助作者从模糊创意发展出能够长期连载的世界观、人物系统和剧情架构，并将结果安全映射到 InkOS；在连载过程中继续维护长期设定、分卷规划、人物构件和必要的运行状态变更，同时严格遵守 InkOS 红黄绿编辑边界。

这个 Skill 包含两个主模式。

## 模式 A：建书前创作

```text
模糊想法
→ 作品承诺
→ 世界观建设
→ 人物塑造
→ 故事发动机
→ 主线与副线
→ 爽点体系
→ 伏笔与谜题
→ 分卷规划
→ 剧情压力测试
→ 最终剧情大纲
→ InkOS 建书包
```

## 模式 B：建书后维护

```text
读取 InkOS 项目
→ 识别当前创作阶段
→ 读取已有正文和状态
→ 判断变更影响
→ 修改绿区或通过受控流程修改黄区
→ Git diff
→ InkOS plan / compose / sync
→ 验证修改是否生效
```

---

# 二、建书前不要只输出一份普通大纲

最终虽然要给作者一份剧情大纲，但建议内部生成一组构件，最后再汇总。

推荐输出：

```text
story-design/
├── 00-project-brief.md
├── 01-story-promise.md
├── 02-world-system.md
├── 03-character-system.md
├── 04-conflict-engine.md
├── 05-plot-architecture.md
├── 06-payoff-system.md
├── 07-foreshadowing-and-mystery.md
├── 08-volume-outline.md
├── 09-story-outline.md
├── 10-readiness-review.md
└── inkos/
    ├── book-brief.md
    ├── author_intent.md
    ├── story_frame.md
    ├── volume_map.md
    ├── book_rules.md
    ├── pending_hooks.md
    └── roles/
```

其中真正交付给作者阅读的是：

```text
09-story-outline.md
```

而 `inkos/` 目录是机器交付包。

这样可以避免一个问题：

> 一份适合人阅读的完整剧情大纲，不一定适合直接作为 InkOS 的运行输入。

---

# 三、建书前创作流程应该分阶段

## 阶段 1：创意定界

确认：

- 平台；
- 题材；
- 目标读者；
- 预计字数和章数；
- 主阅读体验；
- 作者明确不接受的方向；
- 开放结局还是确定结局；
- 现实资料和专业素材来源。

这一阶段的产物是：

```text
作品假设
```

例如：

```yaml
platform: 番茄
genre: 末日基地建设
target_readers: 喜欢生存、经营、团队成长的男性读者
core_experience: 看主角用工程和组织能力把混乱变成秩序
target_chapters: 300
chapter_words: 2500
ending_known: true
```

---

## 阶段 2：作品承诺

必须回答：

```text
读者为什么点进来？
读者为什么读完前三章？
读者为什么追到三十章？
这本书和同类型作品有什么区别？
```

输出一句可执行的作品承诺，而不是主题口号。

例如：

> 一个只擅长排查故障的普通工程师，在城市感染爆发后，把临时避难点一步步建设成可运行的新秩序；每次工程成功都会带来更大的政治和伦理代价。

---

## 阶段 3：世界压力系统

不是单纯补全百科，而是建立持续制造剧情的世界系统：

- 世界的底层规则；
- 资源稀缺；
- 权力如何分配；
- 普通人如何生活；
- 规则如何产生冲突；
- 主角有什么可利用之处；
- 主角无法改变什么；
- 每次突破要付出什么代价。

世界观必须同时输出两种形式：

### 创意说明

解释世界为何有趣。

### 可执行规则

例如：

```markdown
## 感染规则

- 感染仅通过体液传播，不通过空气传播。
- 潜伏期为2至72小时，个体差异不可预测。
- 潜伏期内常规观察无法确认感染。
- 症状出现后失智过程不可逆。
- 当前不存在可靠治疗方式。
```

后者才能进入 `book_rules.md`。

---

## 阶段 4：人物系统

不只创建人物卡，还要建立人物之间的冲突网络：

```text
欲望
利益
价值观
能力
缺陷
秘密
关系债务
不可接受的底线
最终弧光
```

重点检查：

- 主角是否会主动制造剧情；
- 对手是否有合理利益；
- 配角是否能独立行动；
- 角色之间是否存在不依赖误会的冲突；
- 删除某角色后，故事是否没有任何变化；
- 角色弧光是否通过选择体现，而非旁白说明。

---

## 阶段 5：故事发动机

这是长篇最关键的一层。

例如基地建设题材的发动机：

```text
基地出现问题
→ 主角提出方案
→ 缺少资源或权限
→ 外出或谈判
→ 遭遇敌对势力
→ 付出代价
→ 带回资源和新关系
→ 基地状态发生改变
→ 新问题被制造
```

Skill 必须验证这个循环能否运行几十次而不完全重复。

---

## 阶段 6：爽点体系

不要只写“每三章一个爽点”，而要为当前作品定义爽点来源。

例如：

| 爽点类型 | 当前作品中的具体表现               |
| -------- | ---------------------------------- |
| 能力爽   | 主角通过系统分析发现别人忽略的故障 |
| 建设爽   | 废弃设施被恢复，基地状态明显改善   |
| 权力爽   | 主角从技术执行者变成规则制定者     |
| 打脸爽   | 反对方案的人不得不承认结果         |
| 资源爽   | 高风险行动带回关键设备             |
| 揭秘爽   | 表面事故被证明是人为破坏           |
| 情感爽   | 团队成员从怀疑转为主动追随         |

每个爽点还要包含：

```text
压抑
→ 期待
→ 行动
→ 兑现
→ 见证
→ 状态变化
→ 后续代价
```

---

## 阶段 7：伏笔和谜题

建立：

- 前台问题；
- 后台真相；
- 读者所知；
- 主角所知；
- 对手所知；
- 错误解释；
- 公平线索；
- 回收条件；
- 回收位置；
- 回收后的意义变化。

最后映射为 InkOS 的 `pending_hooks.md` 初始种子。

---

## 阶段 8：剧情推演

至少进行三类推演：

### 顺推

按照当前计划，故事是否自然发展。

### 逆推

从结局反推必须提前建立什么。

### 对手推演

如果对手不降智，他下一步会怎么做。

还可以使用 InkOS 的 `forecast` 做局部分支推演，但建书前 Skill 应先完成宏观剧情推演。

---

## 阶段 9：最终剧情大纲

最终剧情大纲建议包含：

1. 一句话核心梗；
2. 作品承诺；
3. 主题和基调；
4. 世界运行规则；
5. 主角发动机；
6. 主要人物和关系；
7. 前台故事；
8. 后台故事；
9. 完整结局；
10. 分卷剧情；
11. 关键转折；
12. 爽点体系；
13. 伏笔和回收；
14. 前三十章方向；
15. 长篇可持续性说明。

对于长篇网文，建议不是3000字的简单梗概，而是：

```text
基础版：8000～15000字
复杂作品：15000～30000字
```

但仍应避免逐章写满几百章。

---

# 四、建书时的交付方式

Skill 生成：

```text
story-design/inkos/book-brief.md
```

然后执行：

```bash
inkos book create \
  --title "作品名" \
  --genre <genre> \
  --platform tomato \
  --target-chapters 300 \
  --chapter-words 2500 \
  --brief story-design/inkos/book-brief.md
```

建书后不能直接信任 InkOS 的二次转换结果。

Skill 应进入“建书对齐”步骤：

```text
原始设计包
          ↓ compare
InkOS 自动生成的 story_frame / volume_map / roles / rules / hooks
          ↓
识别遗漏、曲解和降级
          ↓
修正绿区文件
          ↓
输出对齐报告
```

这是整个系统里非常重要的一步。

---

# 五、建书后的绿区维护

绿区是 Skill 的主要工作面：

```text
story/
├── author_intent.md
├── current_focus.md
├── style_guide.md
├── book_rules.md
├── outline/
│   ├── story_frame.md
│   ├── volume_map.md
│   └── 节奏原则.md
└── roles/**
```

InkOS 的规划阶段会重新读取这些长期文件。

Skill 可以提供以下操作。

## `review-foundation`

系统评审当前：

- 世界观；
- 人物；
- 主线；
- 分卷结构；
- 爽点；
- 伏笔；
- 中期重复风险；
- 结局兑现。

只评审，不修改。

## `revise-world`

修改：

```text
story_frame.md
book_rules.md
相关角色卡
必要时 volume_map.md
```

## `revise-character`

修改：

```text
roles/<角色>.md
关系相关角色文件
必要时 current_focus.md
```

## `revise-plot`

修改：

```text
volume_map.md
current_focus.md
必要时 pending_hooks 的设计提案
```

## `prepare-next-arc`

根据当前正文和状态，规划接下来一个小阶段：

```text
未来5～15章目标
主要冲突
爽点
线索
角色变化
不得提前揭示内容
```

主要落到：

```text
current_focus.md
volume_map.md
```

---

# 六、黄区不能作为普通文件直接修改

这是 Skill 设计中的关键分界。

Skill 可以“维护黄区”，但必须通过操作适配器，而不是直接写文件。

## 1. `book.json`

不要直接写。

通过：

```bash
inkos book update \
  --chapter-words 2500 \
  --target-chapters 300
```

Skill 可以生成和执行命令。

---

## 2. `chapters/*.md`

可外部编辑，但必须判断修改类型。

### 纯文风修改

例如：

- 删除重复描述；
- 调整句子；
- 修改错别字；
- 不改变事实和行为结果。

可以直接修改。

通常不需要重建事实状态，但仍建议运行一次审查。

### 改变本章事实

例如：

- 谁拿到了物品；
- 谁知道了秘密；
- 人物关系变化；
- 伏笔被提前揭示；
- 角色受伤情况改变。

修改后必须：

```bash
inkos write sync <chapter>
```

InkOS 的 `write sync` 会根据编辑后的正文重建 truth 文件和 SQLite 索引。

### 修改历史因果

如果修改第10章，而后面已经写到第30章，并且修改会影响后续剧情：

```text
不能只 write sync 10
```

应使用：

```bash
inkos write rewrite 10
```

因为 InkOS 会恢复到前一章快照，并删除目标章及后续章节后重新生成。

---

## 3. `pending_hooks.md`

需要区分生命周期。

### 尚未开始写第一章

如果 `story/state/hooks.json` 尚不存在，可以把 Skill 设计出的初始伏笔写入 `pending_hooks.md`。

### 已进入正式连载

结构化 `hooks.json` 已经是优先读取源，不能只修改 Markdown。InkOS 的检索逻辑会优先使用结构化伏笔状态。

此时 Skill 应：

- 输出伏笔变更提案；
- 将近期推进要求写入 `current_focus.md`；
- 通过下一章正文完成推进；
- 让 InkOS 正常结算；
- 或修改正文后执行 `write sync`。

v0.1 不建议直接改 `hooks.json`。

---

## 4. `current_state.md`

连载后不直接维护。

因为 `state/current_state.json` 存在时会优先使用结构化状态，后改 Markdown 可能无效。

正确路径是：

```text
修改正文事实
→ write sync
```

或：

```text
让下一章发生预期变化
→ InkOS 自动结算
```

---

## 5. `emotional_arcs.md`

不应直接作为长期人工维护面，因为 Writer 每章可能全量覆盖。

Skill 应修改：

```text
roles/**
volume_map.md
current_focus.md
```

定义人物关系和情绪方向，然后让 InkOS 在章节结算时更新情感状态。

---

# 七、建议建立黄区操作矩阵

| 目标           | Skill 操作                                    | 禁止行为                          |
| -------------- | --------------------------------------------- | --------------------------------- |
| 修改目标章数   | 调用 `inkos book update`                      | 直接写 `book.json`                |
| 修改最新章措辞 | 编辑正文，审查                                | 修改索引                          |
| 修改最新章事实 | 编辑正文 + `write sync`                       | 只改正文不结算                    |
| 修改历史因果   | `write rewrite`                               | 手改历史章并保留后续              |
| 新增长期伏笔   | 写入 `volume_map/current_focus`，通过剧情落地 | 活跃连载时只改 `pending_hooks.md` |
| 修改当前状态   | 通过正文变化 + sync                           | 直接改 `state/current_state.json` |
| 修改情感方向   | 修改角色卡和焦点                              | 把 `emotional_arcs.md` 当权威     |
| 修复状态异常   | `write repair-state`                          | 手改 manifest                     |

---

# 八、Skill 内部要有变更影响分析

每次建书后修改前，必须回答：

```text
这是未来设计变更，还是追溯修改？
是否与已经发布的正文矛盾？
会影响哪些角色？
会影响哪些伏笔？
会影响哪些卷？
需要修改正文吗？
需要 sync 还是 rewrite？
```

建议输出固定格式：

```yaml
change_id: CHANGE-014
change_type: future_design
target:
  - story/outline/volume_map.md
  - story/current_focus.md

affected_chapters:
  written: none
  future: 42-58

affected_characters:
  - 林远
  - 何卫国

affected_hooks:
  - H007
  - H012

runtime_action:
  plan_required: true
  compose_required: true
  sync_required: false
  rewrite_required: false

risk:
  level: medium
  reason: 改变第二卷对手身份，但尚未在正文中揭示
```

---

# 九、建议的 Skill 文件结构

```text
inkos-story-steward/
├── SKILL.md
├── references/
│   ├── prebuild-workflow.md
│   ├── story-promise.md
│   ├── worldbuilding.md
│   ├── character-design.md
│   ├── conflict-engine.md
│   ├── plot-architecture.md
│   ├── payoff-design.md
│   ├── foreshadowing-and-mystery.md
│   ├── outline-review.md
│   ├── inkos-file-contract.md
│   ├── green-zone-editing.md
│   ├── yellow-zone-operations.md
│   └── change-impact-analysis.md
├── templates/
│   ├── project-brief.md
│   ├── story-outline.md
│   ├── world-rules.md
│   ├── character-card.md
│   ├── hook-ledger.md
│   ├── inkos-brief.md
│   ├── integration-report.md
│   └── change-report.md
├── scripts/
│   ├── detect_inkos_project.py
│   ├── classify_edit_zone.py
│   ├── validate_inkos_layout.py
│   ├── inspect_story_diff.py
│   └── verify_runtime_context.py
└── evals/
    ├── prebuild-case/
    ├── green-edit-case/
    ├── chapter-sync-case/
    └── forbidden-red-edit-case/
```

---

# 十、`SKILL.md` 应保持轻量

主文件只负责：

- 判断当前模式；
- 路由到对应流程；
- 执行红黄绿保护；
- 决定需要读取哪些 reference；
- 定义必须输出的报告；
- 决定是否可以直接写文件。

不要把全部网文理论塞进去。

核心路由可以是：

```text
未发现 InkOS 项目
→ PREBUILD

发现 InkOS 项目但没有章节
→ FOUNDATION_ALIGNMENT

存在章节
→ ACTIVE_MAINTENANCE

请求修改正文
→ CHAPTER_EDIT

请求修改黄区状态
→ YELLOW_ZONE_OPERATION

检测到红区写入请求
→ 拒绝并给出替代路径
```

---

# 十一、建议的 v0.1 边界

第一版不要覆盖全部能力。

## v0.1 应实现

### 建书前

- 需求对齐；
- 世界观；
- 人物；
- 故事发动机；
- 主线；
- 分卷；
- 爽点；
- 伏笔；
- 完整剧情大纲；
- InkOS Brief；
- 建书后对齐。

### 建书后

- 读取项目；
- 识别红黄绿；
- 评审绿区；
- 修改绿区；
- 修改最新正文；
- 自动决定是否 `write sync`；
- 输出影响分析；
- 运行 `plan`、`compose` 并验证输入；
- 禁止红区写入。

## v0.1 暂不实现

- 直接修改 `state/*.json`；
- 直接维护 SQLite；
- 自动修改历史大量章节；
- 自动重排几十章正文；
- 自动接受 InkOS 审核；
- 无人值守连续写作；
- 自动根据平台数据重构故事。

这会把第一版控制在可验证范围内。

---

# 十二、这个 Skill 最重要的三条不变量

## 不变量 1

> 建书前设计产物必须经过作者确认，才能进入 InkOS 正式构件。

## 不变量 2

> 建书后所有写入都必须先识别红黄绿区域。

## 不变量 3

> 黄区修改必须通过对应的 InkOS 状态同步机制，不能只追求磁盘文件看起来已经改变。

---

# 最终判断

这个 Skill 的定位已经足够清晰，可以进入正式规划。

它不是：

```text
一个帮助 InkOS 写得更好的提示词
```

而是：

```text
建书前的创意研发系统
+
建书后的故事控制面维护器
+
InkOS 文件安全适配器
```

最合理的实现顺序是：

```text
1. 冻结产品边界和红黄绿契约
2. 定义建书前构件和最终剧情大纲格式
3. 定义建书后变更类型及同步矩阵
4. 编写最小 SKILL.md 路由
5. 实现区域检测和只读诊断脚本
6. 实现绿区编辑
7. 接入正文修改 + write sync
8. 建立真实 InkOS 项目 E2E 测试
```

其中最关键的设计决策是：

> **“修改黄区”应被实现为受控业务操作，而不是开放文件写权限。**
