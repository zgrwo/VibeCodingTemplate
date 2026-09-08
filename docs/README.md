# docs/ — 文档中心

> 仓库唯一文档区：规范信源、治理元文档、设计决策、陷阱清单、方法论按分类存放于子目录。
> 职责矩阵与维护规则的**唯一权威**见 [governance/documentation.md](governance/documentation.md)；
> 目录结构的**唯一权威**见 [governance/project-structure.md](governance/project-structure.md)。

## 分类导航

| 子目录 | 定位 | 文件 |
|--------|------|------|
| `governance/` | 治理与结构（元文档） | [documentation.md](governance/documentation.md)（文档职责）、[project-structure.md](governance/project-structure.md)（结构树） |
| `spec/` | 业务与技术规格（唯一信源） | [context.md](spec/context.md)（术语）、[specification.md](spec/specification.md)（业务）、[api-reference.md](spec/api-reference.md)（API 签名）、[user-manual.md](spec/user-manual.md)（手册） |
| `design/` | 架构设计与决策记录 | [architecture.md](design/architecture.md)、[adr-template.md](design/adr-template.md)、`adr/`（ADR 落地，编号递增） |
| `pitfalls/` | 陷阱与防御契约 | [falsy-pitfalls.md](pitfalls/falsy-pitfalls.md)、[tooling-pitfalls.md](pitfalls/tooling-pitfalls.md)、[sentinel-contract.md](pitfalls/sentinel-contract.md) |
| `methodology/` | 跨项目经验与重构方法论 | [cross-project-synthesis.md](methodology/cross-project-synthesis.md)、[refactoring-plan.md](methodology/refactoring-plan.md) |

## 约定

- **唯一信源原则**：每个事实只在一处定义，其余仅链接引用；新增文件先登记 [governance/project-structure.md](governance/project-structure.md) 目录树（`verify-docs.py --strict` 强制门禁）
- 新增设计文档必须引用 `spec/`、`pitfalls/` 等已有信源，**禁止在 docs/ 重复定义**业务规则
- 重要设计文档发布时同步登记到 `AGENTS.md` 目录树（顶层变更时）
- 过期文档及时归档或删除，避免「两份文档打架」
