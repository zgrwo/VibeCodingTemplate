# AGENTS.md — 项目宪法

> 全局架构、绝对红线与核心流程。编码细节按需加载 Skill（本文件是路由器，领域细节见各唯一信源）。
> 本文件面向 AI 编程助手（QoderCN / Claude Code / Codex / Copilot），是项目唯一宪法文件。
> 兼容性：本文件即 `AGENTS.md`（大写）——2026 年跨工具事实标准，多数 AI 工具直接读取；Claude Code 副本规则见下方「AGENTS.md 生态兼容」。

## 元数据

- **项目名**：`{{PROJECT_NAME}}`
- **语言**：文档与注释默认中文
- **术语**：[context.md](docs/spec/context.md) — 所有领域词汇唯一定义
- **数字唯一基准**：[api-reference.md](docs/spec/api-reference.md) — 函数签名与错误行为以此为准
- **信息单一事实来源 (SSOT)**：每个事实只在一处定义，其余仅链接引用（文档职责矩阵唯一权威：[documentation.md](docs/governance/documentation.md)）

## 四条核心准则

### 1. 先想后写 (Think Before Coding)

- **不确定就提问**，不猜测业务规则——领域语义有确定答案，去查 specification；**说出来你做假设了**；**主动呈现权衡**（如"A 简单 O(N) vs B 复杂 O(1)，当前规模 A 足够"）。
- **发现架构偏离时停下来**。例如：非 UI 线程直接调了 COM → 停下，走 Dispatcher。

### 2. 简洁至上 (Simplicity First)

- **最少代码解决问题**；**不为一成不变的场景建抽象层**（不为"将来可能的迁移"写 Repository 抽象——当前够用就行）。
- **核心约束要尊重**，不因"更好的体验"越过红线。
- **自检**：一个资深开发者看这段代码会觉得过度设计吗？如果是，简化。

### 3. 精准修改 (Surgical Changes)

- **只改该改的**；**匹配现有风格**（即使你更喜欢另一种命名）。
- **发现无关的死代码/注释/格式问题时，提出来——不要擅自改**，记录到 review 文档让团队决定。
- **只清理因你的改动而变成垃圾的 import / 变量 / 函数**。

### 4. 目标驱动 (Goal-Driven Execution)

- **先定义验证方式，再开始写代码**。将指令转化为可验证目标：

| 而不是 | 而是 |
|--------|------|
| "添加缓存" | "第二次调用耗时 < 首次的 10%，且结果一致。去验证。" |
| "修复线程 Bug" | "压力测试连续 30min，0 个线程异常。去验证。" |
| "重构 Repository" | "重构前后所有集成测试通过，且代码行数减少 30%+。去验证。" |

- **多步骤任务格式**：`[写最小复现测试] → verify: FAILS` → `[修复] → verify: PASSES + 无回归` → `[清理] → verify: diff 只含相关改动`。

---

## 技能加载

修改代码前**必须**加载对应 Skill（Skill-first，不凭记忆编造实现方式）。执行方式：直接 Read skill 文件。

| 范围 | Skill 文件 | 内容 |
| :--- | :--- | :--- |
| `{{SCOPE_1}}` | `skills/{{SKILL_1}}` | `{{DESCRIPTION_1}}` |
| `{{SCOPE_2}}` | `skills/{{SKILL_2}}` | `{{DESCRIPTION_2}}` |
| 语言陷阱（按需） | `skills/csharp-SKILL.md` / `skills/python-SKILL.md` / `skills/vba-SKILL.md` / `skills/typescript-SKILL.md` / `skills/go-SKILL.md` / `skills/rust-SKILL.md` | 对应语言的易错点与最佳实践 |
| 工具陷阱（按需） | `docs/pitfalls/tooling-pitfalls.md` | Windows/PowerShell/git 脚本坑位 |
| CI/脚本/PR 陷阱（按需） | `skills/ci-pipeline-SKILL.md` | GitHub Actions / PowerShell 脚本 / PR 与发版流程陷阱（5 项目实证） |
| 过程技能（按需，Superpowers） | `skills/brainstorming/` / `skills/writing-plans/` / `skills/test-driven-development/` / `skills/subagent-driven-development/` / `skills/systematic-debugging/` / `skills/verification-before-completion/` | 头脑风暴→规格 / 多步任务计划 / TDD / 子代理驱动开发 / 系统化调试 / 完成前验证（第三方，英文，来源 obra/superpowers） |

