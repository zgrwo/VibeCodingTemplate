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
# 目标必须是目录（非文件）：-Force 会把文件静默删除并替换成目录，镜像 init-project.py 的拒绝。
if (Test-Path -LiteralPath $Target -PathType Leaf) {
    throw "目标路径是文件，不是目录：$Target"
}
# 目标是符号链接/junction（重解析点）时拒绝：词法 GetFullPath 无法解析重解析点，穿透链接删除
# 会摧毁链接指向的真实文件（镜像 init-project.py 物理 Path.resolve() 的语义）。
if (Test-Path -LiteralPath $Target) {
    $targetItem = Get-Item -LiteralPath $Target -Force
    if ($targetItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        throw "目标路径是符号链接/junction（重解析点）：$Target（请使用实际目录，防穿透删除）"
    }
}
if (-not $Force -and (Test-Path -LiteralPath $Target) -and (Get-ChildItem -LiteralPath $Target -Force | Select-Object -First 1)) {
    throw "目标目录非空：$Target（如确需覆盖请加 -Force）"
}

# target 不能等于模板根、在模板仓库内、或是模板仓库的祖先：下方 Remove-Item 会先递归删除
# 目标内容，若目标是模板祖先会连模板仓库（含 .git）与所有同级项目一并删除（防自删除）。
# 比较按平台大小写语义（Windows 不敏感 / Linux 敏感），镜像 init-project.py 的物理路径守卫。
try {
    $resolvedTarget   = [System.IO.Path]::GetFullPath($Target)
    $resolvedTemplate = [System.IO.Path]::GetFullPath($template)
} catch {
    throw "目标路径无效：$Target（$($_.Exception.Message)）"
}
# 注意：勿用 $IsWindows——它是 PowerShell Core 的只读自动变量，赋值会抛「read-only」错误
$onWindows     = ([System.IO.Path]::DirectorySeparatorChar -eq '\')
$comparison    = if ($onWindows) { [System.StringComparison]::OrdinalIgnoreCase } else { [System.StringComparison]::Ordinal }
$sep           = [System.IO.Path]::DirectorySeparatorChar
$equalOrInside = [string]::Equals($resolvedTarget, $resolvedTemplate, $comparison) -or
                 $resolvedTarget.StartsWith($resolvedTemplate + $sep, $comparison)
$isAncestor    = $resolvedTemplate.StartsWith($resolvedTarget + $sep, $comparison)
if ($equalOrInside -or $isAncestor) {
    throw "target 不能在模板仓库内、等于模板根或包含模板仓库：$Target"
}

# ----------------------------------------------------------------------------
# 2. 复制 template（跳过 .git 与日志/构建产物/AI 工具本地目录）
# ----------------------------------------------------------------------------
Write-Host "==> 复制 template → $Target" -ForegroundColor Cyan
if (Test-Path -LiteralPath $Target) { Get-ChildItem -LiteralPath $Target -Force | Remove-Item -Recurse -Force }
[System.IO.Directory]::CreateDirectory($Target) | Out-Null
# .claude/.codegraph/.qoder 为 AI 工具本地目录（.gitignore 已忽略，不应进入新项目，
# 否则开发者本地 AI 设置随初始化泄漏，且 verify-docs.py --strict 会将其视为未声明目录）
Get-ChildItem -LiteralPath $template -Force | Where-Object { $_.Name -notin @(".git", "logs", ".claude", ".codegraph", ".qoder", ".coverage") } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Target -Recurse -Force
}
# 清理被复制进来的垃圾/构建目录（__pycache__/bin/obj 等不入库，也不应进入新项目；
# 清单与 init-project.py 的 CLEANUP_DIRS 对齐）
foreach ($junk in @("__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".venv", "venv", "env", "node_modules", "bin", "obj", "dist", "TestResults")) {
    Get-ChildItem -LiteralPath $Target -Recurse -Force -Directory -Filter $junk -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force
}
Write-Host "    完成（已跳过 .git / logs / .claude / __pycache__ 等）" -ForegroundColor Green
if (Test-Path (Join-Path $Target "examples")) {
    # P6 审查修复：examples/ 为参考示例，明确告知去向（不需要可删除，
    # 删除后需同步 project-structure.md/AGENTS.md 目录树，否则 verify-docs --strict 报未声明/缺失）
    Write-Host "    [提示] examples/ 示例项目已复制（参考用途：演示多语言 Core/CrossVal/测试写法，不需要可整体删除；删除后请同步 rules/project-structure.md 与 AGENTS.md 目录树）" -ForegroundColor Yellow
}

# ----------------------------------------------------------------------------
# 2.5 删除标记的模板专属段落（README 的「从本模板初始化新项目」等不进入新项目）
# ----------------------------------------------------------------------------
# 与 init-project.py 的 TEMPLATE_ONLY 标记对齐：HTML 注释圈定段落边界，初始化时
# 整体删除。在占位符扫描前执行，被删段落内的 {{...}} 示例不计入下游替换清单。
# 跳过 tests/（扫描夹具目录，与 py 版对齐）；写回保留原文件 BOM 状态。
$startMarker = '<!-- TEMPLATE_ONLY_START -->'
$endMarker   = '<!-- TEMPLATE_ONLY_END -->'
Get-ChildItem -LiteralPath $Target -Recurse -File -Force | Where-Object {
    $_.Extension -eq ".md" -and $_.FullName -notmatch "[\\/]tests([\\/]|$)" -and $_.FullName -notmatch "[\\/]\.git([\\/]|$)"
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
Get-ChildItem -LiteralPath $Target -Recurse -File -Force | Where-Object {
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
                $default = $meta.default  # 可能为 $null（无 manifest 默认值）
                if (-not $default -and [Console]::IsInputRedirected) {
                    throw "非交互模式下 core 占位符 {{$name}} 无默认值：请通过 -Values 提供（如 -Values @{ $name = '...' }）"
                }
                $fallback = if ($default) { $default } else { $name.ToLowerInvariant() }
                $prompt   = if ($meta.prompt) { $meta.prompt } else { "请输入 $name" }
                $answer = Read-Host "    $prompt（Enter 用默认: $fallback）"
                if ([string]::IsNullOrWhiteSpace($answer)) { $answer = $fallback }
                $Values["{{$name}}"] = $answer
                break
            }
            default {
                # manifest 条目缺/错 category：按 content 处理并告警（镜像 init-project.py 的 entry.get('category', 'content')）
                Write-Host "    [WARN] 占位符 $name 的 category 无效（'$($meta.category)'），已按 content 处理，请修正 placeholders.json" -ForegroundColor Yellow
                $Values["{{$name}}"] = $name.ToLowerInvariant()
                $autoFilled++
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
        # 单趟替换：对原内容每个 {{...}} 匹配查表替换，值内若含其他占位符不会被二次展开
        # （镜像 init-project.py 的 pattern.sub 语义，避免 hashtable 遍历顺序造成输出不确定）。
        $new = $placeholderRe.Replace($content, {
            param($m)
            $k = "{{" + $m.Groups[1].Value + "}}"
            if ($Values.ContainsKey($k)) { return [string]$Values[$k] }
            return $m.Value
        })
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
[System.IO.File]::WriteAllText((Join-Path $Target "CHANGELOG.md"), $changelogInit, (New-Object System.Text.UTF8Encoding $true))
Write-Host "==> CHANGELOG.md 已重置为新项目初始态" -ForegroundColor Green

# ----------------------------------------------------------------------------
# 5.6 重置 .release-please-manifest.json 为新项目初始版本（模板自身的发布版本不属于新项目）
# ----------------------------------------------------------------------------
# 与 _reset_changelog 同理（P4 审查修复）：模板仓库 manifest 携带自身发布版本（如 0.1.2），
# 直接复制会使新项目 manifest 与 pyproject.toml（{{VERSION}}）版本漂移，
# 触发 verify-docs.py 版本一致性门禁。
$manifestPath = Join-Path $Target ".release-please-manifest.json"
if (Test-Path $manifestPath) {
    $versionKey = "{{" + "VERSION" + "}}"
    $version = if ($Values.ContainsKey($versionKey)) { [string]$Values[$versionKey] } else { "0.1.0" }
    $manifestJson = @{ "." = $version } | ConvertTo-Json
    [System.IO.File]::WriteAllText($manifestPath, $manifestJson, (New-Object System.Text.UTF8Encoding $true))
    Write-Host "==> .release-please-manifest.json 已重置为版本 $version" -ForegroundColor Green

    # 5.6.1 将复制进新项目的根 pyproject.toml 版本号重置为 VERSION 值（与 _reset_release_manifest 同理，
    # 防新项目版本漂移触发 verify-docs.py 版本一致性门禁，P4 修复）
    $pyProjectPath = Join-Path $Target "pyproject.toml"
    if (Test-Path $pyProjectPath) {
        $pyText = Get-Content $pyProjectPath -Encoding UTF8 -Raw
        $newPyText = $pyText -replace '(?m)^version\s*=\s*"[^"]+"', "version = `"$version`""
        if ($newPyText -ne $pyText) {
            [System.IO.File]::WriteAllText($pyProjectPath, $newPyText, (New-Object System.Text.UTF8Encoding $true))
            Write-Host "==> pyproject.toml 版本号已重置为 $version" -ForegroundColor Green
        }
    }

    # 5.6.2 裁剪生成项目 placeholders.json：仅保留替换后仍被引用的条目（防死条目门禁 FAIL）。
    # 初始化后全部已登记占位符都被替换（如 {{YEAR}} 在 LICENSE），manifest 原样复制会让
    # 生成项目每次跑 verify-registries 都报死条目 FAIL（下游 quality-gate 恒红，审查修复）。
    $phPath = Join-Path $Target (Join-Path "scripts" "placeholders.json")
    if (Test-Path $phPath) {
        $phData = Get-Content $phPath -Encoding UTF8 -Raw | ConvertFrom-Json
        if ($phData -and $phData.placeholders) {
            $referenced = @{}
            Get-ChildItem -LiteralPath $Target -Recurse -File -Force | Where-Object {
                $_.Extension -notin @(".pyc", ".dll", ".exe", ".pdb") -and $_.FullName -notmatch "[\\/]tests([\\/]|$)"
            } | ForEach-Object {
                $content = Get-Content $_.FullName -Encoding UTF8 -Raw -ErrorAction SilentlyContinue
                if ($content) {
                    foreach ($m in $placeholderRe.Matches($content)) { $referenced[$m.Groups[1].Value] = $true }
                }
            }
            $kept = @{}
            foreach ($prop in $phData.placeholders.PSObject.Properties) {
                if ($referenced.ContainsKey($prop.Name)) { $kept[$prop.Name] = $prop.Value }
            }
            if ($kept.Count -ne $phData.placeholders.PSObject.Properties.Count) {
                $pruned = @{ schema_version = $phData.schema_version; placeholders = $kept }
                [System.IO.File]::WriteAllText($phPath, ($pruned | ConvertTo-Json -Depth 5), (New-Object System.Text.UTF8Encoding $true))
                Write-Host "==> scripts/placeholders.json 已裁剪（仅保留替换后仍被引用的条目）" -ForegroundColor Green
            }
        }
    }
}

# ----------------------------------------------------------------------------
# 6. 报告未替换占位符
# ----------------------------------------------------------------------------
$remaining = @{}
# -Force：同上，避免漏扫隐藏目录中的未替换占位符（如 .github/workflows/*.yml）
# 跳过 tests/：测试夹具 token 不应计入"未替换"（与扫描/替换对齐，见步骤 3）
Get-ChildItem -LiteralPath $Target -Recurse -File -Force | Where-Object {
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
$hasRemaining = $false
if ($remaining.Count -gt 0) {
    Write-Host "`n[警告] 以下占位符未替换（请人工处理）：" -ForegroundColor Yellow
    $remaining.Keys | Sort-Object | ForEach-Object { Write-Host "    {{$_}} → $($remaining[$_] -join ', ')" }
    # 不在此处退出：先执行下方 git init / 兼容副本收尾，再以 1 退出（与 init-project.py 对齐，
    # 避免显式请求的 -GitInit/-CreateCompatibilityLinks 被静默跳过）
    $hasRemaining = $true
}

# ----------------------------------------------------------------------------
# 7. 可选收尾：git init / CLAUDE.md 兼容副本
# ----------------------------------------------------------------------------
if ($GitInit) {
    Push-Location $Target
    try {
        # git 缺失（未安装/不在 PATH）抛 CommandNotFoundException，捕获为清晰错误（镜像 init-project.py 的 FileNotFoundError）
        git init 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "git init 退出码 $LASTEXITCODE" }
        # commit-msg 校验 hook：scripts/git-hooks/commit-msg（见 CONTRIBUTING「提交规范」）
        git config core.hooksPath scripts/git-hooks 2>&1 | Out-Null
        $configExit = $LASTEXITCODE
        if ($configExit -ne 0) {
            Write-Host "    [WARN] git config core.hooksPath 失败（exit $configExit），生成的仓库可能不带 commit-msg 校验" -ForegroundColor Yellow
        }
    } catch {
        throw "git init 失败（$Target）：$($_.Exception.Message)"
    } finally {
        Pop-Location
    }
    if ($configExit -eq 0) {
        Write-Host "==> 已执行 git init（commit-msg 校验 hook 已启用）" -ForegroundColor Green
    } else {
        Write-Host "==> 已执行 git init（commit-msg 校验 hook 未启用）" -ForegroundColor Yellow
    }
}

if ($CreateCompatibilityLinks) {
    # 主文件为 AGENTS.md（大写，Codex/Copilot/Windsurf 等直接读取）；仅为 Claude Code 创建副本
    Copy-Item -LiteralPath (Join-Path $Target "AGENTS.md") -Destination (Join-Path $Target "CLAUDE.md") -Force
    Write-Host "==> 已创建 CLAUDE.md（AGENTS.md 副本，供 Claude Code 读取）" -ForegroundColor Green
    Write-Host "    （注意：AGENTS.md 后续更新需重新创建 CLAUDE.md 副本，见 AGENTS.md「AGENTS.md 生态兼容」）" -ForegroundColor Yellow
}

if ($hasRemaining) {
    Write-Host "`n==> 初始化完成（存在未替换占位符，需人工处理）" -ForegroundColor Yellow
    exit 1
}
Write-Host "`n==> 初始化完成，全部占位符已替换 ✔" -ForegroundColor Green
exit 0
