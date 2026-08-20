<#
.SYNOPSIS
    将当前 Workspace 注册的 Skill 通过 Junction 链接同步到多个目标 Agent 的 Skills 目录。

.DESCRIPTION
    Skill Sync Manager 维护一个 JSON 清单（skill-sync.json，位于 Workspace 根目录），
    清单中包含：
      - agents : 目标 Agent 列表（名称 + Skills 目录路径 + 启用状态）
      - skills : 已注册的 Skill 列表（名称 + 启用状态）

    同步采用 Windows Junction（目录联接）方案：在 Agent 的 Skills 目录下创建
    Junction 链接指向 Workspace 中的 Skill 源目录。Junction 创建无需管理员权限，
    修改源目录即实时反映到所有 Agent。

    兼容 Windows PowerShell 5.1 与 PowerShell 7+。

.PARAMETER Command
    子命令：init | scan | list | status | sync | unsync | clean | add | remove |
            enable | disable | agent | menu
    不提供 Command 时进入交互式菜单。

.PARAMETER Rest
    子命令的附加参数（如 add <名称>、agent add <名称> <路径>）。

.PARAMETER Workspace
    要操作的 Workspace 根目录，默认为脚本所在目录。

.PARAMETER Force
    覆盖/强制操作：
      - init -Force   : 覆盖已存在的配置文件
      - sync -Force   : 重建指向其他位置的过期 Junction
      - unsync -Force : 跳过删除确认

.PARAMETER NoColor
    禁用 ANSI 彩色输出。

.EXAMPLE
    .\skill-sync.ps1 init
    .\skill-sync.ps1 agent add codex C:\Users\me\.codex\skills
    .\skill-sync.ps1 scan
    .\skill-sync.ps1 sync
    .\skill-sync.ps1 status

.EXAMPLE
    .\skill-sync.ps1        # 进入交互式菜单
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('init','scan','list','status','sync','unsync','clean','add','remove','enable','disable','agent','menu')]
    [string]$Command = '',

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Rest = @(),

    [string]$Workspace = '',

    [switch]$Force,
    [switch]$NoColor
)

# ============================================================
# 常量与全局状态
# ============================================================
$script:ScriptName    = 'skill-sync.ps1'
$script:Version       = '1.0.0'
$script:ConfigFile    = 'skill-sync.json'
$script:WorkspaceRoot = ''
$script:UseColor      = $true
$script:ExitCode      = 0
$script:ESC           = [char]27
$script:C             = @{
    Reset   = '0'
    Bold    = '1'
    Dim     = '2'
    Red     = '31'
    Green   = '32'
    Yellow  = '33'
    Blue    = '34'
    Magenta = '35'
    Cyan    = '36'
    Gray    = '90'
}

# ============================================================
# 输出辅助
# ============================================================
function Write-C {
    param([string]$Text, [string]$Color = '', [switch]$NoNewline)
    if ($script:UseColor -and $Color) {
        Write-Host "$($script:ESC)[$($script:C[$Color])m$Text$($script:ESC)[0m" -NoNewline:$NoNewline
    } else {
        Write-Host $Text -NoNewline:$NoNewline
    }
}
function Write-OK    { param([string]$Text) Write-C $Text 'Green' }
function Write-Err   { param([string]$Text) Write-C $Text 'Red' }
function Write-Warn  { param([string]$Text) Write-C $Text 'Yellow' }
function Write-Info  { param([string]$Text) Write-C $Text 'Cyan' }
function Write-Dim   { param([string]$Text) Write-C $Text 'Gray' }
function Write-Sect  { param([string]$Text) Write-C $Text 'Bold' }

function Write-Banner {
    Write-Host ''
    Write-C '┌──────────────────────────────────────────────┐' 'Cyan'
    Write-C '│         Skill Sync Manager  v1.0.0          │' 'Cyan'
    Write-C '└──────────────────────────────────────────────┘' 'Cyan'
    Write-Host ''
    Write-Info "Workspace : $($script:WorkspaceRoot)"
    Write-Info "Config    : $(Get-ConfigPath)"
    Write-Host ''
}

# ============================================================
# 配置读写
# ============================================================
function Get-ConfigPath {
    Join-Path $script:WorkspaceRoot $script:ConfigFile
}

