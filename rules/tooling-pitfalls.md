# 工具与脚本坑位清单（Windows / PowerShell / git）

> 从 5 个子项目实际踩坑中提炼的跨项目工具级陷阱。修改 `scripts/`、运行终端命令、处理 git 操作前必读。

## PowerShell 陷阱

| # | 陷阱 | 正确做法 |
|---|------|----------|
| 1 | **`foreach` 语法缺 `in` 关键字**（`foreach $x $list`）→ 语法错误 | `foreach ($x in $list) { ... }` |
| 2 | **`Join-Path` 第二参数不能为空** → 抛异常 | 先判空或拼接非空段；构建路径优先 `Join-Path` 但传入校验后的子路径 |
| 3 | **PowerShell 5.1 处理 UTF-8 文件乱码**（默认 ANSI 读取/写入）；含中文注释的 `.ps1` 文件若**无 BOM**，解析器按 ANSI 读注释 → 语法解析失败 | 读写文件显式指定编码：`Get-Content -Encoding UTF8`、`Set-Content -Encoding UTF8`；**`.ps1` 源文件必须保存为 UTF-8 with BOM**（`[System.IO.File]::WriteAllText($p, $c, (New-Object System.Text.UTF8Encoding $true))`） |
| 4 | **`&&` 语句分隔符**（PowerShell 5.1 不支持） | 用 `;` 分隔命令，或使用 `if ($LASTEXITCODE -eq 0)` 判断 |

## git 陷阱

| # | 陷阱 | 正确做法 |
|---|------|----------|
| 5 | **`git add` 无法暂存未跟踪文件的"删除"**（文件从未提交过，删除后无 stage 记录） | 删除未跟踪文件无需 git 操作；提交过则用 `git rm` 或 `git add -A` |
| 6 | **`git fetch --unshallow` 仅适用于浅克隆仓库** → 普通仓库报错 | 先 `git rev-parse --is-shallow-repository` 确认，或用 `git fetch --unshallow` 前的 fallback |
| 7 | **push 前未确认测试全绿** | AGENTS.md Git 红线：未经用户明确同意不 push |

## Windows 工具陷阱

| # | 陷阱 | 正确做法 |
|---|------|----------|
| 8 | **`robocopy` 退出码 1 表示"复制成功"**（非 0 即失败的错误假设） | `robocopy` 退出码 <8 均算成功；检查 `$LASTEXITCODE -lt 8` |
| 9 | **Bash 工具缺失 `head`/`tail`**（Windows Git Bash 环境无 GNU head） | 用 PowerShell `Select-Object -First N` / `Get-Content | Select-Object -Last N` |
| 10 | **扫描/验证工具单次行数上限**（如 Qoder 安全扫描 10000 行/次） | 大文件分批扫描，或按目录分片执行 |

## 语言/框架特定坑位（跨项目高频）

> **SSOT**：语言级陷阱的权威定义在 `skills/` 语言文件，本表只列索引与跨项目案例定位，不重复内容。

| # | 陷阱 | 权威定义处 |
|---|------|-----------|
| 11 | **.NET Framework 4.8 使用 `record` 需 `IsExternalInit` polyfill** | [csharp-SKILL.md](../skills/csharp-SKILL.md)（双 TFM / IsExternalInit 章节） |
| 12 | **Pydantic v2 不兼容位置参数**（模型构造必须关键字参数） | [python-SKILL.md](../skills/python-SKILL.md) §8.5 |
| 13 | **VBA 不支持 `Optional ByRef` 数组参数** | [vba-SKILL.md](../skills/vba-SKILL.md) §4.0 |
| 14 | **移除 NuGet 包后 .dna 中对应 DLL 引用残留** | [csharp-SKILL.md](../skills/csharp-SKILL.md)（Excel-DNA 章节） |

## 提交前自查

```bash
# 检查脚本中是否出现高频坑位
grep -rn "foreach \$\|Join-Path [^)]*$\|&&" scripts/ --include="*.ps1" || echo "OK"
```

## 维护规则

- 新踩坑并验证修复后，**立即追加到本表**（附真实案例与正确做法）
- 语言级陷阱**只在** `skills/` 语言文件维护（本表只留链接索引，禁止双写）
- 项目专属坑位（非通用）写入该项目 AGENTS.md「历史经验」章节，不放本文件
