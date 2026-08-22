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
│   ├── scripts/                  # 验证脚本自身测试套件
│   └── fixtures/                 # 测试数据/黄金文件
│
├── rules/                        # 规范文档（本目录）
│   ├── documentation.md          # 文档职责规范
│   ├── project-structure.md      # 项目结构（本文件）
│   ├── context.md                # 领域术语表
│   ├── specification.md          # 业务规则与功能范围唯一信源
│   ├── api-reference.md          # API 签名唯一信源
│   ├── user-manual.md            # 用户手册
│   ├── cross-project-synthesis.md# 跨项目共性经验与重构方法论
│   ├── refactoring-plan.md       # 重构计划模板（现状→目标路线图）
│   ├── adr-template.md           # ADR 模板（编号与格式）
│   ├── falsy-pitfalls.md         # Python falsy 陷阱清单
│   ├── tooling-pitfalls.md       # 工具/脚本坑位清单
│   ├── sentinel-contract.md      # 哨兵契约 L1-L5 与 NaN/Inf 守卫清单
│   └── adr/                      # ADR 决策记录（0001-xxx.md，编号递增）
│
├── skills/                       # AI 编码技能文件
│   ├── README.md                 # 技能目录说明（自带 vs 第三方 Superpowers、更新/裁剪指引）
│   ├── csharp-SKILL.md           # C# 编码陷阱与规范
│   ├── python-SKILL.md           # Python 编码陷阱与规范
│   ├── vba-SKILL.md              # VBA 编码陷阱与规范
│   ├── typescript-SKILL.md       # TypeScript 编码陷阱与规范
│   ├── go-SKILL.md               # Go 编码陷阱与规范
│   ├── rust-SKILL.md             # Rust 编码陷阱与规范
│   ├── ci-pipeline-SKILL.md      # CI 管道与脚本技能（GitHub Actions/PowerShell/PR 发版陷阱）
│   ├── architecture-reviewer-SKILL.md  # 架构审查专家（重构生命周期）
│   ├── refactoring-guardian-SKILL.md   # 重构守卫（每 Phase 前后）
│   ├── project-plan-review-SKILL.md    # 规划评审专家
│   ├── brainstorming/            # Superpowers：头脑风暴→规格（第三方，英文）
│   ├── writing-plans/            # Superpowers：多步任务计划（第三方，英文）
│   ├── test-driven-development/  # Superpowers：TDD（第三方，英文）
│   ├── subagent-driven-development/  # Superpowers：子代理驱动开发（第三方，英文）
│   ├── systematic-debugging/     # Superpowers：系统化调试（第三方，英文）
│   └── verification-before-completion/ # Superpowers：完成前验证/闭环验证（第三方，英文）
│
├── scripts/                      # 构建/验证脚本
│   ├── README.md                 # 目录导航索引（脚本职责速查，详见本文件）
│   ├── placeholders.json         # 占位符清单（唯一真相源：分类/默认值/测试值）
│   ├── registries.json           # 注册表一致性门禁配置（registry 键集对声明）
│   ├── _excluded_dirs.py         # 排除目录集合 SSOT（verify-docs/verify-registries/init 共用）
│   ├── verify-registries.py      # 多注册表键集一致性门禁（防注册遗漏）
│   ├── doc-counts.json           # 文档计数源配置（AUTO_COUNTS 标记注入）
│   ├── gen-doc-counts.py         # 文档计数自动注入（防文档数字漂移）
│   ├── doctor.py                 # 环境就绪性诊断（新开发者第一步）
│   ├── test-quality-guard.py     # 测试质量守卫（弱断言/缺测/命名）
│   ├── run-affected-tests.py     # 影响范围测试路由（git-diff → 受影响测试）
│   ├── retry.py                  # 瞬态错误重试装饰器（@retry_transient）
│   ├── placeholder-utils.ps1     # 占位符 manifest 读取工具（init/test 共用）
│   ├── validate-commit-msg.sh    # Conventional Commits 校验（commit hook 与 CI 共用）
│   ├── git-hooks/                # git hooks（commit-msg → core.hooksPath）
│   ├── verify-all.ps1            # 全量验证入口（Windows PowerShell）
│   ├── verify-all.py             # 全量验证入口（跨平台 Python）
│   ├── verify-docs.py            # 文档链接/目录树一致性验证（AST 增强版）
│   ├── verify-manual.py          # 手册示例一致性验证（禁自校验）
│   ├── falsy-audit.py            # Falsy 陷阱静态审计（AST 增强版）
│   ├── init-project.ps1          # 从模板初始化新项目（Windows PowerShell）
│   ├── init-project.py           # 从模板初始化新项目（跨平台 Python）
│   ├── test-template.ps1         # 模板完整性自测（init → verify 三件套，CI template-self-test 调用）
│   ├── crossval/                 # 交叉验证目录（按需创建；verify-manual.py 自动发现 scripts/crossval/ 与 examples/scripts/crossval/）
│   └── ...
│
├── templates/                    # 模块脚手架
│   ├── README.md                 # 脚手架使用说明（占位符约定 + 多语言流程）
│   ├── NewModule/                # 新增模块多语言模板（C#/Python/VBA/TypeScript/Go/Rust）
│   ├── language/                 # 构建配置模板（pyproject/Build.props/nuget/tsconfig/go.mod/Cargo.toml/Dockerfile）
│   └── monorepo/                 # Monorepo 子项目模板（子目录级 AGENTS.md）
│
├── .github/                      # GitHub 协作
│   ├── workflows/ci.yml          # CI 质量门禁（quick/full/quality + commit 规范检查）
│   ├── workflows/security.yml    # CodeQL 安全扫描
│   ├── workflows/release.yml     # release-please 自动发版（Conventional Commits 驱动）
│   ├── workflows/stale.yml       # 僵尸 Issue/PR 关闭
│   ├── workflows/detect-template.yml  # 模板自举检测（reusable workflow）
│   ├── workflows/docker.yml.template  # Docker 构建推送 CI 模板
│   ├── dependabot.yml            # 依赖自动更新
│   ├── release-please/           # release-please 配置（config.json）
│   ├── ISSUE_TEMPLATE/           # Bug/功能/文档/重构模板
│   ├── PULL_REQUEST_TEMPLATE.md  # PR 模板
│   └── CODEOWNERS                # 代码所有者分配（PR 审查路由）
│
├── docs/                         # 用户文档（补充材料）
│   ├── README.md                 # 文档目录说明（与 rules/ 的分工）
│   └── architecture.md           # 架构设计（ADR 决策记录）
│
├── build/                        # 构建配置（按需裁剪）
│   └── README.md                 # 构建目录用途说明
│
├── logs/                         # 运行日志（.gitignore 排除）
│
├── examples/                     # 示例项目（最小可运行的完整实践）
│   ├── README.md                 # 示例说明（Core 多语言实现 + CrossVal + 测试）
│   ├── conftest.py               # pytest 路径引导（使根目录运行 examples/tests 可导入 src.stats）
│   ├── package.json              # TypeScript 示例测试依赖（vitest，已接入 CI）
│   ├── package-lock.json         # npm lock（CI npm ci 使用）
│   ├── go.mod                    # Go 示例 module（module examples，已接入 CI）
│   ├── Cargo.toml                # Rust 示例 crate 定义（cargo test 入口）
│   ├── src/                      # 示例源码（lib.rs = Rust crate 根；stats/ = 多语言实现）
│   ├── tests/                    # 示例测试（test_stats.rs = Rust 集成测试）
│   └── scripts/crossval/         # 交叉验证参考实现
│
├── tools/                        # 辅助工具/脚本
│   └── README.md                 # 辅助工具目录用途说明
│
├── Makefile                      # 跨平台验证入口（Linux/macOS: make verify）
├── pyproject.toml                # Python 项目配置（依赖、lint、格式化）
├── AGENTS.md                     # 项目宪法（AI 约束）
├── README.md                     # 用户入口（中文）
├── README.en.md                  # 用户入口（英文，国际化）
├── CONTRIBUTING.md               # 贡献指南
├── CHANGELOG.md                  # 版本变更记录（release-please 自动维护）
├── SECURITY.md                   # 安全政策
├── CODE_OF_CONDUCT.md            # 行为准则
├── FUNDING.yml                   # 资助信息（社区健康文件）
├── LICENSE                       # 开源许可证
├── .release-please-manifest.json # release-please 版本基线
├── .editorconfig                 # 编辑器统一风格
├── .gitignore                    # 排除规则
├── .gitattributes                # 换行符/二进制标记
├── .pre-commit-config.yaml       # 提交前 lint（可选启用）
└── CLAUDE.md                     # Claude Code 兼容副本（AGENTS.md 副本，可选创建）
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

- **YAGNI**：不需要的目录不要建，需要时再补（遵循 AGENTS.md「简洁至上」）
- **目录即契约**：一旦建目录并入库，删除/移动必须同步更新本文件与 AGENTS.md

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
- [ ] AGENTS.md 目录树已同步（如为顶层变更）
