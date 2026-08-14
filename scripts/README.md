# scripts/ — 构建/验证脚本

> 本模板自举治理门禁与初始化脚本。**职责唯一定义**见 [project-structure.md](../rules/project-structure.md)（结构地图）与 [templates/README.md](../templates/README.md)「治理脚本速查」；本文件仅作导航索引，不重复定义。

## 导航

| 分组 | 脚本 | 作用 |
|------|------|------|
| 全量验证 | `verify-all.py` / `verify-all.ps1` | 全量验证入口（Python 跨平台 / PowerShell Win） |
| 文档一致性 | `verify-docs.py --strict` | 链接 / 目录树 / 语义一致性 |
| 文档一致性 | `verify-manual.py` | 手册一致性 + CrossVal 执行器（禁自校验） |
| 文档一致性 | `gen-doc-counts.py --check` | 文档计数注入（防数字漂移） |
| 注册一致性 | `verify-registries.py` | 多注册表键集一致性（防注册遗漏） |
| 代码质量 | `falsy-audit.py` | Falsy 陷阱静态审计 |
| 测试质量 | `test-quality-guard.py` | 弱断言 / 缺测 / 无意义命名守卫 |
| 影响路由 | `run-affected-tests.py` | git diff → 受影响测试（增量 CI） |
| 环境诊断 | `doctor.py` | 环境就绪性诊断（新开发者第一步） |
| 初始化 | `init-project.py` / `init-project.ps1` | 从模板初始化新项目 |
| 模板自测 | `test-template.ps1` | init → verify 三件套（CI template-self-test 调用） |
| 提交校验 | `validate-commit-msg.sh` | Conventional Commits 校验（hook + CI 共用） |

> **唯一真相源**：占位符清单见 `placeholders.json`；注册表配置见 `registries.json`；文档计数源见 `doc-counts.json`。
