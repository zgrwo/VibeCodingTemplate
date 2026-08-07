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

### Changed

- `scripts/verify-docs.py`：REQUIRED_DIRS 移除 logs（运行时目录）、DOC_FILES 补全、占位符链接跳过、--strict 未声明文件检查
- `scripts/verify-manual.py`：重写为静态检查 + CrossVal 执行器（cross_check/check/section 辅助 API，crossval 缺失时 SKIP 不假装通过）
- `scripts/falsy-audit.py`：支持 `if not x` / `while x` / `x or default` 变体，实现 LOW 级别输出
- `scripts/verify-all.ps1`：自动探测构建系统（dotnet/Python），未检测到时显式跳过
- `scripts/init-project.ps1`：修复 -Values 无大括号 key 静默不替换 bug，新增 -GitInit / -CreateCompatibilityLinks / YEAR
- `.github/workflows/ci.yml`：quality-gate 去除 continue-on-error（硬门禁），paths 补 .github/templates/rules，新增 template-self-test job
- `rules/cross-project-synthesis.md`：SSOT 收敛为案例库 + 索引（删除与 agents.md 重复内容）
- `rules/api-reference.md`：示例段职责收敛至 user-manual，错误值占位符化
- `rules/specification.md`：模块清单去除函数数列（数字唯一信源在 api-reference）
- `rules/falsy-pitfalls.md` / `skills/python-SKILL.md`：falsy 内容 SSOT 收敛（唯一权威声明）
- `rules/tooling-pitfalls.md`：语言级陷阱改为链接索引（禁止双写）
- `skills/`：三语言 SKILL 添加 front matter，vba §8.5 去重
- `templates/`：Core/Udf 模板命名空间统一为 `{{ROOT_NAMESPACE}}`，CrossVal 模板对接 verify-manual 执行器
- `.pre-commit-config.yaml`：补齐 pre-commit-hooks 基础 hooks
- 根目录：LICENSE 年份占位符化，readme 文档索引补全，CONTRIBUTING 补行为准则/安全互链与分支策略

### Fixed

- `init-project.ps1` `-Values` 参数：key 不带 `{{}}` 时静默不替换（H6）
- `init-project.ps1` 替换阶段：`$found.Values` 未展平导致 WriteAllText 收到数组路径而报错（PS 5.1 实测）
- `init-project.ps1` 写回时保留原文件 BOM（避免新项目 .ps1 中文在 PowerShell 5.1 下解析失败）
- 验证脚本输出 emoji 在 Windows GBK 控制台 UnicodeEncodeError（统一为 [OK]/[FAIL]/[SKIP] ASCII 标记）
- `test-template.ps1` 无 BOM 导致 PowerShell 5.1 中文解析失败
- `verify-docs.py` 在模板自身状态下必然失败（logs 目录声明冲突 + 占位符断链）
- PR 模板 `{{ISSUE_NUMBER}}` 误用占位符体系（改为填写式）

## [0.1.0] - {{DATE}}

### Added

- 项目初始化：核心模块、测试体系、文档体系
