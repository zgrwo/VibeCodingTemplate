# AGENTS.md — 项目宪法

> 全局架构、绝对红线与核心流程。编码细节按需加载 Skill。术语见 [context.md](rules/context.md)。
> 本文件面向 AI 编程助手（QoderCN / Claude Code / Codex / Copilot），是项目唯一宪法文件。
> 兼容性：本文件即 `AGENTS.md`（大写）——2026 年跨工具事实标准，多数 AI 工具可直接读取；Claude Code 按需创建 `CLAUDE.md` 副本（见下方「AGENTS.md 生态兼容」）。

## 元数据

- **项目名**：`{{PROJECT_NAME}}`
- **语言**：文档与注释默认中文
- **术语**：[context.md](rules/context.md) — 所有领域词汇唯一定义
- **数字唯一基准**：[api-reference.md](rules/api-reference.md) — 函数签名与错误行为以此为准
- **信息单一事实来源 (SSOT)**：每个事实只在一处定义，其余仅链接引用

## 四条核心准则

### 1. 先想后写 (Think Before Coding)

- **不确定就提问**。不要猜测业务规则——领域语义有确定答案，去查 specification。
- **说出来你做假设了**。"假设 X 不超过 5 级 → 代码按此编写，但如果实际是 6 级，这里会截断。"
- **主动呈现权衡**。"两种方案：A 简单 O(N)，B 复杂 O(1)。当前规模下 A 足够。"
- **发现架构偏离时停下来**。例如：发现自己在非 UI 线程直接调了 COM → 停下，走 Dispatcher。

### 2. 简洁至上 (Simplicity First)

- **最少代码解决问题**。200 行的 Service 写成 50 行更好。
- **不为一成不变的场景建抽象层**。不要为"将来可能的迁移"写 Repository 抽象——当前够用就行。
- **核心约束要尊重**。不要因为"更好的体验"而越过红线。
- **自检**：一个资深开发者看这段代码会觉得过度设计吗？如果是，简化。

### 3. 精准修改 (Surgical Changes)

- **只改该改的**。如果任务是"修复 X 的死锁"，不要顺带重构 Y 的命名约定。
- **匹配现有风格**。即使你更喜欢另一种命名，如果周围代码用现有风格，保持一致。
- **发现无关的死代码/注释/格式问题时，提出来——不要擅自改**。记录到 review 文档，让团队决定。
- **只清理因你的改动而变成垃圾的 import / 变量 / 函数**。

### 4. 目标驱动 (Goal-Driven Execution)

- **先定义验证方式，再开始写代码**。
- 将指令转化为可验证目标：

| 而不是 | 而是 |
|--------|------|
| "添加缓存" | "第二次调用耗时 < 首次的 10%，且结果一致。去验证。" |
| "修复线程 Bug" | "压力测试连续 30min，0 个线程异常。去验证。" |
| "重构 Repository" | "重构前后所有集成测试通过，且代码行数减少 30%+。去验证。" |

- **多步骤任务格式**：
  ```
  1. [写最小复现测试] → verify: 测试 FAILS（证明 Bug 存在）
  2. [写修复]           → verify: 测试 PASSES + 无回归
  3. [清理]             → verify: diff 只含相关改动
  ```

---

## 技能加载

修改代码前**必须**加载对应 Skill（Skill-first，不凭记忆编造实现方式）：

| 范围 | Skill 文件 | 内容 |
| :--- | :--- | :--- |
| `{{SCOPE_1}}` | `skills/{{SKILL_1}}` | `{{DESCRIPTION_1}}` |
| `{{SCOPE_2}}` | `skills/{{SKILL_2}}` | `{{DESCRIPTION_2}}` |
| 语言陷阱（按需） | `skills/csharp-SKILL.md` / `skills/python-SKILL.md` / `skills/vba-SKILL.md` | 对应语言的易错点与最佳实践 |
| 工具陷阱（按需） | `rules/tooling-pitfalls.md` | Windows/PowerShell/git 脚本坑位 |

> **执行方式**：直接 Read skill 文件。
>
> **AGENTS.md 生态兼容**：本文件即 `AGENTS.md`（大写），Codex/Copilot/Windsurf/JetBrains/Gemini 可直接读取；Claude Code 需 `CLAUDE.md` 副本——见下方「AGENTS.md 生态兼容」。

