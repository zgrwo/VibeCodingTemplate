# 文档职责规范

> 本文档定义项目中各文档的职责边界与维护规则。核心原则：**信息只在一处定义，其余各处链接引用（SSOT）**。

## 文档分工矩阵

| 文档 | 受众 | 核心问题 | 维护触发 |
|------|------|----------|----------|
| `AGENTS.md` | AI 助手 | "项目怎么组织？红线在哪？" | 架构/红线/流程变更 |
| `README.md` | 人类用户 | "这是什么？怎么用？" | 功能新增/安装方式变更 |
| `README.en.md` | 国际用户 | "What is this? How to use?"（英文入口） | 功能新增/安装方式变更 |
| `docs/spec/context.md` | AI + 新人 | "术语什么意思？为什么这样设计？" | 新概念引入 |
| `docs/spec/specification.md` | 开发者/AI/利益相关方 | "项目做什么？功能范围在哪？"（**业务唯一信源**） | 功能范围/模块清单变更 |
| `docs/spec/api-reference.md` | 开发者/AI | "函数签名是什么？"（**签名唯一信源**） | 任何 Public 接口变更 |
| `docs/spec/user-manual.md` | 最终用户 | "我要做 X，怎么操作？" | 用户可见功能变更 |
| `docs/governance/project-structure.md` | 开发者/AI | "代码在哪？文件干什么？"（**结构唯一信源**） | 文件新增/删除/移动 |
| `docs/governance/code-review-prompt.md` | AI + 审查者 | "怎么分级审查代码？"（Min/Standard/Max） | 审查维度/豁免规则变更 |
| `docs/governance/pre-release-review-prompt.md` | AI + 审查者 | "发行前查什么？"（Max 18 维度穷尽审计） | 审查方法论/门禁变更 |
| `docs/governance/review-checklist.md` | 人类审查者/PR 作者 | "PR 逐项怎么验？"（可执行命令清单） | 门禁命令/流程变更 |
| `docs/governance/review-exemptions.md` | AI + 维护者 | "哪些风险已接受？"（到期必查清单） | 审查豁免登记/到期复查 |
| `docs/design/adr-template.md` + `docs/design/adr/` | AI + 人类 | "这个架构决策为什么这么做？"（决策历史） | 新增/推翻架构决策 |
| `docs/pitfalls/falsy-pitfalls.md` | AI 编码 | "Python 中 0 被当作 False？" | 发现新 falsy 误判案例 |
| `docs/pitfalls/tooling-pitfalls.md` | AI + 人类 | "PowerShell/git 有什么坑？" | 新踩坑并验证修复后 |
| `docs/pitfalls/sentinel-contract.md` | AI 编码 | "无效输入返回什么？哨兵还是异常？" | 哨兵契约或守卫清单变更 |
| `docs/design/architecture.md` | 人类（模板使用者） | "模板自身为什么这样设计？"（初始化后替换为项目架构文档） | 模板架构变更 |
| `docs/methodology/cross-project-synthesis.md` | AI + 人类 | "别人踩过什么坑？"（反模式案例库） | 新增真实案例 |
| `docs/methodology/refactoring-plan.md` | 重构执行者 | "从能用到卓越怎么走？"（路线图模板） | 重构方法论变更 |
| `ROADMAP.md`（根目录） | 维护者/贡献者 | "下一步做什么？触发条件是什么？"（决策门） | 里程碑/决策门/版本方向变更 |
| `benchmarks/README.md` | 性能优化者 | "基准怎么建？何时必须做？"（非门禁约定） | 基准工具/约定变更 |
| `CONTRIBUTING.md` | 贡献者 | "怎么开发/提 PR/发版？" | 流程变更 |
| `CHANGELOG.md` | 用户/维护者 | "这个版本改了什么？" | 每次发版 |
| `SECURITY.md` | 安全报告者 | "怎么报告漏洞？" | 安全政策变更 |
| `skills/*.md` | AI 编码 | "这个语言/框架有什么陷阱？" | 发现新陷阱/模式 |
| `skills/README.md` | AI + 人类 | "技能目录怎么用？第三方技能的已知断链有哪些？"（上游悬空引用登记表） | 引入/更新/裁剪技能目录，或实证新的上游悬空引用 |
| `docs/governance/repo-hygiene.md` | AI + 维护者 | "仓库现场怎么整理？哪些垃圾不该入库？"（5S 检查清单 + 可执行命令） | 仓库卫生规则变更、发现新的产物/漂移类别 |