> 占位符行由 init-project 按项目实际技能替换（清单见 `scripts/placeholders.json`）；模板自带技能见 skills/ 目录。

### 专家 Skill（重构生命周期）

| 决策前 | 执行中 | 执行后 |
|--------|--------|--------|
| `skills/architecture-reviewer-SKILL.md`（新增组件/层级/依赖前） | `skills/refactoring-guardian-SKILL.md`（每个 Phase 前后） | `skills/project-plan-review-SKILL.md`（里程碑复盘/规划评审） |

## 架构分层

```
{{LAYER_DIAGRAM}}
```

- ✅ 上层不包含业务逻辑；下层不引用上层依赖
- ❌ 禁止跨层直接调用或反向依赖

## 仓库目录树

> 路由地图：文件级职责见 [project-structure.md](docs/governance/project-structure.md)（逐文件唯一定义）。推送规则见 [Git](#git)。

```
{{PROJECT_NAME}}/
├── src/                          # ✅ 源码
├── tests/                        # ✅ 测试
├── docs/                         # ✅ 文档中心（五分类，导航见 docs/README.md）
├── scripts/                      # ✅ 构建/验证脚本
├── templates/                    # ✅ 模块脚手架
├── examples/                     # ✅ 示例项目
├── skills/                       # ✅ Skill 定义
├── tools/                        # ✅ 辅助工具
├── build/                        # ✅ 构建配置
├── .github/                      # ✅ CI 工作流 + Issue/PR 模板
├── logs/                         # ✅ 日志（.gitignore 排除）
├── Makefile                      # ✅ 跨平台验证入口
├── pyproject.toml                # ✅ Python 项目配置
├── AGENTS.md                     # ✅ 项目宪法（本文件）
├── README.md                     # ✅ 用户向功能指南
├── README.en.md                  # ✅ 英文入口
├── CONTRIBUTING.md               # ✅ 贡献指南
├── CHANGELOG.md                  # ✅ 版本变更记录
├── SECURITY.md                   # ✅ 安全政策
├── CODE_OF_CONDUCT.md            # ✅ 行为准则
├── FUNDING.yml                   # ✅ 资助信息
├── LICENSE                       # ✅ 开源许可证（MIT）
├── .release-please-manifest.json # ✅ 版本基线
├── .editorconfig                 # ✅ 编辑器风格
├── .gitignore                    # ✅ 排除规则
├── .gitattributes                # ✅ 换行符标记
├── .pre-commit-config.yaml       # ✅ 提交前 lint
└── CLAUDE.md                     # ✅ Claude Code 副本
```

❌ 不入库：`bin/`、`obj/`、`__pycache__/`、`.venv/`、`node_modules/`、`TestResults/`、`*.pyc` 等（完整清单见 .gitignore）

## 红线规则

### 1. 接口与兼容性

- ✅ 保持 Public 签名不变；新增依赖前确认跨平台/跨版本可用
- ❌ 修改公开接口或破坏向后兼容；引入单平台/单版本依赖

### 2. 防错三原则（违反 = bug）

| 原则 | 核心 |
| :--- | :--- |
| **静默传播阻断** | 显式守卫 `NaN`/`Inf`/`null`/`default!`，不兜底 |
| **防御完整性** | 安全机制覆盖模块所有方法（路径验证 / 超时 / 参数化） |
| **异常过滤器** | 统一排除不可恢复异常（OOM / StackOverflow / AccessViolation） |

> **提交前自检**：`python scripts/verify-docs.py --check-bare-handlers` 必须返回 `[OK]`（注释/docstring 感知；勿用裸 grep——会误伤 docstring 内的 `except:` 教学文字，2026-08-15 实证，见 tooling-pitfalls #20）。

### 3. 闭环验证强制

- **3.1 禁止自校验**：`check(name, X, X)` 永远为 PASS，无验证价值
- **3.2 数值类函数必须交叉验证**：与独立参考实现（Python/scipy 等）比对
- **3.3 修改后必须运行全量验证**：任一步失败 = 不可提交

### 4. 文档同步

- 新增 Public 接口 → `docs/spec/api-reference.md`；新增用户可见功能 → `docs/spec/user-manual.md`；目录结构变更 → `docs/governance/project-structure.md`

## 开发流程

### 修改前（强制）

1. **Read** 对应 Skill 文件（Skill-first）
2. 检查调用者与影响范围；确认不违反红线规则

### 修改后

- 验证与调用方一致（签名/返回值/异常传播链路）；运行构建 + 测试确认无回归
- 缺陷处理：追溯根因 → 写入 memory（禁止仅修表面）

### 遇到 Bug 时

1. 写最小复现测试 → confirm: FAILS（Bug 存在）；修复 → confirm: PASSES + 无回归
2. **保留复现测试**（回归守卫）；检查是否需要更新 spec / skill / review

### 提交前必检

- [ ] 所有新代码有对应的测试
- [ ] 无跨层/跨线程违规；命名空间/模块与文件夹一致
- [ ] 没动无关文件
- [ ] 构建通过 + 测试全绿

### 构建与测试

| 场景 | 命令 |
| :--- | :--- |
| 日常构建 | `{{BUILD_CMD}}` |
| 运行测试 | `{{TEST_CMD}}` |
| 全量验证 | `{{FULL_VERIFY_CMD}}`（Windows: `verify-all.ps1` / 跨平台: `python scripts/verify-all.py` 或 `make verify`） |
| CI（PR 级） | `.github/workflows/ci.yml` quick-check（构建+测试+裸 catch 自检） |
| CI（质量门禁） | quality-gate：手册一致性 / 陷阱审计 / 架构约束 / 代码风格 |

### Git

| ✅ DO | ❌ DON'T |
| :--- | :--- |
| 仅推送目录树中出现的文件路径 | 推送目录树之外的文件 |
| Commit 前确认测试全绿 | 未经用户明确同意执行 `git push` |
| Commit message 描述变更内容与原因 | 空 message 或无意义提交 |

> **目录树变更管控**：对目录树的任何修改必须先获得用户明确批准。

## 历史经验（含 diff 分析）

> 从 commit 历史 / 代码审查记录提炼，随项目演进**持续补充**；新增条目必须附真实案例（出现次数 + 根因），禁止臆造。
> **反模式案例库（10 类）唯一权威**：[cross-project-synthesis.md](docs/methodology/cross-project-synthesis.md)；
> **工具/模板坑位（#1-#29）唯一权威**：`docs/pitfalls/tooling-pitfalls.md`——注册遗漏、数字漂移、元占位符污染（#18）、grep 版本行为变化（#25/#25b）、py/ps1 双实现分叉（#26）、模板模式 CI 门禁盲区（#27）、工具链声明与代码漂移（#29）等高频模式见此，本文件不重复。

| 模式 | 教训 |
|------|------|
| 元占位符污染 | 教学 token（`{{X}}`/`{{UPPER}}`/`{{UPPER_CASE}}`）必须原样存活于本文件——test-template.ps1 断言锚点（详见 tooling-pitfalls #18/#26） |

### 关键设计经验

- **Core 零依赖**（UDF→Core→Foundation 分层，固化提交 `1d06e3f`）：核心计算不引用框架，可独立单元测试。
- **哨兵值优于异常**（costsuite 性能回归）：数值计算用 NaN 表示"无效"，避免热路径 try-catch 开销——已固化为防错三原则。
- **SSOT 收敛是持续战役**（DocAudit 数字漂移 4 次复发）：仅设计 SSOT 不够，需 `verify-docs.py --strict` + CI 硬门禁持续守护。

### 历史教训索引

- 反模式案例库 → `docs/methodology/cross-project-synthesis.md`；语言陷阱 → `skills/`；工具坑位 → `docs/pitfalls/tooling-pitfalls.md`；架构决策与回退 → `docs/design/adr/`（ADR 编号递增）

## 防幻觉铁律

| 铁律 | 说明 |
|------|------|
| **不靠记忆引用文档** | 每次引用 `docs/` 或 `skills/` 中的内容时，先 Read/Grep 确认，不凭印象 |
| **不确定 = 承认不确定** | 不要编造业务规则；说"我需要在 spec 中确认"然后去查 |
| **写过的代码 = 读过的代码** | 不要假设自己知道某个文件内容——Read 它或 Grep 确认后再改 |
| **版本号是事实锚点** | 每个结论标注来源文档版本，防止误用过时信息 |

## 会话管理

- **每完成一个独立功能点**对照四条核心准则自检；**上下文超过 5 个文件 / 20 轮对话**提醒用户开新会话；**反复纠正同一个错误**是幻觉信号——停下来写进文档或更新对应规则。
- 新会话先速览本文件（架构+约束）和对应 Skill；跨会话工作通过 **git commit** 衔接，不依赖对话历史；每个 commit 自包含、可追溯。

### 跨会话接力

```
上一个会话结束时 → 在回复末尾简述：
  ✅ 已完成: [具体交付物]
  🔜 下一步: [下一动作 + 涉及文件]
  ⚠️ 待决策: [阻塞项]
  📄 关键上下文: [后续会话必须知道的约束/假设]
```

## AGENTS.md 生态兼容

> 2026 年 AGENTS.md（大写）已是跨工具事实标准（Codex / Copilot / Windsurf / JetBrains / Gemini 直接读取）；QoderCN 兼容小写 `agents.md`。

- **Claude Code** 读 `CLAUDE.md` → 需静态副本：每次修改本文件后重建（PowerShell：`Copy-Item AGENTS.md CLAUDE.md`；Linux：`ln -s AGENTS.md CLAUDE.md`），初始化可用 `init-project.ps1 -CreateCompatibilityLinks`。
- **Monorepo**：子目录放局部 `AGENTS.md`（越靠近当前目录优先级越高，局部覆盖全局），模板见 `templates/monorepo/`。
- **子级 AGENTS.md 只写 Agent 看不出来又容易猜错的事实**：包管理器/构建工具选择、生成文件目录（禁止直接修改）、聚焦测试命令、安全边界（凭据/迁移/发布需人工确认）、修改模块边界前必读文档。多步骤长任务可选 `PLANS.md`（Codex 实践），与目标驱动格式二选一。

## 参考

> 各文档职责矩阵与维护规则（唯一权威）：[documentation.md](docs/governance/documentation.md)；文档中心五分类导航：[docs/README.md](docs/README.md)。本表仅作高频入口速查。

| 文档 | 角色 |
| :--- | :--- |
| [context.md](docs/spec/context.md) | 术语表（唯一定义） |
| [specification.md](docs/spec/specification.md) | 业务信源 |
| [api-reference.md](docs/spec/api-reference.md) | 数字唯一信源（签名/参数/错误行为） |
| [user-manual.md](docs/spec/user-manual.md) | 学习教程（每函数示例） |
| [project-structure.md](docs/governance/project-structure.md) | 结构地图（逐文件职责） |
| [cross-project-synthesis.md](docs/methodology/cross-project-synthesis.md) | 方法论与反模式案例库 |
| [tooling-pitfalls.md](docs/pitfalls/tooling-pitfalls.md) | 工具/脚本坑位清单 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献/PR/发版流程 |
