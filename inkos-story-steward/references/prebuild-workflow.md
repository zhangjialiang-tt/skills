# 建书前创作流程（PREBUILD 模式）

> 本文件在 PREBUILD 模式下加载。定义从模糊创意到 InkOS 建书包的 11 阶段创作流程。

---

## 总体原则

- 不要只输出一份普通大纲。内部生成一组构件，最后再汇总。
- 暂定方案优先，只追问方向性问题。
- 每轮只提出一个最关键的问题。
- 不是每阶段都需要确认。只在 4 个关键 Gate 处要求作者明确确认（见下方）。
- Coach 只作为阶段性质量 Reviewer，不改变正式构件，也不替代作者确认。

## 确认门（Gate）

只在以下 4 个节点要求作者明确确认后才继续：

| Gate | 位置 | 确认内容 |
|------|------|----------|
| Gate 1 | 阶段 2 完成后 | 作品承诺是否准确 |
| Gate 2 | 阶段 4 完成后 | 主角、核心冲突、结局方向 |
| Gate 3 | 阶段 8 完成后 | 情节结构、爽点、伏笔和分卷架构 |
| Gate 4 | 阶段 10 完成后 | 最终大纲 + InkOS 导入 |

其他阶段采用"先生成暂定方案，只有方向性分歧才追问"。

---

## 产物目录结构

```
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

真正交付给作者阅读的是 `09-story-outline.md`。
`inkos/` 目录是机器交付包：`book-brief.md` 用于 `inkos book create --brief`，其余文件用于建书后对齐时的精确比对基准。

---

## 阶段 1：创意定界

### 输入
用户提供的模糊创意（一句话灵感、角色设定、场景片段等）。

### 确认项
- 平台（番茄/起点/其他）
- 题材
- 目标读者
- 预计字数和章数
- 主阅读体验
- 作者明确不接受的方向
- 开放结局还是确定结局
- 现实资料和专业素材来源

### 产物
`story-design/00-project-brief.md`（YAML 格式作品假设）

使用模板：`templates/project-brief.md`

### 质量检查
- 核心体验是否可用一句话描述
- 目标章数是否与题材匹配
- 是否存在作者明确禁止的方向

---

## 阶段 2：作品承诺 【Gate 1】

### 输入
阶段 1 的作品假设。

### 必须回答
1. 读者为什么点进来？
2. 读者为什么读完前三章？
3. 读者为什么追到三十章？
4. 这本书和同类型作品有什么区别？

### 产物
`story-design/01-story-promise.md`

输出一句可执行的作品承诺，而不是主题口号。

### 质量检查
- 承诺是否具体可执行（不是"写一个好看的故事"）
- 是否回答了"为什么追到三十章"
- 差异化是否真实存在

### Gate 1 Coach 评审

阶段 2 完成后，以只读方式提交：

```yaml
review_id: REVIEW-YYYYMMDD-001
stage: story_promise
artifact_refs:
  - story-design/00-project-brief.md
  - story-design/01-story-promise.md
review_focus:
  - 一句话核心梗
  - 点击理由
  - 前三章承诺
frozen_decisions: []
open_questions: []
permissions:
  read_only: true
  file_write: false
```

作者确认作品承诺，或明确接受 Coach 记录的风险后，才进入阶段 3。

---

## 阶段 3：世界压力系统

### 输入
作品承诺 + 题材。

### 建设内容
不是单纯补全百科，而是建立持续制造剧情的世界系统：

- 世界的底层规则
- 资源稀缺
- 权力如何分配
- 普通人如何生活
- 规则如何产生冲突
- 主角有什么可利用之处
- 主角无法改变什么
- 每次突破要付出什么代价

### 产物
`story-design/02-world-system.md`

世界观必须同时输出两种形式：

**创意说明**：解释世界为何有趣。

**可执行规则**：例如：

```markdown
## 感染规则
- 感染仅通过体液传播，不通过空气传播。
- 潜伏期为2至72小时，个体差异不可预测。
- 潜伏期内常规观察无法确认感染。
- 症状出现后失智过程不可逆。
- 当前不存在可靠治疗方式。
```

后者才能进入 `book_rules.md`。

### 质量检查
- 规则是否自洽
- 是否制造了持续冲突（而非静态百科）
- 主角是否有可利用但不能滥用的空间
- 代价是否真实

---

## 阶段 4：人物系统 【Gate 2】

### 输入
世界压力系统 + 作品承诺。

### 建设内容
不只创建人物卡，还要建立人物之间的冲突网络。每个角色包含：

- 欲望
- 利益
- 价值观
- 能力
- 缺陷
- 秘密
- 关系债务
- 不可接受的底线
- 最终弧光

使用模板：`templates/character-card.md`

### 重点检查
- 主角是否会主动制造剧情
- 对手是否有合理利益
- 配角是否能独立行动
- 角色之间是否存在不依赖误会的冲突
- 删除某角色后，故事是否没有任何变化
- 角色弧光是否通过选择体现，而非旁白说明

### 产物
`story-design/03-character-system.md`

### Gate 2 确认内容
- 主角设定是否准确
- 核心冲突是否成立
- 结局方向是否可接受

### Gate 2 Coach 评审

阶段 4 完成后，以只读方式提交：

```yaml
review_id: REVIEW-YYYYMMDD-002
stage: world_character
artifact_refs:
  - story-design/02-world-system.md
  - story-design/03-character-system.md
  - story-design/04-conflict-engine.md
