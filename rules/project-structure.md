# 项目结构

> 本文件是项目结构的**唯一定义**。新增/删除/移动文件时必须同步更新此文件。

## 目录树

```
{{PROJECT_NAME}}/
│
├── src/                          # 源码（按模块划分）
│   ├── {{MODULE_1}}/             # {{MODULE_1_DESC}}
│   ├── {{MODULE_2}}/             # {{MODULE_2_DESC}}
│   └── ...
│
├── tests/                        # 测试
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   ├── crossval/                 # 交叉验证（与独立参考实现比对）
│   └── fixtures/                 # 测试数据/黄金文件
│
├── rules/                        # 规范文档（本目录）
│   ├── documentation.md          # 文档职责规范
│   ├── project-structure.md      # 项目结构（本文件）
│   ├── context.md                # 领域术语表
│   ├── specification.md          # 业务规则与功能范围唯一信源
│   ├── api-reference.md          # API 签名唯一信源
│   ├── user-manual.md            # 用户手册
│   ├── code-review-prompt.md     # 深度审查 Prompt
│   ├── cross-project-synthesis.md# 跨项目共性经验与重构方法论
│   ├── refactoring-plan.md       # 重构计划模板（现状→目标路线图）
│   ├── adr-template.md           # ADR 模板（编号与格式）
│   ├── falsy-pitfalls.md         # Python falsy 陷阱清单
│   ├── tooling-pitfalls.md       # 工具/脚本坑位清单
│   └── adr/                      # ADR 决策记录（0001-xxx.md，编号递增）
│
├── skills/                       # AI 编码技能文件
│   ├── csharp-SKILL.md           # C# 编码陷阱与规范
│   ├── python-SKILL.md           # Python 编码陷阱与规范
│   ├── vba-SKILL.md              # VBA 编码陷阱与规范
│   ├── architecture-reviewer.md  # 架构审查专家（重构生命周期）
│   ├── refactoring-guardian.md   # 重构守卫（每 Phase 前后）
│   └── project-plan-review.md    # 规划评审专家
│
├── scripts/                      # 构建/验证脚本
│   ├── verify-all.ps1            # 全量验证入口（构建+测试+文档一致性）
│   ├── verify-docs.py            # 文档链接/目录树一致性验证
│   ├── verify-manual.py          # 手册示例一致性验证（禁自校验）
│   ├── falsy-audit.py            # Falsy 陷阱静态审计
│   ├── init-project.ps1          # 从模板初始化新项目（占位符替换）
│   └── ...
│
├── templates/                    # 模块脚手架
│   ├── README.md                 # 脚手架使用说明（占位符约定）
│   ├── NewModule/                # 新增模块四件套（Core/Udf/Tests/CrossVal）
│   └── language/                 # 构建配置模板（pyproject/Build.props/nuget）
│
├── .github/                      # GitHub 协作
│   ├── workflows/ci.yml          # CI 质量门禁（quick/full/quality）
│   ├── workflows/security.yml    # CodeQL 安全扫描
│   ├── workflows/release-drafter.yml  # 自动 Release 草稿
│   ├── workflows/stale.yml       # 僵尸 Issue/PR 关闭
│   ├── dependabot.yml            # 依赖自动更新
│   ├── ISSUE_TEMPLATE/           # Bug/功能/文档/重构模板
│   └── PULL_REQUEST_TEMPLATE.md  # PR 模板
│
├── docs/                         # 用户文档（补充材料）
│   └── README.md                 # 文档目录说明（与 rules/ 的分工）
│
├── logs/                         # 运行日志（.gitignore 排除）
│
├── tools/                        # 辅助工具/脚本
│   └── ...
│
├── agents.md                     # 项目宪法（AI 约束）
├── readme.md                     # 用户入口
├── CONTRIBUTING.md               # 贡献指南
├── CHANGELOG.md                  # 版本变更记录
├── SECURITY.md                   # 安全政策
├── CODE_OF_CONDUCT.md            # 行为准则
├── LICENSE                       # 开源许可证
├── .gitignore                    # 排除规则
├── .gitattributes                # 换行符/二进制标记
└── .pre-commit-config.yaml       # 提交前 lint（可选启用）
```

## 层级依赖规则

```
{{LAYER_DEPENDENCY_DIAGRAM}}
```

- ✅ 依赖方向：上层 → 下层（单向）
- ❌ 禁止反向依赖或跨层调用
- ❌ 底层不感知上层（Model 不引用 UI，Engine 不引用 Services）

## 规模适配（防过度架构）

> 本目录树是**能力基线**，不是最小强制集。社区对 golang-standards/project-layout 的普遍批评是照搬全套目录导致过度架构（参见 Tony Bai《别把 Go 写成 Java》）。按项目规模裁剪：

| 规模 | 建议 |
|------|------|
| 单文件脚本 | 仅 `src/` + `tests/` + 必要规则文档 |
| 小型项目（<5 模块） | `src/` + `tests/` + `scripts/` + `rules/`，可跳过 `templates/`/`docs/`/`build/` |
| 中型项目（5-15 模块） | 本目录树全量 |
| 大型/多仓 | 全量 + 子目录级 `AGENTS.md`（Monorepo） |

- **YAGNI**：不需要的目录不要建，需要时再补（遵循 agents.md「简洁至上」）
- **目录即契约**：一旦建目录并入库，删除/移动必须同步更新本文件与 agents.md

## 文件命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 源码文件 | PascalCase 或 snake_case（按语言惯例） | `StatsCore.cs`, `root_cause.py` |
| 测试文件 | `test_` 前缀（Python）/ `.Tests` 后缀（C#） | `test_stats.py`, `Stats.Tests/` |
| 文档文件 | kebab-case | `api-reference.md`, `user-manual.md` |
| 脚本文件 | kebab-case 或 snake_case | `verify-docs.sh`, `run_all.py` |
| 配置文件 | 按工具惯例 | `.gitignore`, `ci.yml` |

## 新增文件检查清单

- [ ] 文件路径已在本文件目录树中定义
- [ ] 文件放置于正确的层级目录
- [ ] 命名符合上述规范
- [ ] 如为 Public 接口，已同步 api-reference.md
- [ ] agents.md 目录树已同步（如为顶层变更）
