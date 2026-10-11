# 已知豁免登记表（Max 级审查豁免项）

> 规则见 `docs/governance/code-review-prompt.md`「豁免（exemptions）规则」：
> P0 不可豁免；P1 可豁免需写明接受原因 + 到期版本；**登记即责任**——豁免项进入下次审查必查清单。
> 到期后复查；无本文件 = 无豁免项。
>
> **到期门禁（2026-10-11 新增）**：写了 `到期：vX.Y.Z` 的条目由 `scripts/verify-docs.py` 的
> 「豁免到期」向量硬校验——到期版本 <= 当前版本即 FAIL，必须**复查后关闭**（划删除线 + 写复查结论）
> 或**改写到期版本并说明复查依据**。此前只靠人工承诺，实测出现过期 4 个版本仍未复查的条目。
> 引用 `.gitignore` 等清单文件时**写段落名而非行号**（行号随清单增删漂移，已两次失真）。

## 已登记豁免/必查项

- [P3] .pre-commit-config.yaml 的 rev 用 tag 非 commit SHA
  — 接受原因：pre-commit 生态惯例（官方钩子 tag 可变性风险低），ruff 版本已与 pyproject 对齐 — 到期：下次依赖升级复查
- [P3] logs/reviews/（审查报告）不入库（`.gitignore`「日志与临时文件」段的 `logs/`）
  — 接受原因：审查报告为运行时产出（init-project 复制时跳过、verify-docs 排除），非信源文档；
  审查 prompt / 本文件已入库 `docs/governance/`（2026-09 从 `.claude/` 迁移） — 到期：每季度复核（下一次 2026-12）

## 已关闭（到期前处理）

- ~~[P2] 交互模式下 core 无默认值占位符（当时 20 个；同一轮去伪后降为 9 个项目定义项）Enter 空值回退占位符名小写~~ →
  **已修复**（2026-10-11，到期版本 v0.2.0 已过期 4 个版本后复查）：两个实现均改为**重提示**，
  超过 3 次仍未填写则 fail-fast（与非交互路径同语义）——空输入回退占位符名小写会静默生成损坏的
  CI 配置（BUILD_CMD → build_cmd），属红线「静默传播阻断」。回归测试见
  `tests/scripts/test_init_project.py::TestGetPlaceholderValue`（空输入 fail-fast / 重提示取值 /
  有默认值时 Enter 用默认 三条）。

- ~~[P3] .claude/（审查 prompt / 本文件 / 审查报告）不入库（`.gitignore`「AI 会话产物」段）~~ → **已关闭**（2026-09 迁移）：
  审查 prompt 与本文件迁入 `docs/governance/` 入库维护；审查报告归档至 `logs/reviews/`（见上方新条目）
- ~~[P2] examples/tests/* 的 TypeScript/Go/Rust 示例测试未接入 CI~~ → **已接入**（2026-08-14）：
  ci.yml template-self-test「示例多语言测试」步骤执行 TS(vitest 17)/Go(16)/Rust(15 用例)/Python(16)
  四语言测试；examples/ 新增 package.json+lock / go.mod 并登记目录树