function Assert-ConfigExists {
    if (-not (Test-Path -LiteralPath (Get-ConfigPath))) {
        throw "配置文件不存在: $(Get-ConfigPath)（请先运行 init 初始化）"
    }
}

function Read-Config {
    $path = Get-ConfigPath
    if (-not (Test-Path -LiteralPath $path)) {
        throw "配置文件不存在: $path（请先运行 init 初始化）"
    }
    try {
        $raw = [IO.File]::ReadAllText($path, [Text.Encoding]::UTF8)
        $cfg = $raw | ConvertFrom-Json
    } catch {
        throw "配置文件解析失败（$path）: $($_.Exception.Message)。如配置损坏，可运行 init -Force 重建"
    }
    if (-not $cfg.PSObject.Properties['agents']) { $cfg | Add-Member -NotePropertyName 'agents' -NotePropertyValue @() }
    if (-not $cfg.PSObject.Properties['skills']) { $cfg | Add-Member -NotePropertyName 'skills' -NotePropertyValue @() }
    if ($null -eq $cfg.agents) { $cfg.agents = @() }
    if ($null -eq $cfg.skills) { $cfg.skills = @() }
    $cfg
}

function Write-Config {
    param([object]$Config)
    $path = Get-ConfigPath
    $json = $Config | ConvertTo-Json -Depth 8
    $enc  = New-Object System.Text.UTF8Encoding($true)
    [IO.File]::WriteAllText($path, $json, $enc)
}

# ============================================================
# 初始化
# ============================================================
function Initialize-Config {
    $path = Get-ConfigPath
    if (Test-Path -LiteralPath $path) {
        if (-not $Force) {
            throw "配置文件已存在: $path（如需重新生成请使用 init -Force）"
        }
        Write-Warn "覆盖现有配置: $path"
    }
    $cfg = [pscustomobject]@{
        version = 1
        agents  = @()
        skills  = @()
    }
    Write-Config $cfg
    Write-OK "已初始化配置文件: $path"
    Write-Info '下一步：agent add <名称> <Skills目录> 添加目标 Agent；scan 扫描注册 Skill；sync 建立链接'
}

# ============================================================
# Skill 清单操作
# ============================================================
function Scan-Skills {
    Assert-ConfigExists
    $cfg = Read-Config
    $found = @()
    Get-ChildItem -LiteralPath $script:WorkspaceRoot -Directory -Force |
        Where-Object { $_.Name -notlike '.*' } |
        ForEach-Object {
            if (Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md')) {
                $found += $_.Name
            }
        }
    $existing = @($cfg.skills | ForEach-Object { $_.name })
    $added = 0; $skipped = 0
    foreach ($name in ($found | Sort-Object)) {
        if ($existing -contains $name) { $skipped++; continue }
        $cfg.skills += [pscustomobject]@{ name = $name; enabled = $true }
        $added++
    }
    Write-Config $cfg
    Write-Info "扫描完成：发现 $($found.Count) 个 Skill（含 SKILL.md 的目录），新增 $added，已存在 $skipped"
}

function Add-Skill {
    param([string]$Name)
    Assert-ConfigExists
    if (-not $Name) { throw '用法：add <Skill名称>' }
    $src = Join-Path $script:WorkspaceRoot $Name
    if (-not (Test-Path -LiteralPath (Join-Path $src 'SKILL.md'))) {
        throw "Workspace 下不存在 Skill 目录: $src\SKILL.md（请先确认目录存在）"
    }
    $cfg = Read-Config
    if (@($cfg.skills | Where-Object { $_.name -ieq $Name }).Count -gt 0) {
        throw "Skill 已在清单中: $Name"
    }
    $cfg.skills += [pscustomobject]@{ name = $Name; enabled = $true }
    Write-Config $cfg
    Write-OK "已注册 Skill: $Name"
}

function Remove-Skill {
    param([string]$Name)
    Assert-ConfigExists
    if (-not $Name) { throw '用法：remove <Skill名称>' }
    $cfg = Read-Config
    $before = @($cfg.skills | Where-Object { $_.name -ieq $Name }).Count
    if ($before -eq 0) { throw "Skill 不在清单中: $Name" }
    $cfg.skills = @($cfg.skills | Where-Object { $_.name -ine $Name })
    if (-not $cfg.skills) { $cfg.skills = @() }
    Write-Config $cfg
    Write-OK "已移除 Skill: $Name（已存在的链接不会被自动删除，可用 unsync 清理）"
}