### 专家 Skill（重构生命周期）

| 阶段 | Skill | 触发时机 |
|------|-------|----------|
| 决策前 | `skills/architecture-reviewer.md` | 新增组件/层级/依赖前 |
| 执行中 | `skills/refactoring-guardian.md` | 每个 Phase 开始/结束时 |
| 执行后 | `skills/project-plan-review.md` | 里程碑复盘/规划评审时 |

## 架构分层

```
{{LAYER_DIAGRAM}}
```

- ✅ 上层不包含业务逻辑；下层不引用上层依赖
- ❌ 禁止跨层直接调用或反向依赖

## 仓库目录树

> 路由地图：所有文件路径均以此为基准。详细结构见 [project-structure.md](rules/project-structure.md)。推送规则见 [Git](#git)。

```
{{PROJECT_NAME}}/
├── src/                          # ✅ 源码
├── tests/                        # ✅ 测试
├── docs/                         # ✅ 文档（设计文档，见 docs/README.md）
├── scripts/                      # ✅ 构建/验证脚本（verify-all / verify-docs / init-project 等）
├── templates/                    # ✅ 模块脚手架（NewModule 四件套 + language 构建配置）
├── skills/                       # ✅ Skill 定义
├── rules/                        # ✅ 规范文档（含 ADR 决策记录）
├── tools/                        # ✅ 辅助工具
├── build/                        # ✅ 构建配置
├── .github/                      # ✅ CI 工作流 + Issue/PR 模板
│   ├── workflows/ci.yml          # CI 质量门禁（quick/full/quality）
│   ├── workflows/security.yml    # CodeQL 安全扫描（定时 + PR）
│   ├── workflows/release-drafter.yml  # 自动生成 Release 草稿
│   ├── workflows/release.yml     # tag 自动发布（v* tag 触发）
│   ├── workflows/stale.yml       # 僵尸 Issue/PR 自动关闭
│   ├── dependabot.yml            # 依赖自动更新
│   ├── ISSUE_TEMPLATE/           # Bug/功能/文档/重构四类模板
│   └── PULL_REQUEST_TEMPLATE.md  # PR 模板
├── logs/                         # ✅ 日志（.gitignore 排除）
├── AGENTS.md                     # ✅ 项目宪法（本文件）
├── README.md                     # ✅ 用户向功能指南
├── CONTRIBUTING.md               # ✅ 贡献指南（开发/PR/发版流程）
├── CHANGELOG.md                  # ✅ 版本变更记录（keepachangelog）
├── SECURITY.md                   # ✅ 安全政策与漏洞报告
├── CODE_OF_CONDUCT.md            # ✅ 行为准则
├── LICENSE                       # ✅ 开源许可证（MIT）
├── .gitignore                    # ✅ 排除规则
├── .gitattributes                # ✅ 换行符/二进制标记
└── .pre-commit-config.yaml       # ✅ 提交前 lint（可选启用）
```

```
❌ 不入库: bin/  obj/  *.xll  __pycache__/  .venv/  node_modules/
           TestResults/  logs/  *.pyc  .claude/reviews/
```

## 红线规则

### 1. 接口与兼容性

| ✅ DO | ❌ DON'T |
| :--- | :--- |
| 保持 Public 签名不变 | 修改公开接口或破坏向后兼容 |
| 新增依赖前确认跨平台/跨版本可用 | 引入单平台/单版本依赖 |

### 2. 防错三原则（违反 = bug）

| 原则 | 核心 |
| :--- | :--- |
| **静默传播阻断** | 显式守卫 `NaN`/`Inf`/`null`/`default!`，不兜底 |
| **防御完整性** | 安全机制覆盖模块所有方法（路径验证 / 超时 / 参数化） |
| **异常过滤器** | 统一排除不可恢复异常（OOM / StackOverflow / AccessViolation） |

> **提交前自检**：`grep -rn "catch\s*{" src/` 或 `grep -rn "except:" src/` 必须返回空。

### 3. 闭环验证强制

| # | 规则 |
|:---|:---|
| **3.1** | **禁止自校验**：`check(name, X, X)` 永远为 PASS，无验证价值 |
| **3.2** | **数值类函数必须交叉验证**：与独立参考实现（Python/scipy 等）比对 |
| **3.3** | **修改后必须运行全量验证**：任一步失败 = 不可提交 |

### 4. 文档同步

- 新增 Public 接口 → 同步更新 `rules/api-reference.md`
- 新增用户可见功能 → 同步更新 `rules/user-manual.md`
- 目录结构变更 → 同步更新 `rules/project-structure.md`

## 开发流程

### 修改前（强制）

1. **Read** 对应 Skill 文件（Skill-first，不凭记忆编造实现方式）
2. 检查调用者与影响范围
3. 确认不违反红线规则

### 修改后

- 验证与调用方一致（签名/返回值/异常传播链路）
- 运行构建 + 测试确认无回归
- 缺陷处理：追溯根因 → 写入 memory（禁止仅修表面）

### 遇到 Bug 时

1. 写最小复现测试 → confirm: 测试 FAILS（Bug 存在）
2. 修复 → confirm: 复现测试 PASSES + 已有测试无回归
3. **保留复现测试**（它现在是回归守卫——下次同样的 Bug 会被 CI 拦截）
4. 检查是否需要更新 spec / skill / review（Bug 暴露了文档缺口？）

### 提交前必检

- [ ] 所有新代码有对应的测试
- [ ] 无跨层/跨线程违规
- [ ] 命名空间/模块与文件夹一致
- [ ] 没动无关文件
- [ ] 构建通过 + 测试全绿

### 构建与测试

| 场景 | 命令 |
| :--- | :--- |
| 日常构建 | `{{BUILD_CMD}}` |
| 运行测试 | `{{TEST_CMD}}` |
| 全量验证 | `{{FULL_VERIFY_CMD}}` |
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

> 从项目 commit 历史 / 代码审查记录中提炼，随项目演进**持续补充**。新增条目必须附真实案例（出现次数 + 根因），禁止臆造。

### 高频修复模式

| 模式 | 出现次数 | 根因 |
|------|----------|------|
| `{{PATTERN_1}}` | `{N}`+ | `{{ROOT_CAUSE_1}}` |
| `{{PATTERN_2}}` | `{N}`+ | `{{ROOT_CAUSE_2}}` |

> 初始化时从项目历史审查记录填充前 3-5 条；后续每次审查发现新高频模式即追加。

### 关键设计经验

- {{已验证的设计决策/架构约束（附来源 commit 或审查编号）}}

### 历史教训索引

- 语言陷阱（Falsy / 封送 / 数组边界）→ `skills/`
- 工具/脚本坑位（PowerShell / git / robocopy）→ `rules/tooling-pitfalls.md`
- 架构决策与回退记录 → `rules/adr/`（ADR 编号递增）

## 防幻觉铁律

| 铁律 | 说明 |
|------|------|
| **不靠记忆引用文档** | 每次引用 `rules/` 或 `skills/` 中的内容时，先 Read/Grep 确认，不凭印象 |
| **不确定 = 承认不确定** | 不要编造业务规则；说"我需要在 spec 中确认"然后去查 |
| **写过的代码 = 读过的代码** | 不要假设自己知道某个文件内容——Read 它或 Grep 确认后再改 |
| **版本号是事实锚点** | 每个结论标注来源文档版本，防止误用过时信息 |

## 会话管理

### 何时自查

- **每完成一个独立功能点** — 对照四条核心准则自检
- **上下文超过 5 个文件 / 20 轮对话** — 提醒用户开新会话
- **反复纠正同一个错误时** — 这是幻觉信号，停下来写进文档或更新对应规则

### 跨会话接力

```
上一个会话结束时 → 在回复末尾简述：
  ✅ 已完成: [具体交付物]
  🔜 下一步: [下一动作 + 涉及文件]
  ⚠️ 待决策: [阻塞项]
  📄 关键上下文: [后续会话必须知道的约束/假设]
```

### 基本原则

- 新会话中先速览本文件（架构+约束）和对应 Skill（陷阱清单）
- 跨会话工作通过 **git commit** 衔接，不依赖对话历史传递上下文
- 每个 commit 应自包含、可追溯

## AGENTS.md 生态兼容

> 2026 年 AGENTS.md 已成为跨工具事实标准（OpenAI Codex / Claude Code / GitHub Copilot / Windsurf / JetBrains AI / Gemini 均支持）。本文件即 AGENTS.md（大写）标准形态，按以下规则对齐生态：

### 1. 文件命名与兼容

| 工具 | 读取文件 | 处理方式 |
|------|----------|----------|
| Codex / Copilot / Windsurf / JetBrains / Gemini | `AGENTS.md` | 直接读取，无需处理 |
| Claude Code | `CLAUDE.md` | 创建副本：`Copy-Item AGENTS.md CLAUDE.md`（Linux：`ln -s AGENTS.md CLAUDE.md`） |
| QoderCN | `AGENTS.md`（兼容小写 `agents.md`） | 模板默认大写 `AGENTS.md` 即可 |

### 2. 子目录级 AGENTS.md（Monorepo）

- 多模块仓库：在子目录放局部 `AGENTS.md`，写清「你只管 X，不要碰 Y」
- 优先级：越靠近当前目录的文件优先级越高（局部覆盖全局）
- 单模块项目无需子目录级文件

### 3. 「Agent 看不出来的事实」最小清单

> 原则：Agent 能从代码看出来的内容不写；只写它**看不出来又容易猜错**的事实（参考 GitHub AGENTS.md 开放格式与 Phodal Better Harness）：

- [ ] 包管理器/构建工具选择（仓库同时存在多种痕迹时，写明用哪个）
- [ ] 生成文件目录（长得像源码、实际由工具生成的目录，禁止直接修改）
- [ ] 聚焦测试命令（完整测试耗时长的模块，写明改单模块先跑哪条）
- [ ] 安全边界（凭据、数据库迁移、发布操作需人工确认）
- [ ] 修改模块边界前必须阅读的文档（如 `rules/api-reference.md`）

> 长任务可选：对多步骤任务可用 `PLANS.md`（OpenAI Codex 实践），本模板已内置目标驱动格式，二选一即可。

## 参考

> 各文档职责矩阵与维护规则（唯一权威）：[documentation.md](rules/documentation.md)。本表仅作快速索引。

| 文档 | 角色 | 内容 |
| :--- | :--- | :--- |
| [README.md](README.md) | 用户入口 | 安装、模块速览、使用模式 |
| [context.md](rules/context.md) | 术语表 | 所有术语唯一定义 |
| [specification.md](rules/specification.md) | 业务信源 | 项目概述、模块清单、功能规格 |
| [api-reference.md](rules/api-reference.md) | 数字唯一信源 | 函数签名、参数、错误行为 |
| [user-manual.md](rules/user-manual.md) | 学习教程 | 每函数详细示例 + 结果解读 |
| [project-structure.md](rules/project-structure.md) | 结构地图 | 文件职责与层级关系 |
| [documentation.md](rules/documentation.md) | 文档职责 | 各文档分工与维护规则 |
| [code-review-prompt.md](rules/code-review-prompt.md) | 审查模板 | 深度代码审查 Prompt |
| [cross-project-synthesis.md](rules/cross-project-synthesis.md) | 方法论 | 跨项目共性经验与重构方法论 |
| [refactoring-plan.md](rules/refactoring-plan.md) | 重构计划 | 从"能用"到"卓越"的路线图模板 |
| [adr-template.md](rules/adr-template.md) | ADR 模板 | 架构决策记录格式与编号规则 |
| [falsy-pitfalls.md](rules/falsy-pitfalls.md) | 陷阱清单 | Python falsy 值误判检查清单 |
| [tooling-pitfalls.md](rules/tooling-pitfalls.md) | 陷阱清单 | Windows/PowerShell/git 脚本坑位 |
| [templates/README.md](templates/README.md) | 脚手架说明 | 新增模块/构建配置的使用方式 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 | 开发/PR/发版流程 |
| [CHANGELOG.md](CHANGELOG.md) | 变更记录 | 版本变更历史（keepachangelog） |
