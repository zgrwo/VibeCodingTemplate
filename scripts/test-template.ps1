# ============================================================================
# test-template.ps1 — 模板完整性自测（CI: template-self-test job 调用）
#
# 职责：
#   1. 调用 init-project.ps1 生成新项目（自动提供全部占位符值，无交互）
#   2. 运行 verify-docs.py --strict / verify-manual.py / falsy-audit.py
#   3. 断言全部通过 → 模板"初始化后文档一致性"能力被持续验证
#
# 设计：占位符测试值取自 scripts/placeholders.json 的 test 字段（唯一真相源），
#       缺失回退占位符名小写；死条目硬校验（manifest 声明但实际文件无此占位符 → 失败）。
#
# 用法：
#   .\scripts\test-template.ps1            # 默认系统临时目录下生成（跨平台）
#   .\scripts\test-template.ps1 -Target <dir> -Keep   # 指定目录并保留产物
#
# 退出码：0 = 自测通过；1 = 失败（CI 硬门禁）
# ============================================================================
param(
    [string]$Target = "",
    [switch]$Keep
)

$ErrorActionPreference = "Stop"
$template = Split-Path -Parent $PSScriptRoot
if (-not $Target) {
    # 跨平台临时目录：Windows 的 $env:TEMP 在 Linux runner 上为 null，用 .NET API 获取
    $Target = Join-Path ([System.IO.Path]::GetTempPath()) ("template-self-test-" + [guid]::NewGuid().ToString("N"))
}

# ----------------------------------------------------------------------------
# 1. 扫描模板中的全部 {{...}} 占位符
# ----------------------------------------------------------------------------
$placeholderRe = [regex]::new("\{\{([A-Z0-9_]+)\}\}")
$names = @{}
# -Force：pwsh 7 的 Get-ChildItem -Recurse 不递归 .github 等隐藏目录（Windows PS 5.1 会递归），
#         否则 CI（pwsh/Linux）漏扫 ci.yml 的 {{LINT_CMD}} → 死条目误报。
# 排除 .git：避免扫描 VCS 内部文件（无占位符，纯浪费）
Get-ChildItem $template -Recurse -File -Force | Where-Object { $_.FullName -notmatch "[\\/]\.git([\\/]|$)" } | ForEach-Object {
    $content = Get-Content $_.FullName -Encoding UTF8 -Raw -ErrorAction SilentlyContinue
    if ($content) {
        foreach ($m in $placeholderRe.Matches($content)) { $names[$m.Groups[1].Value] = $true }
    }
}
Write-Host "==> 扫描到 $($names.Count) 个占位符" -ForegroundColor Cyan

# ----------------------------------------------------------------------------
# 2. 生成占位符测试值（唯一真相源：scripts/placeholders.json 的 test 值，缺失回退小写）
# ----------------------------------------------------------------------------
. (Join-Path $template (Join-Path "scripts" "placeholder-utils.ps1"))
$manifest = Get-PlaceholderManifest

# 死条目硬校验：manifest 声明了但实际文件无此占位符 → 已失效条目，必须清理
$deadEntries = @()
foreach ($n in $manifest.Keys) {
    if (-not $names.ContainsKey($n)) { $deadEntries += $n }
}
if ($deadEntries.Count -gt 0) {
    Write-Host "❌ placeholders.json 死条目（manifest 声明但实际文件无此占位符，请清理）：$($deadEntries -join ', ')" -ForegroundColor Red
    exit 1
}

# 未登记占位符守卫（双向漂移守护）：
#   死条目（manifest 声明但无文件用）→ 上方硬失败；
#   未登记（文件用但不在 manifest）→ 此处 WARN（测试夹具 {{A}}/{{X1_}} 等
#   属 scanner 测试输入，无法登记，故不硬失败）；真正的元占位符污染由下方
#   生成后断言拦截（教学 token 必须存活、约定文字不得被替换成小写）。
$undeclared = @()
foreach ($n in $names.Keys) {
    if (-not $manifest.ContainsKey($n)) { $undeclared += $n }
}
if ($undeclared.Count -gt 0) {
    Write-Host "[WARN] 以下占位符未在 placeholders.json 登记（新增占位符请登记 manifest；教学引用请用 {{...}} 转义）：$($undeclared -join ', ')" -ForegroundColor Yellow
}

$values = @{}
foreach ($n in $names.Keys) {
    $key = "{{" + $n + "}}"
    if (-not $manifest.ContainsKey($n)) {
        # 未登记教学 token（如 {{X}}/{{UPPER}}/{{UPPER_CASE}}）：不预置小写值，
        # 否则会掩盖 init 的未登记分支、且把教学文字污染成小写（F1 修复，与
        # init-project.py 的 undeclared 保留原样语义对齐）
        continue
    }
    $test = $manifest[$n].test
    if ($test) { $values[$key] = $test }
    else { $values[$key] = $n.ToLower() }
}

# ----------------------------------------------------------------------------
# 3. 初始化生成（无交互：-Values 全覆盖）
# ----------------------------------------------------------------------------
Write-Host "==> 初始化生成 → $Target" -ForegroundColor Cyan
& (Join-Path $template (Join-Path "scripts" "init-project.ps1")) -Target $Target -Values $values -Force
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 初始化失败（占位符未全部替换）" -ForegroundColor Red
    exit 1
}

# ----------------------------------------------------------------------------
# 4. 验证生成产物（文档一致性三件套）
# ----------------------------------------------------------------------------
Push-Location $Target
try {
    $steps = @(
        @{ Name = "verify-docs.py --strict"; Cmd = { python scripts/verify-docs.py --strict } },
        @{ Name = "verify-manual.py";        Cmd = { python scripts/verify-manual.py } },
        @{ Name = "falsy-audit.py";          Cmd = { python scripts/falsy-audit.py } },
        @{ Name = "test-quality-guard.py";   Cmd = { python scripts/test-quality-guard.py } }
    )
    foreach ($s in $steps) {
        Write-Host "`n=== $($s.Name) ===" -ForegroundColor Cyan
        & $s.Cmd
        if ($LASTEXITCODE -ne 0) { throw "$($s.Name) 失败 (退出码 $LASTEXITCODE)" }
    }
    # 元占位符污染断言：未登记教学 token 必须原样存活于生成项目 AGENTS.md
    # （H3 修复 + ps1 对齐的 F1 回归守卫；token 本身未登记，init 会保留原样）
    $agentsText = Get-Content (Join-Path $Target "AGENTS.md") -Encoding UTF8 -Raw
    foreach ($token in @('{{X}}', '{{UPPER}}', '{{UPPER_CASE}}')) {
        if ($agentsText -notmatch [regex]::Escape($token)) {
            throw "教学 token $token 未存活于生成项目 AGENTS.md（元占位符污染回归）"
        }
    }
    Write-Host "`n[OK] 教学 token 存活断言通过（元占位符污染无回归）" -ForegroundColor Green
    Write-Host "`n✅ 模板自测通过：占位符替换完整 + 文档一致性验证通过" -ForegroundColor Green
    if (-not $Keep) {
        Set-Location ([System.IO.Path]::GetTempPath())
        Remove-Item $Target -Recurse -Force
    }
    exit 0
}
catch {
    Write-Host "`n❌ 模板自测失败: $_" -ForegroundColor Red
    Write-Host "    产物保留在: $Target" -ForegroundColor Yellow
    exit 1
}
finally {
    Pop-Location
}
