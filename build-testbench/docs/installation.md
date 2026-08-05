# build-testbench skill 安装

本文件供维护者和首次使用者参考，**不参与每次 skill 执行**。运行规则见 `../SKILL.md`。

## 维护源

本 skill 的唯一维护源是 workspace 的 `.pi/skills/build-testbench/`。

**不要**在 `.agents/skills` 或 `.codex/skills` 下复制或维护独立副本——会与源漂移。其他 agent 入口通过 Junction 指向源目录。

## Codex skill 入口（Junction）

```powershell
$WorkspaceRoot = (python .pi\skills\build-testbench\scripts\workspace_root.py --start .)
$SkillSource = Join-Path $WorkspaceRoot '.pi\skills\build-testbench'
$CodexSkill = Join-Path $HOME '.codex\skills\build-testbench'
New-Item -ItemType Directory -Force -Path (Split-Path $CodexSkill) | Out-Null
New-Item -ItemType Junction -Path $CodexSkill -Target $SkillSource
```

### 已存在的情况

如果 `$CodexSkill` 已存在，先检查它是否为指向当前 `$SkillSource` 的 Junction：
- 目标匹配 → 无需操作
- 目标不匹配 → **停止并报告**，不要覆盖未知目录

Junction 的目标必须是 `.pi\skills\build-testbench`，而不是 `.agents\skills`。

## workspace 根定位

脚本：`scripts/workspace_root.py`

```powershell
$WorkspaceRoot = python .pi\skills\build-testbench\scripts\workspace_root.py --start <rtl_file_or_dir>
```

从提供的路径向上查找最近的 `.git`。找不到时返回非零退出码——此时停止，不要把 RTL 所在子目录默认为 workspace 根。

## 依赖

- Python 3.8+（仅标准库）
- ModelSim 或 QuestaSim（`vlib` / `vlog` / `vcom` / `vsim`）
- Make（Windows 下推荐 MSYS2/MinGW）
