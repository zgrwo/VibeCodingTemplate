# VibeCodingTemplate 吸收计划（A+B+C 档 · 自举为主 · bump 0.2.0）

> **状态：已执行完成（2026-08-12）**。下文基线数字（68 tests / 62% / 33 DOC_FILES / ~117 占位符）为**执行前快照**，
> 当前实际值见 `docs/architecture.md`（AUTO_COUNTS:TESTS）与 `scripts/verify-all.py` 输出。

> **本文件是唯一执行依据** —— 中断后新会话可直接照此执行，不依赖原对话上下文。
> 所有来源路径、目标约定、验证步骤均已写入。执行时先读本文，再按阶段推进。
> 执行第一阶段前应把本计划复制到仓库内 `VibeCodingTemplate/docs/absorption-plan-2026-08.md` 持久化。

## Context（为什么做）

VibeCodingTemplate 是跨项目治理模板（rules/skills/scripts/templates/CI 自举，remote=`github.com/zgrwo/VibeCodingTemplate`）。5 个子项目
（`ExcelAddin函数库`/`ExcelVBA函数库`/`工程分析套件`/`成本分析套件`/`文档审查套件`，均位于 `D:/Workspace/zgrwo/Harmonization/`）
在真实开发中沉淀了一批模板尚未覆盖的高价值工程实践。本计划把这批实践**反哺回模板**，使其自举机制自动防御
AGENTS.md「高频修复模式」已登记痛点（注册遗漏 6+ / 文档数字漂移 6+ / 配置流断裂 4+ / 初始实现防御不足 5×15轮）。

**用户已确认三项决策：**
1. 范围：**A+B+C 档全吸收**（约 25 项，剔除已核实模板已覆盖的 B6 后实际 ~24 项）；D 档领域专属仅作 templates/language 可选参考，不强制
2. 落点：**模板自举为主** —— 新脚本进 `scripts/` 并接入 verify-all/CI 门禁，模板仓库自身也跑
3. 收口：**提交 + bump 版本 0.2.0**（semver minor），走 release-please 流程

**用户明确要求：** 计划做成持久化文件，中断后其他会话能独立接续执行。

---

## 执行前基线核对（第 0 步，必做）

```bash
cd D:/Workspace/zgrwo/Harmonization/VibeCodingTemplate
git status --short          # 必须干净
git describe --tags         # 应为 v0.1.1
python scripts/verify-all.py  # 必须全绿
pytest --cov --cov-fail-under=40  # 必须全过（68 tests / 62%）
```

---

## 目标模板关键约定（新脚本/文档必须遵守 —— 抄自当前实现）

### 脚本契约矩阵（现有 6 个入口）

| 脚本 | 调用签名 | 退出码 0 = | 退出码 1 = |
|---|---|---|---|
| `verify-docs.py` | `python scripts/verify-docs.py [--strict]` | 无断链/目录问题 | 断链/未声明 |
| `verify-manual.py` | `python scripts/verify-manual.py [--check-only]` | 无自校验 + crossval 通过/SKIP | 自校验或 crossval FAIL |
| `falsy-audit.py` | `python scripts/falsy-audit.py [--path dir]` | 无 HIGH 发现（LOW 仅 WARN） | ≥1 个 HIGH |
| `verify-all.py` | `python scripts/verify-all.py [--quick]` | 所有步骤通过（每步独立查退出码，失败即 break） | 任一步骤失败 |
| `verify-all.ps1` | `.\scripts\verify-all.ps1 [-Quick]` | 同上（`Invoke-Step` 内每命令独立 `$LASTEXITCODE` 检查，H1 已修复） | 任一步骤失败 |
| `test-template.ps1` | `.\scripts\test-template.ps1 [-Target dir] [-Keep]` | init→verify-docs/verify-manual/falsy-audit 全过 | 任一步骤失败 |

### 关键实现细节（新增脚本参照）

