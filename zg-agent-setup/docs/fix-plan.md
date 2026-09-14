# zg-agent-setup 修改计划

状态：待执行
适用对象：`zg-agent-setup/SKILL.md`、`scripts/setup_zg.py`、`locales/*`
当前 skill 未纳入版本管理（`git status` → `?? zg-agent-setup/`），可整体重构，无向后兼容负担。

## 目标

把 skill 从"看起来完整"改到"结论可信"：
1. 删掉不存在的机制（`.zgignore`）；
2. 验收判据换成原生可机器判定的信号，杜绝伪称通过；
3. 消除会损坏用户配置的写入路径；
4. 文档里写的命令能直接复制执行。

## 范围边界（本次不做）

- 不改 zvec-grep 本体，不向 upstream 提 issue（另议）。
- 不引入新依赖（保持 stdlib-only）。
- 不新增 `evals/` `manifest.json` `agents/interface.yaml` 等仓库约定件，除非第 12 项决定保留 skill 目录结构对齐（那是独立任务）。

## 前置事实（本机实测，zg 0.2.2）

| # | 事实 | 证据 |
|---|------|------|
| F1 | `.zgignore` 不存在 | `grep -r zgignore dist/**/*.js` → 0 命中；docs/README 0 命中；dist 中唯一 ignore 文件名字面量是 `.gitignore` |
| F2 | 排除机制是默认规则 + 仓库 ignore + CLI flag | `zg index --help` File selection：`-g/--glob`、`--iglob`、`-t/-T`、`--hidden`、`--no-ignore`、`--ignore-file <path>`、`--max-depth`、`--max-filesize`、`-L`、`--reset-paths` |
| F3 | 索引落在仓库内 | README："The index is stored in `.zvec-grep/` under the indexed project root."；实测 `zg status` → `Storage .zvec-grep\index.zvec` |
| F4 | `--check-ready` 是原生就绪信号 | 实测 `zg status` rc=0（未建索引），`zg status --check-ready` rc=1；docs/02-cli.md："exits non-zero unless the index is ready, which is useful in scripts" |
| F5 | 状态字面量确认 | `dist/cli/format/status.js` heading：`ready` / `is updating` / `needs an update` / `failed` / `not created` / `not configured`；失败态不含 `ready` |
| F6 | 查询输出字面量 | `dist/cli/format/context.js` 打印 `Hits: N`（0 命中也打 `Hits: 0`）；无 `File:` 标签 |
| F7 | 新索引必须有 embedding 来源 | `zg index --help`："New indexes require --embedding, ZVEC_GREP_EMBEDDING, or a configured default." |
| F8 | 上游 Codex 条目形态 | 本机 `~/.codex/config.toml` 实际含 `tool_timeout_sec = 600.0`、`default_tools_approval_mode = "approve"` |
| F9 | Claude 有 project 作用域 | `claude mcp add --help` → `-s, --scope <local\|user\|project>`；`claude mcp get <name>`、`claude mcp list` 均存在 |
| F10 | Codex 有原生 MCP 管理 | `codex mcp {list,get,add,remove,login,logout}`；`codex mcp add --help` **无 scope 参数**，读 `~/.codex/config.toml` |
| F11 | **Codex 工程级 MCP 未生效** | 在临时目录放 `.codex/config.toml` + `[mcp_servers.zg_probe_marker]`，于该目录 `codex mcp list` → marker 不出现，只列出全局 3 条 |
| F12 | 本机 CLI 可用性 | `claude` ✓ `codex` ✓ `opencode` ✓ `qodercli` ✓；`qwen` ✗ `cursor` ✗ `qoder` ✗（脚本按 `which(agent)` 探测，qoder 名字对不上） |

F11 是对前一轮评审意见的**自我修正**：我曾判断"Codex 工程级只能手写、故该分支有存在理由"。实测推翻，须先补验证再决定去留。

## P0 阻塞发布（必须改）

### P0-1 删除 `.zgignore` 机制，改为 `.gitignore` + CLI 排除

- 问题：能力 1 的目标文件不存在，且脚本从不把它传给 zg（无 `--ignore-file`），双重失效。
- 改法：
  1. managed block 写入目标从 `.zgignore` 改为 `<root>/.gitignore`，内容只有 `.zvec-grep/`（F3）；
  2. 用户排除规则改为 `zg index -g '!<pattern>'`（可重复）透传，新增 `--exclude` 参数；
  3. 更新 SKILL.md 的"能力边界/默认 managed block/工程级产物"三节，明确唯一入库产物是 `.gitignore` 一行 + 各 agent 的 MCP 配置。