review_focus:
  - 世界规则是否持续制造压力
  - 主角是否主动制造剧情
  - 对手是否有合理利益
  - 配角和冲突网络是否独立运行
frozen_decisions: []
open_questions: []
permissions:
  read_only: true
  file_write: false
```

作者确认主角、核心冲突和结局方向，或明确接受 Coach 记录的风险后，才进入阶段 5。

---

## 阶段 5：故事发动机与核心冲突

### 输入
人物系统 + 世界压力系统。

### 建设内容
这是长篇最关键的一层。定义一个可以反复运行的剧情循环。

示例（基地建设题材）：

```
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

同时明确核心冲突的升级路径：
- 第一层冲突（生存/立足）
- 第二层冲突（权力/资源争夺）
- 第三层冲突（价值观/制度对抗）
- 最终冲突（核心命题的正面回答）

### 验证
必须验证这个循环能否运行几十次而不完全重复。检查：
- 每次循环的输入是否不同
- 代价是否递增
- 关系是否累积变化
- 世界状态是否不可逆

### 产物
`story-design/04-conflict-engine.md`

---

## 阶段 6：情节架构、结局与分卷

### 输入
故事发动机 + 人物系统 + 世界压力系统。

### 建设内容

#### 情节架构
- 前台故事线（读者看到的主线推进）
- 后台故事线（读者前期不能知道的真相线）
- 完整结局（外在目标 + 内在变化 + 代价 + 命题回答）
- 关键转折（至少 3 个，每个改变至少一项：对真相的理解/目标/敌我关系/冲突规模/成败代价）

#### 分卷规划
- 每卷的核心冲突
- 每卷结束时的状态变化
- 卷间升级关系
- 节奏原则（张弛、爽点密度、信息释放节奏）

### 产物
- `story-design/05-plot-architecture.md`（情节架构 + 结局 + 转折）
- `story-design/08-volume-outline.md`（分卷规划）

### 阶段性确认内容
- 故事发动机是否可持续
- 分卷架构是否合理
- 结局方向是否确认

---

## 阶段 7：爽点体系

### 输入
故事发动机 + 分卷规划 + 目标读者。

### 建设内容
不要只写"每三章一个爽点"，而要为当前作品定义爽点来源。

| 爽点类型 | 当前作品中的具体表现 |
|----------|---------------------|
| 能力爽 | （根据作品填写） |
| 建设爽 | （根据作品填写） |
| 权力爽 | （根据作品填写） |
| 打脸爽 | （根据作品填写） |
| 资源爽 | （根据作品填写） |
| 揭秘爽 | （根据作品填写） |
| 情感爽 | （根据作品填写） |

每个爽点还要包含完整节奏：

```
压抑 → 期待 → 行动 → 兑现 → 见证 → 状态变化 → 后续代价
```

为每卷标注爽点分布密度和类型轮换。

### 产物
`story-design/06-payoff-system.md`

---

## 阶段 8：伏笔、谜题与剧情推演

### 输入
故事发动机 + 人物系统 + 分卷规划 + 情节架构。

### 建设内容

#### 伏笔与谜题
每个伏笔/谜题包含：

- 前台问题
- 后台真相
- 读者所知
- 主角所知
- 对手所知
- 错误解释
- 公平线索
- 回收条件
- 回收位置（必须引用分卷规划中的具体卷/章范围）
- 回收后的意义变化

#### 剧情推演

**顺推**：按照当前计划，故事是否自然发展。

**逆推**：从结局反推必须提前建立什么。

**对手推演**：如果对手不降智，他下一步会怎么做。

还可以使用 InkOS 的 `forecast` 做局部分支推演，但建书前应先完成宏观剧情推演。

### 产物
`story-design/07-foreshadowing-and-mystery.md`

最终映射为 InkOS 的 `pending_hooks.md` 初始种子。

---

## Gate 3：情节结构质量评审

阶段 8 完成后，Steward 将以下产物以只读方式提交给 `novel-coach` 的
`DELEGATED_REVIEW`：

