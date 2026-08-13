# VibeCodingTemplate 发行前审查报告（Max 18 维度）

**审查级别**: Max（结合 `rules/code-review-prompt.md` 10 维度 + `rules/pre-release-review.md` 18 维度）
**审查日期**: 2026-08-13
**审查基线**: `c6693e9`（`fix(ci): pip-audit 定向审计项目依赖`）
**目标版本**: v0.2.0
**审查方式**: 6 路并行审查代理（Python 脚本 / 模板 / CI·CD / 文档·规则·技能 / 示例跨语言 / 安全）+ 主会话对抗验证

---

## 执行摘要

- 总发现数: **56**
- P0（阻塞）: **0**
- P1（高风险）: **2**
- P2（改善）: **18**
- P3（建议）: **36**
- 对抗验证驳回: **2**（docs 代理 2 项「34 tests」P1 降级为 P2，属文档漂移非功能阻断）
- 结论: 🟡 **修复 P1+P2 后可发行**（无 P0，核心自举机制有 1 处真实缺陷）

### 门禁基线（全部通过）

| 门禁 | 结果 |
|------|------|
| `python scripts/verify-all.py` | ✅ 通过（构建 / 测试 / 文档 / 手册 / falsy / 注册表 / 计数 / 测试守卫） |
| `python -m ruff check scripts/ tests/ examples/` | ✅ 零违规 |
| `python -m pytest tests/ --cov=scripts` | ✅ **169 passed · 覆盖率 79%**（远高于 35% 底线与 40% 目标） |
| `git status` | ✅ 干净（缓存产物均 gitignored） |

### 回归确认（上一轮 Max 审查 P1/P2/P3 修复状态）

上一轮（基线 `22a2eca`）的 P1 清单经抽查**全部真实修复**：`falsy-audit.py:208` break 已移入 `if level:` 分支、`{Name}Core.Tests.cs` 用 `Be(1.0)` 实参、`run-affected-tests.py` 连字符归一化（`replace("-","_")`）、`init-project.ps1` tests/ 三处跳过、`ci.yml` 补 `pip install -e ".[dev]"` + `test-quality-guard.py` 接线、`tsconfig` 移除 baseUrl、`subprocess` 补 `encoding="utf-8"`。本轮 P1 均为**上一轮未覆盖的新缺陷**。

---

## 各维度结果

### 维度 1: 门禁全绿 — 🟢
无缺陷。基线见上表。

### 维度 2: 占位符 SSOT 审计 — 🟢
114 项占位符与 README「114 项」一致；`verify-registries.py` 仅报 2 条教学性转义 WARN（`{{B}}`/`{{BAR}}`），无死条目。

### 维度 3: 模板穷尽审查 — 🟡
- `[P2] templates/NewModule/{Name}Core.cs.template:46` — Compute 默认实现 `return input`（恒等），而 Go/Python/TS Core 模板均 `value * 2.0`，四语言脚手架语义发散，跨语言交叉验证无法对齐同一数值行为。修复：统一为 `result = input * 2.0` 或在 README 显式声明 C# 恒等为有意。
- `[P2] templates/NewModule/{Name}Udf.bas.template:29` — UDF 调用 `{Name}VariantKit.NormalizeInput`，`{Name}` 替换后变成 `WeatherVariantKit`；但 VariantKit 是固定名基础设施模块（`skills/vba-SKILL.md` §1.2 与 ExcelVBA 库 `VBA-Core/VariantKit.cls` 均固定名），而 `{Name}VariantKit.bas.template:3` 又指示「`{Name}` 替换为基础设施名」→ 产生 `VariantKitVariantKit.bas` 自相矛盾。修复：Udf 引用固定名 `VariantKit.NormalizeInput`，VariantKit 模板去 `{Name}` 前缀。
- `[P2] templates/NewModule/test_{Name}Core.py.template:21` — `from src.{Module}.{Name}Core import ...` 但 `language/pyproject.toml.template` 打包 `src/{{PACKAGE_NAME}}/`，pytest 段无 `pythonpath=["src"]`，`src/`/`tests/` 无 `__init__.py`。`pytest tests/` 开箱即 `ModuleNotFoundError`。修复：pytest 配置补 `pythonpath=["src"]` 并对齐目标目录与 `{{PACKAGE_NAME}}`。
- `[P2] templates/NewModule/{Name}CrossVal.py.template:31` — 只 import `check/cross_check/section`，从不 import 被测模块，示例调用未定义 `your_impl(...)`，verify-manual 的「0 PASS/0 FAIL」守卫必然硬失败。修复：补 `# from src.{Module}.{Name}Core import compute, process` 并让 `your_impl` 基于该 import 定义。
- `[P3]` 7 项：`{Name}CrossVal.py.template` 的 `manual_check` 未 import、`numpy/scipy` 死 import（F401）；`test_{Name}Core.py` 的 `import pytest` 未使用（F401）；`{Name}Core.py` 缺 NaN/Inf 输入守卫（仅 None，与 C#/Go/TS 不对称）；`{Name}Core.go` 注释引用未声明的 `ComputeResult` 类型；`{Name}Foundation.cs` 的 `{Name}` 语义与 Core/Udf 不一致（namespace 实为硬编码 `.Foundation`）；`{Name}.Tests.csproj` 头部指示替换不存在的 `{{ROOT_NAMESPACE}}`。

