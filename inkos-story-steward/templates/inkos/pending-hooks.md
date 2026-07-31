# InkOS 原生格式：pending_hooks.md

> 此模板用于编译包 `story-design/inkos/pending_hooks.md`。
> **必须使用 InkOS 表格格式，且整个文件只能有一张数据表。**
> InkOS 的 `parseMarkdownTableRows()` 会收集文件内所有 `|` 开头行作为数据行。
> 如果存在第二张表格（如字段说明），会被错误解析为额外伏笔。
> 人类可读的完整谜题设计保留在 `07-foreshadowing-and-mystery.md`。

---

## 待回收伏笔

| hook_id | 起始章节 | 类型 | 状态 | 最近推进 | 预期回收 | 回收节奏 | 上游依赖 | 回收卷 | 核心 | 半衰期 | 升级 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H001 | 3 | mystery | open | 0 | 仓库损耗真相：有人系统性偷窃物资建立私人储备 | near-term | 无 | 第一卷 | 是 | 8 | 是 | 前台问题：3号仓库异常损耗原因；公平线索：第三章接线被动过、第四章物资清点差异 |
| H002 | 5 | foreshadow | open | 0 | 何卫国的军方背景将在第二卷揭示 | slow-burn | [H001] | 第二卷 | 是 | 12 | 否 | 前台问题：何卫国为何对组织秩序有执念；公平线索：第五章签字习惯、第二章指挥风格 |

---

## 字段说明

- **hook_id**：伏笔编号（H001 起），递增不跳号
- **起始章节**：埋设章节号（建书前填预期值）
- **类型**：mystery（谜题）/ foreshadow（伏笔）/ suspense（悬念）
- **状态**：InkOS 支持四种——open（未推进）/ progressing（推进中）/ deferred（搁置）/ resolved（已回收）
- **最近推进**：最近一次推进的章节号（0 = 尚未推进）
- **预期回收**：一句话描述回收内容（具体章节范围也可放这里）
- **回收节奏**：InkOS 支持五种——immediate（立即）/ near-term（近期）/ mid-arc（中程）/ slow-burn（慢烧）/ endgame（终局）
- **上游依赖**：需要先完成的其他 hook_id（无 = 无依赖，格式 [H001, H002]）
- **回收卷**：预期在哪一卷回收
- **核心**：是否为核心伏笔（是/否）
- **半衰期**：读者好奇心衰减半衰期（章数，越大越耐等）
- **升级（promoted）**：是 = 该 Architect seed 已晋升为活跃伏笔债务，InkOS 会将其纳入当前活跃伏笔；否 = 仍是种子，InkOS 不会将其作为当前活跃伏笔处理
- **备注**：前台问题、后台真相、公平线索、错误解释、信息释放顺序、回收条件和意义反转等补充信息

---

## 使用说明

- 建书前：此文件作为初始伏笔种子写入编译包
- 建书后无章节且无 hooks.json：可直接修正此文件
- 建书后有章节：不直接修改，通过 current_focus.md 推进 + InkOS 结算
- **整个文件只能有一张 Markdown 表格**（数据表），字段说明不得使用表格格式
- 编号递增，不跳号
- 每个伏笔的完整设计（误导、知识不对称、回收条件）保留在 `07-foreshadowing-and-mystery.md`
- 状态值必须使用 InkOS 枚举：open / progressing / deferred / resolved
- 回收节奏必须使用 InkOS 枚举：immediate / near-term / mid-arc / slow-burn / endgame
- 冻结源码参考：Narcooo/inkos master, packages/core/src/utils/story-markdown.ts parsePendingHooksMarkdown()
