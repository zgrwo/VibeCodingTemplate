# ============================================================================
# init-project.ps1 — 从 _template 初始化新项目
#
# 职责：
#   1. 复制 template 到目标目录（跳过 .git / logs）
#   2. 扫描文档中的 {{...}} 占位符
#   3. 交互式（默认）或 -Values 参数式替换占位符
#   4. 输出未替换占位符清单（防止遗漏导致文档断链）
#   5. 可选：git init / 创建 CLAUDE.md 兼容副本（AGENTS.md 即主文件）
#
# 用法：
#   .\scripts\init-project.ps1 -Target d:\Workspace\zgrwo\MyNewProject
#   .\scripts\init-project.ps1 -Target d:\...\MyNewProject `
#       -Values @{ "PROJECT_NAME" = "MyNewProject"; "VERSION" = "1.0.0" } `
#       -GitInit -CreateCompatibilityLinks
#
# 注意：-Values 的 key 可带或不带花括号（自动归一化），如：
#       @{ "PROJECT_NAME" = "MyNewProject" } 即可，无需手动加双花括号。
#
# 退出码：0 = 全部占位符已替换；1 = 存在未替换占位符（仍可继续开发，但需人工处理）
# ============================================================================
param(
    [Parameter(Mandatory = $true)]
    [string]$Target,
    [hashtable]$Values = @{},
    [switch]$Force,
    [switch]$GitInit,
    [switch]$CreateCompatibilityLinks
)

$ErrorActionPreference = "Stop"
$template = Split-Path -Parent $PSScriptRoot   # template 根目录（scripts/ 的上一级）

# ----------------------------------------------------------------------------
# 0. 归一化 -Values：key 统一为 {{键名}} 形式（兼容带/不带大括号两种写法）
# ----------------------------------------------------------------------------
$normalized = @{}
foreach ($k in $Values.Keys) {
    $key = "$k"
    if ($key -notmatch "^\{\{") { $key = "{{" + $key + "}}" }
    $normalized[$key] = $Values[$k]
}
$Values = $normalized

# ----------------------------------------------------------------------------
# 1. 校验目标目录
# ----------------------------------------------------------------------------
if (-not $Force -and (Test-Path $Target) -and (Get-ChildItem $Target -Force | Select-Object -First 1)) {
    throw "目标目录非空：$Target（如确需覆盖请加 -Force）"
}

# ----------------------------------------------------------------------------
# 2. 复制 template（跳过 .git 与日志/构建产物/AI 工具本地目录）
# ----------------------------------------------------------------------------
Write-Host "==> 复制 template → $Target" -ForegroundColor Cyan
if (Test-Path $Target) { Get-ChildItem $Target -Force | Remove-Item -Recurse -Force }
New-Item -ItemType Directory -Path $Target -Force | Out-Null
# .claude/.codegraph/.qoder 为 AI 工具本地目录（.gitignore 已忽略，不应进入新项目，
# 否则开发者本地 AI 设置随初始化泄漏，且 verify-docs.py --strict 会将其视为未声明目录）
Get-ChildItem $template -Force | Where-Object { $_.Name -notin @(".git", "logs", ".claude", ".codegraph", ".qoder") } | ForEach-Object {
    Copy-Item $_.FullName $Target -Recurse -Force
}
# 清理被复制进来的垃圾/构建目录（__pycache__/bin/obj 等不入库，也不应进入新项目）
foreach ($junk in @("__pycache__", ".venv", "node_modules", "bin", "obj")) {
    Get-ChildItem $Target -Recurse -Force -Directory -Filter $junk -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force
}
Write-Host "    完成（已跳过 .git / logs / .claude / __pycache__ 等）" -ForegroundColor Green

# ----------------------------------------------------------------------------
# 3. 扫描 {{...}} 占位符
# ----------------------------------------------------------------------------
$placeholderRe = [regex]::new("\{\{([A-Z0-9_]+)\}\}")
$found = @{}
Get-ChildItem $Target -Recurse -File | Where-Object {
    $_.Extension -notin @(".dll", ".exe", ".pdb")
} | ForEach-Object {
    $content = Get-Content $_.FullName -Encoding UTF8 -Raw -ErrorAction SilentlyContinue
    if ($content) {
        foreach ($m in $placeholderRe.Matches($content)) {
            $name = $m.Groups[1].Value
            if (-not $found.ContainsKey($name)) { $found[$name] = @() }
            $found[$name] += $_.FullName
        }
    }
}

