"""StatsCore.py — 统计均值计算核心层

目标位置：src/stats/StatsCore.py
设计原则（见 skills/python-SKILL.md）：
- Falsy 陷阱：0 是有效值（均值=0 表示数据全零），用 is not None 不用 if x
- 哨兵契约：空列表/NaN 输入返回 NaN，不抛异常
- 零外部依赖：纯逻辑实现，可独立单元测试
"""

from __future__ import annotations

import math


def mean(values: list[float] | None) -> float:
    """计算算术均值。

    Args:
        values: 数值列表；None 或空列表返回 NaN。

    Returns:
        均值；无效输入返回 NaN。
    """
    # 1. 哨兵守卫：None → NaN（勿用 if values，空列表是有效输入但返回 NaN）
    if values is None:
        return float("nan")

    # 2. 防御：空列表 → NaN
    if len(values) == 0:
        return float("nan")

    # 3. 防御：NaN/Inf 过滤（哨兵契约：静默传播阻断）
    clean = [v for v in values if isinstance(v, (int, float)) and math.isfinite(v)]
    if len(clean) == 0:
        return float("nan")

    # 4. 核心逻辑
    result = sum(clean) / len(clean)

    # 5. 结果守卫：防止溢出
    if math.isinf(result) or math.isnan(result):
        return float("nan")

    return result


def weighted_mean(values: list[float] | None, weights: list[float] | None) -> float:
    """计算加权均值。

    Args:
        values: 数值列表
        weights: 权重列表（长度须与 values 一致）

    Returns:
        加权均值；无效输入返回 NaN。
    """
    if values is None or weights is None:
        return float("nan")

    if len(values) == 0 or len(weights) == 0:
        return float("nan")

    if len(values) != len(weights):
        return float("nan")

    # 与 mean() 对齐：逐对过滤非有限（NaN/Inf）值及其配对权重，否则 NaN 会毒化整个结果
    pairs = [
        (v, w)
        for v, w in zip(values, weights, strict=True)
        if isinstance(v, (int, float))
        and math.isfinite(v)
        and isinstance(w, (int, float))
        and math.isfinite(w)
    ]
    total_weight = sum(w for _, w in pairs)
    if total_weight == 0:
        return float("nan")

    result = sum(v * w for v, w in pairs) / total_weight

    if math.isinf(result) or math.isnan(result):
        return float("nan")

    return result
