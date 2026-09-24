# 审查检查清单（人工版）

> 面向**人类审查者 / PR 作者**的逐项检查表，每条附可执行命令（证据先于判断）。
> AI 深度审查用 [code-review-prompt.md](code-review-prompt.md)（Min/Standard/Max）与
> [pre-release-review-prompt.md](pre-release-review-prompt.md)（发行前）；
> 提交者摘要见 [.github/PULL_REQUEST_TEMPLATE.md](../../.github/PULL_REQUEST_TEMPLATE.md)。
> 红线规则唯一定义见 [AGENTS.md](../../AGENTS.md)，本清单不重复定义。

## A. 提交前自检（作者）

| # | 检查项 | 命令 | 判定 |
|---|--------|------|------|
| A1 | 全量验证 | `python scripts/verify-all.py` | 全绿（任一步失败即不可提交） |
| A2 | Lint + 格式 | `python -m ruff check scripts/ tests/ examples/ && python -m ruff format --check scripts/ tests/ examples/` | 0 错误 |
| A3 | 提交信息规范 | `git show -s --format=%B HEAD \| bash scripts/validate-commit-msg.sh` | Conventional Commits |
| A4 | 无裸异常捕获 | `python scripts/verify-docs.py --check-bare-handlers` | `[OK]` |
| A5 | 无自校验 / 恒真断言 | `python scripts/test-quality-guard.py --max-warn 0` | 0 FAIL / 0 WARN |
| A6 | Falsy 陷阱 | `python scripts/falsy-audit.py` | 0 HIGH |
| A7 | 文档计数一致 | `python scripts/gen-doc-counts.py --check` | `[OK]` |
| A8 | 注册表一致 | `python scripts/verify-registries.py` | 0 FAIL |
| A9 | 架构边界 | `python scripts/verify-arch.py` | 0 违规 |
| A10 | 影响范围测试 | `python scripts/run-affected-tests.py` | 无 FAIL（存在未映射源码变更时显式失败） |
| A11 | 覆盖率门禁 | `python scripts/coverage.py` | ≥ pyproject `[tool.coverage]` `fail_under` |

## B. 变更内容审查（审查者）

| # | 检查项 | 怎么看 |
|---|--------|--------|
| B1 | diff 只含相关改动 | `git diff --stat`；无关文件/格式化噪声零容忍 |
| B2 | 分层与依赖方向 | 上层不反向依赖下层，底层不感知上层；跨层调用见 `architecture.json` 规则 |
| B3 | 新 Public 接口已登记 | [api-reference.md](../spec/api-reference.md) 有签名 + 错误行为 |
| B4 | 新文件已登记目录树 | [project-structure.md](project-structure.md)；`verify-docs.py --strict` 强制 |
| B5 | 退化输入已处理 | 空/单元素/全等值/NaN/Inf 路径有测试（防错三原则见 AGENTS.md） |
| B6 | 新依赖满足决策门 | 跨平台可用 + 维护活跃；在 PR 描述注明选型依据 |
| B7 | 无静默降级 | 失败/跳过路径有显式输出，不假装通过 |

## C. 数值与闭环验证（如适用）

| # | 检查项 | 怎么看 |
|---|--------|--------|
| C1 | 数值结果走交叉验证 | `cross_check()`（两条独立路径），禁用 `check(X, X)` 自校验 |
| C2 | 容差按算法选档 | 参考 `TOLERANCE_TIERS`（精确 1e-10 / 迭代 1e-6 / 统计 1e-2 等） |
| C3 | 手册数值有 CLAIM 标记 | `<!-- CLAIM:NAME -->值<!-- /CLAIM:NAME -->`，由 `verify-manual.py` 实跑比对 |
| C4 | 验证产物新鲜 | 被测实现与验证对象同源同版本（重建后再验证，防陈旧产物假绿） |
| C5 | 覆盖率不下降 | CI coverage 构件对比；门禁命令含显式阈值 |

## D. 合并前（审查者）

| # | 检查项 | 怎么看 |
|---|--------|--------|
| D1 | CI 全链路绿 | 不只看当前失败 job；上层失败会掩盖下游（见 `skills/ci-pipeline-SKILL.md` C3） |
| D2 | 文档同步链完整 | `documentation.md`「同步更新链」逐节点核对 |
| D3 | 豁免有登记与到期 | 风险接受写入 [review-exemptions.md](review-exemptions.md)（P0 不可豁免） |
| D4 | CHANGELOG 交由 release-please | 不手工编辑 CHANGELOG / 版本号（见 CONTRIBUTING.md） |
| D5 | 决策门核对 | 涉及新接口/依赖/破坏性变更时对照 [ROADMAP.md](../../ROADMAP.md) |