- **verify-manual.py 公共 API**（crossval 脚本 `from verify_manual import ...` 导入）：
  - `cross_check(name, actual, expected, tol=1e-10)` —— 数值交叉验证，任一 None 计 FAIL
  - `check(name, actual, expected)` —— 确定性相等（禁止 `check(name,X,X)` 自校验）
  - `section(name, count)` —— 打印 `=== name -- count items ===`
  - crossval 发现：扫描 `ROOT/scripts/crossval/*.py`，用 `spec_from_file_location` 加载（`sys.modules.setdefault("verify_manual", sys.modules.get("__main__"))` 解决连字符文件名）；目录缺失/空 → `[SKIP]` 返回 0；执行但 0 PASS/0 FAIL → 显式 FAIL
- **verify-docs.py**：`DOC_FILES` 静态注册表（当前 33 项，**新增文档必须手动登记**）；`EXCLUDED_DIRS = {logs,.git,.claude,.codegraph,.qoder,.pytest_cache,.ruff_cache,__pycache__,.coverage}`；检查函数 `check_links / check_backtick_paths / check_dirs / check_agents_tree / check_undeclared(--strict) / check_subdir_undeclared(--strict)`；`check_agents_tree()` 是"双注册表比对"的先例 → A1 多注册表门禁直接仿此
- **falsy-audit.py**：已内置 HIGH/LOW 风险分级（`HIGH_RISK_PATTERNS` 硬失败 / `LOW_RISK_PATTERNS` 仅 WARN），AST 优先 + 正则兜底 → C3 只需**补 MEDIUM 档**，复用 `FalsyAuditor(ast.NodeVisitor)` 扩展
- **placeholders.json**：`schema_version:1`，~117 个占位符，三类 `core`(交互询问)/`content`(小写占位)/`auto`(rule:today/year)；**新增模板占位符必须先登记**；未登记 token init 时 WARN
- **test-template.ps1 破坏约束**：init→3 项验证循环必须保持完整；任何新脚本要么被 verify-all 编排，要么显式加入 test-template 验证步骤
- **doctor 脚本确认不存在**（模板无环境诊断）—— B1 是净新增

### 目录树 / SSOT 登记（每新增文件必做，verify-docs --strict 依赖）

1. `rules/project-structure.md` 目录树登记新文件（`scripts/`/`rules/`/`templates/` 代码块内加一行）
2. `rules/documentation.md` 职责矩阵登记新文档 + `verify-docs.py` 的 `DOC_FILES` 列表（当前 33 项，手动登记）
3. `AGENTS.md` 技能加载表/参考表 + 目录树同步（如新增 skill/rule/顶层文件）
4. `placeholders.json`（如新增模板占位符）

### CI 落点（ci.yml 结构已核实）

- quality-gate job（`needs: quick-check`，无 continue-on-error）现有 4 个**始终运行**步骤：
  `verify-manual.py` → `falsy-audit.py` → `verify-docs.py --strict` → （另有依赖审查/风格/覆盖率，`is_template != 'true'` 门控）
- **新增门禁（A1/A3/B1/B3/C6/C7）应插为 quality-gate 的"始终运行"步骤**，紧跟 `verify-docs --strict` 之后，遵循"根路径 + 退出码 0/1"约定
- template-self-test job（`is_template=='true'`，ubuntu+windows 矩阵）跑 `test-template.ps1`，并 grep `templates/NewModule/` 中 `{{` 泄漏——**任何新 NewModule 模板不得引入双花括号占位符**（模块级用单花括号 `{PascalCase}`）
- security.yml CodeQL 仅 `[python, javascript-typescript]`（C#/Go 只在 .template 文件，不可构建）

### 测试约定（新增脚本必须配测试，覆盖阈值 `--cov=scripts --cov-fail-under=40`）

- 测试放 `tests/scripts/test_<名>.py`，用 `importlib.util.spec_from_file_location` 动态导入目标脚本（不加 scripts 到 sys.path 之外的安装）
- 最少含 `TestMainCLI` 类（monkeypatch `sys.argv` 测退出码）+ 正常/边界/失败路径
- 现有测试：`test_verify_docs.py`(30) / `test_falsy_audit.py`(20) / `test_init_project.py`(19) / `test_verify_manual.py`(16) / `test_verify_all.py`(6)，共 68 tests / 62%
- 运行：`pytest tests/ -v --cov=scripts --cov-fail-under=40`

