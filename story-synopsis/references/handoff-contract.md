# StorySynopsisPackage 交接契约规则

> 本文件定义 story-synopsis 生成 synopsis-contract.yaml 的详细规则。
> 在用户确认定稿时加载。

---

## 生成触发条件

必须同时满足：

1. 用户明确表示定稿意图（"定稿"、"确认"、"就这样"等）
2. 故事已从开端写到结局
3. 幕后真相明确
4. 主要人物弧光完整
5. 关键反转和伏笔已说明
6. 成稿审查已完成
7. 无 blocking issue

不满足时不生成 contract，不设置 handoff_ready: true。

---

## 字段提取规则

### 从已确认事实提取

- protagonist 各字段：从"已确认事实"中的主角设定提取
- opposition：从已确认的对手/阻碍设定提取
- core_conflict：从已确认的核心冲突提取
- world_rules：从已确认的世界规则提取
- story_truth：从已确认的幕后真相提取
- ending：从已确认的结局提取
- major_turning_points：从已确认的关键转折提取

### 不从暂定事实提取

暂定事实（用户尚未确认的方案）不得进入 contract 的 frozen 字段。如果某个关键信息仍为暂定，应：
- 标记为 unresolved_non_blocking（如果不阻塞交接）
- 或阻止交接（如果阻塞）

### 已否决方向

用户明确否决的方向进入 `prohibited_directions`。例如：
- "不要后宫"
- "不要让主角死"
- "不要用时间旅行"

---

## adaptation_boundaries 填写指南

### frozen_facts

不可改变的故事真相。判断标准：如果改变这一点，故事的核心体验会完全不同。

典型包括：
- 幕后真相
- 主角最终选择
- 结局代价
- 核心命题的回答
- 主要人物的最终命运
- 世界核心规则

### expandable_zones

下游（webnovel-serial-designer）可以合法扩展的区域。

典型包括：
- 阶段性对手/配角
- 中间事件
- 世界层级扩展
- 支线故事
- 具体场景设计
- 能力/资源升级细节

### prohibited_directions

用户明确禁止的方向 + 会破坏故事核心的方向。

### unresolved_non_blocking

未决定但不影响连载化的事项。例如：
- 配角的具体名字
- 某个次要地点的名称
- 尾声的具体时间线

---

## revision 规则

- 首次定稿：revision = 1
- 定稿后用户要求修改并再次确认：revision +1
- 每次 revision 递增时，检查 frozen 字段是否被修改
- 如果 frozen 字段被修改，必须在 contract 中体现（更新内容，保持 frozen: true）
- 下游记录消费的 revision，两者不一致时警告

---

## 与 synopsis.md 的关系

- synopsis.md 是完整叙事（3000-5000 字），包含因果过程和情绪
- synopsis-contract.yaml 是机器契约（100-250 行），只包含结论和边界
- 两者构成同一版本的 StorySynopsisPackage
- 实质矛盾时包无效，应修复后重新生成
- 下游不得自行选择其中一份覆盖另一份

---

## handoff_ready 语义

```yaml
handoff_ready: true
```

表示：
- 故事核心已冻结
- 下游可以开始连载化设计
- 不需要再回到 story-synopsis 补完故事

```yaml
handoff_ready: false
```

表示：
- 仍有 blocking issue 或故事未完整
- 下游不应消费此包
- 需要继续开发或修复
