# ============================================================================
# test-template.ps1 — 模板完整性自测（CI: template-self-test job 调用）
#
# 职责：
#   1. 调用 init-project.ps1 生成新项目（自动提供全部占位符值，无交互）
#   2. 运行 verify-docs.py --strict / verify-manual.py / falsy-audit.py
#   3. 断言全部通过 → 模板"初始化后文档一致性"能力被持续验证
#
# 设计：占位符值由映射表 + 通用规则生成（特殊值保证链接真实存在，
#       其余占位符用占位符名小写填充），确保替换后 verify-docs 链接全部可解析。
#
# 用法：
#   .\scripts\test-template.ps1            # 默认 $env:TEMP 下生成
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
    $Target = Join-Path $env:TEMP ("template-self-test-" + [guid]::NewGuid().ToString("N"))
}

# ----------------------------------------------------------------------------
# 1. 扫描模板中的全部 {{...}} 占位符
# ----------------------------------------------------------------------------
$placeholderRe = [regex]::new("\{\{([A-Z0-9_]+)\}\}")
$names = @{}
Get-ChildItem $template -Recurse -File | ForEach-Object {
    $content = Get-Content $_.FullName -Encoding UTF8 -Raw -ErrorAction SilentlyContinue
    if ($content) {
        foreach ($m in $placeholderRe.Matches($content)) { $names[$m.Groups[1].Value] = $true }
    }
}
Write-Host "==> 扫描到 $($names.Count) 个占位符" -ForegroundColor Cyan

# ----------------------------------------------------------------------------
# 2. 生成占位符测试值（特殊值映射 + 通用规则）
# ----------------------------------------------------------------------------
$special = @{
    "PROJECT_NAME" = "TemplateSelfTest"
    "ONE_LINE_DESCRIPTION" = "模板自测生成项目（验证后删除）"
    "SKILL_1" = "csharp-SKILL.md"
    "SKILL_2" = "python-SKILL.md"
    "SCOPE_1" = "C# 代码"
    "SCOPE_2" = "Python 代码"
    "DESCRIPTION_1" = "C# 编码陷阱与规范"
    "DESCRIPTION_2" = "Python 编码陷阱与规范"
    "LAYER_DIAGRAM" = "UDF -> Core -> Foundation"
    "LAYER_DEPENDENCY_DIAGRAM" = "UI -> Service -> Engine -> Data"
    "VERSION" = "0.1.0"
    "DATE" = "2026-01-01"
    "YEAR" = "2026"
    "AUTHOR" = "Test Author"
    "SECURITY_CONTACT" = "security@example.com"
    "BUILD_CMD" = "python -m compileall -q src"
    "TEST_CMD" = "python -m pytest tests/ -x -q"
    "FULL_VERIFY_CMD" = "./scripts/verify-all.ps1"
    "LINT_CMD" = "python -m ruff check src/ scripts/"
    "COVERAGE_CMD" = "python -m pytest --cov=src --cov-fail-under=0"
    "PACKAGE_CMD" = "python -m build"
    "ROOT_NAMESPACE" = "TemplateSelfTest"
    "PACKAGE_NAME" = "template_self_test"
    "REPO_URL" = "https://github.com/example/template-self-test"
    "OWNER" = "example"
    "REPO_NAME" = "template-self-test"
    "PRODUCT_NAME" = "TemplateSelfTest"
    "KEYWORD_1" = "template"
    "KEYWORD_2" = "self-test"
    "MODULE_1" = "Stats"
    "MODULE_2" = "Text"
    "MODULE_3" = "Convert"
    "MODULE_1_DESC" = "统计计算模块"
    "MODULE_2_DESC" = "文本处理模块"
    "COUNT_1" = "3"
    "COUNT_2" = "2"
    "TOTAL" = "5"
    "TERM_1" = "哨兵值"
    "DEFINITION_1" = "不可转换值的类型零值"
    "PROJECT_1" = "TemplateSelfTest"
    "TERM_2" = "交叉验证"
    "DEFINITION_2" = "独立实现比对"
    "PROJECT_2" = "TemplateSelfTest"
    "COMMIT_COUNT" = "120"
    "CRITICAL_PATH_CMD" = "python scripts/verify-manual.py"
    "INSTALL_COMMANDS" = "pip install -e .[dev]"
    "INSTALL_INSTRUCTIONS" = "pip install -e .[dev]"
    "VERIFY_INSTALL" = "python -c ""import template_self_test"""
    "PATTERN_1" = "注册/同步遗漏"
    "ROOT_CAUSE_1" = "新增功能后忘记更新关联位置"
    "PATTERN_2" = "文档数字漂移"
    "ROOT_CAUSE_2" = "数字多处硬编码"
}
$values = @{}
foreach ($n in $names.Keys) {
    $key = "{{" + $n + "}}"
    if ($special.ContainsKey($n)) { $values[$key] = $special[$n] }
    else { $values[$key] = $n.ToLower() }
}

# ----------------------------------------------------------------------------
# 3. 初始化生成（无交互：-Values 全覆盖）
# ----------------------------------------------------------------------------
Write-Host "==> 初始化生成 → $Target" -ForegroundColor Cyan
& (Join-Path $template "scripts\init-project.ps1") -Target $Target -Values $values -Force
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
        @{ Name = "falsy-audit.py";          Cmd = { python scripts/falsy-audit.py } }
    )
    foreach ($s in $steps) {
        Write-Host "`n=== $($s.Name) ===" -ForegroundColor Cyan
        & $s.Cmd
        if ($LASTEXITCODE -ne 0) { throw "$($s.Name) 失败 (退出码 $LASTEXITCODE)" }
    }
    Write-Host "`n✅ 模板自测通过：占位符替换完整 + 文档一致性验证通过" -ForegroundColor Green
    if (-not $Keep) {
        Set-Location $env:TEMP
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
