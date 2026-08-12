# Max 审查全量修复执行文档（新会话冷启动依据）

> 审查基线: 22a2eca · 目标: v0.2.0 · 2026-08-12
> **本文件是唯一执行依据**——中断后新会话可直接照此逐项修复，不依赖对话上下文。
> 执行顺序：P1（必须修）→ P2（改善）→ P3（建议）。每项修复后跑验证命令。
> 修复完成后：登记 SSOT（project-structure/documentation/DOC_FILES/AGENTS参考表）+ 更新知识库（AGENTS高频模式/tooling-pitfalls/cross-project-synthesis）。

## 验证命令（每批修复后运行）

```bash
cd D:/Workspace/zgrwo/Harmonization/VibeCodingTemplate
python scripts/verify-all.py            # 全绿
python -m ruff check scripts/ tests/    # 零违规
python -m pytest tests/ -q --cov=scripts --cov-fail-under=35
python scripts/verify-docs.py --strict  # SSOT 无漂移
scripts/test-template.ps1               # 端到端自举
```

## 仓库状态须知（P1-6 前置）

- 本地 main 已与 origin/main 分叉：远程已发布 v0.1.2（tag 存在），本地 CHANGELOG/manifest 仍 0.1.1
- **修复前先同步**：git fetch origin && git merge origin/main（或 rebase），纳入 25decc8/f a5c61c 两个 0.1.2 发布提交
- 同步后 .release-please-manifest.json 应为 0.1.2，再发 0.2.0

## P1 修复清单（9 项，必须修复，已对抗验证）

### P1-1 templates/NewModule/{Name}Core.Tests.cs.template:20 [编译检查 / C# 测试模板]
- **问题**: 测试模板 Compute_normal_input 调用 Should().Be(/* {期望值} */)，期望值整个被注释掉，生成 Be() 零参数调用，替换占位符后无法编译（CS1501）。
- **影响**: 按 README 复制 Core/Tests 并替换 {Name}/{Module}/{{ROOT_NAMESPACE}} 后，tests/{Module}.Tests 项目 dotnet build 直接失败（已实测：CS1501 “Be 方法没有采用 0 个参数的重载”）。CI 的模板自测（test-template.ps1）不编译任何语言模板，因此此缺陷无门禁拦截，用户拿到手就是编译不过的测试项目。且 {期望值} 未登记在 templates/README.md 占位符表，用户不知道要替换它。
- **修复**: 把 `Be(/* {期望值} */)` 改为带具体值的断言，如 `Be(2.0)`（模板内 compute(1.0)=2.0 的语义一致）；或在 {期望值} 前补默认值，保证占位符替换后 Be() 有实参。

### P1-2 templates/language/offline-setup.py.template:14 [可运行性 / 新增模板契约]
- **问题**: docstring 与 README 宣传的干跑用法 `python offline-setup.py install --src wheels/ --print-cmd` 中，主解析器的 --print-cmd 放在子命令之后，argparse 无法识别。
- **影响**: 已实测（Python 3.14）：`python offline-setup.py install --src wheels/ --print-cmd` 报错 `unrecognized arguments: --print-cmd`（exit=2）。该模板的核心卖点——--print-cmd 特权操作安全门——按文档命令无法使用；download 子命令同理。
- **修复**: 把 --print-cmd 挪到子命令之前（如 `python offline-setup.py --print-cmd install --src wheels/`）并同步修正 docstring 第 12-14 行三个示例；更稳妥的做法是用 argparse parents=[common_parser] 让 download/install 两个子解析器都继承该选项，两种调用顺序均可。

### P1-3 templates/NewModule/{Name}VariantKit.bas.template:23 [正确性 / VBA 模板]
- **问题**: NormalizeInput 的 Range 分支只处理 IsArray(arr) 的展平，未把单格 Range 的标量 .Value 包装成单元素数组；配合 Udf.bas 的 IsArrayEmpty 守卫，单格输入被判定为空数组返回 CVErr(xlErrValue)。
- **影响**: 最常见调用 `={PREFIX}_COMPUTE(A1)`（单格引用）会返回 #VALUE!：Range 分支 arr=v.Value 为标量（非数组），跳过展平，函数返回标量；Udf.bas 中 IsArrayEmpty(arr) 对非数组执行 UBound 触发运行时错误 9，On Error Resume Next 下 Err.Number<>0 → IsArrayEmpty=True → 直接 CVErr(xlErrValue)。单值→数组的包装逻辑只存在于 Else 分支（非 Range 输入），Range→标量路径漏掉，VBA 无 CI 无法自动捕获。
- **修复**: 在 Range 分支 `If IsArray(arr)` 之后补 `If Not IsArray(arr) Then`：把标量包成 0 To 0 单元素数组（与 Else 分支同构），或复用第 39-41 行的单值包装逻辑。

