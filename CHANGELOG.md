# Changelog

All notable changes to {{PROJECT_NAME}}.

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

> 本模板自身的变更记录（新项目初始化时请重置为项目自己的变更历史）。

### Added

- 新增 `.github/workflows/release.yml`：tag 推送自动构建/测试/生成 Release（正文取自 CHANGELOG 对应段落）
- 新增 `scripts/test-template.ps1`：模板完整性自测（init → verify-docs/manual/falsy）
- 新增 `templates/NewModule/{Name}Foundation.cs.template`：补齐 UDF 模板的 Foundation 依赖
- 新增 `.github/CODEOWNERS` 与 `.github/ISSUE_TEMPLATE/config.yml`
- 新增 `.github/ISSUE_TEMPLATE/{feature_request,docs_request,refactor_request}.yml`：Issue 模板升级为 GitHub Issue Forms（结构化字段 + 必填校验）

### Changed

- `agents.md` → `AGENTS.md`、`readme.md` → `README.md`：文件名大小写对齐 2026 年跨工具惯例（AGENTS.md 为大写事实标准；README 惯例大写），全部内部引用同步更新
- `scripts/init-project.ps1`：-CreateCompatibilityLinks 仅创建 CLAUDE.md 副本（AGENTS.md 即主文件，Codex/Copilot/Windsurf 等直接读取）
- `verify-docs.py`：REQUIRED_DIRS 移除 logs（运行时目录）、DOC_FILES 补全、占位符链接跳过、--strict 未声明文件检查
- `scripts/verify-manual.py`：重写为静态检查 + CrossVal 执行器（cross_check/check/section 辅助 API，crossval 缺失时 SKIP 不假装通过）
- `scripts/falsy-audit.py`：支持 `if not x` / `while x` / `x or default` 变体，实现 LOW 级别输出
- `scripts/verify-all.ps1`：自动探测构建系统（dotnet/Python），未检测到时显式跳过
- `scripts/init-project.ps1`：修复 -Values 无大括号 key 静默不替换 bug，新增 -GitInit / -CreateCompatibilityLinks / YEAR
- `.github/workflows/ci.yml`：quality-gate 去除 continue-on-error（硬门禁），paths 补 .github/templates/rules，新增 template-self-test job
- `.github/workflows/ci.yml`：三 job 加 `detect` 步骤检测模板仓库自身（`{{PROJECT_NAME}}` 未替换即跳过占位符命令，模板仓库 CI 自举可用）；paths 去重；新增 concurrency 并发取消 + timeout-minutes（H1/M2/L1/L8）
- `scripts/verify-docs.py`：顶层目录检查改为从 project-structure.md 目录树解析（目录树即契约，规模裁剪自动适配，替代硬编码 REQUIRED_DIRS）（H2）
- `scripts/init-project.ps1`：占位符机制说明文字 `{{...}}` 化（不再被自扫描替换）；交互询问 Enter 用占位符名默认值（输入量 90+ 降至核心几项）；初始化完成后 CHANGELOG 重置为新项目初始态（H3/M3/M8）
- `.github/ISSUE_TEMPLATE/bug_report.md`：VERSION 由占位符改为填写式（H3）
- `AGENTS.md` / `rules/project-structure.md`：目录树补 release.yml 条目（M1）
- `.github/dependabot.yml`：pip/nuget 条目注释化（初始化后按需取消注释，避免无清单报错）（M4）
- `scripts/verify-manual.py`：自校验扫描扩展至 crossval/（独立实现比对一并检查）（M5）
- `skills/project-plan-review.md`：YAGNI 四问收敛为链接引用（唯一权威：architecture-reviewer.md）（M6）
- `README.md` / `AGENTS.md`：文档职责表加唯一权威注（documentation.md 为 SSOT，表格仅导航）（M7）
- `.github/ISSUE_TEMPLATE/config.yml`：链接改用 `{{REPO_NAME}}`（M9）
- `scripts/test-template.ps1`：Invoke-Expression 改为 scriptblock 执行；移除 RELEASE_ASSETS 死条目（L2/L3）
- `.gitattributes`：`*.ps1` 固定 eol=crlf（Windows 脚本跨平台一致性）（L4）
- `README.md`：徽章启用说明（取消注释 + 替换 OWNER/REPO_NAME）（L5）
- `scripts/falsy-audit.py`：覆盖属性访问（`x.y`）与 `return x or` 变体（L6）
- `AGENTS.md` / `rules/refactoring-plan.md`：`{{N}}` 归位为 `{N}`（源码级待填标记，不参与 init 替换）（L7）
- `scripts/verify-all.ps1`：`$LASTEXITCODE` 判断简化（L9）
- `rules/cross-project-synthesis.md`：SSOT 收敛为案例库 + 索引（删除与 AGENTS.md 重复内容）
- `rules/api-reference.md`：示例段职责收敛至 user-manual，错误值占位符化
- `rules/specification.md`：模块清单去除函数数列（数字唯一信源在 api-reference）
- `rules/falsy-pitfalls.md` / `skills/python-SKILL.md`：falsy 内容 SSOT 收敛（唯一权威声明）
- `rules/tooling-pitfalls.md`：语言级陷阱改为链接索引（禁止双写）
- `skills/`：三语言 SKILL 添加 front matter，vba §8.5 去重
- `templates/`：Core/Udf 模板命名空间统一为 `{{ROOT_NAMESPACE}}`，CrossVal 模板对接 verify-manual 执行器
- `.pre-commit-config.yaml`：补齐 pre-commit-hooks 基础 hooks
- 根目录：LICENSE 年份占位符化，readme 文档索引补全，CONTRIBUTING 补行为准则/安全互链与分支策略
- 安全加固：全部 workflow 第三方 actions 固定 commit SHA（供应链安全）；ci.yml 顶层加 `permissions: contents: read` 最小化；quality-gate 新增 dependency-review（PR 依赖审查）
- `verify-docs.py`：--strict 未声明检查改为从 project-structure.md 目录树解析（文件+目录，自动收录 CLAUDE.md）；DOC_FILES 补 skills/、templates/、docs/；新增 AGENTS.md 与 project-structure.md 顶层目录一致性校验
- 结构一致性：crossval 目录统一至 `scripts/crossval/`（删除 tests/crossval 死条目）；project-structure.md 补 build/、.editorconfig、CLAUDE.md 条目；AGENTS.md 五件套与技能表占位符说明、CLAUDE.md 副本维护提示
- `README.md`：模块速览表统一为 MODULE_1/2；必填占位符清单以 test-template.ps1 为权威；收尾清单补徽章启用步骤
- `CODE_OF_CONDUCT.md` 新增 `{{COC_CONTACT}}` 占位符；`SECURITY.md` 新增披露响应时间表
- `templates/`：新增 `language/{Name}.Tests.csproj.template`（xUnit 测试项目）；修复 Udf/Foundation 模板注释损坏字符
- `init-project.ps1`：复制后清理 `__pycache__/bin/obj` 等垃圾目录；CLAUDE.md 副本维护提示
- `release.yml`：Build/Test 加 is_template 检测（模板仓库自身无构建系统）；release-drafter.yml 补双发布机制分工说明

