# benchmarks/ — 性能基准（非门禁）

> 性能基准用于**趋势观测与回归告警**，不是提交门禁：CI 上共享 runner 抖动大，
> 硬阈值必然误伤（参考项目均采用"告警不阻断"策略）。
> 何时需要基准：性能优化 PR 必须附前后对比；决策门见 [ROADMAP.md](../ROADMAP.md)。

## 各语言基准工具

| 语言 | 工具 | 运行方式 | 产物（已 gitignore） |
|------|------|----------|---------------------|
| Python | pytest-benchmark | `pytest benchmarks/ --benchmark-only --benchmark-json=bench.json` | `.benchmarks/`、`bench.json` |
| C# | BenchmarkDotNet | `dotnet run -c Release --project benchmarks/<Proj>` | `BenchmarkDotNet.Artifacts/` |
| TypeScript | vitest bench | `npx vitest bench` | 控制台 |
| Go | testing.B | `go test -bench=. -benchmem ./...` | 控制台 |
| Rust | criterion | `cargo bench` | `target/criterion/` |

## 编写约定

- **测真实路径**：基准走公开入口（含参数校验/编排），而非只测内部函数
- **数据规模分层**：小（1e3）/ 中（1e4）/ 大（1e5）各一组，标注规模
- **固定环境噪声**：Python 侧设置 `OMP_NUM_THREADS=1` 等（防 BLAS 线程抖动）
- **不设硬阈值**：结果作为构件上传对比；回归告警阈值建议 ≥150%（保守）

## CI 接入

- 模板：[.github/workflows/benchmarks.yml.template](../.github/workflows/benchmarks.yml.template)
  （按项目语言保留一个 job，重命名为 `benchmarks.yml` 启用）
- 参考项目实践：BenchmarkDotNet + `benchmark-action/github-action-benchmark`（周更 + 构件保留 90 天）
