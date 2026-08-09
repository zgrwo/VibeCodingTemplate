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
# 防错三原则：JSON 缺失/损坏时 fail-fast（抛错提示修复 manifest），
#            不使用内置回退表——内置表与 placeholders.json 双写必然漂移
#            （曾漏 9 个 core 键：APP_PORT/DB_*/IMAGE_NAME 等），违反 SSOT。
# ============================================================================

# 读取占位符清单（唯一真相源）；失败时 fail-fast（不静默降级）
function Get-PlaceholderManifest {
    $manifestPath = Join-Path $PSScriptRoot "placeholders.json"
    if (-not (Test-Path $manifestPath)) {
        throw "placeholders.json 缺失（$manifestPath）——占位符唯一真相源不可用，请检查 scripts/ 完整性"
    }
    try {
        $raw = Get-Content $manifestPath -Encoding UTF8 -Raw
        $data = $raw | ConvertFrom-Json
        if (-not ($data -and $data.placeholders)) {
            throw "placeholders.json 结构无效（缺少 placeholders 节点）"
        }
        # 转为 name -> hashtable（PS 5.1 ConvertFrom-Json 属性为 PSCustomObject，转 hashtable 便于索引）
        $result = @{}
        foreach ($prop in $data.placeholders.PSObject.Properties) {
            $entry = @{}
            foreach ($p in $prop.Value.PSObject.Properties) { $entry[$p.Name] = $p.Value }
            $result[$prop.Name] = $entry
        }
        return $result
    } catch {
        throw "placeholders.json 解析失败（$manifestPath）: $($_.Exception.Message)——请修复 manifest，勿用回退表（SSOT 防漂移）"
    }
}
