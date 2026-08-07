# 贡献指南

感谢你对 {{PROJECT_NAME}} 的关注！{{ONE_LINE_DESCRIPTION}}

> 参与本项目即表示你同意遵守 [行为准则](CODE_OF_CONDUCT.md)；报告安全问题请走 [SECURITY.md](SECURITY.md) 的私密漏洞上报流程，**不要**在 Issue/PR 中公开细节。

## 开发环境

```bash
git clone <repository-url>
cd {{PROJECT_NAME}}
{{INSTALL_COMMANDS}}
```

## 修改流程（强制）

> 完整流程见 [AGENTS.md](AGENTS.md)「开发流程」章节。核心：**Skill-first + 闭环验证 + 文档同步**。

1. **Read** 对应 Skill 文件（`skills/{{SKILL_1}}` 等），不凭记忆编造实现方式
2. 检查调用者与影响范围（Grep 调用链）
3. 实现功能 + 同步写测试（边界/退化输入必须覆盖）
4. 运行全量验证（{{FULL_VERIFY_CMD}}）
5. 执行深度审查（`rules/code-review-prompt.md`，按变更范围选 Min/Standard/Max）
6. 同步文档（api-reference / user-manual / project-structure）
7. 提交前必检清单（见 [AGENTS.md](AGENTS.md#提交前必检)）

## 代码规范

- **架构分层**：{{LAYER_DIAGRAM}}（严格单向依赖，底层不感知上层）
- **防错三原则**：静默传播阻断 / 防御完整性 / 异常过滤器（无裸 catch / bare except）
- **闭环验证**：数值类必须与独立参考实现交叉比对，禁止自校验 `check(X, X)`
- **文档同步**：Public 接口变更必须同步 `rules/api-reference.md`
- **语言陷阱**：见 `skills/`（Falsy / 封送 / 数组边界等高频错误）

## 提交前必检

```bash
{{FULL_VERIFY_CMD}}   # 全量验证（构建 + 测试 + 一致性）
```

- [ ] 所有新代码有对应的测试
- [ ] 无跨层/跨线程违规
- [ ] 没动无关文件（Surgical Changes）
- [ ] 构建通过 + 测试全绿

## PR 规范

1. 每个 PR 自包含、可追溯
2. commit message 格式：`type(scope): 简述`（如 `fix(engine): 修复 anova 效应量计算`）
3. 涉及数值变更的 PR 必须附交叉验证输出对比
4. 新增功能必须完成文档同步链（api-reference + user-manual + project-structure）

## Issue 规范

- **Bug**：使用 bug 模板，附最小复现步骤 + 期望/实际输出
- **功能建议**：使用 feature 模板
- 报告前先确认已在最新版本复现

## 分支策略

- `main` 为唯一长期分支，始终保持可发布状态（Protected：禁止直接 push，合并须经 PR + CI 通过）
- 功能/修复在 `feature/xxx` 分支开发，PR 合并到 `main`
- 发版从 `main` 打 tag：`v{MAJOR}.{MINOR}.{PATCH}`

## 发版与 tag 规范

1. 更新 `CHANGELOG.md`（keepachangelog 格式）
2. 更新版本号（代码/配置/文档三处一致）
3. `git tag v{MAJOR}.{MINOR}.{PATCH}`（monorepo 中 tag 需带项目前缀）
4. 推送 tag 后由 [release.yml](.github/workflows/release.yml) 自动构建 → 测试 → 生成 Release（正文取自 CHANGELOG 对应段落）
5. 验证 Release 产物可用

## 许可证

提交代码即表示同意以 [MIT](LICENSE) 许可证发布。
