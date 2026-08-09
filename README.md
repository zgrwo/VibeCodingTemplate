# {{PROJECT_NAME}}

{{ONE_LINE_DESCRIPTION}}

[English](README.en.md) | **中文**

<!-- 徽章区（初始化后按需启用：取消注释，并将 OWNER/REPO_NAME 替换为实际值）：
[![CI](https://github.com/{{OWNER}}/{{REPO_NAME}}/actions/workflows/ci.yml/badge.svg)](https://github.com/{{OWNER}}/{{REPO_NAME}}/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
-->

---

## 安装

{{INSTALL_INSTRUCTIONS}}

### 验证安装

{{VERIFY_INSTALL}}

---

## 模块速览

> 完整签名、参数说明见 **[API 参考](rules/api-reference.md)**；每个函数的详细示例见 **[用户手册](rules/user-manual.md)**。

| 模块 | 做什么 | 试一试 |
|------|------|-------|
| `{{MODULE_1}}` | {{DESC_1}} | `{{EXAMPLE_1}}` |
| `{{MODULE_2}}` | {{DESC_2}} | `{{EXAMPLE_2}}` |

---

## 使用模式

{{USAGE_PATTERNS}}

---

## 架构特点

```
{{LAYER_DIAGRAM}}
```

{{ARCHITECTURE_NOTES}}

---

## 错误处理

{{ERROR_HANDLING_DESCRIPTION}}

> 完整错误清单见 **[API 参考 → 错误参考](rules/api-reference.md#错误参考)**。

---

## 安全

{{SECURITY_NOTES}}

---

## 质量保证

{{QUALITY_ASSURANCE}}

---

## 已知限制

{{KNOWN_LIMITATIONS}}

---

## 贡献

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献流程（fork → PR → review）。

---

## 许可证

[MIT](LICENSE) &copy; {{AUTHOR}}

---

## 从源码构建

```bash
{{BUILD_COMMANDS}}
```

---

## 文档索引

| 文档 | 角色 | 内容 |
|------|------|------|
| [specification.md](rules/specification.md) | 业务信源 | 项目概述、模块清单、功能规格（做什么） |
| [API 参考](rules/api-reference.md) | 数字唯一信源 | 函数完整签名、参数说明、错误表（怎么调用） |
| [用户手册](rules/user-manual.md) | 学习教程 | 每个函数详细示例 + 结果解读指南 |
| [context.md](rules/context.md) | 术语表 | 所有术语唯一定义 |
| [documentation.md](rules/documentation.md) | 文档职责 | 各文档分工与维护规则 |
| [project-structure.md](rules/project-structure.md) | 结构地图 | 文件职责与层级关系 |
| [AGENTS.md](AGENTS.md) | 项目宪法 | 架构分层、红线规则、开发流程 |
| [ADR 记录](rules/adr-template.md) | 决策历史 | 架构决策记录（编号递增） |
| [审查模板](rules/code-review-prompt.md) | 审查工具 | Min/Standard/Max 三级代码审查 Prompt |
| [跨项目经验](rules/cross-project-synthesis.md) | 方法论 | 反模式案例库、重构方法论、对标清单 |
| [重构计划](rules/refactoring-plan.md) | 路线图 | 从"能用"到"卓越"的重构模板 |
| [陷阱清单](rules/falsy-pitfalls.md) | 避坑手册 | Falsy 值误判等高频陷阱 |
| [工具坑位](rules/tooling-pitfalls.md) | 避坑手册 | PowerShell/git 脚本坑位 |
| [贡献指南](CONTRIBUTING.md) | 贡献入口 | 开发/PR/发版流程 |
| [变更记录](CHANGELOG.md) | 版本历史 | keepachangelog 格式 |

---

## 治理体系说明

本项目遵循 [Harmonization 治理规范](https://github.com/zgrwo/Harmonization) 模板体系：

> 文档职责分工与维护规则（唯一权威）：[rules/documentation.md](rules/documentation.md)。下表仅为导航速览。

| 文件 | 面向 | 职责 |
|------|------|------|
| `AGENTS.md` | AI 编程助手 | 项目宪法——架构、红线、编码准则、防幻觉铁律（AGENTS.md 生态兼容） |
| `README.md` | 人类用户 | 功能指南——安装、模块速览、使用模式（本文件） |
| `rules/` | AI + 人类 | 规范文档——API 参考、用户手册、术语表、ADR、陷阱清单 |
| `skills/` | AI 编码 | 技能定义——语言陷阱、编码模式、重构守则 |
| `.github/` | CI + 协作 | 质量门禁、CodeQL 安全扫描、依赖更新、Issue/PR 模板 |
| `CONTRIBUTING.md` / `CHANGELOG.md` / `LICENSE` | 协作与合规 | 贡献流程、版本历史、开源许可 |

**核心原则**：SSOT（信息只在一处定义）、Skill-first（修改代码前加载技能）、四条核心准则、闭环验证。

---

## 从本模板初始化新项目

> 本模板沉淀了 5 个子项目（Excel 函数库 / VBA 库 / 工程分析 / 成本分析 / 文档审查）的共性治理经验。初始化新项目时按以下顺序执行：

### 1. 复制与重命名

```powershell
# 自动方式（Windows 推荐）：复制 + 占位符扫描/替换一体
.\scripts\init-project.ps1 -Target d:\path\<PROJECT_NAME>
```

```bash
# 自动方式（Linux/macOS/跨平台）：Python 版
python scripts/init-project.py /path/to/<PROJECT_NAME> --git-init
```

```bash
# 手动方式：
cp -r VibeCodingTemplate <PROJECT_NAME>  # robocopy /E /XD .git (Windows)
# 然后替换全部 {{...}} 占位符（README.md / AGENTS.md / CONTRIBUTING.md / LICENSE）
```

### 2. 必填占位符清单

| 占位符 | 含义 |
|--------|------|
| `{{PROJECT_NAME}}` | 项目名（目录名与文档一致） |
| `{{ONE_LINE_DESCRIPTION}}` | 一句话项目描述 |
| `{{LAYER_DIAGRAM}}` / `{{LAYER_DEPENDENCY_DIAGRAM}}` | 架构分层图 |
| `{{BUILD_CMD}}` / `{{TEST_CMD}}` / `{{FULL_VERIFY_CMD}}` | 构建/测试/验证命令 |
| `{{AUTHOR}}` / `{{DATE}}` | 作者与日期 |

> 上表为必填核心项；模板实际含 **114 项**占位符（CI / 模块 / 文档 / 联系方式等），自动方式下由 init-project.ps1 一次扫描全部替换。完整占位符清单（分类/默认值/测试值）以 `scripts/placeholders.json` 为**唯一权威**（init-project.ps1 与 test-template.ps1 均从该文件读取）。

> 用 `scripts/init-project.ps1` 自动初始化时，脚本会扫描全部 `{{...}}` 占位符，对核心值（项目名 / 所有者 / 验证命令等）交互式询问，其余内容占位符自动用占位符名占位，完成后报告遗漏项。

### 3. 按语言填充

- **src/ 目录树**：按实际模块创建 `src/<Module>/` 结构
- **skills/**：仅保留本项目语言对应的 SKILL.md，删除其余语言文件
  （**必做**：删除语言技能后，同步清理 `rules/tooling-pitfalls.md` 语言索引表中
   指向已删 SKILL 的链接，否则 `verify-docs.py --strict` 会报断链）
- **CI**：在 `.github/workflows/ci.yml` 中替换语言 setup 与命令占位符；启用多版本矩阵/覆盖率门禁（按需）
- **安全与协作**：`security.yml`（CodeQL）按项目语言调整 `language` 矩阵；`dependabot.yml` 按项目语言保留 pip/nuget 条目；首次推送后检查 Actions 权限
- **AGENTS.md 生态兼容**：主文件即为 `AGENTS.md`（大写），Codex/Copilot/Windsurf 等直接读取；如使用 Claude Code，创建 `CLAUDE.md` 副本（见 AGENTS.md「AGENTS.md 生态兼容」）
- **rules/api-reference.md / user-manual.md / context.md**：按项目领域填写

### 4. 初始化收尾（质量门禁）

- [ ] 全量验证脚本可运行（{{FULL_VERIFY_CMD}}）
- [ ] 徽章区启用：README.md 顶部取消注释，替换 `{{OWNER}}` / `{{REPO_NAME}}`
- [ ] 首个 ADR（`rules/adr/0001-xxx.md`）记录初始架构决策
- [ ] AGENTS.md「历史经验」填充项目已知高频模式
- [ ] CHANGELOG.md 标记 v0.1.0 初始化版本
- [ ] 目录树与 project-structure.md 一致
- [ ] 空目录已放置 .gitkeep 并入库