```yaml
review_id: REVIEW-YYYYMMDD-003
stage: plot_structure
artifact_refs:
  - story-design/05-plot-architecture.md
  - story-design/06-payoff-system.md
  - story-design/07-foreshadowing-and-mystery.md
  - story-design/08-volume-outline.md
review_focus:
  - 结局前置条件
  - 爽点和节奏
  - 伏笔公平线索与回收
  - 对手推演
frozen_decisions: []
open_questions: []
permissions:
  read_only: true
  file_write: false
```

Coach 重点检查：结局是否能反推前置条件、第一卷是否兑现作品承诺、爽点是否有铺垫和兑现、
伏笔是否有公平线索、对手是否会降智以及中期是否会重复。Coach 只返回
`CoachReviewResult`；作者确认后才进入阶段 9。

---

## 阶段 9：最终剧情大纲

### 输入
前 8 阶段全部产物。

### 大纲结构（15 项）

1. 一句话核心梗
2. 作品承诺
3. 主题和基调
4. 世界运行规则
5. 主角发动机
6. 主要人物和关系
7. 前台故事
8. 后台故事
9. 完整结局
10. 分卷剧情
11. 关键转折
12. 爽点体系
13. 伏笔和回收
14. 前三十章方向
15. 长篇可持续性说明

### 篇幅建议

- 基础版：8000～15000 字
- 复杂作品：15000～30000 字

避免逐章写满几百章。

使用模板：`templates/story-outline.md`

### 产物
`story-design/09-story-outline.md`

---

## 阶段 10：Readiness Review 【Gate 4】

### 输入
全部前 9 阶段产物。

### 检查维度

- [ ] 作品承诺是否可执行
- [ ] 世界规则是否自洽且可执行
- [ ] 主角发动机能否运行 50+ 次不重复
- [ ] 核心冲突升级路径是否清晰
- [ ] 分卷之间是否有不可逆的状态变化
- [ ] 爽点分布是否均匀
- [ ] 伏笔回收位置是否在分卷规划中有对应
- [ ] 结局是否回应核心命题
- [ ] 前三十章方向是否足够具体
- [ ] 是否存在作者禁止的方向被无意引入
- [ ] 长篇可持续性是否有结构性保障

### 产物
`story-design/10-readiness-review.md`

格式：
```markdown
# Readiness Review

## 通过项
- ...

## 风险项（需作者确认）
- ...

## 阻塞项（必须修复才能建书）
- ...

## 结论
- [ ] 可以进入 InkOS 编译
- [ ] 需要回退修复（指明回退到哪个阶段）
```

### Gate 4 Coach 评审

在确认进入 InkOS 编译前，提交以下只读评审请求：

```yaml
review_id: REVIEW-YYYYMMDD-004
stage: final_outline
artifact_refs:
  - story-design/09-story-outline.md
  - story-design/10-readiness-review.md
review_focus:
  - 最终大纲可执行性
  - 前三章和第一卷承诺
  - 长篇可持续性
frozen_decisions: []
open_questions: []
permissions:
  read_only: true
  file_write: false
```

只有 `CoachReviewResult.verdict` 为 `pass`，或作者明确接受 `revise` / `block` 中的风险，且
`10-readiness-review.md` 已记录结论，才允许进入阶段 11。Coach 的建议不直接修改大纲；如需
修订，回退到对应阶段重新生成产物。

---

## 阶段 11：InkOS 编译包

### 输入
Readiness Review 通过后的全部产物。

### 编译内容

生成 InkOS 建书包（机器交付包）：

```
story-design/inkos/
├── book-brief.md          # 用于 --brief 参数
├── author_intent.md       # 作者意图精确版
├── story_frame.md         # 世界观精确版
├── volume_map.md          # 分卷规划精确版
├── book_rules.md          # 可执行规则精确版
├── pending_hooks.md       # 初始伏笔种子
└── roles/                 # 角色卡（InkOS 原生格式）
    ├── 主要角色/<角色名>.md
    └── 次要角色/<角色名>.md
```

使用模板：
- `templates/inkos-brief.md`（book-brief.md）
- `templates/inkos/story-frame.md`
- `templates/inkos/volume-map.md`
- `templates/inkos/role-card.md`
- `templates/inkos/book-rules.md`
- `templates/inkos/pending-hooks.md`

### 建书命令

```bash
inkos book create \
  --title "作品名" \
  --genre <genre> \
  --platform tomato \
  --target-chapters 300 \
  --chapter-words 2500 \
  --brief story-design/inkos/book-brief.md
```

### 编译前确认

- Gate 4 已通过，或作者已明确接受记录在 `10-readiness-review.md` 中的风险。
- 最终大纲已定稿。
- 编译包准确反映设计意图。
- 作者确认执行建书命令。

### 建书后

建书后不能直接信任 InkOS 的二次转换结果。应提示用户进入 FOUNDATION_ALIGNMENT 模式，使用精确编译包（而非仅 brief）进行对齐比对。
