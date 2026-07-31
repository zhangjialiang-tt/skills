# 变更影响分析报告模板

> 建书后执行任何修改前，必须先完成此分析。
> 完整格式用于修改绿区/黄区/正文；简化格式用于纯文风修改和焦点更新。

---

## 完整格式（YAML）

```yaml
change_id: CHANGE-<NNN>
change_type: future_design | retroactive_fix

target:
  - <被修改的文件路径>

affected_chapters:
  written: none | <章节范围，如 "10-15">
  future: none | <章节范围，如 "42-58">

affected_characters:
  - <角色名>

affected_hooks:
  - <伏笔编号，如 H007>

runtime_action:
  plan_required: true | false
  compose_required: true | false
  sync_required: true | false
  rewrite_required: true | false

risk:
  level: low | medium | high | critical
  reason: <一句话说明风险原因>
```

---

## 简化格式（纯文风/焦点更新）

```yaml
change_id: CHANGE-<NNN>
change_type: future_design
target:
  - <文件路径>
risk:
  level: low
  reason: 纯文风修改，不影响事实 | 仅更新近期方向
```

---

## 7 个必答问题（分析过程）

1. 这是未来设计变更，还是追溯修改？
2. 是否与已经发布的正文矛盾？
3. 会影响哪些角色？
4. 会影响哪些伏笔？
5. 会影响哪些卷？
6. 需要修改正文吗？
7. 需要 sync 还是 rewrite？

---

## 风险等级参考

| 等级     | 含义                         | 需要用户确认 |
| -------- | ---------------------------- | ------------ |
| low      | 只影响未来设计               | 否           |
| medium   | 影响当前卷但未在正文揭示     | 建议         |
| high     | 与已写正文矛盾，需要 sync    | 是           |
| critical | 影响多章因果链，需要 rewrite | 是（强制）   |