## 建议阅读顺序

> 文档间存在大量交叉引用，以下顺序避免"文档跳转迷宫"。

| 角色 | 阅读顺序 | 预计耗时 |
|------|----------|----------|
| **新贡献者** | README.md → AGENTS.md → context.md → CONTRIBUTING.md | 20 min |
| **AI 编码助手** | AGENTS.md → 对应 skills/*.md → docs/pitfalls/falsy-pitfalls.md（Python） | 10 min |
| **代码审查者** | AGENTS.md → 对应 skills/*.md | 15 min |
| **架构决策者** | AGENTS.md → docs/governance/project-structure.md → skills/architecture-reviewer-SKILL.md → docs/design/adr-template.md | 20 min |
| **重构执行者** | docs/methodology/refactoring-plan.md → skills/refactoring-guardian-SKILL.md → AGENTS.md「防错三原则」 | 15 min |

> 跳过项：`docs/methodology/cross-project-synthesis.md`（方法论库，按需查阅，不必线性阅读）
>
> 文档中心导航（五分类速查表）见 `docs/README.md`。

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
  → docs/spec/api-reference.md（签名 + 参数 + 错误行为）
  → docs/spec/user-manual.md（示例 + 结果解读）
  → README.md 模块速览（如为新模块）

新增/删除/移动文件
  → docs/governance/project-structure.md（结构树）
  → AGENTS.md 目录树（如为顶层变更）

新增/移动用户向文档（docs/spec、pitfalls 等）
  → mkdocs.yml nav（站点导航；治理/ADR/方法论有意不入 nav）
  → docs/index.md 快速入口表（如为高入口文档）

引入新领域术语
  → docs/spec/context.md（唯一定义）

新增/推翻架构决策
  → docs/design/adr/NNNN-xxx.md（新 ADR 记录，原 ADR 标记已废弃）

新踩工具/脚本坑位
  → docs/pitfalls/tooling-pitfalls.md（附真实案例）
  → 条数由 AUTO_COUNTS 标记自动注入（scripts/doc-counts.json）；**禁止手写条数**

新增反模式案例
  → docs/methodology/cross-project-synthesis.md（附真实案例：出现次数 + 根因）
  → 案例数由 AUTO_COUNTS 标记自动注入（scripts/doc-counts.json）；**禁止手写「N 类」**

新增/调整 init-project 开关（如 --with-examples / --values-file）
  → README.md「从本模板初始化新项目」段（用法与新开关）
  → scripts/test-template.ps1 补对应断言（生成项目侧的可验证结论，而非仅文档描述）
  → 双实现同步：init-project.py 与 init-project.ps1 必须行为一致（tooling-pitfalls #26）

修改 AGENTS.md（项目宪法）
  → 重建 CLAUDE.md 静态副本：`Copy-Item AGENTS.md CLAUDE.md`（Linux: `cp AGENTS.md CLAUDE.md`）
  → verify-docs.py「宪法副本一致性」向量硬校验二者逐字节一致（副本存在时才校验；删除副本即自动跳过）

新增/移除第三方（vendored）技能子树的悬空引用
  → skills/README.md 的 VENDORED_DANGLING_REFS 登记表（该类子树被链接检查排除，只有登记表 + 两向门禁替你看守）

登记/关闭审查豁免
  → docs/governance/review-exemptions.md；写了「到期：vX.Y.Z」的条目由 verify-docs.py「豁免到期」向量硬校验
  → 关闭时划删除线并写复查结论（划删除线才跳过检查）

新增治理脚本（本模板自举门禁）
  → docs/governance/repo-hygiene.md 第四节「漂移类别 → 门禁」对照表补行（新门禁必须进入对照表，否则无人知道它看守什么）
  → docs/governance/project-structure.md 目录树登记（verify-docs --strict 强制）
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