function Set-SkillEnabled {
    param([string]$Name, [bool]$Enabled)
    Assert-ConfigExists
    if (-not $Name) { throw '用法：enable|disable <Skill名称>' }
    $cfg = Read-Config
    $target = @($cfg.skills | Where-Object { $_.name -ieq $Name })
    if (-not $target) { throw "Skill 不在清单中: $Name" }
    $target[0].enabled = $Enabled
    Write-Config $cfg
    Write-OK "Skill '$Name' 已$(if ($Enabled) { '启用' } else { '禁用' })"
}

function Show-List {
    Assert-ConfigExists
    $cfg = Read-Config
    Write-Sect '── Skill Sync 清单 ──'
    Write-Info "配置文件 : $(Get-ConfigPath)"
    Write-Info "Workspace: $($script:WorkspaceRoot)"
    Write-Host ''
    $agents = @($cfg.agents)
    if ($agents) {
        Write-C "Agents ($($agents.Count)):" 'Gray'
        foreach ($a in $agents) {
            $mark = if ($a.enabled) { '[x]' } else { '[ ]' }
            $tail = if ($a.enabled) { '' } else { ' (已禁用)' }
            Write-C "  $mark $($a.name)$tail -> $($a.skillsDir)"
        }
    } else {
        Write-Warn 'Agents (0)：尚未配置，运行 agent add <名称> <Skills目录路径>'
    }
    Write-Host ''
    $skills = @($cfg.skills)
    if ($skills) {
        Write-C "Skills ($($skills.Count)):" 'Gray'
        foreach ($s in $skills) {
            $mark = if ($s.enabled) { '[x]' } else { '[ ]' }
            $tail = if ($s.enabled) { '' } else { ' (已禁用)' }
            Write-C "  $mark $($s.name)$tail"
        }
    } else {
        Write-Warn 'Skills (0)：尚未注册，运行 scan 自动扫描'
    }
}

# ============================================================
# Agent 操作
# ============================================================
function Add-Agent {
    param([string]$Name, [string]$Dir)
    Assert-ConfigExists
    if (-not $Name -or -not $Dir) { throw '用法：agent add <名称> <Skills目录路径>' }
    $cfg = Read-Config
    if (@($cfg.agents | Where-Object { $_.name -ieq $Name }).Count -gt 0) {
        throw "Agent 已存在: $Name"
    }
    $full = [IO.Path]::GetFullPath($Dir)
    $cfg.agents += [pscustomobject]@{ name = $Name; skillsDir = $full; enabled = $true }
    Write-Config $cfg
    Write-OK "已添加 Agent: $Name -> $full"
}

function Remove-Agent {
    param([string]$Name)
    Assert-ConfigExists
    if (-not $Name) { throw '用法：agent remove <名称>' }
    $cfg = Read-Config
    $before = @($cfg.agents | Where-Object { $_.name -ieq $Name }).Count
    if ($before -eq 0) { throw "Agent 不存在: $Name" }
    $cfg.agents = @($cfg.agents | Where-Object { $_.name -ine $Name })
    if (-not $cfg.agents) { $cfg.agents = @() }
    Write-Config $cfg
    Write-OK "已移除 Agent: $Name（其链接不会自动删除，可用 unsync 清理）"
}

function Set-AgentEnabled {
    param([string]$Name, [bool]$Enabled)
    Assert-ConfigExists
    if (-not $Name) { throw '用法：agent enable|disable <名称>' }
    $cfg = Read-Config
    $target = @($cfg.agents | Where-Object { $_.name -ieq $Name })
    if (-not $target) { throw "Agent 不存在: $Name" }
    $target[0].enabled = $Enabled
    Write-Config $cfg
    Write-OK "Agent '$Name' 已$(if ($Enabled) { '启用' } else { '禁用' })"
}

function List-Agents {
    Assert-ConfigExists
    $cfg = Read-Config
    $agents = @($cfg.agents)
    if (-not $agents) { Write-Warn '未配置任何 Agent（agent add <名称> <路径>）'; return }
    Write-Info "Agent 列表 ($($agents.Count)):"
    foreach ($a in $agents) {
        $mark = if ($a.enabled) { '[x]' } else { '[ ]' }
        $tail = if ($a.enabled) { '' } else { ' (已禁用)' }
        Write-C "  $mark $($a.name)$tail -> $($a.skillsDir)"
    }
}

