---
name: zg-agent-setup
description: "对当前工程做 zvec-grep (zg) 工程级接入：生成/维护 .zgignore、构建索引、为指定 agent 写入工程级 MCP 配置，并做配置+端到端验收。当用户要给某工程配置 zg/zvec-grep、接 agent 搜索、建 workspace index、写工程级 MCP，或说「zg 接入 / zg install 工程级 / 配置 zvec_grep」时使用。"
---

# zg-agent-setup

把 **zvec-grep (`zg`)** 接到当前工程，并写入指定 agent 的**工程级** MCP 配置。

## 能力边界

**做：**
1. 生成/幂等更新工程根 `.zgignore`（managed block）
2. 执行 `zg status` / `zg index`（可选 `--rebuild`）
3. 为 agent 写入工程级 MCP（`zg server --stdio`）
4. 验收：配置文件正确 + `zg` 本体可用；CLI 可用时做 agent 内真实搜索

**不做：**
- 全局 `zg install`（那是用户级，不是工程级）
- 修改 embedding 模型 / 远程 embedding 授权策略
- 删除或 `--drop` 索引（除非用户明确要求）
- 替用户 git commit

## 输入

| 输入 | 说明 |
|------|------|
| `project_root` | 工程根目录；默认当前工作目录 |
| `agents` | 目标 agent 列表：`codex` `claude` `opencode` `cursor` `qwen` `qoder` |
| `ignore_rules` | 追加到 `.zgignore` 的规则；可省略用默认 |
| `rebuild` | 是否 `zg index --rebuild` |
| `e2e` | 是否做 agent 内真实搜索（默认 true，CLI 缺失则降级） |

## 执行

优先用脚本（幂等、可重复）：

```bash
# 全流程：ignore + index + mcp + verify
"$MIMO_PYTHON" <skill_dir>/scripts/setup_zg.py all \
  --project-root <path> --agents codex,claude

# 分步
"$MIMO_PYTHON" <skill_dir>/scripts/setup_zg.py ensure-ignore --project-root <path>
"$MIMO_PYTHON" <skill_dir>/scripts/setup_zg.py index --project-root <path> [--rebuild]
"$MIMO_PYTHON" <skill_dir>/scripts/setup_zg.py mcp --project-root <path> --agents claude,codex
"$MIMO_PYTHON" <skill_dir>/scripts/setup_zg.py verify --project-root <path> --agents claude
```

`<skill_dir>` 为本 skill 目录。Windows 下用 `$env:MIMO_PYTHON`。

## 工程级 MCP 目标路径

| Agent | 工程级文件 | 格式要点 |
|-------|------------|----------|
| claude | `<root>/.mcp.json` | `mcpServers.zvec_grep` → command `zg`, args `["server","--stdio"]` |
| codex | `<root>/.codex/config.toml` | `[mcp_servers.zvec_grep]` command/args |
| opencode | `<root>/opencode.json`（无则创建） | `mcp.zvec_grep.type=local` |
| cursor | `<root>/.cursor/mcp.json` | 同 Claude 形状 |
| qwen / qoder | 按官方 target 文件；无稳定工程级格式则只报路径与缺失证据 |

Codex：**优先项目** `.codex/config.toml`；若运行时不生效，在报告中说明，可回退全局 `~/.codex/config.toml`（需用户确认）。

## 默认 `.zgignore` managed block

```
# zg-agent-setup:begin
**/*_bak*
**/*_bak.*
.worktrees/**
# zg-agent-setup:end
```

只维护 begin/end 之间内容；块外用户规则保留。

## 验收线

| 级别 | 条件 |
|------|------|
| 配置 | 目标 MCP 文件存在且含 `zvec_grep` + `zg server --stdio` |
| 本体 | `zg status` ready；一条工程相关 `zg query` 有命中 |
| e2e | 目标 CLI 可执行时，在工程根用该 agent 发起一次真实 MCP 搜索并拿到结果 |
| 缺失 | CLI 不在 PATH → 配置仍写入，e2e 标记 `missing evidence`，**不得伪称通过** |

## 输出

运行结束后向用户报告：
- 修改了哪些文件（ignore / index / MCP）
- `zg status` 摘要（files/entities/coverage）
- 每个 agent：配置路径、e2e 结果或 missing evidence
- 未验证风险与下一步

## 风险

- 写 MCP 配置会改工程内文件；合并时保留无关键
- `index --rebuild` 会重新 embedding，耗时随文件数增加
- 不要在报告中复述 API key / token
