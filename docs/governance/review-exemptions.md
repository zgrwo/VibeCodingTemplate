# 已知豁免登记表（Max 级审查豁免项）

> 规则见 `docs/governance/code-review-prompt.md`「豁免（exemptions）规则」：
> P0 不可豁免；P1 可豁免需写明接受原因 + 到期版本；**登记即责任**——豁免项进入下次审查必查清单。
> 到期后复查；无本文件 = 无豁免项。

## 已登记豁免/必查项（2026-08 Max 审查登记）

- [P2] 交互模式下 core 无默认值占位符（BUILD_CMD/TEST_CMD 等 20 个）Enter 空值回退占位符名小写
  — 接受原因：与 init-project.ps1 行为对等（两端一致），提示文案已展示回退值（"Enter 用默认: xxx"）；
  非交互路径已有 fail-fast — 到期：v0.2.0 复查（建议改为重新提示或为命令类占位符提供真实默认值）
- [P3] .pre-commit-config.yaml 的 rev 用 tag 非 commit SHA
  — 接受原因：pre-commit 生态惯例（官方钩子 tag 可变性风险低），ruff 版本已与 pyproject 对齐 — 到期：下次依赖升级复查
- [P3] logs/reviews/（审查报告）不入库（.gitignore:73）
  — 接受原因：审查报告为运行时产出（init-project 复制时跳过、verify-docs 排除），非信源文档；
  审查 prompt / 本文件已入库 `docs/governance/`（2026-09 从 `.claude/` 迁移） — 到期：每季度复核

## 已关闭（到期前处理）

- ~~[P3] .claude/（审查 prompt / 本文件 / 审查报告）不入库（.gitignore:67）~~ → **已关闭**（2026-09 迁移）：
  审查 prompt 与本文件迁入 `docs/governance/` 入库维护；审查报告归档至 `logs/reviews/`（见上方新条目）
- ~~[P2] examples/tests/* 的 TypeScript/Go/Rust 示例测试未接入 CI~~ → **已接入**（2026-08-14）：
  ci.yml template-self-test「示例多语言测试」步骤执行 TS(vitest 17)/Go(16)/Rust(15 用例)/Python(16)
  四语言测试；examples/ 新增 package.json+lock / go.mod 并登记目录树