### 维度 4: CI/CD 穷尽审计 — 🔴（1 项 P1）
- `[P1] .github/workflows/ci.yml:67`（同 :119/:144/:212 与 `detect-template.yml:38`）— **模板自举检测失效**。检测用 `grep -rq '{{' AGENTS.md` 区分模板/项目模式，但 AGENTS.md 在 init 后**永久残留** `{{...}}` 字面量：① 第 71 行 `{{SCOPE_1/2}}`/`{{SKILL_1/2}}`/`{{DESCRIPTION_1/2}}` 含 `/`，扫描正则 `\{\{([A-Z0-9_]+)\}\}`（init-project.py:85/232）永不匹配；② 第 239 行 `{{X}}`/`{{UPPER}}`/`{{UPPER_CASE}}` 为未登记教学字面量，init 按「保留原样」处理（init-project.py:94/104/258）。→ 新项目 `is_template` 恒为 true，Build/Test/全量验证/LINT/COVERAGE/dependency-review 全部跳过，且 `template-self-test` 对真实项目运行（死条目硬校验会对约 180 个已替换占位符报错）。**已对抗验证 CONFIRMED**。修复：检测改为 grep 一个 init 必替换的登记核心占位符，如 `grep -rq '{{PROJECT_NAME}}' AGENTS.md`，5 处全部同步。
- `[P3] ci.yml:14` — `pull_request.paths` 缺 `pyproject.toml`/`Makefile`/`.pre-commit-config.yaml`，仅改依赖/工具文件的 PR 不触发任何 CI。
- `[P3] release-please/config.json:7` — `changelog-sections` 无 `style`/`revert`/`release`，但 `validate-commit-msg.sh:42` 接受这三类 → 提交过检却不出现在 CHANGELOG。
- `[P3] dependabot.yml:7` — 注释称「无语言清单文件」，但仓库根有 pyproject.toml，理由失实。
- `[P3] security.yml:55` — pip-audit 无清单时硬 `exit 1`，非 Python 项目未删 matrix 的 `python` 时 CI 必红。

### 维度 5: 文档穷尽审查 — 🟡
- `[P2] rules/pre-release-review.md:83 / :131` — Med 级硬编码「34 项通过」「当前 34 tests」，实际 169，审查模板 5 倍失真，误导后续审查。（对抗验证：降级为 P2 文档漂移，非功能阻断。）
- `[P2] rules/pre-release-review.md:269` — 覆盖率基线「35%」过时（实际 79%）。
- `[P2] CHANGELOG.md:60` — `[Unreleased]` 段位于 `[0.1.2]`（:7）/`[0.1.1]`（:14）**之下**，违反 Keep-a-Changelog（Unreleased 应在顶部），release-please 接管时可能错位。
- `[P2] docs/review-max-2026-08-12.md:15` — 「164 tests / 80%」过时（现 169 / 79%）。
- `[P2] docs/fix-max-review-2026-08-12.md:25` — 标题「9 项」实列 12 项，且 P1-6≡P1-12、P1-8≡P1-11 重复。
- `[P3]` 7 项：`review-max-2026-08-12.md:16` P1 计数矛盾、`fix-max-review-2026-08-12.md:168/204` 164/80 快照、`absorption-plan-2026-08.md:58/60/67`「33 项/117 占位符」、`README.en.md:119` 工作流表把 `dependabot.yml` 误列为 workflow 且漏 `detect-template.yml`、`sentinel-contract.md:59` 与 `csharp-SKILL.md` 存在语言落地事实双定义（轻 SSOT 张力）。

