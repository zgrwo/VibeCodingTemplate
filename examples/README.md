# examples/ — 最小示例项目

> 本目录演示使用 VibeCodingTemplate 初始化后的项目长什么样。
> 一个完整的"统计均值计算"模块，展示 Core 多语言实现（Python/TypeScript/Go/Rust）+ CrossVal + 测试的完整实践。

> **初始化去向**：`init-project` 会把本目录整体复制进新项目（参考用途，不需要可删除；
> 删除后请同步 `rules/project-structure.md` 与 `AGENTS.md` 目录树）。
> **自举闭环验证**：模板仓库自身的 `scripts/verify-manual.py` 自动发现并执行
> `examples/scripts/crossval/StatsCrossVal.py`（numpy 独立参考实现比对），
> 确保示例 CrossVal 不是死代码。

## 目录结构

```
examples/
├── README.md                    # 本文件
├── Cargo.toml                   # Rust crate 定义（cargo test 入口）
├── src/
│   ├── lib.rs                   # Rust crate 根（pub mod stats）
│   └── stats/
│       ├── StatsCore.py         # 核心层 Python
│       ├── StatsCore.ts         # 核心层 TypeScript
│       ├── StatsCore.go         # 核心层 Go
│       └── mod.rs               # 核心层 Rust
├── tests/
│   ├── test_stats.py            # Python 单元测试（pytest，16 tests）
│   ├── test_stats.test.ts       # TypeScript 单元测试（vitest，17 tests）
│   ├── test_stats_test.go       # Go 单元测试（table-driven，16 tests）
│   └── test_stats.rs            # Rust 集成测试（cargo test，15 tests）
└── scripts/
    └── crossval/
        └── StatsCrossVal.py     # 交叉验证
```

## 运行示例

```bash
# Python 示例（需在 examples/ 下运行，src/ 结构在包路径内）
cd examples
pip install numpy pytest
pytest tests/test_stats.py -v  # 16 tests

# TypeScript 示例（需 Node.js 18+）
npm install -g vitest
npx vitest run examples/tests/  # 17 tests（文件后缀 .test.ts 匹配 vitest 默认 glob）

# Go 示例（需 Go 1.22+）
cd examples && go mod init examples && go test ./tests/... -v  # 16 tests

# Rust 示例（需 Rust edition 2021+）
cd examples && cargo test  # 15 tests
```

## 设计要点

1. **Core 零依赖**：所有 Core 实现不引用外部框架，可独立单元测试
2. **Falsy 守卫**：0 是有效值（均值=0 表示数据全为零），用 `is not None` 不用 `if x:`
3. **哨兵契约**：空/NaN 输入返回 NaN，不抛异常（四种语言一致）
4. **闭环验证**：CrossVal 与 numpy 独立参考实现比对，禁止自校验

## 与模板的对应关系

| 示例文件 | 来源模板 |
|----------|----------|
| `examples/src/stats/StatsCore.py` | `templates/NewModule/{Name}Core.py.template` |
| `examples/src/stats/StatsCore.ts` | `templates/NewModule/{Name}Core.ts.template` |
| `examples/src/stats/StatsCore.go` | `templates/NewModule/{Name}Core.go.template` |
| `examples/src/stats/mod.rs` | `templates/NewModule/{Name}Core.rs.template` |
| `examples/tests/test_stats.py` | `templates/NewModule/test_{Name}Core.py.template` |
| `examples/tests/test_stats.test.ts` | `templates/NewModule/{Name}Core.test.ts.template` |
| `examples/tests/test_stats_test.go` | `templates/NewModule/{Name}Core_test.go.template` |
| `examples/tests/test_stats.rs` | `templates/NewModule/{Name}Core.rs.template`（测试用例独立为集成测试） |
| `examples/scripts/crossval/StatsCrossVal.py` | `templates/NewModule/{Name}CrossVal.py.template` |
