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
| `NewModule/VariantKit.bas.template` | Variant 输入归一化基础层（Range/数组统一入口，固定名） | VBA |
| `NewModule/{Name}Core.ts.template` | 核心逻辑（纯函数 + strict null check + Result 模式） | TypeScript |
| `NewModule/{Name}Core.test.ts.template` | 单元测试（正常/边界/null/NaN） | TypeScript (vitest) |
| `NewModule/{Name}Core.go.template` | 核心逻辑（哨兵值 NaN + error 包装 + 零 panic） | Go |
| `NewModule/{Name}Core_test.go.template` | 单元测试（table-driven + 0 有效值 + NaN 哨兵） | Go (testing) |
| `NewModule/{Name}Core.rs.template` | 核心逻辑（哨兵值 NaN + 零 panic + 内联 #[cfg(test)] 测试） | Rust |
| `language/pyproject.toml.template` | Python 项目构建配置 | Python |
| `language/tsconfig.json.template` | TypeScript 项目构建配置（strict 模式） | TypeScript |
| `language/Directory.Build.props.template` | .NET 统一构建属性 | .NET |
| `language/nuget.config.template` | NuGet 源配置 | .NET |
| `language/{Name}.Tests.csproj.template` | .NET 测试项目（xUnit） | .NET |
| `language/go.mod.template` | Go 模块定义 | Go |
| `language/Cargo.toml.template` | Rust crate 定义 | Rust |
| `language/Dockerfile.template` | 通用容器化模板（multi-stage, Python/Node/.NET） | Docker |
| `language/docker-compose.yml.template` | 开发环境编排（含健康检查） | Docker Compose |
| `language/offline-setup.py.template` | 离线安装工具（零依赖，含 `--print-cmd` 干跑安全门） | Python |
| `monorepo/AGENTS.md.template` | Monorepo 子目录级 AGENTS.md（子项目宪法） | Monorepo |
| `monorepo/README.md` | Monorepo 使用说明与依赖规则 | Monorepo |

## 占位符约定

> **双语法体系**（故意设计，非冗余）：

| 语法 | 用途 | 替换时机 | 示例 | 被谁替换 |
|------|------|----------|------|----------|
| `{{...}}` | 项目级占位符 | `init-project` 初始化时 | `{{...}}` | init-project.ps1 / .py |
| `{PascalCase}` | 模块级占位符 | 新增模块时手动替换 | `{Name}`, `{Module}` | 开发者 |

**为什么用两种语法？**

`{{}}` 双花括号 → init-project 的正则 `\{\{([A-Z0-9_]+)\}\}`（仅大写 token）匹配，初始化时自动替换。
`{}` 单花括号 → 不被 init-project 匹配，复制到 `src/` 后仍保留，等开发者创建新模块时替换。

**如果误混用**：
- `{{Name}}`（含小写）出现在 NewModule 模板中 → init-project 不匹配（正则仅大写 `[A-Z0-9_]`），原样保留；泄漏由 ci.yml 模板守卫（grep `{{` templates/NewModule/）兜底
- `{PROJECT_NAME}` 出现在根目录文档中 → init-project 不会匹配，占位符残留

→ CI 中有 `模板守卫` step 检测 NewModule 模板中的 `{{` 泄漏（见 ci.yml）。

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `{Name}` | 模块名 PascalCase | `Weather` |
| `{Module}` | 所在模块目录 | `Analytics` |
| `{module}` | Go 包名 / Rust crate 名（小写，源码 `package` 声明 / Cargo.toml `name` 用） | `stats` |
| `{module_path}` | Go 模块路径（go.mod `module` 指令用） | `github.com/org/repo` |
| `{PREFIX}` | UDF 前缀（大写） | `WEATHER` |
| `{N}` | CrossVal 示例用例序号（section 标题） | `2` |
| `{模块说明}` | 模块功能一句话说明（CrossVal 头部） | `温度转换` |
| `{{ROOT_NAMESPACE}}` | 项目根命名空间（初始化时确定） | `Acme.Stats` |

## 新增模块流程（按语言选择对应模板）

**C#（Excel-DNA）**
```
1. 复制 Core/Udf/Foundation/Tests/CrossVal 五个文件到目标目录（按需裁剪）
2. 复制 language/{Name}.Tests.csproj.template 到 tests/{Module}.Tests/（.NET 项目）
2b. 新建 src/{Module}/{Module}.csproj（classlib——Tests.csproj 的 ProjectReference 指向它），
    并复制 language/Directory.Build.props.template 到仓库根（全局属性）
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
1. 复制 {Name}Udf.bas + VariantKit.bas 到 src/{Module}/，导入 VBE（文件 → 导入文件）
2. 替换 {Name}/{PREFIX}；VariantKit 提供 NormalizeInput（Range/数组统一入口），
   首次使用即复制，后续模块共用
3. Public 参数一律 As Variant；错误三模式（CVErr / Err.Raise / Cleanup）
4. 测试：在测试工作簿或 Rubberduck 中调用 {PREFIX}_ 函数（VBA 无自动化测试框架）
5. 同步规则文档（api-reference / user-manual）
```

