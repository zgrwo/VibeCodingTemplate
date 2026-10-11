# skills/ — AI 编码技能目录

> 本目录包含两类技能：**模板自带技能**（语言陷阱 / 工具陷阱 / 三位审查专家）与
> **第三方过程技能**（Superpowers，来源 [obra/superpowers](https://github.com/obra/superpowers)）。

## 模板自带技能

- `csharp-SKILL.md` / `python-SKILL.md` / `vba-SKILL.md` / `typescript-SKILL.md` / `go-SKILL.md` / `rust-SKILL.md` — 语言陷阱与规范
- `ci-pipeline-SKILL.md` — CI 管道与脚本技能（GitHub Actions / PowerShell / PR 与发版流程陷阱，5 项目实证）
- `architecture-reviewer-SKILL.md` / `refactoring-guardian-SKILL.md` / `project-plan-review-SKILL.md` — 重构生命周期专家
- 语言技能按项目语言裁剪（删除后同步 `docs/pitfalls/tooling-pitfalls.md` 语言索引表，否则 verify-docs 报断链）

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

### 已知差异：上游悬空引用登记（VENDORED_DANGLING_REFS）

Superpowers 为**按需子集**引入（只取本项目用到的技能目录），上游正文里指向**未引入目录**的相对引用在本地是断的。
这类断链**不改写**（改了就破坏「保持上游原样、便于上游更新」的前提），而是登记在此表，供读者按上游仓库自取。

`scripts/verify-docs.py` 的链接检查排除了这些子树（见该脚本的 `_DOC_EXCLUDED_PREFIXES`），
但**登记表本身有门禁**：子树内新出现的悬空引用若未登记 → `verify-docs.py --strict` 失败；
已登记的引用不再悬空（上游补齐或本地引入）→ 同样失败（防登记表陈旧）。

<!-- VENDORED_DANGLING_REFS_START -->
| 悬空引用 | 出现位置 | 说明 |
|----------|----------|------|
| `../requesting-code-review/code-reviewer.md` | `skills/subagent-driven-development/SKILL.md`（正文 1 处 + 流程图节点 3 处） | 上游 `requesting-code-review` 技能目录未引入，本地无此文件。需要「最终整支代码审查」的提示词时，改用同目录的 `task-reviewer-prompt.md` / `re-review-prompt.md`，或按需从 [obra/superpowers](https://github.com/obra/superpowers) 取该文件 |
<!-- VENDORED_DANGLING_REFS_END -->

> **门禁覆盖范围（写实）**：只扫描 markdown 链接与反引号路径，且跳过围栏代码块；mermaid 图与示例代码块内的引用**不被扫描**
> ——发现新的上游悬空引用时请手动补登本表（没有门禁替你看着这一部分）。

### 更新方式

```bash
git clone --depth 1 https://github.com/obra/superpowers.git /tmp/superpowers
# 对比 skills/<name>/ 与 /tmp/superpowers/skills/<name>/，更新后同步 project-structure.md 目录树
```

### 裁剪建议（下游项目）

- 不需要的过程技能可直接删除对应目录（同时裁剪 `docs/governance/project-structure.md` 与 `AGENTS.md` 技能表的对应行，否则 `verify-docs.py --strict` 报未声明/缺失）
- 保留 `verification-before-completion/` 与 `test-driven-development/` 通常收益最高（与模板闭环验证/测试完备性要求互补）