> ✅ 双目录树（AGENTS.md ↔ project-structure.md）**一致**（12 顶层目录完全匹配）；断链检查 `verify-docs.py --strict` 通过。

### 维度 6: Python 脚本深度审查 — 🟡
- `[P2] scripts/retry.py:40` — `_default_classifier` 返回 `(ConnectionError, TimeoutError, OSError)`，前两者是 OSError 子类，元组退化为仅 OSError，把 `FileNotFoundError`/`PermissionError` 误判为「瞬时可重试」。
- `[P2] scripts/falsy-audit.py:127` — `_type_hints` 是单一全局 dict 未按作用域清理；`def f(count: bool)` 会让后续无注解的 `def g(count): if count:` 被静默跳过，产生 CI 硬门禁假阴性。
- `[P2] scripts/run-affected-tests.py:65` — `get_changed_files` 捕获 git 失败返回 `[]`，main 映射为 `[SKIP]` exit 0，与 docstring「git 错误=1」自相矛盾，违反防门禁说谎。
- `[P2] scripts/verify-manual.py:37` — `SELF_CHECK_RE` 仅匹配裸标识符，`check("X", self.mean, self.mean)` / `obj.attr` / `d["k"]` 自校验可绕过「禁止自校验」红线。
- `[P2] scripts/gen-doc-counts.py:184` — 块状标记 suffix 提取 `line[m.end():].split("-->",1)` 因 `_MARK_START` 已吞掉尾部 `-->` 而永远取不到，块状 `<!-- AUTO_COUNTS:X_START --> 文字` 重写时静默丢尾文字。
- `[P3]` 11 项：`doctor.py:49` stdout/stderr 参数错位；`init-project.py:266` `remaining` 死逻辑（build_replacements 已全分类）；`init-project.py:186` `_in_skip_dirs` 用 any-depth 匹配（docstring 称「顶层」）；`verify-registries.py:83` 同 any-depth；`verify-manual.py:283` markdown 自校验扫描误伤教学反例；`test-quality-guard.py:88` weak 正则未去注释；`:39` `_STRONG_ASSERT_RE` 不识别 `math.isclose(...)` 调用断言；`verify-docs.py:225` 多处 read_text 无 try/except（非 UTF-8 崩溃）；`:424` bare-catch 正则无注释/字符串感知；`verify-all.py:41` `except (FileNotFoundError, OSError)` 冗余；`falsy-audit.py:287` 正则兜底无字符串感知。

### 维度 7: 代码质量 — 🟢
跨语言示例语义对齐见维度 3/10；脚本死代码/命名见维度 6 P3。无独立 P0/P1。

### 维度 8: 测试穷尽审计 — 🟢
覆盖率 79%（≥40% 目标）；`verify-registries` 的 regex_extract、falsy or 链多操作数、verify-manual compare 类型不匹配等路径仍缺用例（承接上一轮 P3-14，未阻塞）。

