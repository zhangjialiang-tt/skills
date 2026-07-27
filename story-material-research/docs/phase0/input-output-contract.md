# Input/Output Contract

**Skill:** `story-research-prompt`
**Status:** Phase 0 — Frozen Baseline
**Last Updated:** 2026-07-27

---

## 1. Input Contract

### 1.1 用户请求结构

```yaml
UserRequest:
  target_work:
    title: string           # 作品名
    creator?: string        # 作者/导演/编剧
    year?: number           # 发布年份（消歧用）
    type: enum              # novel | film | tv_series | script | theme
    version?: string        # 版本/改编信息
  research_goal:
    purpose: enum           # comprehensive | structure | character | mystery | pacing | worldbuilding | adaptation | comparative
    scope: enum             # full | partial（指定章节/片段）
    target_dimensions: []   # 希望分析的维度
  constraints:
    languages: []           # 接受的资料语言，默认 ["zh", "en"]
    user_materials?: []     # 用户提供的文件/笔记
  output_prefs:
    language: enum          # 输出语言，默认与请求语言一致
    target_tool: enum       # chatGPT_deep_research | qianwen | generic
```

### 1.2 消歧确认触发

当检测到同名作品时，Skill 必须先消歧：

```yaml
DisambiguationRequest:
  candidates:
    - title: string
      creator: string
      year: number
      type: string
      description: string
  selected_index: number    # 用户选择，-1 表示都不是
  user_clarification?: string
```

### 1.3 输入验证规则

| 检查 | 失败处理 |
|------|---------|
| 目标作品标题为空 | 返回错误，要求提供 |
| 无法确认作品身份 | 触发消歧流程 |
| 研究目标过于模糊 | 请求用户澄清 |

---

## 2. Output Contract

### 2.1 产物：Deep Research 提示词

Skill 的输出是一份**完整的、可直接提交给 Deep Research 工具的提示词**。

### 2.2 提示词结构

```
1. 角色定义
2. 任务背景
3. 研究对象与版本说明
4. 研究目的
5. 研究问题（可执行的具体问题）
6. 来源策略（优先级、禁止来源、查询模板）
7. 证据规则（事实/观点/推断的区分、引用规范）
8. 分析方法（如何整理、对比、建模）
9. 输出结构（固定章节）
10. 质量检查清单
```

### 2.3 输出结构（Deep Research 最终报告）

提示词必须要求 Deep Research 按以下结构输出：

```
1. 研究对象与版本说明
2. 资料覆盖情况
3. 故事整体概述
4. 核心故事机制
5. 人物与关系结构
6. 情节推进与因果链
7. 悬念、谜题与信息控制
8. 情绪节奏与高潮设计
9. 伏笔、误导和回收
10. 作品成功与不足
11. 可迁移的创作方法
12. 不可直接照搬的作品特征
13. 证据索引
14. 资料缺口与不确定结论
```

---

## 3. 提示词质量约束

### 3.1 强制约束

- 提示词必须包含来源优先级
- 提示词必须包含禁止来源清单
- 提示词必须要求事实与观点分离
- 提示词必须要求标注资料缺口
- 提示词必须包含固定输出结构
- 提示词必须包含质量检查清单

### 3.2 防诱导约束

| 禁止行为 | 说明 |
|---------|------|
| 诱导大篇幅复述作品 | 提示词应要求"概述"而非"全文复述" |
| 诱导自行补全剧情 | 提示词应要求"无法确认"而非推测 |
| 诱导把评论当事实 | 提示词应要求明确区分 |

---

## 4. 输出版本与兼容性

| 字段 | 说明 |
|------|------|
| `prompt_version` | 提示词框架版本 |
| `schema_version` | 输出结构版本 |
| `target_tool` | 目标 Deep Research 工具 |

**兼容性规则：**
- 主版本号变更 = 不兼容
- 次版本号变更 = 向后兼容（新增可选模块）
- 补丁号变更 = 完全兼容