**所有语言通用（最后一步）**
```
同步规则文档：specification.md → api-reference.md → user-manual.md → project-structure.md
```

**TypeScript**
```
1. 复制 {Name}Core.ts + {Name}Core.test.ts 到 src/{Module}/ 与 tests/{Module}/
2. 替换 {Name}/{Module}（测试模板已用相对 import 引用 src/{Module}/{Name}Core，无需调整路径）
3. Core 遵循 strict null check 与 Result 模式（见 skills/typescript-SKILL.md）
4. 运行 npx vitest run tests/{Module}/（或 npx jest）
5. 数值结果可加 CrossVal（与 numpy/scipy 独立比对，见 Python 流程）
6. 容器化：复制 language/Dockerfile.template 到根目录，按需取消注释对应阶段
```

**Go**
```
1. 复制 {Name}Core.go + {Name}Core_test.go 到 src/{Module}/
2. 替换 {Name}/{module}（包名小写）；初始化 go mod（如尚未有）
3. Core 遵循哨兵值模式（NaN 表示无效，0 是有效值）与 error 包装（见 skills/go-SKILL.md）
4. 运行 go test ./src/{Module}/... -v
5. 数值结果可加 CrossVal（与 numpy/scipy 独立比对，见 Python 流程）
6. 容器化：复制 language/Dockerfile.template，取消注释 Go 对应阶段
```

**Rust**
```
1. 复制 {Name}Core.rs 到 src/{Module}/；复制 language/Cargo.toml.template 到仓库根为 Cargo.toml
2. 替换 {Name}/{module}（crate 名 snake_case）；如尚未有则 cargo init --lib
3. Core 遵循哨兵值模式（NaN 表示无效，0 是有效值）与零 panic（见 skills/rust-SKILL.md）
4. 运行 cargo test（单元测试在 #[cfg(test)] 内联模块，不同于 Go 的独立 _test.go）
5. 数值结果可加 CrossVal（与 numpy/scipy 独立比对，见 Python 流程）
6. 容器化：复制 language/Dockerfile.template，取消注释 Rust 对应阶段（或用 rust 官方镜像）
```

**Monorepo（新增子项目）**
```
1. 复制 monorepo/AGENTS.md.template 到 src/{子项目名}/AGENTS.md
2. 替换 {子项目名}/{子项目语言}/{子项目入口文件}
3. 填写子项目特有红线（在根 AGENTS.md 基础上追加，不可覆盖根红线）
4. 同步根目录 rules/project-structure.md 与 AGENTS.md 目录树
5. 子项目间通信必须通过 foundation/ 共享层或显式接口
```

## 注意事项

- **禁止自校验**：CrossVal 必须与独立实现（scipy/numpy）比对，`check(name, X, X)` 无效
- **Core 零依赖**：不引用 Excel-DNA / UI 框架，可独立单元测试
- **Udf 无业务逻辑**：业务逻辑在 Core，Udf 只做参数适配与错误包装

## 治理脚本速查（本模板自举能力）

> 这些脚本是本模板从 5 个子项目反哺吸收的自举门禁，
> 初始化后在新项目中**自动保留**，作为项目治理基线。

> **离线安装**：`language/offline-setup.py.template` 提供零依赖离线安装工具
> （download/install/`--print-cmd` 干跑），复制后使用。

| 脚本 | 作用 | 何时运行 |
|------|------|---------|
| `scripts/verify-registries.py` | 多注册表键集一致性（防注册遗漏） | `make verify` / CI |
| `scripts/gen-doc-counts.py --check` | 文档计数自动注入（防数字漂移） | `make verify` / CI |
| `scripts/verify-docs.py --strict` | 链接/目录树/语义一致性 | `make verify` / CI |
| `scripts/verify-manual.py` | 手册一致性 + CrossVal 执行器 | `make verify` / CI |
| `scripts/test-quality-guard.py` | 测试质量守卫（弱断言/缺测/命名） | `make verify` / CI |
| `scripts/run-affected-tests.py` | 影响范围测试路由（git diff → 受影响测试，增量 CI） | `make test` / 开发增量 |
| `scripts/doctor.py` | 环境就绪诊断（新开发者第一步） | `make doctor` |

### 技能创作约定（来源：跨项目共识）

- **决策树格式**（来源：工程分析 analysis-decision-tree / 成本分析线程策略）：领域知识
  编码为 if-then 路由（"用户想 X？→ 用方法 Y"），AI 可据此路由请求到正确实现。
- **术语治理**（来源：文档审查 glossary/vocab）：`rules/context.md` 定义术语后，如需机器执行，
  建 `vocab/accept.txt`/`reject.txt` 词表 + 校验脚本（模板提供模式，不强制部署）。
- **双 AI 工具格式**（来源：成本分析 skills/+.qoder/skills/）：同一技能维护
  `skills/*.md`（人类/Claude 可读）与 `.qoder/skills/*/SKILL.md`（机器解析格式）
  两份；模板默认 `skills/` 即可，`.qoder/` 按需。
