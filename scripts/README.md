# scripts/ — 构建/验证脚本

> 本模板自举治理门禁与初始化脚本。**职责唯一定义**见 [project-structure.md](../docs/governance/project-structure.md)（结构地图）与 [templates/README.md](../templates/README.md)「治理脚本速查」；本文件仅作导航索引，不重复定义。

## 导航

| 分组 | 脚本 | 作用 |
|------|------|------|
| 全量验证 | `verify-all.py` / `verify-all.ps1` | 全量验证入口（Python 跨平台 / PowerShell Win） |
| 文档一致性 | `verify-docs.py --strict` | 链接（动态发现全仓 .md）/ 目录树 / 语义 / 版本锚点一致性 |
| 文档一致性 | `verify-manual.py` | 手册一致性 + CrossVal 执行器（禁自校验） |
| 文档一致性 | `gen-doc-counts.py --check` | 文档计数注入（防数字漂移） |
| 注册一致性 | `verify-registries.py` | 多注册表键集一致性（防注册遗漏） |
| 架构边界 | `verify-arch.py` | 配置驱动 AST 分层依赖检查（`architecture.json` 规则） |
| 覆盖率门禁 | `coverage.py` | 清旧产物 + pytest-cov 阈值门禁（pyproject `[tool.coverage]` 为 SSOT） |
| 代码质量 | `falsy-audit.py` | Falsy 陷阱静态审计 |
| 测试质量 | `test-quality-guard.py` | 弱断言 / 恒真断言 / 自校验 / 缺测 / 命名守卫（`--max-warn` 预算） |
| 影响路由 | `run-affected-tests.py` | git diff → 受影响测试（增量 CI） |
| 环境诊断 | `doctor.py` | 环境就绪性诊断（新开发者第一步） |
| 初始化 | `init-project.py` / `init-project.ps1` | 从模板初始化新项目 |
| 模板自测 | `test-template.ps1` | init → verify 三件套（CI template-self-test 调用） |
| 提交校验 | `validate-commit-msg.sh` | Conventional Commits 校验（hook + CI 共用） |
| 共享常量 | `_excluded_dirs.py` | 排除目录集合 SSOT（verify-docs / verify-registries / init 共用） |

> **唯一真相源**：占位符清单见 `placeholders.json`；注册表配置见 `registries.json`；架构边界规则见 `architecture.json`；覆盖率范围/阈值见 `pyproject.toml [tool.coverage]`；文档计数源见 `doc-counts.json`。
