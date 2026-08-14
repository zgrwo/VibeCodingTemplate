# ============================================================================
# verify-all.ps1 — 全量验证入口
#
# 职责：一个命令完成「构建 + 测试 + 文档一致性」全量验证，
#       对应 AGENTS.md 中的 {{FULL_VERIFY_CMD}}。
#
# 设计：
#   - 构建/测试自动探测（*.sln → dotnet；pyproject.toml → Python）
#   - 未检测到构建系统时显式 [跳过] 并提示，不假装通过
#   - 文档一致性依赖 Python（verify-docs/verify-manual/falsy-audit），
#     未安装 python 时显式 [跳过] 警告
#
# 用法：
#   .\scripts\verify-all.ps1          # 全量验证
#   .\scripts\verify-all.ps1 -Quick   # 仅构建 + 测试（跳过文档检查）
#
# 退出码：0 = 通过；非 0 = 失败（CI 可直接调用）
# ============================================================================
param(
    [switch]$Quick
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

function Invoke-Step {
    param([string]$Name, [scriptblock]$Body)
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    & $Body
    if ($LASTEXITCODE) {
        throw "步骤失败: $Name (退出码 $LASTEXITCODE)"
    }
}

try {
    # ---- 构建（自动探测构建系统；未检测到时显式跳过）----
    $sln = Get-ChildItem $root -Filter *.sln -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($sln) {
        Invoke-Step "构建 (.NET)" { dotnet build $sln.FullName -c Release }
    } elseif (Test-Path "$root\pyproject.toml") {
        Invoke-Step "构建 (Python)" { python -m compileall -q "$root\src" }
    } else {
        Write-Host "`n=== 构建 ===`n  [跳过] 未检测到 *.sln / pyproject.toml，请按项目语言在脚本中配置 ({{BUILD_CMD}})" -ForegroundColor Yellow
    }

    # ---- 测试 ----
    if ($sln) {
        Invoke-Step "测试 (.NET)" { dotnet test $sln.FullName -c Release }
    } elseif (Test-Path "$root\pyproject.toml") {
        Invoke-Step "测试 (Python)" { python -m pytest "$root\tests" -x -q }
    } else {
        Write-Host "`n=== 测试 ===`n  [跳过] 未检测到构建系统，请配置 ({{TEST_CMD}})" -ForegroundColor Yellow
    }

    # ---- 文档一致性 ----
    if (-not $Quick) {
        $py = Get-Command python -ErrorAction SilentlyContinue
        if (-not $py) {
            Write-Host "`n=== 文档一致性 ===`n  [跳过] 未检测到 python（verify-docs / verify-manual / falsy-audit 依赖，建议安装或配置代理脚本）" -ForegroundColor Yellow
        } else {
            Invoke-Step "文档一致性" {
                # 每条命令独立检查退出码：任一失败立即抛异常（$LASTEXITCODE 只保留最后一条，
                # 若整体一次性执行会被 verify-docs 的失败掩盖，门禁失效）
                python "$root\scripts\verify-docs.py" --strict
                if ($LASTEXITCODE) { throw "verify-docs.py 失败 (退出码 $LASTEXITCODE)" }
                python "$root\scripts\verify-manual.py"
                if ($LASTEXITCODE) { throw "verify-manual.py 失败 (退出码 $LASTEXITCODE)" }
                python "$root\scripts\falsy-audit.py"
                if ($LASTEXITCODE) { throw "falsy-audit.py 失败 (退出码 $LASTEXITCODE)" }
                python "$root\scripts\verify-registries.py"
                if ($LASTEXITCODE) { throw "verify-registries.py 失败 (退出码 $LASTEXITCODE)" }
                python "$root\scripts\gen-doc-counts.py" --check
                if ($LASTEXITCODE) { throw "gen-doc-counts.py 失败 (退出码 $LASTEXITCODE)" }
                python "$root\scripts\test-quality-guard.py"
                if ($LASTEXITCODE) { throw "test-quality-guard.py 失败 (退出码 $LASTEXITCODE)" }
                # 模板自身治理脚本的"缺测"检测（默认 --src src 在模板仓库为空转；
                # 2026-08 Max 审查 #D8 修复：scripts/ 公共函数必须被 tests/scripts 引用）
                python "$root\scripts\test-quality-guard.py" --src scripts --tests tests/scripts
                if ($LASTEXITCODE) { throw "test-quality-guard.py（scripts 缺测）失败 (退出码 $LASTEXITCODE)" }
            }
        }
    }

    Write-Host "`n✅ 全量验证通过" -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "`n❌ 验证失败: $_" -ForegroundColor Red
    exit 1
}
