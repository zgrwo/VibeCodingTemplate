# ============================================================================
# placeholder-utils.ps1 — 占位符清单共享工具
#
# 职责：读取 scripts/placeholders.json（占位符唯一真相源），提供
#       Get-PlaceholderManifest 供 init-project.ps1 / test-template.ps1 共用。
#
# manifest schema：
#   { "schema_version": 1,
#     "placeholders": {
#       "NAME": { "category": "core|content|auto",
#                 "prompt": "中文提示（core/auto 用）",
#                 "default": "core 的提示默认值（可选）",
#                 "rule": "auto 的动态规则：today|year",
#                 "test": "test-template 使用的测试值（可选，缺失回退占位符名小写）" } } }
#
#   category 语义：
#     core    — 初始化时交互询问（缺之则项目/CI 不可用）
#     content — 自动用占位符名小写占位，开发期填写文档时替换
#     auto    — 自动计算（rule: today = 当前日期 / year = 当前年份），不询问
#
# 防错三原则：JSON 缺失/损坏时回退内置默认表（至少覆盖 core 键）并输出警告，
#            不让 init/test 流程因 manifest 问题而崩溃。
# ============================================================================

# 内置回退表：仅覆盖 core 键 + 动态键（manifest 损坏时的兜底）
function Get-PlaceholderManifestFallback {
    return @{
        "PROJECT_NAME"          = @{ category = "core"; prompt = "项目名（目录名与文档一致）" }
        "OWNER"                 = @{ category = "core"; prompt = "GitHub 用户名/组织" }
        "REPO_NAME"             = @{ category = "core"; prompt = "仓库名" }
        "AUTHOR"                = @{ category = "core"; prompt = "作者姓名" }
        "VERSION"               = @{ category = "core"; prompt = "初始版本号"; default = "1.0.0" }
        "BUILD_CMD"             = @{ category = "core"; prompt = "构建命令" }
        "TEST_CMD"              = @{ category = "core"; prompt = "测试命令" }
        "FULL_VERIFY_CMD"       = @{ category = "core"; prompt = "全量验证命令" }
        "LINT_CMD"              = @{ category = "core"; prompt = "代码风格检查命令" }
        "COVERAGE_CMD"          = @{ category = "core"; prompt = "覆盖率命令" }
        "SECURITY_CONTACT"      = @{ category = "core"; prompt = "安全漏洞联系邮箱" }
        "COC_CONTACT"           = @{ category = "core"; prompt = "行为准则联系邮箱" }
        "ROOT_NAMESPACE"        = @{ category = "core"; prompt = "项目根命名空间"; default = "Acme.Project" }
        "TARGET_FRAMEWORK"      = @{ category = "core"; prompt = "目标框架"; default = "net8.0" }
        "PACKAGE_NAME"          = @{ category = "core"; prompt = "Python 包名"; default = "my_project" }
        "SKILL_1"               = @{ category = "core"; prompt = "主技能文件"; default = "csharp-SKILL.md" }
        "SKILL_2"               = @{ category = "core"; prompt = "次技能文件"; default = "python-SKILL.md" }
        "SCOPE_1"               = @{ category = "core"; prompt = "技能 1 适用范围"; default = "C# 代码" }
        "SCOPE_2"               = @{ category = "core"; prompt = "技能 2 适用范围"; default = "Python 代码" }
        "DESCRIPTION_1"         = @{ category = "core"; prompt = "技能 1 内容说明"; default = "C# 编码陷阱与规范" }
        "DESCRIPTION_2"         = @{ category = "core"; prompt = "技能 2 内容说明"; default = "Python 编码陷阱与规范" }
        "LAYER_DIAGRAM"         = @{ category = "core"; prompt = "架构分层图"; default = "UDF -> Core -> Foundation" }
        "LAYER_DEPENDENCY_DIAGRAM" = @{ category = "core"; prompt = "层级依赖图"; default = "UI -> Service -> Engine -> Data" }
        "DATE"                  = @{ category = "auto"; rule = "today"; prompt = "日期" }
        "YEAR"                  = @{ category = "auto"; rule = "year";  prompt = "年份" }
    }
}

# 读取占位符清单（唯一真相源）；失败回退内置默认表
function Get-PlaceholderManifest {
    $manifestPath = Join-Path $PSScriptRoot "placeholders.json"
    if (Test-Path $manifestPath) {
        try {
            $raw = Get-Content $manifestPath -Encoding UTF8 -Raw
            $data = $raw | ConvertFrom-Json
            if ($data -and $data.placeholders) {
                # 转为 name -> hashtable（PS 5.1 ConvertFrom-Json 属性为 PSCustomObject，转 hashtable 便于索引）
                $result = @{}
                foreach ($prop in $data.placeholders.PSObject.Properties) {
                    $entry = @{}
                    foreach ($p in $prop.Value.PSObject.Properties) { $entry[$p.Name] = $p.Value }
                    $result[$prop.Name] = $entry
                }
                return $result
            }
        } catch {
            Write-Host "[WARN] placeholders.json 解析失败，回退内置默认表: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[WARN] placeholders.json 缺失，回退内置默认表（请检查 scripts/ 完整性）" -ForegroundColor Yellow
    }
    return Get-PlaceholderManifestFallback
}