- 不做：不保留 `.zgignore` 作为 `--ignore-file` 的自定义名。理由：F2 里规则会被索引存储并继承，跨机器漂移风险高于收益。
- 验证：临时目录跑 `ensure-ignore` 两次 → 第二次 `changed=False`，`.gitignore` 无重复块，块外用户内容保留。

### P0-2 验收换成原生信号

- 问题：claude 分支 `rc == 0 and bool(out.strip())` 恒 pass；且无 `--allowedTools`，非交互下 MCP 调用会被拒（`zg install --help`："Codex and Claude Code receive local tool pre-approval"）。codex 分支靠模型自觉输出 `TOOL_UNAVAILABLE`。
- 改法：拆成两级，模型调用变成可选第三级。
  - `configured`：`claude mcp get zvec_grep` / `codex mcp get zvec_grep`（F9/F10），rc==0 且输出含 `zvec_grep`；
  - `connected`：`claude mcp list` / `codex mcp list` 中该条目的状态列；
  - `usable`（可选、需用户同意，会产 token 费用）：agent 内真实搜索，判据改为响应里出现 MCP 工具调用记录（`--output-format stream-json --verbose` 抓 `tool_use` 且 name 含 `zvec_grep`），**不再用"输出非空"**。
  - Claude 分支补 `--allowedTools "mcp__zvec_grep"`（或 `--permission-mode`），否则不判 usable。
- 验证：故意把 command 写成不存在的 binary → `connected` 必须 FAIL；当前工程未建索引 → `usable` 必须是 missing evidence 而非 pass。

### P0-3 配置解析失败不得静默清空用户配置

- 问题：`merge_json_mcp` 与 opencode 分支捕获 `JSONDecodeError` 后备份 + `data = {}` 重写，用户其它 `mcpServers` 全丢；`ok: path.exists()` 恒真 → 步骤报 `[OK]`。
- 改法：删掉两处兜底，解析失败即 `raise`（detail 带备份路径），步骤 FAIL。
- 验证：构造含非法 JSON 的 `.mcp.json` → 脚本 FAIL、原文件未被覆盖、退出码 1。

### P0-4 修掉 `$MIMO_PYTHON`

- 问题：全仓 `grep MIMO_PYTHON` 只命中本 skill 的 SKILL.md，无定义来源，文档命令不可复制执行。
- 改法：统一 `python3`（正文注明 Windows 用 `python`）；脚本本身保持 stdlib-only + `from __future__ import annotations` 以兼容 3.8+。
- 验证：按 SKILL.md 原文逐条复制执行，命令均能启动（不要求成功）。

### P0-5 `index` 步骤前置对齐 + 交互防挂死

- 问题：新索引必须有 embedding 来源（F7），脚本无 `--embedding` 透传 → 干净机器 `all` 在第 2 步必 FAIL；`run()` 未设 `stdin` → 授权/确认类交互会挂到 900s；且建索引会把工作区内容送进 embedding provider，属实际数据出口，与 SKILL.md"不修改远程授权策略"的声明冲突。
- 改法：
  1. 新增 `--embedding` / `--allow-remote` 透传；不带时先读 `zg status` 的 `Policy`/`Next` 与 `zg auth status`，缺来源就 FAIL 并给出候选命令，不猜默认值；
  2. `run()` 加 `stdin=subprocess.DEVNULL`；
  3. `all` 拆为默认 `ensure-ignore + mcp + verify`，`index` 只在显式 `--with-index` 时执行；
  4. SKILL.md 把"建索引 = 可能远程发送内容"列进风险，并标注需用户确认（High-Impact）。
- 验证：无默认模型的临时目录跑 `all` → 在 index 前给出可执行建议并 FAIL（不挂死、不静默）。

## P1 质量项（发布前应完成）

