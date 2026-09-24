# 路线图（ROADMAP）

> 本文档公开项目演进方向与**决策门**：新功能 / 新依赖 / 行为变更先满足触发条件再排期，
> 用规则替代"猜优先级"。功能范围定义见 [specification.md](docs/spec/specification.md)，
> 版本历史见 [CHANGELOG.md](CHANGELOG.md)；本文件不重复定义二者内容。

## 决策门

> 每项决策列出**全部满足才启动**的触发条件；未满足即不排期（YAGNI，见
> [architecture-reviewer-SKILL.md](skills/architecture-reviewer-SKILL.md)）。

| 决策 | 触发条件 | 状态 | 依据 |
|------|----------|------|------|
| 新增 Public 接口 | specification 已登记 + api-reference 有签名 + 有测试与跨验证 | 🟡 按需 | [AGENTS.md](AGENTS.md) 开发流程 |
| 新增第三方依赖 | 跨平台/跨版本可用 + 维护活跃 + 无自研替代 | 🟡 按需 | [architecture-reviewer-SKILL.md](skills/architecture-reviewer-SKILL.md) 依赖五项检查 |
| 性能优化 | 有基准基线 + profiler 热点定位 + 预期收益显著 | ⬜ 未触发 | [benchmarks/README.md](benchmarks/README.md) |
| 破坏性变更 | 有 ADR + 迁移说明 + major 版本规划 | ⬜ 未触发 | [adr-template.md](docs/design/adr-template.md) |
| 发布到包管理器 | 连续 ≥2 个 release 无安装问题 + 依赖锁稳定 | ⬜ 未触发 | [CONTRIBUTING.md](CONTRIBUTING.md) 发版规范 |
| 启用多版本 CI 矩阵 | 明确支持版本范围 + 各版本回归可运行 | ⬜ 未触发 | [ci.yml](.github/workflows/ci.yml) 矩阵注释 |

> 状态图例：⬜ 未触发 ／ 🟡 条件满足（可排期）／ ✅ 已完成

## 里程碑

| 版本 | 目标 | 状态 | 说明 |
|------|------|------|------|
| v0.1.0 | 项目初始化：目录树 + 治理门禁 + 首个模块 | ⬜ | 由 `init-project` 生成后填写 |
| v0.2.0+ | 按决策门逐项排期 | ⬜ | 每项完成后同步 CHANGELOG |

## good first issue 候选

| 候选任务 | 涉及位置 | 验收标准 |
|----------|----------|----------|
| 为首个模块补独立参考实现（CrossVal） | scripts/crossval/（按需创建，模板见 `templates/NewModule/{Name}CrossVal.py.template`） | `verify-manual.py` 全绿且 `cross_check()` 计数大于 0 |
| 启用 Python 覆盖率门禁 | `.github/workflows/ci.yml` | `COVERAGE_CMD` 替换为带 `--cov-fail-under` 的命令并跑绿 |
| 填写项目架构文档 | `docs/design/architecture.md` | 分层图与 `project-structure.md` 层级依赖规则一致 |
| 首个 ADR | `docs/design/adr/0001-xxx.md` | 按 `adr-template.md` 格式，含"何时必须写 ADR"判定 |

## 维护规则

- 排期前先对照决策门；条件未满足不启动（拒绝"顺便做"）
- 里程碑完成后更新状态与 CHANGELOG 条目，并在本表标注日期
- 本文件不硬编码统计数字（测试数/覆盖率等）；需要数字时用 AUTO_COUNTS 标记或链接到唯一信源
- 决策门新增/调整 → 同步 `docs/governance/documentation.md` 职责矩阵
