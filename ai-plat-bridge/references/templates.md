# 模板参考

本文件包含 ai-plat-bridge 使用的所有写入模板。

## 今日日志模板

文件：`10-Daily/YYYY-MM-DD.md`

```markdown
# YYYY-MM-DD

## 今天做了什么
- <项目名>：<具体动作>

## 今天推进了哪些项目
- <项目列表>

## 今天遇到的问题

## 今天形成的结论

## 明天最重要的一件事
```

创建时保留固定节标题，但只填写本次能够确认的内容：
- 不使用"无""暂无""待定"等占位条目。
- 不知道明天最重要的一件事时，保持该节为空。
- 不根据上下文擅自推断用户明天的优先事项。

## 任务卡片模板

文件：`20-Tasks/active/<date>-<slug>.md`

```markdown
---
created: YYYY-MM-DD
status: active
tags: [task, <project-tag>]
---

# <标题>

## 任务目标

## 背景信息

## 相关路径

## 已知现象

## 约束条件

## 执行记录

## 最终结果

## 下一步动作
```

归档时：将状态改为 `resolved` 或移动到 `20-Tasks/done/`，追加 `## 最终结果` 节。

## 每日记忆模板

文件：`.workbuddy/memory/YYYY-MM-DD.md`

追加简洁的工作记录行，格式：`- <项目>：<动作/结论>`。

## 项目文件 frontmatter 格式

为提高匹配确定性，项目文件 YAML frontmatter 可包含：

```yaml
aliases: [ZC29A_FPGA, zc29a]
repo_paths:
  - C:\100-Working\102-Working-Prj\zc29a\02\
```

## 变更标注格式

新信息与已有记录冲突时，不静默覆盖。保留旧记录并以如下标注追加变更说明：

```markdown
> [!note]- YYYY-MM-DD 变更
> <冲突内容和更新原因>
```

## 写后验证输出格式

```text
已同步到工作台：

- 10-Daily/2026-07-17.md
  - 追加"今天做了什么"
- 30-Projects/zc29a.md
  - 更新"当前状态"
  - 更新"下一步动作"

未更新：
- MEMORY.md：本次信息不具备长期复用价值
- 任务卡片：本次不涉及独立任务生命周期
```
