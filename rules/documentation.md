# 文档职责规范

> 本文档定义项目中各文档的职责边界与维护规则。核心原则：**信息只在一处定义，其余各处链接引用（SSOT）**。

## 文档分工矩阵

| 文档 | 受众 | 核心问题 | 维护触发 |
|------|------|----------|----------|
| `AGENTS.md` | AI 助手 | "项目怎么组织？红线在哪？" | 架构/红线/流程变更 |
| `README.md` | 人类用户 | "这是什么？怎么用？" | 功能新增/安装方式变更 |
| `README.en.md` | 国际用户 | "What is this? How to use?"（英文入口） | 功能新增/安装方式变更 |
| `rules/context.md` | AI + 新人 | "术语什么意思？为什么这样设计？" | 新概念引入 |
| `rules/api-reference.md` | 开发者/AI | "函数签名是什么？"（**签名唯一信源**） | 任何 Public 接口变更 |
| `rules/user-manual.md` | 最终用户 | "我要做 X，怎么操作？" | 用户可见功能变更 |
| `rules/project-structure.md` | 开发者/AI | "代码在哪？文件干什么？"（**结构唯一信源**） | 文件新增/删除/移动 |
| `rules/adr-template.md` + `rules/adr/` | AI + 人类 | "这个架构决策为什么这么做？"（决策历史） | 新增/推翻架构决策 |
| `rules/falsy-pitfalls.md` | AI 编码 | "Python 中 0 被当作 False？" | 发现新 falsy 误判案例 |
| `rules/tooling-pitfalls.md` | AI + 人类 | "PowerShell/git 有什么坑？" | 新踩坑并验证修复后 |
| `rules/sentinel-contract.md` | AI 编码 | "无效输入返回什么？哨兵还是异常？" | 哨兵契约或守卫清单变更 |
| `CONTRIBUTING.md` | 贡献者 | "怎么开发/提 PR/发版？" | 流程变更 |
| `CHANGELOG.md` | 用户/维护者 | "这个版本改了什么？" | 每次发版 |
| `SECURITY.md` | 安全报告者 | "怎么报告漏洞？" | 安全政策变更 |
| `skills/*.md` | AI 编码 | "这个语言/框架有什么陷阱？" | 发现新陷阱/模式 |

## 建议阅读顺序

> 文档间存在大量交叉引用，以下顺序避免"文档跳转迷宫"。

| 角色 | 阅读顺序 | 预计耗时 |
|------|----------|----------|
| **新贡献者** | README.md → AGENTS.md → context.md → CONTRIBUTING.md | 20 min |
| **AI 编码助手** | AGENTS.md → 对应 skills/*.md → rules/falsy-pitfalls.md（Python） | 10 min |
| **代码审查者** | AGENTS.md → 对应 skills/*.md | 15 min |
| **架构决策者** | AGENTS.md → rules/project-structure.md → skills/architecture-reviewer-SKILL.md → rules/adr-template.md | 20 min |
| **重构执行者** | rules/refactoring-plan.md → skills/refactoring-guardian-SKILL.md → AGENTS.md「防错三原则」 | 15 min |

> 跳过项：`rules/cross-project-synthesis.md`（方法论库，按需查阅，不必线性阅读）

## 禁止事项

| ❌ 禁止 | 原因 |
|---------|------|
| 在多处重复定义同一信息 | 更新时必然遗漏，导致不一致 |
| 在 README 中写架构细节 | README 面向用户，架构属于 AGENTS.md |
| 在代码注释中写使用教程 | 教程属于 user-manual.md |
| 在 api-reference 中写实现细节 | api-reference 只写签名和行为契约 |
| 在 AGENTS.md 中写编码细节 | 编码细节属于 skills/ |

## 维护规则

### 同步更新链

```
新增 Public 函数
  → rules/api-reference.md（签名 + 参数 + 错误行为）
  → rules/user-manual.md（示例 + 结果解读）
  → README.md 模块速览（如为新模块）

新增/删除/移动文件
  → rules/project-structure.md（结构树）
  → AGENTS.md 目录树（如为顶层变更）

引入新领域术语
  → rules/context.md（唯一定义）

新增/推翻架构决策
  → rules/adr/NNNN-xxx.md（新 ADR 记录，原 ADR 标记已废弃）

新踩工具/脚本坑位
  → rules/tooling-pitfalls.md（附真实案例）

新增治理脚本（本模板自举门禁）
  → rules/project-structure.md 目录树登记（verify-docs --strict 强制）
  → scripts/verify-all.py/.ps1 + Makefile docs target + ci.yml quality-gate 接入
  → templates/README.md「治理脚本速查」表 + cross-project-synthesis 索引表登记

发版（release-please 自动）
  → 提交遵循 Conventional Commits（scripts/validate-commit-msg.sh 强制）
  → release-please 自动维护 CHANGELOG.md + 版本号 + tag + Release
  → 人工无需编辑 CHANGELOG / 三处版本号 / push tag（见 CONTRIBUTING「发版流程」）
```

### 数字一致性

- 函数计数、模块计数等数字**仅在 api-reference.md 中维护**
- 其他文档如需引用数字，使用"见 api-reference"链接，不硬编码数字
- 若必须硬编码（如 README 概述），则 api-reference 变更时必须同步
- **版本号 SSOT**：`.release-please-manifest.json` 根版本、`pyproject.toml` 的 `[project] version`、
  `CHANGELOG.md` 最新发布版本三者必须一致（发版由 release-please 自动维护；
  `scripts/verify-docs.py` 语义检查强制，防 release-type 不管理语言版本文件时漂移）
- **手册关键数值**（effect size/阈值/均值等）用 CLAIM 标记（`<!-- CLAIM:NAME -->值<!-- /CLAIM:NAME -->`）圈定，
  `scripts/verify-manual.py` 的 `manual_check()` 实跑比对（防文档数字漂移；语法见 user-manual.md）

### 格式规范

- 所有文档使用 UTF-8 编码
- Markdown 标题层级不超过 4 级（####）
- 代码块标注语言（```python / ```csharp / ```vba）
- 表格对齐，列宽适中
- 中文文档中英文术语首次出现时附原文

## 模板专属段落（TEMPLATE_ONLY）

模板仓库的 `README.md` 同时充当「下游项目模板」与「自身落地页」：落地页需要自我说明，但模板专属内容（如「从本模板初始化新项目」）不应进入新项目。

- 用 HTML 注释圈定段落边界：`<!-- TEMPLATE_ONLY_START -->` … `<!-- TEMPLATE_ONLY_END -->`
- `init-project.py` / `init-project.ps1` 初始化时整体删除标记段落（复制后、占位符扫描前执行），被删段落内的 `{{...}}` 示例不计入下游替换清单
- **维护触发**：新增模板专属内容时沿用此标记；标记必须成对闭合——未闭合（有 START 无 END）会触发 init 告警并保留段落（防误删文件后半部分）
- **注意**：被圈定段落内请勿引用标记字面量（`<!-- TEMPLATE_ONLY_... -->`）；裁剪逻辑虽以深度计数容忍成对字面量，但不成对会破坏配对
- 实现见 `scripts/init-project.py` 的 `_strip_template_only_blocks()`；裁剪只作用于 `.md` 文件

## 审查检查项

文档变更时逐项确认：

- [ ] 变更内容属于该文档的职责范围
- [ ] 未在其他文档中重复定义同一信息
- [ ] 引用的链接目标存在且正确
- [ ] 数字/计数与 api-reference.md 一致
- [ ] 新增术语已在 context.md 中定义