### 维度 9: 安全穷尽审查 — 🟡
- `[P2] scripts/init-project.ps1:59` — ps1 缺「target 不得在模板仓库内」守卫（py 版 :461 有）。`-Target <模板根> -Force` 会先 `Remove-Item -Recurse` 递归删除模板源码再自我复制。修复：镜像 py 版拒绝 target 等于/位于 `$template` 内。
- `[P3] scripts/init-project.py:144` — `--force` 对任意目标目录递归删除无守卫（`~`/`/` 误输入即灾难），无 `--dry-run`/确认。
- `[P3] scripts/init-project.py:236` / `init-project.ps1:240` — 占位符值逐字写入 .py/.yml 无净化（py 仅 WARN，ps1 无任何校验），`\n`/`${{`/反引号/`$(` 可改写生成项目 CI/代码语义。
- `[P3] pyproject.toml:21` — dev 依赖宽松范围 vs `.pre-commit-config.yaml:51` 锁定 `ruff==0.15.20`，CI 环境可漂移。

> ✅ 密钥检测：仅 placeholders.json 的 `DB_PASSWORD: secret` 与示例邮箱为有意占位测试值，无真实密钥；所有 subprocess 用 list args（无 shell=True/os.system）；CI 权限最小化、三方 action 全 SHA 锁定、无 PR 写权限泄密。

### 维度 10: 跨语言一致性穷尽审计 — 🔴（1 项 P1）
- `[P1] examples/tests/test_stats.go:1` — 文件名 `test_stats.go` **不以 `_test.go` 结尾**，`go test ./tests/...` 不发现任何测试（编译为普通包源码，报「[no test files]」），16 个 Go 测试静默跳过且绿码；README.md:19/38 谎称「16 tests」通过，且示例违背自身模板 `{Name}Core_test.go.template` 的命名约定。**已确认**（文件列表直接可见 + Go 框架 glob 规则）。修复：重命名 `test_stats_test.go`。
- `[P2] examples/conftest.py:11` — `sys.path.insert` 指向 `parent/"src"`，但测试 `from src.stats.StatsCore import` 需 `examples/` 在 path 上；docstring 的修复实为 no-op（仅因 pytest 顺带把 conftest 目录加入 path 才碰巧可用）。
- `[P2] examples/src/stats/StatsCore.py:35`（go:19 / ts:27 同构）— `mean()` 静默过滤 NaN/Inf（`mean([1,nan,3])==2.0`），而 `weighted_mean()`（:75）不过滤返回 NaN；同模块两函数无效值语义不一致，哨兵契约未统一应用。
- `[P3]` 4 项：`StatsCore.py:6` 头注释契约与实现矛盾；三语言均缺负权重/零和权重/溢出测试用例；`StatsCrossVal.py:29`「3 UDFs」实为 2；`StatsCore.py:24` docstring `Raises: TypeError` 未兑现。

### 维度 11-13: 架构合规 / 反模式 / 性能 — 🟢
层级依赖方向正确（scripts 不依赖 tests；rules 不依赖 skills）；SSOT 收敛基本到位；未发现 O(N²) 热路径（`test-quality-guard` 三次 rglob、`run-affected-tests` 循环内 rglob 已记 P3 级优化）。

### 维度 14: 兼容性 — 🟢
运行于 Python 3.14.5，代码目标 `py310`、未使用 PEP 695 等新语法；ps1/py 功能对等缺口见维度 9（P2 自删除守卫）与上一轮已修的 tests/ 跳过。

### 维度 15: 国际化 — 🟡
`README.en.md:119` 工作流表失真（见维度 5）；英文版验证脚本说明滞后（上一轮 P3-24 未复检，仍缺 6 个自举脚本表）。

### 维度 16: 发行准备 — 🟡
git tag `v0.1.1`/`v0.1.2` 与 manifest `0.1.2` 一致，CHANGELOG 含 `[0.1.2]`（上一轮 P1-6/12 分支分叉已合并）；但 `[Unreleased]` 段位置错乱（见维度 5）需在 release-please 接管前整理。

### 维度 17: 对抗验证轮次
对 2 项 P1 独立复核（非仅代理断言）：
- **CI 检测失效** — 主会话直接 grep 确认 5 处检测点 + init-project.py 扫描正则（`[A-Z0-9_]+` 不匹配 `/`）+ 未登记「保留原样」三处实现，**CONFIRMED**。
- **test_stats.go 命名** — 文件列表直接可见非 `_test.go` 结尾，Go 框架 glob 为事实标准，**CONFIRMED**。
- docs 代理 2 项「34 tests」P1 → 复核为文档漂移（非功能阻断），**驳回降级 P2**。