### P1-4 templates/language/tsconfig.json.template:28 [编译检查 / TypeScript 构建配置]
- **问题**: tsconfig 使用已被 TypeScript 6/7 移除的 baseUrl，且 paths 目标值 src/{Module}/* 非相对路径；当前工具链下 `npx tsc --noEmit` 直接失败。
- **影响**: 已实测（TypeScript 7.0.2）：`npx tsc --noEmit` 报 TS5102 “Option 'baseUrl' has been removed” + TS5090 “Non-relative paths are not allowed”。模板不锁定 TS 版本，README 仅指示 npx tsc/vitest，用户在最新 TS 下拿到即崩；去掉 baseUrl 并把 paths 改相对后源码可零错误通过，证明问题仅在构建配置模板本身。
- **修复**: 删除 `"baseUrl": "."`，把 paths 目标改为 `"./src/{Module}/*"`（相对路径）；如需兼容 TS 5.x 旧版可加注释说明 baseUrl 已废弃。

### P1-5 .github/workflows/ci.yml:168 [CI 质量门禁 / 依赖安装]
- **问题**: quality-gate job 设了 setup-python（137-139 行）却没有任何依赖安装步骤，LINT_CMD/COVERAGE_CMD 在裸 runner 上必失败
- **影响**: 该 job 运行 {{LINT_CMD}}（注释文档为 `ruff check src/`）与 {{COVERAGE_CMD}}（注释文档为 `pytest --cov=src --cov-fail-under=80，需 dev 依赖 pytest-cov`），但 ubuntu-latest 裸机未装 ruff/pytest/pytest-cov，也没有 setup-dotnet（.NET 项目的 dotnet format 同理）。模板仓库自身因 is_template 跳过这两步不受影响，但任何按模板注释替换占位符的下游新 Python 项目，首次 PR 的'硬门禁'就会因工具缺失而红，且报错与代码质量无关，用户无法区分是环境问题还是质量问题。
- **修复**: 在 quality-gate 的 LINT/COVERAGE 之前增加依赖安装步骤（Python: `python -m pip install -e ".[dev]"`；.NET: 增加 actions/setup-dotnet），或在 ci.yml 注释/占位符中明确要求 {{LINT_CMD}}/{{COVERAGE_CMD}} 自行包含安装命令。建议同时把该安装步骤作为显式 step 而非塞进占位符，便于排障。

### P1-6 D:/Workspace/zgrwo/Harmonization/VibeCodingTemplate/CHANGELOG.md:7 [CHANGELOG 与 git tag 一致性]
- **问题**: v0.1.2 已发布（本地 refs/tags/v0.1.2 与远程 origin/main fa5c61c 均存在），但 HEAD CHANGELOG.md 无 [0.1.2] 节，且 .release-please-manifest.json 仍为 0.1.1；本地 main 与 origin/main 已分叉（各 ahead/behind 2 提交，未包含 25decc8 与 fa5c61c 两个 0.1.2 发布提交）。
- **影响**: 从当前分支发 0.2.0 时，release-please 基于 v0.1.1 与 manifest 计算版本，生成的 CHANGELOG 将遗漏已发布的 0.1.2 条目，且新 tag 与远程 v0.1.2 冲突/重复，发版结果与线上发布历史不一致。
- **修复**: 发版前先合并/变基 origin/main（纳入 25decc8 'release 0.1.2' 与 fa5c61c 合并提交），.release-please-manifest.json 同步为 0.1.2，再触发 release-please 发 0.2.0。

### P1-7 scripts/falsy-audit.py:208 [准确性]
- **问题**: _check_or_fallback 在遇到第一个"可命名但未命中风险名单"的操作数时无条件 break，漏检其后真正的 HIGH/MEDIUM 风险操作数（如 `return result or threshold or 0.05`、`if result or threshold:`）。
- **影响**: 这是 falsy-audit 文档明确列出的检测变体（'x or <default> —— or 回退模式（threshold=0 时被默认值覆盖）'），但最常见的写法 `return result or threshold` 完全漏检：已实测 `def f(result, threshold): return result or threshold or 0.05` 产出 0 条 finding。CI 硬门禁（零 HIGH）会放行真实的 falsy 误判缺陷。
- **修复**: 把 line 208 的 `break` 移到 `if level:` 分支内部，未命中名单的变量操作数继续扫描后续操作数（与函数调用操作数 `continue` 的行为一致），直到找到已分类操作数或链尾。

### P1-8 scripts/run-affected-tests.py:93 [维度7-代码质量]
- **问题**: find_tests_for() 子串匹配未归一化连字符：kebab-case 脚本（verify-docs.py/gen-doc-counts.py 等）永不匹配其 snake_case 测试（test_verify_docs.py 等），工具在自身仓库真实场景直接误报 FAIL
- **影响**: 实测 `python scripts/run-affected-tests.py --dry-run`（HEAD~1..HEAD 改动 4 个脚本）返回退出码 1，把 gen-doc-counts/run-affected-tests/test-quality-guard/verify-registries 全部误报为"疑似缺测"——而这 4 个都有对应测试。与工具 docstring「防门禁说谎」自相矛盾：开发者改完脚本跑增量路由必得假阴性；若 CI 接入将阻塞合入。根因：第 94 行 `if stem.lower() in p.name.lower()` 中 "verify-docs"（连字符）不是 "test_verify_docs.py"（下划线）的子串
- **修复**: 匹配前把连字符归一为下划线：`stem_n = stem.lower().replace("-", "_")`，对 `test_*.py` 与 `*Tests.cs` 两个分支均用 `stem_n in p.name.lower()` 判断

### P1-9 .github/workflows/ci.yml:153 [维度12-配置流断裂]
- **问题**: 本轮新增的 test-quality-guard.py 未接入 ci.yml quality-gate 与 Makefile docs target，违反 documentation.md:76 规定的注册链，且与 templates/README.md:148 声称的"make verify / CI"行为漂移
- **影响**: test-quality-guard.py 只接入 verify-all.py:96 与 verify-all.ps1:74，但 ci.yml quality-gate（153-167 行：verify-manual/falsy-audit/verify-docs/verify-registries/gen-doc-counts/代码风格/覆盖率）与 Makefile docs 目标（29-34 行）均无该步骤，模板自身 template-self-test 也不跑它。后果：携带弱断言/缺测/无意义命名的 PR 可通过 CI 硬门禁；templates/README.md:148 声称它运行于 "make verify / CI" 与 CI 实际行为不一致，属配置流断裂 + 文档行为漂移（AGENTS.md 高频修复模式「注册/同步遗漏」与「配置流断裂」的现场复发）
- **修复**: 在 ci.yml quality-gate 的 gen-doc-counts 步骤后追加 `python scripts/test-quality-guard.py`，Makefile docs 目标追加同命令，并同步 test-template.ps1 自测清单；或若有意不在 CI 跑则修正 templates/README.md:148 的声称

### P1-10 scripts/init-project.ps1:151 [compatibility]
- **问题**: init-project.ps1 与 init-project.py 功能不对等：ps1 在占位符扫描/替换/未替换检查三处均不跳过 tests/ 目录，会把测试夹具 token（{{A}}/{{B}}/{{FOO}}/{{BAR}}/{{X1_}}/{{PROJECT_NAME}}）替换为小写/真实值，静默破坏生成项目的测试套件；而 py 版已用 SKIP_PLACEHOLDER_DIRS={"tests"}（init-project.py:56）显式跳过。
- **影响**: Windows 用户用 init-project.ps1 初始化的新项目，tests/scripts/test_init_project.py 中 `scan_placeholders("a a b") == ["A","B"]`（原 {{A}}/{{B}} 被替换为 a/b）与 `scan_placeholders(text) == ["PROJECT_NAME","X1_"]` 等断言必然失败，pytest 无法通过；且 test-template.ps1（CI）只跑 verify-docs/verify-manual/falsy-audit，不跑生成项目的 pytest，故 CI 全绿掩盖此缺陷。ps1 第 186-190 行把未登记 token 按 content 处理为 name.lower()，第 234-249 行对含 tests/ 的全部文件执行替换。
- **修复**: 与 py 版对齐：在 ps1 扫描（第 151 行 Where-Object）、替换（第 234 行 $files 构造）、未替换检查（第 279 行）三处加入跳过条件 `$_.FullName -notmatch "[\\/]tests([\\/]|$)"`，或在扫描前排除 tests/ 目录。

### P1-11 scripts/run-affected-tests.py:94 [13 性能 / 工具就绪性]
- **问题**: find_tests_for 用 `stem.lower() in p.name.lower()` 子串匹配，未把连字符归一化为下划线：`scripts/gen-doc-counts.py` 的 stem `gen-doc-counts` 永远不匹配 `test_gen_doc_counts.py`，导致 --dry-run 对 4 个本有测试的脚本谎报"缺测"
- **影响**: 实际可复现：`python scripts/run-affected-tests.py --dry-run` 报 FAIL，列出 gen-doc-counts/run-affected-tests/test-quality-guard/verify-registries 四个"疑似缺测"，但 tests/scripts/ 下对应 test_*.py 全部存在（我已在隔离环境复现：4 个全返回空列表）。非 dry-run 模式在 target_tests 为空时直接 return 1（第 126-130 行），编辑任意连字符命名脚本的开发者在非 dry-run 下会得到假性阻断，且其真实测试不会被运行。该回归正是 HEAD 提交 22a2eca"纳入 src/ 与 scripts/"所引入——此前只扫 src/（无连字符文件）不触发，现扩到 scripts/ 后必然触发
- **修复**: 在 find_tests_for 比较前做分隔符归一化，例如 `if stem.lower().replace('-', '_') in p.name.lower():`（或对两边统一 replace('-','_')）。并补一条测试用例：`scripts/gen-doc-counts.py` → `test_gen_doc_counts.py`。当前 test_run_affected_tests.py 只覆盖 src/foo/bar.py→test_bar.py 这种下划线对齐场景，未覆盖连字符文件名

### P1-12 CHANGELOG.md:7 [16 发行准备]
- **问题**: 本地审查基线分支已与 origin/main 分叉：本地 CHANGELOG 最新 release 段为 [0.1.1]、.release-please-manifest.json=0.1.1，但远端 main 已在 fa5c61c 合并 v0.1.2（PR #8），远端 manifest=0.1.2 且存在远端 tag v0.1.2，本地这两笔 release 提交（25decc8/fa5c61c）不在本地历史中
- **影响**: git merge-base= ddf0d11；本地独有 3410791+22a2eca，远端独有 25decc8+fa5c61c。直接基于当前分支推 v0.2.0 会先与远端 v0.1.2 合并，生成的 CHANGELOG/manifest 与已发布的 v0.1.2 不一致（本地无 v0.1.2 条目、无对应 tag），v0.2.0 release-please 从旧 base 计算 diff 可能重复 0.1.2 内容或产生冲突。发行前必须先把 origin/main（含 v0.1.2）合入/重定基到本分支
- **修复**: 发版前执行 `git pull --rebase origin main`（或合并 origin/main），使本分支包含 v0.1.2 release 提交与 tag，并确认 CHANGELOG 出现 [0.1.2] 条目、manifest 对齐到 0.1.2 后再生成 v0.2.0 release PR

## P2 修复清单（19 项，改善）

### P2-1 docs/architecture.md:31
- **问题**: 占位符机制文档与实现不一致：docs/architecture.md:31 与 templates/README.md:45 均称 init 使用正则 `\{\{(\w+)\}\}`，templates/README.md:49 断言 `{{Name}}` 会被 init 误替换为小写 `name`；但实际实现 scripts/init-project.py:85（scan_placeholders/replace_placeholders）与 scripts/init-project.ps1:148（$placeholderRe）均为 `\{\{([A-Z0-9_]+)\}\}`（仅大写）。当前实现下 `{{Name}}`（含小写）与 `.github/workflows/docker.yml.template:38` 的 GH Actions 原生 `{{version}}` 根本不会被匹配或替换。
- **修复**: 将 docs/architecture.md:31 与 templates/README.md:45 的正则更正为 `\{\{([A-Z0-9_]+)\}\}`，并把 README:49 的"误替换为 name"改写为"`{{Name}}` 不被 init 匹配、原样保留；泄漏由 ci.yml 模板守卫（grep `{{` templates/NewModule/）兜底"。

### P2-2 templates/NewModule/{Name}Udf.bas.template:28
- **问题**: Udf 模板硬编码 `VariantKit.NormalizeInput`，但 VariantKit 模板的目标文件名是 `{Name}VariantKit.bas` 且无 `Attribute VB_Name`，导入 VBE 后模块名由文件名决定，不等于 VariantKit，引用无法解析。
- **修复**: 三选一：(1) 目标文件统一命名为 VariantKit.bas（共享层，README 已写“首次使用即复制，后续模块共用”）；(2) 模板顶部加 `Attribute VB_Name = "VariantKit"` 固定模块名；(3) Udf 模板改用与文件名一致的引用（如 `{Name}VariantKit.NormalizeInput`）并在 README 说明。

### P2-3 templates/NewModule/{Name}Core.Tests.cs.template:20
- **问题**: C# 测试模板未覆盖 L4 溢出/最大值的 Inf 结果断言之外的 L5 未知类型路径也仅以注释形式给出，且 {Name}Core.Tests 无 CrossVal 配对（C# 数值结果无交叉验证模板）。
- **修复**: 为 double.MaxValue/MinValue 增加显式 NaN 期望断言（Compute 当前返回输入值，测试实为恒真），并把 L5 invalid-type 反例从注释改为可执行测试（如传入 object 非数值场景）。

### P2-4 .github/workflows/security.yml:43
- **问题**: pip-audit 步骤的依赖安装链路 `... || true` + `2>/dev/null` 会在两条安装路径都失败时静默吞掉，审计退化为仅扫 runner 环境
- **修复**: 去掉尾部 `|| true`，改为显式检查：有清单则安装并失败硬退出，无清单则 `|| { echo "::error::未找到 pyproject.toml 或 requirements.txt，pip-audit 无法审计项目依赖"; exit 1; }`；主路径去除 `2>/dev/null` 以便看到真实安装错误。

### P2-5 D:/Workspace/zgrwo/Harmonization/VibeCodingTemplate/CHANGELOG.md:164
- **问题**: CHANGELOG.md 第 164 行 `## [0.1.0] - {{DATE}}` 含未替换的 {{DATE}} 占位符，而 [0.1.1] 节已有真实日期（2026-08-09），同文件同层级格式不一致。
- **修复**: 将 {{DATE}} 替换为实际日期，或移除遗留的 [0.1.0] 手工段（release-please 首次接管时会重建）。

### P2-6 D:/Workspace/zgrwo/Harmonization/VibeCodingTemplate/rules/cross-project-synthesis.md:13
- **问题**: 第 13 行声明'以下 8 类问题在 5 个项目中反复出现'，但该章节实际有 9 个编号条目（### 1 至 ### 9，含本轮新增的'测试文件命名与框架 glob 不匹配'）；AGENTS.md:253 同步的'反模式案例库（8 类）'同样过期。
- **修复**: 将 cross-project-synthesis.md:13 与 AGENTS.md:253 的'8 类'改为'9 类'（或合并第 9 类到已有类别）。

### P2-7 D:/Workspace/zgrwo/Harmonization/VibeCodingTemplate/templates/README.md:23
- **问题**: 目录文件表缺 `language/offline-setup.py.template`：language 段只列 8 行（pyproject/tsconfig/Directory.Build.props/nuget/{Name}.Tests.csproj/go.mod/Dockerfile/docker-compose.yml），而 templates/language/ 实际有 9 个文件；全表 23 行 vs 实际 24 个模板文件。offline-setup.py.template 仅在'治理脚本速查'第 139 行被提到。
- **修复**: 在 language 段补一行 `language/offline-setup.py.template`（离线安装工具，含 --print-cmd 干跑）。

### P2-8 D:/Workspace/zgrwo/Harmonization/VibeCodingTemplate/rules/sentinel-contract.md:1
- **问题**: 本轮 A4 新增的 CLAIM 声称值校验约定（verify-manual.py 的 _CLAIM_RE/manual_check）仅在 templates/NewModule/{Name}CrossVal.py.template（第 17/50 行）与 scripts/verify-manual.py 中体现；user-manual.md、documentation.md、sentinel-contract.md 均未登记该约定，sentinel-contract.md 全文无任何 CLAIM 标记引用（与任务标注'含 CLAIM 标记引用'不符）。
- **修复**: 在 user-manual.md（或 documentation.md）补 CLAIM 标记语法与 manual_check 用法说明；sentinel-contract.md 守卫清单补充指向 CLAIM/manual_check 的交叉引用。

### P2-9 scripts/falsy-audit.py:210
- **问题**: visit_AnnAssign 只收集类型注解，从不检查 `node.value` 是否为 or-fallback（BoolOp Or），导致 `total: int = count or 0`（count 为 HIGH 名）在默认 AST 模式下漏检，而正则兜底模式却能检出。
- **修复**: 在 visit_AnnAssign 中仿照 visit_Assign 增加对 `node.value` 的 BoolOp 检查，调用 `self._check_or_fallback(node.value, "assign or")`。

### P2-10 scripts/test-quality-guard.py:39
- **问题**: _STRONG_ASSERT_RE 只识别 `assert a == b` 的裸标识符形式，不识别下标/属性访问断言（`assert df["col"].sum() == 5`）与 `assert len(x) == 2` 这类 len==N 相等断言。
- **修复**: 扩展 _STRONG_ASSERT_RE 以匹配下标/属性访问（如 `assert\s+\w+(\[.*\]|\.\w+)*\s*[=!]=\s*\w+`）以及 `len(...)==N`/`len(...)!=N` 形式；并补充对应测试。

### P2-11 scripts/verify-manual.py:131
- **问题**: compare() 序列分支对数值型期望元素执行 `float(a)` 强制转换，当 actual 含非数值元素（如字符串列表）时抛出未捕获的 ValueError。
- **修复**: 在 float(a) 处包 try/except (ValueError, TypeError)，捕获时记 FAIL 并打印元素级 '[FAIL] 类型不匹配'，保持与 compare 其余分支一致的降级语义。

### P2-12 scripts/verify-registries.py:126
- **问题**: regex_extract 分支用 `pattern.findall(text)` 直接 update 进集合，当配置的正则含 2 个以上捕获组时返回元素为 tuple 而非 str，与 json_keys 的字符串键比较产生垃圾输出。
- **修复**: 限制 regex_extract 只能取第 1 个捕获组（无组则取整段匹配），或对多捕获组模式给出[配置错误]并返回非零；补充单组/多组/无组三种模式的测试。

### P2-13 scripts/run-affected-tests.py:137
- **问题**: 混合变更场景（部分 src 文件有测试、部分没有）时，打印的提示文案引用'见上 FAIL 提示'，但 FAIL 块只在全部文件无测试时(line 126)才会输出；且此时 exit 0，缺测源文件未获任何强制。
- **修复**: 在混合场景下对每个 unmatched 源文件单独输出 '[FAIL] ... 无对应测试' 行（或在存在 unmatched 时返回非零），使提示与实际退出码一致。

### P2-14 tests/scripts/test_run_affected_tests.py:32
- **问题**: run-affected-tests 自身测试仅覆盖 snake_case 映射（test_bar.py/BarTests.cs），无 kebab-case 脚本名用例，导致连字符映射缺陷逃过门禁
- **修复**: 补用例：`find_tests_for("scripts/gen-doc-counts.py", tmp) == ["test_gen_doc_counts.py"]`，断言连字符源文件可命中对应测试

### P2-15 templates/README.md:142
- **问题**: 新脚本 run-affected-tests.py 未登记「治理脚本速查」表（templates/README.md 142-149 行）与 cross-project-synthesis 索引表（170-185 行），违反 documentation.md:77 维护链对新治理脚本的登记要求
- **修复**: 在 templates/README.md 速查表补一行 `run-affected-tests.py`（影响范围测试路由，何时运行：make test/开发增量），并在 cross-project-synthesis 索引表补对应条目

### P2-16 scripts/run-affected-tests.py:43
- **问题**: 三个 subprocess.run(..., capture_output=True, text=True) 未指定 encoding，在 GBK 区域（中文 Windows）下用 cp936 解码 git 的 UTF-8 输出；已在本机（Python 3.14, locale cp936）复现：变更含非 ASCII 文件名的文件时抛出 UnicodeDecodeError（'gbk' codec can't decode byte 0xad），脚本无 catch 直接崩溃（except 只捕获 FileNotFoundError/TimeoutExpired）。
- **修复**: 在三个 subprocess.run 调用（43、50、56 行）追加 `encoding="utf-8", errors="replace"`；或将 `git -c core.quotepath=false` 输出先按 bytes 读再显式 decode 为 utf-8。

### P2-17 skills/go-SKILL.md:32
- **问题**: 哨兵契约术语跨语言技能不一致：SSOT 规则 rules/sentinel-contract.md 标题与 csharp-SKILL.md:77 用「哨兵契约」，而 go-SKILL.md:32「错误哨兵值」/:38「哨兵值模式」描述同一概念；python-SKILL.md / typescript-SKILL.md / vba-SKILL.md 则完全未引用该术语或 rules/sentinel-contract.md。
- **修复**: 统一采用 SSOT 术语「哨兵契约」，在 go-SKILL.md 等文件同步替换/加别名注记；python/typescript/vba 技能补充对 rules/sentinel-contract.md 的引用（其 Core 模式同样依赖 NaN 哨兵）。

### P2-18 README.md:103
- **问题**: README.md 文档索引（第103-119行）未收录本轮 v0.2.0 新增的核心规则 rules/sentinel-contract.md，也未收录 rules/pre-release-review.md；而 README.en.md Key Concepts（第76行）收录了 pre-release-review.md 却同样缺失 sentinel-contract.md，中英文索引不对称。
- **修复**: README.md 文档索引补入 sentinel-contract.md（哨兵契约/守卫清单）与 pre-release-review.md 两行；README.en.md Key Concepts 表补入 sentinel-contract.md 条目，使中英文收录对齐。

### P2-19 rules/tooling-pitfalls.md:55
- **问题**: 本轮审查发现的新坑位未登记知识库："源文件命名用连字符、测试文件名用下划线，工具子串匹配未归一化分隔符→匹配失效"（即 run-affected-tests 假"缺测"），tooling-pitfalls.md 现有 23 条中无此条目
- **修复**: 在 tooling-pitfalls.md 追加 #24："工具命名映射未归一化连字符/下划线（如 gen-doc-counts.py vs test_gen_doc_counts.py）→ 子串匹配失效、门禁谎报缺测"，正确做法：比较前统一 replace('-', '_')；在 AGENTS.md 高频修复模式表加一行（根因：文件命名分隔符不一致 + 工具未归一化），cross-project-synthesis.md 反模式库补第 10 类或并入现有命名类

## P3 修复清单（28 项，建议）

### P3-1 scripts/verify-all.py:1
- **问题**: 维度1「门禁全绿」无缺陷：实测 verify-all.py 全流程退出码 0（构建 compileall / pytest 164 passed / 文档一致性 --strict / 手册一致性 / Falsy 审计 / 注册表一致性 / 文档计数 --check / 测试质量守卫），`python -m ruff check src/ scripts/` 输出 All checks passed，`pytest --cov=scripts --cov-fail-under=35` 为 164 passed 覆盖率 79.95%（≥35%），git status 干净无变更。
- **修复**: 无需修复。

### P3-2 scripts/verify-registries.py:57
- **问题**: placeholder_scan 会扫描脚本自身源码注释与 AGENTS.md，导致每次 verify-all/CI 恒定输出 7 条未登记 WARN（A/FOO/NAME/UPPER/UPPER_CASE/X/X1_）：来源为 verify-registries.py:30 `{{NAME}}`、:57 `{{FOO}}`/`{{A}}`（docstring 示例）、init-project.py:54 `{{A}}/{{X1_}}`、:466 `{{X}}`（源码注释）、AGENTS.md:239 `{{X}}/{{UPPER}}/{{UPPER_CASE}}`。这与 EXCLUDED_DIRS 注释（第56-60行）"tests/ 含夹具，计入会大量 WARN 淹没真实信号故排除"的设计理由自相矛盾——同样的噪声源（源码注释/AGENTS.md）却未排除。
- **修复**: 在 verify-registries.py 为这些教学转义 token（A/FOO/NAME/UPPER/UPPER_CASE/X/X1_）加显式 allowlist，或让 placeholder_scan 跳过源码注释行，使 WARN 仅代表真实未登记占位符。

### P3-3 scripts/placeholders.json:110
- **问题**: 占位符编号序列化不一致：DEFAULT_2（第110行）是全库唯一"有 _2 无 _1"的 token（rules/api-reference.md:26 用作 PARAM_2 默认值，语义属"参数下标"而非"家族序号"，与 MODULE_1/2、PREFIX_1/2、DESC_1/2 等家族编号混用）；另有 9 个 `_1` 单例无 `_2`：EDGE_1、ERROR_CONDITION_1、ERROR_FIXABLE_1、ERROR_MEANING_1、ERROR_VALUE_1、FUNCTION_1、INPUT_1、OUTPUT_1、PARAM_EXAMPLE_1。rules/specification.md 功能细表（第39行）仅覆盖 MODULE_1，开发者补 MODULE_2 细表时需自造未登记的 FUNCTION_2/EDGE_2 等 token。
- **修复**: 统一编号语义：`_1` 单例去后缀（EDGE/ERROR_CONDITION/FUNCTION/INPUT/OUTPUT 等），或为 DEFAULT 补 DEFAULT_1（与 api-reference.md 参数表行对齐）；在 rules/pre-release-review.md 占位符检查中增加"`_1/_2` 家族完整性"断言。

### P3-4 templates/language/{Name}.Tests.csproj.template:28
- **问题**: 测试 csproj 模板的 ProjectReference 指向 `../../src/{Module}/{Module}.csproj`，但 templates/README.md 的 C# 流程只复制 Core/Udf/Foundation/Tests/CrossVal，未创建 src/{Module}/{Module}.csproj。
- **修复**: 在 README C# 流程中补充“新建 src/{Module}/{Module}.csproj（classlib，含 Directory.Build.props）”一步，或说明该流程基于已存在的模块项目。

### P3-5 templates/NewModule/{Name}CrossVal.py.template:34
- **问题**: CrossVal 模板使用 {N} 与 {模块说明} 两个单花括号占位符，未列入 templates/README.md 占位符表。
- **修复**: 在 templates/README.md 占位符表中补登 {N}、{模块说明} 两行，或改用在表中已登记的占位符表述。

### P3-6 templates/language/docker-compose.yml.template:26
- **问题**: compose 健康检查硬编码 `python -c ...`，但 Dockerfile 运行时支持 Go/Node 且 placeholders.json 中 RUNTIME_IMAGE 测试值为 gcr.io/distroless/static-debian12（无 python）。
- **修复**: healthcheck 改为多阶段条件式（如 Python 用 urllib、Go/Node 各自探测），或在模板顶部注释中明确该 healthcheck 仅适用于 Python 运行时需手动替换。

### P3-7 .github/workflows/security.yml:44
- **问题**: `python -m pip_audit` 审计的是整个已安装环境（含 runner 预装系统包与 pip-audit 自身依赖），而非仅项目依赖
- **修复**: 改用项目依赖文件定向审计：`python -m pip_audit -r requirements.txt`（有 requirements.txt 时）或 `python -m pip_audit -r <(pip freeze)`；无清单时显式失败（见上一发现）。

### P3-8 .github/release-please/config.json:6
- **问题**: config.json 开启 `bump-patch-for-minor-pre-major: true` 且 manifest=0.1.1，含 v0.2.0 意图的 feat 提交在下次发版时自动推导为 0.1.2 而非 0.2.0
- **修复**: 发版时在 release PR 的 commit body 加 `Release-As: 0.2.0`；若希望自动推导 0.2.0，需将 config 中 `bump-patch-for-minor-pre-major` 改为 false（或移除），使 pre-major 下 feat 升 minor。

### P3-9 .github/workflows/ci.yml:212
- **问题**: 模板守卫 `grep -rn "{{" templates/NewModule/ | grep -v ROOT_NAMESPACE` 是行级过滤：同一行同时含合法 {{ROOT_NAMESPACE}} 与泄漏的双花括号占位符时整行被剔除，泄漏被隐藏
- **修复**: 改为按占位符粒度过滤：先提取 `{{...}}` 再剔除恰为 `{{ROOT_NAMESPACE}}` 的 token（如 `grep -rn -o "{{[A-Za-z_]*}}" templates/NewModule/ | sort -u | grep -v '^{{ROOT_NAMESPACE}}$'`），并保留命中行号。

### P3-10 D:/Workspace/zgrwo/Harmonization/VibeCodingTemplate/docs/absorption-plan-2026-08.md:30
- **问题**: 计划内基线计数已过期：第 30/80 行'68 tests / 62%'（现为 164 tests / 80%）、第 55/64 行 DOC_FILES'当前 33 项'（现为 34 项）、第 57 行'~117 个占位符'（现为 114 项）。
- **修复**: 在计划头部标注'已执行完成（2026-08-12）'，并将基线数字限定为'执行前快照'或更新为当前真实值。

### P3-11 D:/Workspace/zgrwo/Harmonization/VibeCodingTemplate/README.md:101
- **问题**: README.md『文档索引』表（第 101-119 行）缺 sentinel-contract.md 与 pre-release-review.md，而 AGENTS.md『参考』表第 337/343 行已登记这两份文档；README.en.md『Key Concepts』亦未列 sentinel-contract.md。
- **修复**: 在 README.md 文档索引补 sentinel-contract.md（防御契约）与 pre-release-review.md（审查模板）两行，并在 README.en.md Key Concepts 同步 sentinel-contract.md。

### P3-12 scripts/verify-manual.py:208
- **问题**: manual_check 每次调用都重新执行 load_claims()，即每比对一个声称值就重读并重扫整个 user-manual.md。
- **修复**: 在 run_crossval() 开头加载一次 claims 缓存为模块级或闭包变量，manual_check 复用该缓存。

### P3-13 scripts/retry.py:42
- **问题**: 公共函数 retry_transient 的 classifier 参数与返回类型未注解，内部 decorator/wrapper 也无返回注解（_default_classifier 已注解）。
- **修复**: 补全签名：`classifier: Callable[[BaseException], bool] | None = None` 及 `-> Callable[[Callable[P, R]], Callable[P, R]]`（或简单 `-> Callable`），与 ruff ANN 约定对齐。

### P3-14 tests/scripts/test_verify_registries.py:26
- **问题**: 覆盖率最低模块的关键错误路径无测试：verify-registries 的 regex_extract 分支（本轮新增）零用例；falsy-audit 的 or 链多操作数、AnnAssign 形式无用例；verify-manual 的 compare 类型不匹配崩溃路径无用例；run-affected-tests 的 git 子进程失败路径无用例（模块覆盖率 60%）；verify-all main()/--quick 编排无用例（覆盖率 53%，为最低）。
- **修复**: 为上述路径各补一条检出型测试：regex_extract 单/多捕获组、falsy or 链首操作数未分类、AnnAssign or 回退、compare 数值 vs 字符串序列、get_changed_files 子进程异常。

### P3-15 scripts/test-quality-guard.py:149
- **问题**: check_missing_tests 内 `rel = _rel(p)` 与 `problems.append(...)` 缩进 20 空格，超出外层 if 块 16 空格 4 层，属过度缩进，与文件其余 4 空格步进不一致
- **修复**: 将 149-152 行缩进从 20 空格对齐为 16 空格

### P3-16 scripts/gen-doc-counts.py:97
- **问题**: update_doc() 函数从 97 行到 201 行共 105 行，超过单函数 ≤50 行的可读性阈值，内联/块状两种标记形态逻辑耦合在同一个 while 循环
- **修复**: 将内联处理与块状处理拆分为 `_update_inline(...)` 与 `_update_block(...)` 两个辅助函数，各自 ≤40 行，主函数仅做分发

### P3-17 scripts/doc-counts.json:8
- **问题**: doc-counts.json 定义了 scripts/rules/skills 三个计数源，但全仓库无任何 AUTO_COUNTS:SCRIPTS/RULES/SKILLS 标记引用（实测仅 architecture.md 用 TESTS、README.md 用 PLACEHOLDERS），属死配置条目
- **修复**: 删除 doc-counts.json 中 scripts/rules/skills 三个未使用计数源（或在使用时再登记），保持配置即使用

### P3-18 scripts/gen-doc-counts.py:185
- **问题**: 块状 AUTO_COUNTS 标记重写分支用硬编码 `\n` 重建三行（185-187），未沿用原文件行尾；若源文档为 CRLF，运行 `gen-doc-counts.py`（update 模式）会把该块写成 LF，产生混合行尾，违反本仓 .gitattributes eol=lf 与 .pre-commit mixed-line-ending 门禁。当前仓库未触发（README.md 为 LF；docs/architecture.md 唯一标记是内联形态，内联分支保留原行尾），属潜在缺陷。
- **修复**: 按原文件行尾生成块：判断 source line 的终止符（`line.endswith('\r\n')` 用 CRLF，否则 LF），替换 185-187 三行 f-string 末尾的 `\n`。

### P3-19 scripts/init-project.ps1:63
- **问题**: init-project.ps1 复制模板时未跳过根级 .coverage 运行产物，且清理列表（67 行）仅含 __pycache__/.venv/node_modules/bin/obj，不含 .pytest_cache/.ruff_cache/.mypy_cache/dist/TestResults/venv/env，与 py 版 SKIP_TOP_FILES={".coverage"}+CLEANUP_DIRS（init-project.py:48-53）不对等。
- **修复**: 在 ps1 复制 Where-Object 排除 .coverage，并把 py 版 CLEANUP_DIRS 全量清单同步到 67 行 $junk 数组。

### P3-20 scripts/init-project.py:444
- **问题**: init-project target 仅做 resolve() 与"非空需 --force"校验，未阻止 target 位于 TEMPLATE_ROOT 内部或等于模板根；copy_template 在 target.mkdir 后才迭代 TEMPLATE_ROOT（137-177 行），若 target 是模板子目录，复制循环会把已创建的 target 自身及其父目录再拷进 target（如 examples/ 连同新建子目录被 copytree 嵌套），污染模板树。
- **修复**: 在 main 校验段增加守卫：`if TEMPLATE_ROOT == target or target.is_relative_to(TEMPLATE_ROOT): print('[ERROR] target 不能在模板仓库内'); return 1`。

### P3-21 scripts/init-project.py:249
- **问题**: 占位符替换值（--values JSON 或交互输入）被逐字写入 .py/.ps1/.yml/.json 等所有文件，无任何校验/转义；含换行、引号、反引号、`$(`、`{{`、`${{ ... }}` 的值可直接改写生成项目的 CI 工作流或代码语义（自注入，值由运行者本人提供，非权限边界，但缺纵深防御）。
- **修复**: 在 replace_placeholders 对值做合法性检查（非交互 --values 时尤其）：值含 `\n`/`\r`/`${{`/`{{` 等字符时打印 [WARN] 提示可能破坏目标文件，交互输入时给出确认。

### P3-22 .github/workflows/security.yml:43
- **问题**: pip-audit 步骤用 `|| true` 吞掉依赖安装失败：`pip install -e ".[dev]" ... || pip install -r requirements.txt ... || true`，两步都失败后仍继续 `pip_audit`，审计的是残缺环境（缺失依赖不审计），且本仓不存在 requirements.txt 回退项。
- **修复**: 区分安装与审计：`pip install -e ".[dev]"` 失败即 `exit 1`（回退 `-r requirements.txt` 仅当文件存在），确保安装成功后才运行 pip-audit。

### P3-23 .github/workflows/ci.yml:41
- **问题**: 安全子维度核验结果（无发现，备案）：全仓扫描 password|secret|token|api_key 仅命中教学/夹具提及（placeholders.json:103 "secret" 为 DB_PASSWORD 的 demo test 值，rules/pre-release-review.md:280 为检测命令教学），无真实密钥；CI 各 workflow 权限最小化（ci.yml contents:read、security.yml 仅 +security-events:write、release.yml/stale.yml 仅在对应 job 需要的 write）；pre-commit 全部来自 pinned 官方仓库（.pre-commit-config.yaml:23/42/50）；git-hooks/commit-msg 以引号参数 exec validate-commit-msg.sh，validate-commit-msg.sh 用 case/grep 匹配提交信息而不 eval 其内容，无注入路径；错误消息仅暴露本地 CLI 用户自输入路径，无信息泄露边界。
- **修复**: 无需修复；建议发版前用 `gitleaks` 或 GitHub secret scanning 复核一次全仓历史。

### P3-24 README.en.md:44
- **问题**: 本轮 v0.2.0 新增的 6 个自举验证脚本（verify-registries.py / gen-doc-counts.py / verify-docs.py / verify-manual.py / test-quality-guard.py / doctor.py）在英文版 README 完全无对应，Verify 节仅列 verify-all.py / verify-all.ps1（第44-52行），脚本作用仅存在于中文 templates/README.md「治理脚本速查」。
- **修复**: 在 README.en.md 增加简要'验证脚本'表（脚本名 + 作用 + 触发时机，对应 make verify / make doctor），或提供双语说明段。

### P3-25 CHANGELOG.md:164
- **问题**: 已发布历史段 `## [0.1.0] - {{DATE}}` 残留未替换的 {{DATE}} 占位符
- **修复**: 顺手把 `[0.1.0] - {{DATE}}` 填为实际日期（如 `2026-08-07`），或确认 release-please 接管策略已覆盖此段后保留（建议前者，成本极低）

### P3-26 scripts/test-quality-guard.py:98
- **问题**: check_weak_asserts / check_naming / check_missing_tests 三个函数各自独立 rglob("test_*.py")（第 98/116/133 行）对 tests 目录做 3 次全量遍历
- **修复**: 将 tests 目录的 test_*.py 列表一次性 rglob 后在三个 check 函数间共享（如模块级缓存或传入预扫列表）

### P3-27 scripts/run-affected-tests.py:93
- **问题**: find_tests_for 在每个变更源文件循环内执行 rglob("test_*.py") + rglob("*Tests.cs")，对 tests 树做 O(变更数 × 树大小) 次全量遍历
- **修复**: 将 tests 目录扫描结果提升到循环外一次性构建索引（按 stem 分组），find_tests_for 只做集合查找，复杂度降为 O(树) + O(变更数)

### P3-28 .claude/exemptions.md:1
- **问题**: 本轮无需要豁免的项，且 .claude/exemptions.md 不存在——与审查基线"无 exemptions.md"一致，属正常状态，无需登记
- **修复**: 无操作；若后续选择将 run-affected-tests 命名映射问题作为已知风险延期，则须按规则登记到 .claude/exemptions.md 并附到期版本

## 完成标准
- P1 全部修复并验证
- P2 修复大多数（技术债项可记录豁免）
- P3 至少修复文档/SSOT 类（低成本高价值）
- 知识库更新（AGENTS高频模式/tooling-pitfalls/cross-project-synthesis）
- 最终：git commit + push 触发 release-please 发 0.2.0