if ($found.Count -eq 0) {
    Write-Host "==> 未发现占位符，无需替换" -ForegroundColor Green
} else {
    Write-Host "`n==> 发现 $($found.Count) 个占位符：" -ForegroundColor Cyan
    $found.Keys | Sort-Object | ForEach-Object { Write-Host "    {{$_}}  ($($found[$_].Count) 处)" }

    # ----------------------------------------------------------------------------
    # 4. 交互式填充缺失的占位符
    # ----------------------------------------------------------------------------
    $missing = @($found.Keys | Where-Object { -not $Values.ContainsKey("{{$_}}") } | Sort-Object)
    if ($missing.Count -gt 0) {
        Write-Host "    提示：内容填充类占位符将自动用占位符名占位（初始化后人工完善）；以下核心值请手动输入。" -ForegroundColor Yellow
    }
    # 核心键：替换为占位符名会导致文档/CI 不可用，必须在初始化时由用户提供
    # 其余内容占位符（用户手册/规格/FAQ 等）自动用占位符名小写占位，初始化后填写文档时一并替换
    $coreKeys = @(
        "PROJECT_NAME", "OWNER", "REPO_NAME", "AUTHOR",
        "SECURITY_CONTACT", "COC_CONTACT",
        "BUILD_CMD", "TEST_CMD", "FULL_VERIFY_CMD", "LINT_CMD", "COVERAGE_CMD"
    )
    $autoFilled = 0
    foreach ($name in $missing) {
        if ($name -notin $coreKeys -and $name -notin @("VERSION", "DATE", "YEAR")) {
            $Values["{{$name}}"] = $name.ToLowerInvariant()
            $autoFilled++
            continue
        }
        $default = switch ($name) {
            "VERSION" { "1.0.0" }
            "DATE" { Get-Date -Format "yyyy-MM-dd" }
            "YEAR" { (Get-Date).Year.ToString() }
            # 核心键：Enter 用占位符名小写（初始化后需人工确认替换）
            default { $name.ToLowerInvariant() }
        }
        $answer = Read-Host "    请输入 {{$name}} 的值（Enter 用默认: $default）"
        if ([string]::IsNullOrWhiteSpace($answer)) { $answer = $default }
        $Values["{{$name}}"] = $answer
    }
    if ($autoFilled -gt 0) {
        Write-Host "    （$autoFilled 个内容占位符已自动用占位符名占位，初始化后在文档填写时替换）" -ForegroundColor Yellow
    }

    # ----------------------------------------------------------------------------
    # 5. 执行替换
    # ----------------------------------------------------------------------------
    $replaced = 0
    # 展平 $found.Values（每个占位符的值是路径数组 → 合并为路径列表），去重后逐文件替换
    $files = @()
    foreach ($paths in $found.Values) {
        foreach ($p in $paths) { $files += $p }
    }
    $files = @($files | Sort-Object -Unique)
    foreach ($file in $files) {
        $content = Get-Content $file -Encoding UTF8 -Raw
        $new = $content
        foreach ($key in $Values.Keys) {
            $new = $new.Replace($key, [string]$Values[$key])
        }
        if ($new -ne $content) {
            # 写回时保留原文件 BOM 状态（.ps1 必须 UTF-8 with BOM，否则 PowerShell 5.1 中文解析失败）
            $bytes = [System.IO.File]::ReadAllBytes($file)
            $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
            $enc = if ($hasBom) { New-Object System.Text.UTF8Encoding $true }
                   else { New-Object System.Text.UTF8Encoding $false }
            [System.IO.File]::WriteAllText($file, $new, $enc)
            $replaced++
        }
    }
    Write-Host "`n==> 已更新 $replaced 个文件" -ForegroundColor Green
}

# ----------------------------------------------------------------------------
# 5.5 重置 CHANGELOG 为新项目初始态（模板自身的变更历史不属于新项目）
# ----------------------------------------------------------------------------
# 拼接生成占位符键，避免源文件内 `{{PROJECT_NAME}}` 字面量被自扫描替换为实际项目名后，
# 该副本再次运行时 ContainsKey 查不到原键（回退目录名，通常恰好一致故低危，但应防患）
$projectNameKey = "{{" + "PROJECT_NAME" + "}}"
$projName = if ($Values.ContainsKey($projectNameKey)) { $Values[$projectNameKey] } else { (Split-Path $Target -Leaf) }
$changelogInit = @"
# Changelog

All notable changes to $projName.

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

> 新项目初始状态：首个功能落地后在此登记变更。
"@
[System.IO.File]::WriteAllText("$Target\CHANGELOG.md", $changelogInit, (New-Object System.Text.UTF8Encoding $true))
Write-Host "==> CHANGELOG.md 已重置为新项目初始态" -ForegroundColor Green

# ----------------------------------------------------------------------------
# 6. 报告未替换占位符
# ----------------------------------------------------------------------------
$remaining = @{}
Get-ChildItem $Target -Recurse -File | Where-Object {
    $_.Extension -notin @(".dll", ".exe", ".pdb")
} | ForEach-Object {
    $content = Get-Content $_.FullName -Encoding UTF8 -Raw -ErrorAction SilentlyContinue
    if ($content) {
        foreach ($m in $placeholderRe.Matches($content)) {
            if (-not $remaining.ContainsKey($m.Groups[1].Value)) { $remaining[$m.Groups[1].Value] = @() }
            $remaining[$m.Groups[1].Value] += (Split-Path $_.FullName -Leaf)
        }
    }
}
if ($remaining.Count -gt 0) {
    Write-Host "`n[警告] 以下占位符未替换（请人工处理）：" -ForegroundColor Yellow
    $remaining.Keys | Sort-Object | ForEach-Object { Write-Host "    {{$_}} → $($remaining[$_] -join ', ')" }
    exit 1
}

# ----------------------------------------------------------------------------
# 7. 可选收尾：git init / CLAUDE.md 兼容副本
# ----------------------------------------------------------------------------
if ($GitInit) {
    Push-Location $Target
    git init 2>$null | Out-Null
    Pop-Location
    Write-Host "==> 已执行 git init（请按需添加首次 commit）" -ForegroundColor Green
}

if ($CreateCompatibilityLinks) {
    # 主文件为 AGENTS.md（大写，Codex/Copilot/Windsurf 等直接读取）；仅为 Claude Code 创建副本
    Copy-Item "$Target\AGENTS.md" "$Target\CLAUDE.md" -Force
    Write-Host "==> 已创建 CLAUDE.md（AGENTS.md 副本，供 Claude Code 读取）" -ForegroundColor Green
    Write-Host "    （注意：AGENTS.md 后续更新需重新创建 CLAUDE.md 副本，见 AGENTS.md「AGENTS.md 生态兼容」）" -ForegroundColor Yellow
}

Write-Host "`n==> 初始化完成，全部占位符已替换 ✔" -ForegroundColor Green
exit 0