### 模板/示例约定（新增模板必须同步）

- NewModule 占位符：模块级用单花括号 `{Name}`/`{Module}`/`{PREFIX}`，项目级用双花括号 `{{ROOT_NAMESPACE}}` 等——**CI 门控禁止 `{{` 泄漏进 NewModule**
- 每新增 NewModule 模板：`templates/README.md` 文件表 + 占位符表 + 该语言新增模块流程各加一行；examples 目录加对应示例文件（`StatsCrossVal.py` 是 CrossVal 规范参考）
- CrossVal 契约：脚本必须 `from verify_manual import check, cross_check, section`，`section(name,N)` 声明数量，禁 `if __name__=="__main__"` 包裹（spec_from_file_location 下永不触发，会被 detect）
- monorepo 模板：N 点同步清单/多注册表门禁的自然落点是 `templates/monorepo/REGISTRY.md.template` + scripts/ 验证脚本

---

## 吸收清单（来源 → 目标落点 → 依赖）

### 档 A：直接命中模板已知痛点（P0）

| # | 能力 | 来源文件 | 目标落点 |
|---|------|---------|---------|
| A1 | 多注册表一致性门禁 | 工程分析 `.github/workflows/ci.yml` consistency job（`TASK_REGISTRY==DEFAULT_PARAMS==LABELS`） | 新 `scripts/verify-registries.py`（仿 `check_agents_tree` 双注册表比对，泛化 N 注册表）+ ci.yml quality job + verify-all 接入 |
| A2 | 文档数字漂移防线 | ExcelVBA `scripts/generate_counts.py`（`<!-- AUTO_COUNTS_START/END -->` 注入 + `--check`） | 新 `scripts/gen-doc-counts.py` + `--check` 入 CI；`DOC_FILES` 登记 |
| A3 | 语义交叉检查（计数/版本比对） | ExcelAddin `scripts/verify-docs.sh`（8 向量） | `verify-docs.py` 新增检查函数（并入现有 6 检查） |
| A4 | 手册数值实跑比对 | 工程分析 `scripts/verify_manual_claims.py` | `verify-manual.py` 新增 run-and-compare 模式 |
| A5 | 配置流断裂防御 | 文档审查 `src/engines/custom_rules.py` 陷阱#4（回退路径键集==路由路径键集） | `rules/tooling-pitfalls.md` 补条 + 防御代码模式 |
| A6 | L1-L5 哨兵契约 + NaN/Inf 守卫 | ExcelAddin `skills/excel-dna-project.md:310-320` + `docs/guard-checklist.md` | 新 `rules/sentinel-contract.md` + 模板 NewModule 注释教育 |

### 档 B：跨 2+ 子项目共识（P1）