### 维度 18: 知识库更新
本次新增反模式建议登记：
- [ ] AGENTS.md 高频修复模式：新增「**模板自举检测锚点失配**」——检测 grep 用「任意 `{{`」而 AGENTS.md 恒留教学字面量（`/` 分隔或未登记 token），导致 is_template 永不翻转（根因：检测锚点未选「init 必替换」的登记核心占位符）。
- [ ] tooling-pitfalls.md：`grep '{{' AGENTS.md` 类「存在性探测」应锚定 `{{PROJECT_NAME}}` 等必替换 token，而非 `{{` 通配。
- [ ] cross-project-synthesis.md：反模式库补「示例代码未遵循自身模板约定」（test_stats.go 违 `_test.go`）。

---

## 修复后验证（已执行 2026-08-14）

全量修复后回归：

| 门禁 | 结果 |
|------|------|
| `python scripts/verify-all.py` | ✅ 全量通过（构建 / 测试 / 文档 / 手册 / falsy / 注册表 / 计数 / 测试守卫） |
| `python -m ruff check scripts/ tests/ examples/` | ✅ 零违规 |
| `python -m pytest tests/ -q` | ✅ 169 passed |

### 修复状态

- **P1（2/2）** ✅ 已修复
  - CI 检测锚点 `grep '{{'` → `grep '{{PROJECT_NAME}}'`（ci.yml ×4 + detect-template.yml ×1）
  - `test_stats.go` → `test_stats_test.go`（git mv + 头注释 + examples/README 映射）
- **P2（18/18）** ✅ 已修复（scripts 5 / templates 4 / examples 2 / security 1 / docs 5 / 其他 1）
- **P3（部分修复，12 项）** 代码级 + CI/文档级关键项已修复：
  - `doctor.py` stdout/stderr 参数对调；`verify-all.py` 冗余 except 合并为 `except OSError`
  - `StatsCrossVal.py`「3 UDFs」→「2 UDFs」；`StatsCore.py` 删除虚假 Raises TypeError
  - `{Name}Core.py.template` 补 NaN/Inf 输入守卫（跨语言对称）；`{Name}Core.go.template` 补 `ComputeResult` 类型别名
  - `ci.yml` paths 补 pyproject.toml / Makefile / .pre-commit-config.yaml
  - release-please 补 style / revert；dependabot.yml 更正「无语言清单」注释；README.en.md 工作流表补 detect-template.yml 并标注 dependabot 为 config
  - `test-quality-guard.py` 弱断言检测补注释剔除；`init-project.py` 补自删除护栏（与 ps1 对齐）

### P3 未修复项（如实说明）

以下 P3 属低价值 / 判断性 / 历史快照类，本轮未改动：

- 历史审查报告（review-max-2026-08-12.md / fix-max-review-2026-08-12.md / absorption-plan-2026-08.md）内陈旧计数 —— 历史快照，改动会失真
- `rules/sentinel-contract.md` 与 `skills/csharp-SKILL.md` 的哨兵契约「双定义」—— 需跨文件 SSOT 收敛，属结构决策
- `{Name}Foundation.cs` 的 `{Name}` 语义一致性 —— 属模板命名约定决策
- 模板示例注释中 numpy/scipy/`import pytest` 的 F401（注释示例，初始化填码后才激活）
- 三语言 negative-weight / zero-weight / overflow 边界测试补充（测试增强，非缺陷）
- `_in_skip_dirs` / `verify-registries` any-depth 判定、`verify-docs.py` read_text 容错、`falsy-audit` / `verify-manual` 正则字符串感知等健壮性 / 低价值项

## 签署

- 审查执行: Claude Code（max mode，6 路并行 + 对抗验证）
- 修复执行: Claude Code（P1+P2 全量 + P3 代码 / CI / 文档关键项）
- 最终结论: 🟢 **P1/P2 已全部修复并通过全量门禁**；P3 剩余项为建议级（文档 / 健壮性 / 测试增强），不阻断发行