### Removed

- `.github/ISSUE_TEMPLATE/*.md`：四个手写 Issue 模板移除（被 .yml Issue Forms 替代）（L10）

### Fixed

- `init-project.ps1` `-Values` 参数：key 不带 `{{}}` 时静默不替换（H6）
- `init-project.ps1` 替换阶段：`$found.Values` 未展平导致 WriteAllText 收到数组路径而报错（PS 5.1 实测）
- `init-project.ps1` 写回时保留原文件 BOM（避免新项目 .ps1 中文在 PowerShell 5.1 下解析失败）
- 验证脚本输出 emoji 在 Windows GBK 控制台 UnicodeEncodeError（统一为 [OK]/[FAIL]/[SKIP] ASCII 标记）
- `test-template.ps1` 无 BOM 导致 PowerShell 5.1 中文解析失败
- `verify-docs.py` 在模板自身状态下必然失败（logs 目录声明冲突 + 占位符断链）
- PR 模板 `{{ISSUE_NUMBER}}` 误用占位符体系（改为填写式）
- `ci.yml` 在模板仓库自身运行时占位符命令必然失败（三 job 加 is_template 检测跳过，模板仓库 CI 全绿）（H1）
- `verify-docs.py` REQUIRED_DIRS 硬编码 10 目录，与规模裁剪冲突（改为从 project-structure.md 目录树解析）（H2）
- `init-project.ps1` 元占位符污染：描述占位符机制的注释文字被自扫描替换（统一 `{{...}}` 形式排除）（H3）
- `verify-docs.py` 初始化后 `--strict` 必报 CLAUDE.md 未声明（白名单改为从目录树解析，CLAUDE.md 已登记）（P-A）
- `project-structure.md` 声明 `tests/crossval/` 与 `scripts/crossval/` 双目录冲突（SSOT 统一至 scripts/）（P-D）
- `ci.yml` 无 permissions 声明、第三方 actions 用 tag 引用（最小化权限 + 固定 commit SHA）（P-B/P-C）
- `release.yml` 在模板仓库自身运行时占位符命令必然失败（补 is_template 检测）（P-G）
- `init-project.ps1` 复制携带 `scripts/__pycache__` 等垃圾目录（复制后清理）（P-N）
- `templates/NewModule/` 注释中 7 处损坏字符 `?`（修复为 `-`）（P-M）

## [0.1.0] - {{DATE}}

### Added

- 项目初始化：核心模块、测试体系、文档体系