| # | 能力 | 来源文件 | 目标落点 |
|---|------|---------|---------|
| B1 | 环境医生 Doctor | ExcelVBA `scripts/doctor.py` / 成本分析 `BomAddIn.Diagnostic` / 文档审查 CLI doctor | 新 `scripts/doctor.py`（stdlib only，py 三层探测 + UTF-8 + PASS/FAIL 输出）+ verify-all 接入 |
| B2 | 通用跨语言 CrossVal runner | ExcelVBA `tests/crossval/build_common.py`（容差分层 exact/1e-10/1e-6/1e-5/1e-2/physical + 分类型比较器 scalar/array/bool/str/dict） | 升级 `verify-manual.py` 加入 runner 骨架（比较器+容差）+ `{Name}CrossVal.py.template` 同步 |
| B3 | 测试质量/缺口门禁 | 成本分析 `tools/test-quality-guard.ps1`（弱断言/缺测/命名/统计）+ `tools/detect-test-gaps.ps1` | 新 `scripts/test-quality-guard.py` + ci.yml |
| B4 | 多入口一致性黄金测试 | 文档审查 `tests/test_integration.py`（CLI==Web==API）/ 工程分析 CLI vs Web | `rules/cross-project-synthesis.md` 记录 + 示例模板 |
| B5 | 文档术语治理机器化 | 文档审查 glossary/vocab(accept/reject)/styles | templates/language 可选参考 + 文档说明（不强制） |
| ~~B6~~ | ~~分层代码审查~~ | ~~成本分析~~ | **已核实模板 `code-review-prompt.md` 已内置 Min(3)/Standard(6)/Max(10) 分级 + P0-P3 + 豁免规则，与成本分析同构——不吸收** |
| B7 | 离线安装 + 零依赖启动器 | 工程分析 `scripts/common.py`+`setup_offline.py` / 文档审查 common.py | 新 `scripts/common.py`（stdlib only）+ 离线脚本模板 |
| B8 | 决策树技能格式 | 工程分析 `skills/analysis-decision-tree.md` | `skills/` 创作约定说明 |
| B9 | 双 AI 工具格式 skills/+.qoder/skills/ | 成本分析 / 工程分析 `.qoder/skills/*/SKILL.md` | 文档化 + init 可选生成 |
| B10 | YAGNI 移除文档模式 | 成本分析 `rules/specification.md:123-129`（「为什么移除 X」+ git 引用） | `rules/adr-template.md` 或 `documentation.md` 补模式 |

### 档 C：单点高价值（P2，语言无关）

| # | 能力 | 来源文件 | 目标落点 |
|---|------|---------|---------|
| C1 | git-diff 影响范围测试路由 | ExcelAddin `scripts/run-affected-tests.ps1`（源→测试类名映射 + --filter） | 新 `scripts/run-affected-tests.py` |
| C2 | 瞬态错误重试装饰器 | ExcelVBA `tests/retry_decorator.py`（`com_retry` + 可插拔错误分类） | 新 `scripts/retry.py`（`@retry_transient`，错误分类器可注入） |
| C3 | falsy 补 MEDIUM 风险档 | 工程分析 `scripts/falsy_audit.py`（HIGH/MED/LOW 按命名启发式） | 升级 `scripts/falsy-audit.py`：模板已内置 HIGH/LOW（`HIGH_RISK_PATTERNS` 硬失败 / `LOW_RISK_PATTERNS` 仅 WARN），**只补 MEDIUM 档**（`MEDIUM_RISK_PATTERNS`，如 `*_score/_rank/_total`，WARN），复用 `FalsyAuditor(ast.NodeVisitor)`，保持 HIGH=exit1 语义 |
| C4 | 集中常量模块 | 工程分析 `src/smartsuite/engine/_constants.py`（Cohen 1988 文献出处） | NewModule 骨架注释 + 架构约定 |
| C5 | per-file ruff ignore 必带理由 | 工程分析 `pyproject.toml:85-101`（每条中文注释 WHY） | 模板 `pyproject.toml` 约定 + rules 说明 |
| C6 | pip-audit + vulture 入 CI | 工程分析 `.github/workflows/ci.yml` | ci.yml security 步骤 |
| C7 | 覆盖率门禁含缺失数据警告 | 成本分析 `.github/workflows/ci.yml:105-128` | verify-all/CI 覆盖率步骤 |
| C8 | `--print-cmd` dry-run 模式 | 工程分析 `scripts/setup_offline.py`（`run_or_print()` 统一门） | scripts 工具约定（写进 tooling-pitfalls） |
| C9 | 双 TFM / 多版本矩阵 CI | ExcelAddin `.github/workflows/ci.yml` | templates/language 可选参考 |
| C10 | nuget packageSourceMapping | ExcelAddin `nuget.config` | templates/language 可选参考 |

---

## 分阶段执行（每阶段改完即验证，全部通过再进下一阶段）

### 阶段 0：基线 + 持久化
- [ ] 基线核对（上文命令全绿）
- [ ] 复制本计划到 `docs/absorption-plan-2026-08.md`
- [ ] `docs/architecture.md` 登记新文档（防未声明）
- [ ] 验证：`verify-docs.py --strict` 通过（计划文档已登记）

