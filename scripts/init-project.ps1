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

# 占位符清单（唯一真相源：scripts/placeholders.json，见 placeholder-utils.ps1）
. (Join-Path $PSScriptRoot "placeholder-utils.ps1")

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
Get-ChildItem $template -Force | Where-Object { $_.Name -notin @(".git", "logs", ".claude", ".codegraph", ".qoder", ".coverage") } | ForEach-Object {
    Copy-Item $_.FullName $Target -Recurse -Force
}
# 清理被复制进来的垃圾/构建目录（__pycache__/bin/obj 等不入库，也不应进入新项目；
# 清单与 init-project.py 的 CLEANUP_DIRS 对齐）
foreach ($junk in @("__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".venv", "venv", "env", "node_modules", "bin", "obj", "dist", "TestResults")) {
    Get-ChildItem $Target -Recurse -Force -Directory -Filter $junk -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force
}
Write-Host "    完成（已跳过 .git / logs / .claude / __pycache__ 等）" -ForegroundColor Green

# ----------------------------------------------------------------------------
# 2.5 删除标记的模板专属段落（README 的「从本模板初始化新项目」等不进入新项目）
# ----------------------------------------------------------------------------
# 与 init-project.py 的 TEMPLATE_ONLY 标记对齐：HTML 注释圈定段落边界，初始化时
# 整体删除。在占位符扫描前执行，被删段落内的 {{...}} 示例不计入下游替换清单。
# 跳过 tests/（扫描夹具目录，与 py 版对齐）；写回保留原文件 BOM 状态。
$startMarker = '<!-- TEMPLATE_ONLY_START -->'
$endMarker   = '<!-- TEMPLATE_ONLY_END -->'
Get-ChildItem $Target -Recurse -File -Force | Where-Object {
    $_.Extension -eq ".md" -and $_.FullName -notmatch "\\(tests)\\" -and $_.FullName -notmatch "\\.git\\"
} | ForEach-Object {
    $content = Get-Content $_.FullName -Encoding UTF8 -Raw
    $new = $content
    while ($true) {
        $i = $new.IndexOf($startMarker)
        if ($i -lt 0) { break }
        # 深度计数找配对 END：段内文档若引用了标记字面量（成对出现）视为嵌套而非真实边界
        $depth = 1
        $pos = $i + $startMarker.Length
        $endPos = -1
        while ($depth -gt 0) {
            $nextS = $new.IndexOf($startMarker, $pos)
            $nextE = $new.IndexOf($endMarker, $pos)
            if ($nextE -lt 0) { break }  # 未闭合
            if ($nextS -ge 0 -and $nextS -lt $nextE) {
                $depth++      # 段内 START 字面量 → 深度 +1
                $pos = $nextS + $startMarker.Length
            } else {
                $depth--      # END：深度回到 0 才视为真实段落边界
                $endPos = $nextE
                $pos = $nextE + $endMarker.Length
            }
        }
        if ($endPos -lt 0) {
            Write-Host "  [WARN] $($_.Name) 含未闭合 TEMPLATE_ONLY 标记（仅 START），段落保留" -ForegroundColor Yellow
            break
        }
        $j = $endPos + $endMarker.Length
        # 吞掉 END 标记所在行末尾的换行（最多一个 CRLF 或两个换行符，与 py 版对齐）
        if ($j -lt $new.Length -and ($new[$j] -eq "`r" -or $new[$j] -eq "`n")) {
            $j++
            if ($j -lt $new.Length -and $new[$j] -eq "`n") { $j++ }
        }
        $new = $new.Substring(0, $i) + $new.Substring($j)
    }
    if ($new -ne $content) {
        # 裁剪文件尾部多余空行，保留最后一行内容的行尾风格（CRLF/LF 不变）
        $trimmed = $new.TrimEnd("`t`r`n ")
        if ($trimmed.Length -eq 0) {
            $new = $content  # 整文件为空白：不改写
        } else {
            $rest = $new.Substring($trimmed.Length)
            $nlIdx = $rest.IndexOf("`n")
            if ($nlIdx -lt 0) {
                $new = $trimmed + "`n"  # 尾部无换行：补一个 LF
            } else {
                $term = if ($nlIdx -gt 0 -and $rest.Substring($nlIdx - 1, 1) -eq "`r") { "`r`n" } else { "`n" }
                $new = $trimmed + $term
            }
        }
        if ($new -ne $content) {
            # 写回时保留原文件 BOM 状态（.ps1 必须 UTF-8 with BOM，否则 PowerShell 5.1 中文解析失败）
            $bytes = [System.IO.File]::ReadAllBytes($_.FullName)
            $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
            $enc = if ($hasBom) { New-Object System.Text.UTF8Encoding $true }
                   else { New-Object System.Text.UTF8Encoding $false }
            [System.IO.File]::WriteAllText($_.FullName, $new, $enc)
            Write-Host "  ==> 已删除 $($_.Name) 中的模板专属段落" -ForegroundColor Green
        }
    }
}

# ----------------------------------------------------------------------------
# 3. 扫描 {{...}} 占位符
# ----------------------------------------------------------------------------
$placeholderRe = [regex]::new("\{\{([A-Z0-9_]+)\}\}")
$found = @{}
# -Force：pwsh 7 的 Get-ChildItem -Recurse 不递归 .github 等隐藏目录，漏扫会导致 CI 下占位符未替换
# 跳过 tests/：测试夹具 token（{{A}}/{{B}}/{{FOO}} 等）是 scanner 测试输入，不能被替换或计入未替换检查（与 init-project.py 的 SKIP_PLACEHOLDER_DIRS 对齐）
Get-ChildItem $Target -Recurse -File -Force | Where-Object {
    $_.Extension -notin @(".dll", ".exe", ".pdb") -and $_.FullName -notmatch "[\\/]tests([\\/]|$)"
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
    # 4. 按 manifest 分派填充缺失的占位符（唯一真相源：scripts/placeholders.json）
    #    core    → 交互询问（缺之项目/CI 不可用）
    #    auto    → 自动计算（DATE/YEAR，不询问）
    #    content → 占位符名小写自动占位（开发期填写文档时替换）
    #    未登记   → 按 content 处理 + 告警（双向漂移守护）
    # ----------------------------------------------------------------------------
    $manifest = Get-PlaceholderManifest
    $missing = @($found.Keys | Where-Object { -not $Values.ContainsKey("{{$_}}") } | Sort-Object)
    if ($missing.Count -gt 0) {
        Write-Host "    提示：内容类占位符自动用占位符名占位（初始化后人工完善）；以下核心值请手动输入。" -ForegroundColor Yellow
    }
    $autoFilled = 0
    $warnUndeclared = @()
    foreach ($name in $missing) {
        $meta = $manifest[$name]
        if (-not $meta) {
            # 未在 manifest 登记：按 content 处理并告警（新增占位符需补充 placeholders.json）
            $Values["{{$name}}"] = $name.ToLowerInvariant()
            $warnUndeclared += $name
            $autoFilled++
            continue
        }
        switch ($meta.category) {
            "auto" {
                switch ($meta.rule) {
                    "today" { $Values["{{$name}}"] = Get-Date -Format "yyyy-MM-dd" }
                    "year"  { $Values["{{$name}}"] = (Get-Date).Year.ToString() }
                    default { $Values["{{$name}}"] = $name.ToLowerInvariant() }
                }
                break
            }
            "content" {
                $Values["{{$name}}"] = $name.ToLowerInvariant()
                $autoFilled++
                break
            }
            "core" {
                $default = if ($meta.default) { $meta.default } else { $name.ToLowerInvariant() }
                $prompt  = if ($meta.prompt) { $meta.prompt } else { "请输入 $name" }
                $answer = Read-Host "    $prompt（Enter 用默认: $default）"
                if ([string]::IsNullOrWhiteSpace($answer)) { $answer = $default }
                $Values["{{$name}}"] = $answer
                break
            }
        }
    }
    if ($warnUndeclared.Count -gt 0) {
        Write-Host "    [WARN] 以下占位符未在 placeholders.json 登记（已按内容类占位，请补充 manifest）：$($warnUndeclared -join ', ')" -ForegroundColor Yellow
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
    # 防御性跳过 tests/（扫描已排除，此处双保险，避免路径来源差异引入夹具文件）
    $files = @($files | Where-Object { $_ -notmatch "[\\/]tests([\\/]|$)" } | Sort-Object -Unique)
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
# -Force：同上，避免漏扫隐藏目录中的未替换占位符（如 .github/workflows/*.yml）
# 跳过 tests/：测试夹具 token 不应计入"未替换"（与扫描/替换对齐，见步骤 3）
Get-ChildItem $Target -Recurse -File -Force | Where-Object {
    $_.Extension -notin @(".dll", ".exe", ".pdb") -and $_.FullName -notmatch "[\\/]tests([\\/]|$)"
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
    # commit-msg 校验 hook：scripts/git-hooks/commit-msg（见 CONTRIBUTING「提交规范」）
    git config core.hooksPath scripts/git-hooks 2>$null | Out-Null
    Pop-Location
    Write-Host "==> 已执行 git init（commit-msg 校验 hook 已启用）" -ForegroundColor Green
}

if ($CreateCompatibilityLinks) {
    # 主文件为 AGENTS.md（大写，Codex/Copilot/Windsurf 等直接读取）；仅为 Claude Code 创建副本
    Copy-Item "$Target\AGENTS.md" "$Target\CLAUDE.md" -Force
    Write-Host "==> 已创建 CLAUDE.md（AGENTS.md 副本，供 Claude Code 读取）" -ForegroundColor Green
    Write-Host "    （注意：AGENTS.md 后续更新需重新创建 CLAUDE.md 副本，见 AGENTS.md「AGENTS.md 生态兼容」）" -ForegroundColor Yellow
}

Write-Host "`n==> 初始化完成，全部占位符已替换 ✔" -ForegroundColor Green
exit 0
