---
name: omp-session-analyzer
description: 将 OMP Agent 的 session 对话数据（JSONL）导出为交互式 HTML 可视化报告，便于分析 Agent 行为。支持 token 用量、工具调用、耗时、成本等维度分析。用户提到导出 OMP 对话、分析 OMP session、OMP 可视化、omp --export 增强、Agent 行为分析时使用。
---

# OMP Session Analyzer

将 OMP Agent（Oh My Pi）的 session JSONL 数据解析并生成交互式 HTML 分析报告。

## 数据源

OMP session 存储在 `~/.omp/agent/sessions/<编码路径>/<session-id>.jsonl`。

路径编码规则：将绝对路径 `C:\foo\bar` 中 `\` 替换为 `-`，`:` 替换为 `--`，前缀 `-`。
例：`C:\100-Working\foo` → `--C--100-Working-foo--`

## JSONL 事件类型

| type | 说明 |
|------|------|
| `session` | session 元信息（id, timestamp, cwd, title） |
| `title` / `title_change` | 标题 |
| `message` | 对话消息（role: user/assistant/toolResult） |
| `toolCall` | 工具调用（name, arguments, usage） |
| `thinking` | 模型推理过程 |
| `custom` (tool_execution_start) | 工具执行开始标记 |
| `model_change` / `thinking_level_change` | 配置变更 |

`message.message.content` 是数组，元素类型包括 `text`、`toolCall`、`thinking`、`image`。

## 使用方式

```bash
# 分析单个 session
python scripts/analyze_session.py ~/.omp/agent/sessions/<path>/<id>.jsonl

# 分析整个项目目录（合并所有 session）
python scripts/analyze_session.py ~/.omp/agent/sessions/<path>/

# 分析所有 session（全局）
python scripts/analyze_session.py ~/.omp/agent/sessions/

# 指定输出路径
python scripts/analyze_session.py <input> -o report.html
```

## 报告内容

1. **总览面板**：session 数、总 token、总成本、总耗时、模型列表
2. **Token 用量趋势**：按 session 或按 turn 的 token 消耗折线图
3. **工具调用统计**：各工具调用次数、平均耗时、token 消耗
4. **对话时间线**：每个 turn 的角色、token、耗时、工具调用
5. **完整对话**：可折叠的逐条消息视图（含 thinking 展开）

## 实现约束

- 纯 Python 3，仅使用标准库 + 内嵌 ECharts（CDN）
- 输出单文件 HTML，离线可用
- 大文件（>10MB）自动采样，避免浏览器卡顿
- 不修改源数据
