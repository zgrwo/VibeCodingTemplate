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

## 验证脚本陷阱（SSOT 守卫盲区）

> 本仓库 `scripts/` 自身踩坑（已修复），经验可复用到任何"目录树即契约"的治理项目。

| # | 陷阱 | 正确做法 |
|---|------|----------|
| 15 | **`Path.rglob` 在文件上不迭代** → `falsy-audit --path <文件>` 静默输出"无发现"（门禁说谎） | 扫描入口先校验 `scope.is_dir()`，文件路径显式报错 |
| 16 | **`check_undeclared` 只查根级**（`ROOT.iterdir()`）→ 子目录新增 `rules/*.md` 等静默通过 SSOT 守卫 | 对 SSOT 关键子目录（rules/skills/scripts/docs/.github/templates/examples）逐文件比对目录树声明 |
| 17 | **类型注解安全判定用子串匹配**（`"list" in hint.lower()`）→ `Optional[list[float]]`（None/空列表混淆）、自定义 `MyList` 被误判安全 | 解析注解 AST 取顶层类型构造器（`_top_type_name`），`X \| None` 联合视为 Optional |
| 18 | **init 把未登记 `{{X}}` 元文档引用替换为小写**（`get_placeholder_value` 落到 `name.lower()`）→ 教学文档（如 pre-release-review.md 的占位符约定表）被污染成 `upper`/`x`，且 CI 自测无法发现 | 未登记 token 返回 None 保留原样；文档内教学引用统一 `{{...}}` 转义（三点号不匹配 `[A-Z0-9_]+`）；tests/ 目录跳过占位符扫描（内含 scanner 测试夹具） |
| 19 | **spec 加载 crossval 脚本时 `if __name__ == "__main__"` 守卫被绕过** → 脚本 0 PASS/0 FAIL 仍 exit 0（门禁说谎） | 用 `spec_from_file_location` 加载时 `__name__` 恒为模块 stem，任何包裹 main-guard 的校验都不会执行；要求 `_PASS + _FAIL > 0` 否则显式 FAIL |
| 20 | **自校验正则误伤 docstring/注释中的反例教学文字**（如「禁止自校验 check(name, X, X)」）→ quality-gate 必红 | 自校验扫描跳过注释/docstring 行（`line.lstrip().startswith(('#', '"', "'"))`）；或将反例改写为不匹配形式（`check(name, X, Y)` + 说明） |
| 21 | **测试文件命名不匹配测试框架默认 glob**（`test_X.ts` vs vitest/Jest `**/*.{test,spec}.*`）→ 测试永不运行、CI 静默通过 | 后缀用框架默认匹配（TS `.test.ts`）；或显式配置 include glob |
| 22 | **配置流断裂（声明→解析→传递→读取→使用任一环断开）**（来源：文档审查套件 STR-004 在 4 节点断裂；cross-project-synthesis #4）→ 规则/参数在配置中声明但链路某节点静默失效，报错时已在用点 | 防御模式：回退路径的 config 键集**必须与主路径一致**（文档审查套件 `_resolve_auditor_config()` 注释"陷阱 #4：回退路径 config 键集必须与 build_auditors 一致"）；新增注册点后立即用 `verify-registries.py`（档 A-A1）断言多注册表键集一致 |
| 23 | **ruff per-file ignore 无理由注释**（来源：工程分析套件 pyproject.toml）→ 后人 copy-paste 忽略规则，无上下文 | 每条 per-file-ignores/noqa 必须带中文理由注释（如 `"N806" 大写变量是有意的 SPC 常量 A2/D3/D4`）；新增规则类别需先确认非"覆盖问题"而是"约定豁免" |
| 24 | **工具命名映射未归一化连字符/下划线**（源文件 `gen-doc-counts.py` 用连字符、测试 `test_gen_doc_counts.py` 用下划线，工具 `stem in name` 子串匹配失效）→ 门禁谎报"缺测"（run-affected-tests 对 4 个本有测试的脚本全报 FAIL） | 比较前统一分隔符：`stem.replace('-', '_')`（两边都归一化到 `_`）再子串匹配；补 kebab-case 源文件 → snake_case 测试的回归用例 |
| 25 | **init 把 CI 检测脚本中的占位符字面量一并替换**（ci.yml / detect-template.yml 的 detect 步骤 grep 模式里的 PROJECT_NAME 双花括号字面量被 init-project 替换成项目名，而生成项目 AGENTS.md 必然包含项目名 → `is_template` 恒为 true，**下游项目 CI 的构建/测试/质量门禁被永久跳过**；模板自身 CI 不执行生成项目的 CI，故长期未暴露，2026-08 审查实证） | 检测"未替换占位符"的 grep 模式**运行时拼装**（`open='{{'` / `close='}}'` + `grep -Fq "${open}PROJECT_NAME${close}"`），文件内不出现可被 init 匹配的字面占位符；凡 init 会扫描的文件中出现的**已登记**占位符字面量默认都会被替换，检测/教学类引用需显式逃逸或使用 `{{...}}` 三点号转义 |
| 25b | **BRE 转义 `\{\{` 依赖 grep 版本宽容行为**（grep BRE 中 `\{` 是区间表达式起始符，旧版 GNU grep 对"`\{` 后非数字"宽容处理为字面量，新版 grep 3.11 直接报 `Invalid content of \{\}` exit 2——2026-08-15 runner 镜像 20260810.271.1 升级后，detect 步骤的 `2>/dev/null` 吞掉错误 → `is_template` 恒 false → Build 执行字面 `{{BUILD_CMD}}`（exit 127），模板模式跳过逻辑静默失效，release PR CI 全红；同一提交本地 Git grep（3.1）正常命中，8-14 同镜像系列旧版（20260810.271 无 .1 后缀）也正常，镜像补丁升级后必现） | 固定串匹配 `grep -F`（无正则解析，版本无关）；detect 等关键分支**不要 `2>/dev/null` 吞错误**（grep 出错应暴露在日志）；CI 中自举检测逻辑加回归测试（用 `{{PROJECT_NAME}}` 存在/缺失两种内容断言 is_template 输出） |
| 26 | **py/ps1 双实现行为分叉且 CI 只测单侧**（init-project.py 对未登记 token 返回 None 保留原样，init-project.ps1 仍替换为占位符名小写 → Windows 初始化把 AGENTS.md 教学 token 污染成小写；test-template.ps1 以 -Values 预置小写值全覆盖，ps1 未登记分支在 CI 自测中永不触发，2026-08 Max 审查 4 维度独立确认） | 双实现共享行为规范并各配回归守卫：ps1 未登记分支保留原样 + remaining 扫描跳过 undeclared + test-template.ps1 教学 token 存活断言（`{{X}}`/`{{UPPER}}`/`{{UPPER_CASE}}` 必须原样存在于生成项目） |
| 27 | **模板模式 CI 门禁盲区**（模板仓库自身 is_template=true 时 quick-check 的 Build/Test 与 quality-gate 的 LINT/COVERAGE 全部被 `!= 'true'` 门控跳过——占位符命令在模板不可执行；template-self-test 只跑 verify 四件套 → 模板自身的 pytest/ruff 无 CI 守卫，2026-08 实证 ruff 对 examples/ 报 I001 而 CI 全绿） | quality-gate 模板模式分支加**字面命令**硬门禁（非占位符）：`python -m pytest tests/ -q`、`python -m ruff check scripts/ tests/ examples/`；依赖安装步骤（numpy）必须先于使用它的 verify-manual 步骤 |
| 28 | **PS 5.1 的 `Split-Path -LiteralPath <x> -Parent` 参数集歧义**（LiteralPathSet 与 PathSet 均含 -Parent，`-LiteralPath` + `-Parent` 组合报 AmbiguousParameterSet——2026-08 Max 审查在 init-project.ps1 junction 防护中实证） | 改用 .NET API `[System.IO.Path]::GetDirectoryName($path)`（返回 null 即到根，循环自然终止）；或先用 `-Path`（无通配符场景等价） |

## 提交前自查

```bash
# 检查脚本中是否出现高频坑位
grep -rn "foreach \$\|Join-Path [^)]*$\|&&" scripts/ --include="*.ps1" || echo "OK"
```

## 维护规则

- 新踩坑并验证修复后，**立即追加到本表**（附真实案例与正确做法）
- 语言级陷阱**只在** `skills/` 语言文件维护（本表只留链接索引，禁止双写）
- 项目专属坑位（非通用）写入该项目 AGENTS.md「历史经验」章节，不放本文件