# ============================================================
# 链接状态与同步
# ============================================================
function Normalize-Path {
    param([string]$Path)
    try { $full = [IO.Path]::GetFullPath($Path) } catch { return $Path }
    return $full.TrimEnd('\')
}

# 返回: Linked / Stale / Blocked / Missing / NoSource
function Get-LinkStatus {
    param([string]$LinkPath, [string]$SourcePath)
    if (-not (Test-Path -LiteralPath $SourcePath)) { return 'NoSource' }
    $item = Get-Item -LiteralPath $LinkPath -Force -ErrorAction SilentlyContinue
    if (-not $item) { return 'Missing' }
    if ($item.LinkType -eq 'Junction') {
        $t = Normalize-Path ([string]$item.Target)
        $s = Normalize-Path $SourcePath
        if ($t -ieq $s) { return 'Linked' }
        return 'Stale'
    }
    return 'Blocked'
}

function Sync-OneLink {
    param($Agent, $Skill, [switch]$ForceFlag)
    $link = Join-Path $Agent.skillsDir $Skill.name
    $src  = Join-Path $script:WorkspaceRoot $Skill.name
    $status = Get-LinkStatus $link $src
    switch ($status) {
        'Linked' { return 'Linked' }
        'Missing' {
            if (-not (Test-Path -LiteralPath $Agent.skillsDir)) {
                New-Item -ItemType Directory -Path $Agent.skillsDir -Force -ErrorAction Stop | Out-Null
            }
            New-Item -ItemType Junction -Path $link -Target $src -ErrorAction Stop | Out-Null
            return 'Created'
        }
        'Stale' {
            if ($ForceFlag) {
                Remove-Item -LiteralPath $link -Force -Recurse -ErrorAction Stop
                New-Item -ItemType Junction -Path $link -Target $src -ErrorAction Stop | Out-Null
                return 'Rebuilt'
            }
            return 'Stale'
        }
        'NoSource' { return 'NoSource' }
        default    { return 'Blocked' }
    }
}

function Sync-All {
    Assert-ConfigExists
    $cfg = Read-Config
    $agents = @($cfg.agents | Where-Object { $_.enabled })
    if (-not $agents) { throw '没有已启用的 Agent（agent add 添加，或 agent enable 启用）' }
    $skills = @($cfg.skills | Where-Object { $_.enabled })
    if (-not $skills) { throw '清单中没有已启用的 Skill（scan 扫描，或 add 注册）' }

    $total = 0; $ok = 0; $fail = 0
    foreach ($a in $agents) {
        Write-Sect "── 同步 Agent '$($a.name)' -> $($a.skillsDir) ──"
        foreach ($s in $skills) {
            $total++
            try {
                $r = Sync-OneLink $a $s -ForceFlag:$Force
                switch ($r) {
                    'Created' { $ok++; Write-OK   "  [LINK]    $($s.name)  已创建 Junction" }
                    'Linked'  { $ok++; Write-Dim  "  [SKIP]    $($s.name)  已链接且指向正确" }
                    'Rebuilt' { $ok++; Write-Warn "  [REBUILD] $($s.name)  已重建（原链接指向其他位置）" }
                    'Stale'   { $fail++; Write-Warn "  [STALE]   $($s.name)  链接指向其他位置，使用 sync -Force 重建" }
                    'Blocked' { $fail++; Write-Err "  [BLOCK]   $($s.name)  目标位置被真实目录/文件占用，跳过" }
                    'NoSource'{ $fail++; Write-Err "  [NOSRC]   $($s.name)  源目录不存在: $src" }
                    default   { $fail++; Write-Err "  [FAIL]    $($s.name)  未知状态: $r" }
                }
            } catch {
                $fail++
                Write-Err "  [FAIL]    $($s.name)  $($_.Exception.Message)"
            }
        }
    }
    Write-Host ''
    Write-Info "同步完成：共 $total 项，成功 $ok，失败 $fail"
    if ($fail -gt 0) { $script:ExitCode = 1 }
}

function Unsync-All {
    Assert-ConfigExists
    $cfg = Read-Config
    $targets = @()
    foreach ($a in @($cfg.agents | Where-Object { $_.enabled })) {
        foreach ($s in @($cfg.skills | Where-Object { $_.enabled })) {
            $link = Join-Path $a.skillsDir $s.name
            $item = Get-Item -LiteralPath $link -Force -ErrorAction SilentlyContinue
            if ($item -and $item.LinkType -eq 'Junction') {
                $targets += [pscustomobject]@{ Agent = $a.name; Link = $link; Target = $item.Target }
            }
        }
    }
    if (-not $targets) { Write-Info '没有需要清理的 Junction 链接'; return }

    Write-Warn "将删除 $($targets.Count) 个 Junction 链接（仅删除链接本身，不影响源目录）:"
    foreach ($t in $targets) { Write-Dim "  - $($t.Agent): $($t.Link)" }
    if (-not $Force) {
        $ans = Read-Host '确认删除？[y/N]'
        if ($ans -notmatch '^[yY]') { Write-Info '已取消'; return }
    }
    foreach ($t in $targets) {
        try {
            Remove-Item -LiteralPath $t.Link -Force -Recurse -ErrorAction Stop
            Write-OK "  [OK]  已删除: $($t.Link)"
        } catch {
            Write-Err "  [ERR] 删除失败: $($t.Link)  $($_.Exception.Message)"
            $script:ExitCode = 1
        }
    }
}

function Show-Status {
    Assert-ConfigExists
    $cfg = Read-Config
    Write-Sect '── 同步状态 ──'
    Write-Info "Workspace : $($script:WorkspaceRoot)"
    Write-Info "Config    : $(Get-ConfigPath)"
    Write-Host ''
    $agents = @($cfg.agents)
    if (-not $agents) { Write-Warn '未配置 Agent（agent add <名称> <路径>）' }
    foreach ($a in $agents) {
        $state = if ($a.enabled) { '启用' } else { '禁用' }
        Write-Sect "Agent '$($a.name)' [$state] -> $($a.skillsDir)"
        if (-not (Test-Path -LiteralPath $a.skillsDir)) {
            Write-Warn '  (目标目录不存在，sync 时将自动创建)'
        }
        $skills = @($cfg.skills)
        if (-not $skills) { Write-Dim '  (清单为空，先运行 scan)' }
        foreach ($s in $skills) {
            if (-not $s.enabled) { Write-Dim "  [OFF]    $($s.name)  (已禁用)"; continue }
            $link = Join-Path $a.skillsDir $s.name
            $st = Get-LinkStatus $link (Join-Path $script:WorkspaceRoot $s.name)
            switch ($st) {
                'Linked'  { Write-OK   "  [OK]     $($s.name)" }
                'Missing' { Write-Dim  "  [MISS]   $($s.name)  未链接" }
                'Stale'   {
                    $t = (Get-Item -LiteralPath $link -Force).Target
                    Write-Warn "  [STALE]  $($s.name)  指向其他位置: $t（sync -Force 可重建）"
                }
                'Blocked' { Write-Err  "  [BLOCK]  $($s.name)  被真实目录/文件占用" }
                'NoSource'{ Write-Err  "  [NOSRC]  $($s.name)  源目录不存在" }
            }
        }
        Write-Host ''
    }
}

# ============================================================
# 子命令路由
# ============================================================
function Invoke-AgentCommand {
    $sub = if ($Rest.Count -gt 0) { $Rest[0].ToLower() } else { '' }
    switch ($sub) {
        'add'     { Add-Agent $Rest[1] $Rest[2] }
        'remove'  { Remove-Agent $Rest[1] }
        'rm'      { Remove-Agent $Rest[1] }
        'enable'  { Set-AgentEnabled $Rest[1] $true }
        'disable' { Set-AgentEnabled $Rest[1] $false }
        'list'    { List-Agents }
        default   { throw '用法：agent <add|remove|rm|enable|disable|list> [...]' }
    }
}

function Invoke-CommandRouter {
    switch ($Command.ToLower()) {
        'init'    { Initialize-Config }
        'scan'    { Scan-Skills }
        'list'    { Show-List }
        'status'  { Show-Status }
        'sync'    { Sync-All }
        'unsync'  { Unsync-All }
        'clean'   { Unsync-All }
        'add'     { Add-Skill $Rest[0] }
        'remove'  { Remove-Skill $Rest[0] }
        'enable'  { Set-SkillEnabled $Rest[0] $true }
        'disable' { Set-SkillEnabled $Rest[0] $false }
        'agent'   { Invoke-AgentCommand }
        'menu'    { Show-Menu }
        default   { throw "未知命令: $Command" }
    }
}

# ============================================================
# 交互菜单
# ============================================================
function Show-Menu {
    Write-Banner
    while ($true) {
        Write-C '  1) 初始化配置 (init)'                 'Gray'
        Write-C '  2) 扫描并注册 Skill (scan)'          'Gray'
        Write-C '  3) Skill 清单 (list)'                'Gray'
        Write-C '  4) 同步状态 (status)'                'Gray'
        Write-C '  5) 同步全部链接 (sync)'              'Gray'
        Write-C '  6) 清理全部链接 (unsync)'            'Gray'
        Write-C '  7) 添加 Skill (add <名称>)'          'Gray'
        Write-C '  8) 移除 Skill (remove <名称>)'       'Gray'
        Write-C '  9) 添加 Agent (agent add <名称> <路径>)' 'Gray'
        Write-C '  A) 移除 Agent (agent remove <名称>)' 'Gray'
        Write-C '  B) Agent 列表 (agent list)'          'Gray'
        Write-C '  Q) 退出'                             'Gray'
        Write-Host ''
        $choice = ''
        try {
            $choice = (Read-Host '请选择').Trim().ToLower()
        } catch {
            Write-Err '无法读取输入（非交互环境请使用子命令模式，如 sync、status）'
            exit 1
        }
        $script:ExitCode = 0
        try {
            switch ($choice) {
                '1' { Initialize-Config }
                '2' { Scan-Skills }
                '3' { Show-List }
                '4' { Show-Status }
                '5' { Sync-All }
                '6' { Unsync-All }
                '7' {
                    $n = (Read-Host 'Skill 名称').Trim()
                    Add-Skill $n
                }
                '8' {
                    $n = (Read-Host 'Skill 名称').Trim()
                    Remove-Skill $n
                }
                '9' {
                    $n = (Read-Host 'Agent 名称').Trim()
                    $d = (Read-Host 'Skills 目录路径').Trim()
                    Add-Agent $n $d
                }
                'a' {
                    $n = (Read-Host 'Agent 名称').Trim()
                    Remove-Agent $n
                }
                'b' { List-Agents }
                'q' { Write-Info '再见'; return }
                default { Write-Err "无效选择: $choice" }
            }
        } catch {
            Write-Err "操作失败: $($_.Exception.Message)"
            $script:ExitCode = 1
        }
        if ($choice -ne 'q') {
            Write-Host ''
            try { Read-Host '按回车键继续...' | Out-Null } catch { exit 1 }
        }
    }
}

# ============================================================
# 主入口
# ============================================================
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$OutputEncoding = [System.Text.Encoding]::UTF8

try {
    if ($PSVersionTable.PSVersion.Major -lt 5) {
        throw "需要 PowerShell 5.0+（当前 $($PSVersionTable.PSVersion)，Junction 创建依赖此版本）"
    }

    if ($Workspace) {
        $script:WorkspaceRoot = [IO.Path]::GetFullPath($Workspace)
        if (-not (Test-Path -LiteralPath $script:WorkspaceRoot)) {
            throw "Workspace 不存在: $script:WorkspaceRoot"
        }
    } else {
        if (-not $PSScriptRoot) {
            throw '无法确定脚本所在目录，请使用 -Workspace 显式指定 Workspace 根目录'
        }
        $script:WorkspaceRoot = [IO.Path]::GetFullPath($PSScriptRoot)
    }

    $script:UseColor = (-not $NoColor) -and (-not $env:NO_COLOR)

    if (-not $Command) {
        Show-Menu
    } else {
        Invoke-CommandRouter
    }
    exit $script:ExitCode
} catch {
    Write-Err "错误: $($_.Exception.Message)"
    if ($_.Exception.InnerException) { Write-Err "  原因: $($_.Exception.InnerException.Message)" }
    exit 1
}
