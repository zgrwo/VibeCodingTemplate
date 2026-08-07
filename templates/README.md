# templates/ — 模块脚手架

> 新增模块/功能时的起点文件。来自 ExcelAddin 函数库的 NewModule 实践（已验证有效）。
> 使用方式：复制对应文件到目标位置，替换占位符后开始实现。

## 目录

| 文件 | 用途 | 目标语言 |
|------|------|----------|
| `NewModule/{Name}Core.cs.template` | 核心逻辑（纯计算，零框架依赖） | C# |
| `NewModule/{Name}Udf.cs.template` | UDF 入口（仅分发与适配） | C# (Excel-DNA) |
| `NewModule/{Name}Foundation.cs.template` | Foundation 层基础设施（参数归一化/逐元素映射/错误包装） | C# (Excel-DNA) |
| `NewModule/{Name}Core.Tests.cs.template` | 单元测试（正常/边界/哨兵契约） | C# (xUnit) |
| `NewModule/{Name}CrossVal.py.template` | 交叉验证（独立实现比对） | Python |
| `NewModule/{Name}Core.py.template` | 核心逻辑（纯函数 + 类型注解 + falsy 守卫） | Python |
| `NewModule/test_{Name}Core.py.template` | 单元测试（正常/边界/falsy/异常） | Python (pytest) |
| `NewModule/{Name}Udf.bas.template` | UDF 入口（Variant 参数 + 错误三模式） | VBA |
| `language/pyproject.toml.template` | Python 项目构建配置 | Python |
| `language/Directory.Build.props.template` | .NET 统一构建属性 | .NET |
| `language/nuget.config.template` | NuGet 源配置 | .NET |
| `language/{Name}.Tests.csproj.template` | .NET 测试项目（xUnit） | .NET |

## 占位符约定

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `{Name}` | 模块名 PascalCase | `Weather` |
| `{Module}` | 所在模块目录 | `Analytics` |
| `{PREFIX}` | UDF 前缀（大写） | `WEATHER` |
| `{{ROOT_NAMESPACE}}` | 项目根命名空间（初始化时确定） | `Acme.Stats` |

> 与根目录文档使用的 `{{...}}`（大括号双写）不同——`templates/` 内的文件被复制到 `src/` 使用，`{Name}` 是源码级占位符；`{{ROOT_NAMESPACE}}` 与根目录占位符同体系（init-project.ps1 统一替换）。

## 新增模块流程（按语言选择对应模板）

**C#（Excel-DNA）**
```
1. 复制 Core/Udf/Foundation/Tests/CrossVal 五个文件到目标目录（按需裁剪）
2. 复制 language/{Name}.Tests.csproj.template 到 tests/{Module}.Tests/（.NET 项目）
3. 替换 {Name}/{Module}/{PREFIX}/{{ROOT_NAMESPACE}}
4. Core 实现纯计算逻辑（哨兵契约 L1-L5）；Udf 仅做分发（MapOver + WrapError）
5. 测试覆盖：正常路径 + 哨兵契约 + 边界值
6. CrossVal 放入 scripts/crossval/ 目录（verify-manual.py 自动发现并执行）
```

**Python**
```
1. 复制 {Name}Core.py + test_{Name}Core.py 到 src/{Module}/ 与 tests/（或 tests/{Module}/）
2. 替换 {Name}/{Module}；按实际包结构调整测试 import 路径
3. Core 遵循 falsy 守卫（is not None）与类型注解（见 skills/python-SKILL.md）
4. 运行 pytest tests/ -x -q（pyproject.toml 已配 testpaths 与 test_*.py 发现规则）
5. 数值结果加 CrossVal（scripts/crossval/，verify-manual.py 自动执行）
```

**VBA（无构建系统，模块复制进 VBE）**
```
1. 复制 {Name}Udf.bas.template 到 src/{Module}/，导入 VBE（文件 → 导入文件）
2. 替换 {Name}/{PREFIX}；确认依赖 VariantKit 模块已导入
3. Public 参数一律 As Variant；错误三模式（CVErr / Err.Raise / Cleanup）
4. 测试：在测试工作簿或 Rubberduck 中调用 {PREFIX}_ 函数（VBA 无自动化测试框架）
5. 同步规则文档（api-reference / user-manual）
```

**所有语言通用（最后一步）**
```
同步规则文档：specification.md → api-reference.md → user-manual.md → project-structure.md
```

## 注意事项

- **禁止自校验**：CrossVal 必须与独立实现（scipy/numpy）比对，`check(name, X, X)` 无效
- **Core 零依赖**：不引用 Excel-DNA / UI 框架，可独立单元测试
- **Udf 无业务逻辑**：业务逻辑在 Core，Udf 只做参数适配与错误包装
