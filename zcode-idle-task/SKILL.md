---
name: zcode-idle-task
description: >-
  生成 ZCode 闲时任务的任务合同和任务指令。用户提到"闲时任务""让 ZCode
  夜间执行""交给 ZCode 后台审查""创建 ZCode 自动化任务"或希望无人值守分析
  当前工程时使用。把自然语言需求转换成有项目、有范围、有交付物、有验收标准
  和权限边界的任务指令，在用户确认后输出供用户自行提交到 ZCode 界面。
  不操作 ZCode UI；如果用户只是要求当前立即分析，不触发本 Skill。
---

# ZCode Idle Task

## Purpose

生成可交给 ZCode 无人值守执行的任务合同和任务指令。Skill 负责理解需求、补齐
任务合同、生成任务指令、在输出前展示预览，用户确认后产出可复制的指令文本，
由用户自行粘贴到 ZCode 的"自动化 → 新建闲时任务"界面。

支持三级任务权限：read_only（默认）、modify_files、modify_and_commit。
高级别权限需用户明确授权并在预览中单独确认。

## Hard boundary

- "闲时任务"专指 ZCode UI 中的自动化任务，不是 Codex `create_thread`，也不是普通子 Agent。
- 本 Skill 只生成指令文本，不操作 ZCode UI，不通过 Computer Use 提交任务。
- 任务的项目、workspace、模型、推理强度以用户实际环境为准，不猜测。
- 不修改项目源文件，不创建临时工程文件，不提交 Git，除非任务合同明确授权。
- 不把 UI 占位提示文字、历史任务摘要或默认值当成用户需求。

## Trigger and non-trigger

触发：

- "帮我创建一个闲时任务，让 ZCode 晚上扫描 RTL。"
- "把这个 FPGA 架构审查交给 ZCode 后台执行。"
- "创建 ZCode 自动化任务，明早给我一份测温链路一致性报告。"

不触发：

- "现在帮我分析这个 RTL 文件。"（即时分析，非闲时任务）
- "创建一个 Codex 后台任务。"（不是 ZCode 闲时任务）
- "帮我写一个普通的 Python 脚本。"（不涉及闲时任务）

## Workflow

### 1. Inspect context

读取当前 workspace 的 `AGENTS.md`、项目 README、Git 状态和用户点名的文件。
只读取与任务范围有关的内容。优先使用真实项目路径、真实顶层文件和真实测试入口。

至少确定：project/workspace 路径、任务类型、目标模块/目录、是否允许修改文件或提交 Git、
交付物和验收标准。缺少的信息会改变任务边界时先询问；可安全默认时使用只读最小方案。

### 2. Build task contract

按 `references/task-contract.md` 的字段和规则构建任务合同。合同字段：

```yaml
title, workspace, objective, scope, deliverables,
constraints, acceptance, stop_conditions,
execution: { permission, model, reasoning }
```

`permission` 取值：`read_only` | `modify_files` | `modify_and_commit`。

### 3. Generate task prompt

按 `references/prompt-templates.md` 中的模板生成任务指令，依次覆盖：
角色与目标 → 项目和 workspace → 检查范围 → 执行步骤 → 输出格式 →
约束和权限 → 验收标准 → 停止条件。

只读任务必须明确写出：不修改/删除/重命名文件、不修改 golden/checker、不 commit/push/reset、
区分事实/观察/推导/未验证项、给出实际执行命令和真实结果。

modify_files 任务必须列出允许修改的文件集合和回滚边界。
modify_and_commit 任务必须限定提交范围、提交条件和提交信息格式。

### 4. Preview and confirmation

向用户展示：任务标题、项目和 workspace、权限模式、主要范围、交付物、
是否修改文件/运行测试/提交 Git、完整任务指令。

以下动作必须在输出前取得用户明确确认：

- 允许修改项目文件（modify_files）
- 允许提交、推送或改写 Git 历史（modify_and_commit）
- 允许执行高风险或不可逆操作

即使用户已提出"创建任务"，也不把高风险变更默认包含进任务。

### 5. Output

用户确认后，输出可直接复制的任务指令文本块，并附摘要：

```text
任务标题：...
项目：...
权限：...
模型与推理强度：...（用户指定值或"保留 ZCode 默认"）
交付物：...
```

提示用户将指令粘贴到 ZCode 的"自动化 → 新建闲时任务"界面，并按合同字段填写对应项。

## Default task policy

用户未明确说明时使用最小安全默认：

```yaml
permission: read_only
modify_files: false
git_commit: false
git_push: false
deliverable: markdown_report
```

默认优先生成报告，不直接修复问题。发现的问题列为建议，不静默扩大工作范围。

## Resources

- `references/task-contract.md`: 任务合同字段、类型策略和质量检查清单
- `references/prompt-templates.md`: ZCode 任务指令模板（只读审查/测试验证/代码修改）
- `scripts/validate_idle_task.py`: 校验任务合同的确定性脚本
- `evals/evals.json`: 触发、排除和任务生成测试用例