| 项 | 改法 | 依据 |
|----|------|------|
| P1-6 就绪判定 | `cmd_status` 的 `"ready" in low` 换/补 `zg status --check-ready`，并保留原输出用于报告；同时把 stale（`needs an update`）与 ready 分开报，不再同算 OK | F4/F5 |
| P1-7 命中判据 | 解析 `Hits: (\d+)` 且 `> 0` 才判有命中，与 SKILL.md 验收线一致；`Groups`/`Files` 一并入报告 | F6 |
| P1-8 Codex 条目补字段 | 手写段落补 `tool_timeout_sec`、`default_tools_approval_mode = "approve"`（若 P0-2 决定保留工程级手写路线） | F8 |
| P1-9 与 `zg install` 的关系 | SKILL.md 明确本 skill 是"工程级补充"，并写清：手写条目是 unmanaged、后续 `zg install` 需 `--force`、`zg uninstall` 不会回收；新增 `uninstall` 子命令删除自己写入的 managed block 与条目 | `zg install --help` / docs/01-agents.md |
| P1-10 qwen/qoder 分支 | 停止向仓库写 `.zg-agent-setup-*-MCP.md`；改为只报告上游 target 路径 + `zg install --target <agent>` 建议命令。同时 e2e 探测名修正为 `qodercli` | docs/01-agents.md 表格；F12 |
| P1-11 TOML 去重检测 | `[mcp_servers.<name>]` 判定改为逐行正则（容忍 quoted 形式、排除注释行），避免产出重复键导致 config 解析失败 | 代码审查 |
| P1-12 输出分流 | 进度 `[OK]/[FAIL]` 改 stderr，stdout 只留 JSON，保证 `... all \| jq` 可用 | 代码审查 |
| P1-13 `ensure_zg()` 位置 | 移出 `main` 无条件调用，只在真正需要 zg 的步骤里 `ensure` | 代码审查 |
| P1-14 超时可调 | 180/900 硬编码改 `--timeout`（index 单独 `--index-timeout`），超时后报告写明"索引可能处于半成品状态，建议 `zg index --rebuild`" | 代码审查 |
| P1-15 locales 去留 | 二选一：删 `locales/`（全仓无消费者，skill-sync.ps1 只按 `SKILL.md` 识别目录），或补 `manifest.json` 对齐仓库约定。默认**删** | 仓库结构核查 |
| P1-16 版本声明 | SKILL.md 增加"已验证 zg 版本 0.2.2"，verify 步骤把 `zg version` 写入报告 | 上游 flag 漂移风险 |

## 前置验证任务（决定 P0-2/P1-8 形态，先做）

- V0-1 Codex 工程级 MCP：F11 结论需排除"项目未信任"这一变量。做法：在临时目录（或某个已 `/trust` 的工程）写 `[mcp_servers.zg_probe_marker]`，跑 `codex mcp list`；再对照 `codex --cd <dir> mcp list`。
  - 仍不出现 → **删除 codex 工程级写入分支**，改为报告全局配置指引（写 `~/.codex/config.toml` 属用户级、需明确确认）；SKILL.md 输入表移除 codex 或标注"仅全局"。
  - 出现（说明与 trust 相关）→ 保留手写分支，并在 SKILL.md 写明前置条件 + P1-8 补字段。
- V0-2 Cursor 工程级 `.cursor/mcp.json`：本机无 `cursor`/`cursor-agent`（F12），无法闭环 → 保留 `missing evidence` 标签，SKILL.md 把该行从"工程级文件"改为"上游 target 是 `~/.cursor/mcp.json`，工程级未验证"。
- V0-3 OpenCode e2e CLI 形状：本机有 `opencode`（F12），可跑 `opencode --help` 核实 `run` 子命令与参数；作者自己标了 best-effort。

## 验证门禁（怎样算改完）

1. `python3 scripts/setup_zg.py all --project-root <tmp>` 在无 zg 索引的干净临时工程上：退出码语义正确、`missing evidence` 不被计入 OK。
2. 幂等：连续跑两次，第二次所有步骤 `changed=False`、`.gitignore`/MCP 文件字节不变。
3. 抗破坏：非法 JSON 的 `.mcp.json` / 已含 `[mcp_servers."zvec_grep"]` 的 config → FAIL 且原文件未被改。
4. 反伪证：command 写成不存在的 binary → `connected` FAIL；未建索引 → `usable` 为 missing evidence。
5. 文档可执行：SKILL.md 每条命令复制即可运行；`ensure-ignore` 不再提 `.zgignore`。
6. 至少一次真实工程试跑（建议拿 `zc29a/02`，该工程已配置过 zg），报告含 `zg version`、status 摘要、各 agent 三级验收结果。

## 执行顺序

1. V0-1（决定 Codex 分支去留）→ 2. P0-1 → 3. P0-3 → 4. P0-4 → 5. P0-5 → 6. P0-2（依赖 V0-1/V0-3）→ 7. P1 批量 → 8. 门禁 1~5 → 9. `novelos`-无关的 checkpoint：临时工程跑通后落一次 commit（需用户确认）。

单条 P0 失败不阻塞其余：P0-1/3/4 是纯局部修改，可先落。
