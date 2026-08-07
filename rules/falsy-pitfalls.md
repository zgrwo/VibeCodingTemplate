# Falsy 陷阱检查清单

> **SSOT 声明**：本文件是 falsy 值误判检查的**唯一权威信源**（检查清单 + 高风险变量名 + 历史案例）。
> [python-SKILL.md](../skills/python-SKILL.md) 中的 falsy 内容只链接引用本文件，不重复维护；审计工具 [falsy-audit.py](../scripts/falsy-audit.py) 以本文件高风险名单为基准。
>
> 提炼自工程分析套件 Phase 0 审计（14 项历史 falsy 修复）。**Python 中 0 是有效值**：效应量=0、均值=0、计数=0，不能用 `if x:` 检查。

## 核心规则

Python 中 `if x:` 对以下值判假：`0`, `0.0`, `""`, `[]`, `{}`, `None`, `False`

| 变量类型 | 检查方式 | 原因 |
|----------|----------|------|
| 数值变量（统计量/效应量/计数） | `if x is not None:` | 0 是有效值 |
| 可选参数（阈值/容差/置信度） | `if x is not None:` | 0 是合法配置 |
| 布尔变量（开关标志） | `if x:` | 布尔值语义安全 |
| 集合/列表（数据容器） | `if x:` | 空容器 = 无数据，语义正确 |

## 正反示例

```python
# ❌ 错误：effect_size=0（无效应）时跳过报告
if effect_size:
    report(effect_size)

# ✅ 正确
if effect_size is not None:
    report(effect_size)

# ❌ 错误：threshold=0 是合法阈值，却被当作未设置
if alpha:
    threshold = alpha

# ✅ 正确
if alpha is not None:
    threshold = alpha
```

## 高风险变量名（遇到必须用 `is not None`）

| 变量名模式 | 原因 |
|-----------|------|
| `*_shape`, `*_scale` | 分布参数，>0 但可能 None |
| `cp`, `cpk`, `ppm` | 过程能力指数，0 是有效值 |
| `threshold`, `tolerance`, `alpha` | 阈值/显著性水平，0 是有效值 |
| `effect_size`, `statistic` | 效应量/检验统计量，0 表示无效应 |
| `sigma`, `mean`, `std`, `var` | 统计量，0 是有效值 |
| `offset`, `shift`, `count` | 偏移量/计数，0 是有效值 |
| `correlation`, `coefficient` | 相关系数，0 表示无相关 |

## 常见误判场景（历史案例）

1. `if weibull_shape:` — β=0 时跳过报告（拟合失败场景）
2. `if count:` — 计数=0 时跳过统计
3. `if correlation:` — r=0 时误判"无结果"而非"无相关"
4. `if p_value:` — p=0.0（极小值）时误判

## 审计命令（可选，Python 项目）

```bash
# 建议在 CI quality-gate 中接入
python scripts/falsy-audit.py
```

验收标准：零 HIGH 风险警告。

## 相关 Skill

- 完整 Python 陷阱（pandas/scipy/matplotlib/异常处理）→ `skills/python-SKILL.md`
