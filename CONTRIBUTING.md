# 贡献指南

感谢你对 {{PROJECT_NAME}} 的关注！{{ONE_LINE_DESCRIPTION}}

> 参与本项目即表示你同意遵守 [行为准则](CODE_OF_CONDUCT.md)；报告安全问题请走 [SECURITY.md](SECURITY.md) 的私密漏洞上报流程，**不要**在 Issue/PR 中公开细节。

## 目录

- [如何开始（新手指引）](#如何开始新手指引)
- [开发环境](#开发环境)
- [修改流程（强制）](#修改流程强制)
- [代码规范](#代码规范)
- [提交规范（Conventional Commits）](#提交规范conventional-commits)
- [提交前必检](#提交前必检)
- [代码审查](#代码审查)
- [PR 规范](#pr-规范)
- [Issue 规范](#issue-规范)
- [分支策略](#分支策略)
- [发版流程（release-please 自动发版）](#发版流程release-please-自动发版)
- [许可证](#许可证)

## 如何开始（新手指引）

- **先阅读** [README.md](README.md)（项目是什么）+ [AGENTS.md](AGENTS.md)（架构、红线、流程）——架构分层、防错三原则、闭环验证是协作基础。
- **找入口**：在 Issues 中搜索 `good first issue` 或 `help wanted` 标签——它们经过筛选，适合新贡献者。若选择未打标签的 Issue，先留言确认避免与他人重复。
- **报告前先确认**：Bug 请在**最新版本**复现后再提交（Issue 模板有此必填项）。
- **文档地图**：各文档职责分工见 [rules/documentation.md](rules/documentation.md)（唯一权威）——改动前确认该内容属于哪个文档，避免重复定义（SSOT）。

## 开发环境

```bash
git clone <repository-url>
cd {{PROJECT_NAME}}
{{INSTALL_COMMANDS}}
```

- **提交规范校验 hook**（推荐启用）：初始化时 `init-project.ps1 -GitInit` 或 `python scripts/init-project.py --git-init` 已自动配置；手动启用：
  ```bash
  git config core.hooksPath scripts/git-hooks
  ```
  hook 会拦截不符合 Conventional Commits 的提交（紧急情况可用 `git commit --no-verify` 逃生，不推荐）。
- **跨平台验证**：
  - Windows：`.\scripts\verify-all.ps1`
  - Linux/macOS/WSL：`python scripts/verify-all.py` 或 `make verify`
- **IDE 提示**：`.editorconfig` 已统一缩进/换行/编码，主流 IDE 自动生效；PowerShell 脚本须保持 UTF-8 with BOM（见 [rules/tooling-pitfalls.md](rules/tooling-pitfalls.md)）。

## 修改流程（强制）

> 完整流程见 [AGENTS.md](AGENTS.md)「开发流程」章节。核心：**Skill-first + 闭环验证 + 文档同步**。

1. **Read** 对应 Skill 文件（`skills/{{SKILL_1}}` 等），不凭记忆编造实现方式
2. 检查调用者与影响范围（Grep 调用链）
3. 实现功能 + 同步写测试（边界/退化输入必须覆盖）
4. 运行全量验证（{{FULL_VERIFY_CMD}}）
5. 执行深度审查（按变更范围选 Min/Standard/Max，见[代码审查](#代码审查)）
6. 同步文档（api-reference / user-manual / project-structure）
7. 提交前必检清单（见 [AGENTS.md](AGENTS.md#提交前必检)）

## 代码规范

- **架构分层**：{{LAYER_DIAGRAM}}（严格单向依赖，底层不感知上层）
- **防错三原则**：静默传播阻断 / 防御完整性 / 异常过滤器（无裸 catch / bare except）
- **闭环验证**：数值类必须与独立参考实现交叉比对，禁止自校验 `check(X, X)`
- **文档同步**：Public 接口变更必须同步 `rules/api-reference.md`
- **语言陷阱**：见 `skills/`（Falsy / 封送 / 数组边界等高频错误）

## 提交规范（Conventional Commits）

提交信息格式：`type(scope): 描述`（scope 可选）。此格式是 **release-please 自动发版** 的输入——`feat`/`fix` 决定版本号升降；`docs`/`build`/`ci` 等配置了 changelog section 的类型**也会触发发版**（0.x 下 bump patch，2026-08-22 实证：build→0.2.2、docs→0.2.3）。**格式错误会被 commit hook 与 CI 同时拦截**。

| type | 含义 | 发版影响（release-please，0.x 实证口径） |
|------|------|---------------------------|
| `feat` | 新功能 | minor（0.x 下 bump-patch-for-minor-pre-major → patch） |
| `fix` | Bug 修复 | patch |
| `feat!` / `feat(scope)!:` | 破坏性变更（BREAKING CHANGE） | major（pre-1.0 时为 minor） |
| `docs` | 文档 | **patch（实证会触发发版）** |
| `style` | 代码风格（无逻辑变化） | 无（未实证，以 release-please 实测为准） |
| `refactor` | 重构（无行为变化） | 无（未实证） |
| `test` | 测试 | 无（未实证） |
| `build` | 构建 | **patch（实证会触发发版）** |
| `ci` | CI 配置 | **patch（实证会触发发版）** |
| `perf` | 性能优化 | 无（未实证） |
| `revert` | 回滚 | 无（未实证） |
| `chore` | 维护（依赖/杂务） | 无（release-please 自身提交类型，不触发） |
| `release` | 发版（release-please 自动提交） | 无 |

示例：`fix(engine): 修复 anova 效应量计算`、`feat!(api): 移除已废弃的导出参数`、`docs(用户手册): 补充阈值参数说明`。

校验规则唯一权威：`scripts/validate-commit-msg.sh`（本地 hook 与 CI 共用，见[开发环境](#开发环境)）。

## 提交前必检

```bash
{{FULL_VERIFY_CMD}}   # 全量验证（构建 + 测试 + 一致性）
```

- [ ] 所有新代码有对应的测试
- [ ] 无跨层/跨线程违规
- [ ] 没动无关文件（Surgical Changes）
- [ ] 构建通过 + 测试全绿

## 代码审查

- **选择级别**：单文件小修复 → Min；功能迭代（≤5 文件）→ Standard；发版前全量 → Max。
- **审查者期望**：收到 review 请求后 **48 小时内** 给出首轮反馈；审查聚焦正确性/防御性/架构合规，风格问题由 CI 拦截。
- **提交方期望**：PR 保持小粒度（一个逻辑变更一个 PR），及时响应 review 意见并 resolve 讨论。

## PR 规范

1. 每个 PR 自包含、可追溯
2. commit message 遵循 [提交规范](#提交规范conventional-commits)（CI 自动校验）
3. 涉及数值变更的 PR 必须附交叉验证输出对比
4. 新增功能必须完成文档同步链（api-reference + user-manual + project-structure）
5. 填写 PR 模板验证记录：构建/测试/全量验证均已通过

## Issue 规范

- **Bug**：使用 bug 模板，附最小复现步骤 + 期望/实际输出
- **功能建议**：使用 feature 模板
- **报告前先确认**已在最新版本复现
- 想参与贡献？认领带 `good first issue` 或 `help wanted` 标签的 Issue（见[如何开始](#如何开始新手指引)）

## 分支策略

- `main` 为唯一长期分支，始终保持可发布状态（Protected：禁止直接 push，合并须经 PR + CI 通过）
- 功能/修复在 `feature/xxx` 分支开发，PR 合并到 `main`
- 发版无需手动打 tag（见下节）

## 发版流程（release-please 自动发版）

> 本模板引入 [release-please](https://github.com/googleapis/release-please) 自动发版，从 Conventional Commits 推导版本号。**不再手工编辑 CHANGELOG、维护三处版本号或推送 tag**。

1. 开发 → 提交遵循 [提交规范](#提交规范conventional-commits) → PR 合并到 `main`
2. 当 `main` 上积累了需要发版的 `feat`/`fix` 提交，release-please 自动打开 **release PR**（含版本号提升与 CHANGELOG 更新）
3. 审查并合并 release PR → 自动创建 tag `vX.Y.Z` + GitHub Release（正文取自 CHANGELOG 对应段落）
4. 手动覆盖版本：在 release PR 的 commit body 中加 `Release-As: x.y.z`
5. 验证：Release 产物可用；若有构建产物，可配 tag 触发的构建 workflow

**发行前检查清单**（合并 release PR 前逐项确认；完整 18 维度穷尽审计见 `.claude/prompts/pre-release-review.md`）：

- [ ] `python scripts/verify-all.py` 全绿（构建/测试/文档一致性/手册一致性/注册表/计数/质量守卫）
- [ ] `python -m ruff check scripts/ tests/ examples/` 零违规
- [ ] 版本一致性：`.release-please-manifest.json` == `pyproject.toml` == CHANGELOG 最新段（verify-docs 门禁已覆盖）
- [ ] 模板仓库自身：`test-template.ps1` 通过（含教学 token 存活断言）
- [ ] `git status` 干净，无未提交/未追踪文件
- [ ] 模板模式下 CI（pytest/ruff 字面命令步骤）为绿色

工作流：`.github/workflows/release.yml`（release-please-action）+ 配置 `.github/release-please/config.json` + 版本基线 `.release-please-manifest.json`。

## 许可证

提交代码即表示同意以 [MIT](LICENSE) 许可证发布。