### 阶段 1：档 A（P0）
- [ ] A1 `scripts/verify-registries.py`（可参数化，JSON 声明注册表对）+ 测试 + ci.yml quality job 接入
- [ ] A2 `scripts/gen-doc-counts.py`（`--check` 模式）+ 测试 + verify-docs/CI 接入
- [ ] A3 `verify-docs.py` 新增语义检查（计数/版本向量）+ 测试
- [ ] A4 `verify-manual.py` 新增 run-and-compare（实跑代码对手册值）+ 测试
- [ ] A5 `rules/tooling-pitfalls.md` 补配置流断裂条目
- [ ] A6 新 `rules/sentinel-contract.md`（L1-L5 + NaN/Inf 守卫清单 + grep 自检命令）
- [ ] SSOT 登记（project-structure / documentation / DOC_FILES）
- [ ] **验证**：`verify-all.py` 全绿 + `test-template.ps1` 通过 + 新脚本各有测试

### 阶段 2：档 B（P1）
- [ ] B1 `scripts/doctor.py` + 测试 + verify-all 接入
- [ ] B2 `verify-manual.py` runner 骨架升级（比较器+容差分层）+ `{Name}CrossVal.py.template` 同步 + 测试
- [ ] B3 `scripts/test-quality-guard.py` + 测试 + ci.yml
- [ ] B4-B5、B7-B10 文档化/模板化（按清单落点；B6 已核实模板覆盖，跳过）
- [ ] SSOT 登记
- [ ] **验证**：同上 + `test-template.ps1`

### 阶段 3：档 C（P2）
- [ ] C1 `scripts/run-affected-tests.py`（语言无关，命名约定映射）+ 测试
- [ ] C2 `scripts/retry.py`（`@retry_transient`）+ 测试
- [ ] C3 `falsy-audit.py` 补 MEDIUM 档 + 测试（确认 HIGH 仍硬失败、LOW/MED 仅 WARN）
- [ ] C4-C8 按清单落点（常量模块约定/ruff 理由注释/pip-audit/覆盖率警告/dry-run）
- [ ] C9-C10 templates/language 可选参考文件
- [ ] SSOT 登记
- [ ] **验证**：同上

### 阶段 4：SSOT 收口 + 版本
- [ ] `rules/project-structure.md` 目录树登记全部新文件（verify-docs 依赖）
- [ ] `rules/documentation.md` 职责矩阵 + `verify-docs.py` DOC_FILES 补全
- [ ] `AGENTS.md` 技能加载表/参考表补新 skill/rule；`placeholders.json` 补新增占位符（如有）
- [ ] CHANGELOG 补 0.2.0 条目 + `.release-please-manifest.json` bump 到 0.2.0
- [ ] 触发 release-please（或按仓库发版流程）发版 0.2.0

---

## 验证与完成标准（最终全量）

```bash
cd D:/Workspace/zgrwo/Harmonization/VibeCodingTemplate
python scripts/verify-all.py            # 全绿（含所有新增检查）
scripts/test-template.ps1               # init→verify 端到端通过
pytest --cov --cov-fail-under=40        # 全过，每新脚本有对应测试
ruff check                              # 零违规，per-file ignore 带理由注释
python scripts/verify-docs.py --strict  # 无未声明文件/断链
```

1. 门禁全绿 2. 自举端到端过 3. 测试覆盖率 ≥40% 4. lint 零违规 5. 0.2.0 版本一致 6. SSOT 无漂移

---

## 备注（本轮不吸收）

- 档 D：BenchmarkDotNet、PE 二进制补丁、Authenticode 签名、DuckDB 二进制供应、COM 加载循环、Vale 全量部署 —— 领域专属，仅做 templates/language 可选参考，不强制
- `VibeCodingTemplate-optimized/` 是旧快照，**不修改**；吸收只针对 `VibeCodingTemplate/`
- 每个新脚本：stdlib 优先、UTF-8 + ASCII `[OK]/[FAIL]` 标记、退出码语义正确、CLI 入口带测试、中文注释密度匹配现有脚本
