# 编译流程详解

> 本文件定义 inkos-brief-compiler 的完整编译流程。
> 在编译执行时加载。

---

## 前置条件

编译只在以下条件全部满足时执行：

1. `serial/serial-contract.yaml` 存在且可解析
2. `serial_design_status == frozen`
3. `handoff_ready == true`
4. `readiness_verdict == pass`
5. Gate A status == approved
6. Gate B status == approved
7. 上游 synopsis_revision 与 serial-contract 记录一致
8. 所有 importance == critical 的 assertion status == confirmed

---

## 编译步骤

### 步骤 1：加载和验证

- 解析 serial-contract.yaml
- 验证 schema_version
- 提取 serialization_target（平台、章数、字数）
- 提取 upstream_integrity（冻结事实、禁止方向）

### 步骤 2：收集 confirmed assertions

- 过滤 status == confirmed 的 assertions
- 按 type 分组
- 标记 importance（critical/major/supporting）
- provisional/proposal/optional/rejected 不进入正式编译

### 步骤 3：查询策略表

对每个 assertion：
- 读取 assertion.type
- 查询 inkos-compilation-policy.yaml 中对应 profile
- 确定 requirement、compression、omission、default_targets

### 步骤 4：读取源材料

- 根据 assertion.source_ref 定位 Markdown 章节
- 读取相关内容
- 如果 source_ref 无效，记录 unmapped_warning

### 步骤 5：执行映射

按 compression 策略：

**verbatim**：原文复制到目标文件对应段落

**semantic_summary**：
- 提取核心语义
- 用 InkOS 目标文件的语言重新表达
- 保持 semantic_invariants 中列出的约束
- 允许压缩长度，不允许改变含义

**structured_split**：
- 按 InkOS 文件结构拆分
- 角色信息 → 多个角色卡
- 分卷信息 → volume_map 各行
- 伏笔信息 → pending_hooks 表格行
- 世界规则 → book_rules 条目

**prohibited**：不编译，保留在源文件中

### 步骤 6：生成 InkOS 文件

按 InkOS 原生格式生成：

- `book-brief.md`：紧凑建书输入（使用 inkos-brief 模板）
- `author_intent.md`：作者意图和长期约束
- `story_frame.md`：世界观和核心设定
- `volume_map.md`：分卷地图
- `book_rules.md`：可执行规则
- `pending_hooks.md`：InkOS 13 列表格
- `roles/`：角色卡

### 步骤 7：覆盖率校验

检查 compilation_policy.block_if_missing 中的类型：
- story_engine 是否有对应产物
- volume_architecture 是否有对应产物
- protagonist_arc_checkpoints 是否有对应产物
- endgame_convergence 是否有对应产物
- first_three_chapters 是否有对应产物

缺失则 blocked。

### 步骤 8：上游忠实度校验

检查 upstream_integrity.preserved_synopsis_facts：
- 每条冻结事实是否在编译产物中有对应表达
- 如果找不到，标记 blocked

检查 forbidden_story_changes：
- 编译产物中是否出现禁止方向的内容
- 如果出现，标记 blocked

### 步骤 9：生成 mapping-plan.yaml

记录每个 assertion 的实际映射结果：
- assertion_id
- 使用的 profile
- 实际目标文件和段落
- result（mapped/split/summarized/retained_as_baseline/omitted_allowed/unmapped_warning/blocked）
- information_loss（none/low/medium/high）
- override（如果有作者例外审批）

### 步骤 10：生成 compilation-report.yaml

汇总：
- 总 assertion 数
- 各 result 类型计数
- unmapped 列表（含原因和严重度）
- information_loss 列表
- proposals_blocked 列表（status != confirmed 被阻止的）
- 上游忠实度检查结果
- 覆盖率检查结果

### 步骤 11：判定编译结果

- 任何 blocked → 编译失败，不生成建书命令
- 无 blocked → 编译成功，输出建书命令

### 步骤 12：输出建书命令

从 serialization_target 和 identity 生成命令参数。

---

## 异常处理

### 源材料缺失

assertion.source_ref 指向的文件或段落不存在：
- importance == critical → blocked
- importance == major → unmapped_warning
- importance == supporting → 记录，不阻塞

### 压缩损失过高

semantic_summary 后无法保持 semantic_invariants：
- 尝试更保守的压缩
- 仍无法保持 → 升级为 retained_as_baseline + warning
- critical 的 invariant 无法保持 → blocked

### 目标文件冲突

多个 assertion 映射到同一文件同一位置：
- 合并（如果语义兼容）
- 无法合并 → 按 importance 排序，低优先级记为 summarized

### 策略表无对应类型

assertion.type 不在策略表中：
- 记录 unmapped_warning
- 默认处理为 retained_as_baseline

---

## 编译器不做的事

- 不读取 serial/design/*.md 中未被 assertion.source_ref 引用的内容
- 不自行判断"这段设计也应该进入 brief"
- 不补充 serial designer 遗漏的设计
- 不修改 assertion 的 status 或 importance
- 不改变 upstream_integrity 中的任何内容
- 不生成超出策略表定义的目标文件
