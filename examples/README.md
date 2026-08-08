# examples/ — 最小示例项目

> 本目录演示使用 VibeCodingTemplate 初始化后的项目长什么样。
> 一个完整的"统计均值计算"模块，展示 Core / Udf / Foundation 分层 + CrossVal + 测试的完整实践。

## 目录结构

```
examples/
├── README.md           # 本文件（使用说明）
├── src/
│   └── stats/
│       ├── StatsCore.py     # 核心层（纯逻辑，零依赖）
│       └── StatsUdf.py      # UDF 层（参数适配 + 错误包装）
├── tests/
│   └── test_stats.py        # 单元测试（正常/边界/falsy/异常）
└── scripts/
    └── crossval/
        └── StatsCrossVal.py # 交叉验证（与 scipy 独立比对）
```

## 运行示例

```bash
# 进入示例目录
cd examples

# 安装依赖（仅 scipy/numpy 用于交叉验证）
pip install scipy numpy pytest

# 运行测试
pytest tests/ -v

# 运行交叉验证（回到模板根目录执行）
cd .. && python scripts/verify-manual.py
```

## 设计要点

1. **Core 零依赖**：`StatsCore.py` 不引用任何外部框架，可独立单元测试
2. **Falsy 守卫**：0 是有效值（均值=0 表示数据全为零），用 `is not None` 不用 `if x:`
3. **哨兵契约**：空列表/NaN 输入返回 NaN，不抛异常
4. **闭环验证**：CrossVal 与 `scipy.stats` 独立比对，禁止自校验

## 与模板的对应关系

| 示例文件 | 来源模板 |
|----------|----------|
| `src/stats/StatsCore.py` | `templates/NewModule/{Name}Core.py.template` |
| `src/stats/StatsUdf.py` | `templates/NewModule/{Name}Udf.cs.template`（Python 变体） |
| `tests/test_stats.py` | `templates/NewModule/test_{Name}Core.py.template` |
| `scripts/crossval/StatsCrossVal.py` | `templates/NewModule/{Name}CrossVal.py.template` |
