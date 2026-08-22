# skills/ — AI 编码技能目录

> 本目录包含两类技能：**模板自带技能**（语言陷阱 / 工具陷阱 / 三位审查专家）与
> **第三方过程技能**（Superpowers，来源 [obra/superpowers](https://github.com/obra/superpowers)）。

## 模板自带技能

- `csharp-SKILL.md` / `python-SKILL.md` / `vba-SKILL.md` / `typescript-SKILL.md` / `go-SKILL.md` / `rust-SKILL.md` — 语言陷阱与规范
- `ci-pipeline-SKILL.md` — CI 管道与脚本技能（GitHub Actions / PowerShell / PR 与发版流程陷阱，5 项目实证）
- `architecture-reviewer-SKILL.md` / `refactoring-guardian-SKILL.md` / `project-plan-review-SKILL.md` — 重构生命周期专家
- 语言技能按项目语言裁剪（删除后同步 `rules/tooling-pitfalls.md` 语言索引表，否则 verify-docs 报断链）

## 第三方过程技能（Superpowers，英文原版）

来源：[obra/superpowers](https://github.com/obra/superpowers)（MIT），2026-08-14 引入，
导入 commit `b36e082`（`git ls-remote` 实测）。**内容保持上游原样，不做本地改写**（便于上游更新）。

| 目录 | 触发时机 |
|------|----------|
| `brainstorming/` | 任何创造性工作前：探索意图/需求/设计后再实现 |
| `writing-plans/` | 有多步任务的规格后、动代码前：写执行计划 |
| `test-driven-development/` | 实现功能/修 Bug 前：先写测试 |
| `subagent-driven-development/` | 按计划执行独立任务：每任务派发新子代理 + 任务审查 + 分支终审 |
| `systematic-debugging/` | 遇到 Bug/测试失败/意外行为：先定位根因再修 |
| `verification-before-completion/` | 声称"完成/通过"前：先跑验证命令，证据先于断言（与模板「闭环验证强制」一致） |

### 更新方式

```bash
git clone --depth 1 https://github.com/obra/superpowers.git /tmp/superpowers
# 对比 skills/<name>/ 与 /tmp/superpowers/skills/<name>/，更新后同步 project-structure.md 目录树
```

### 裁剪建议（下游项目）

- 不需要的过程技能可直接删除对应目录（同时裁剪 `rules/project-structure.md` 与 `AGENTS.md` 技能表的对应行，否则 `verify-docs.py --strict` 报未声明/缺失）
- 保留 `verification-before-completion/` 与 `test-driven-development/` 通常收益最高（与模板闭环验证/测试完备性要求互补）
