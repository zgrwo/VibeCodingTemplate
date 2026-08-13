#!/usr/bin/env python3
"""StatsCrossVal.py — 统计模块交叉验证

使用方式：
  复制到 scripts/crossval/StatsCrossVal.py
  由 scripts/verify-manual.py 自动发现并执行

原则（防错三原则之闭环验证）：
  - 禁止自校验：check(name, X, Y) 中 X 与 Y 相同则永远 PASS，无验证价值
  - 数值型必须 cross_check()（与 numpy 独立参考实现比对）
"""
import sys
from pathlib import Path

import numpy as np

# 使 `from src.stats.StatsCore import ...` 可解析：
#   - 示例在 examples/scripts/crossval/ → parent.parent.parent = examples/，
#     `src.stats` 解析到 examples/src/stats/（与 examples/conftest.py 同思路）
#   - 复制到 scripts/crossval/ 后 → parent.parent.parent = 仓库根，
#     `src.stats` 解析到生成项目的 src/stats/
# （verify-manual.py 已把仓库根与 scripts/ 加入 sys.path，这里仅兜底非根位置。）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.stats.StatsCore import mean, weighted_mean  # noqa: E402
from verify_manual import check, cross_check, section  # noqa: E402

# ========================================================================
# Stats — 2 UDFs
# ========================================================================
section("Stats — 均值计算", 3)

# 示例 1：均值交叉验证（与 numpy 独立实现比对）
test_data = [1.0, 2.0, 3.0, 4.0, 5.0]
cross_check("STATS.MEAN", mean(test_data), float(np.mean(test_data)))

# 示例 2：加权均值交叉验证
values = [1.0, 2.0, 3.0]
weights = [0.5, 1.0, 1.5]
expected = float(np.average(values, weights=weights))
cross_check("STATS.WEIGHTED_MEAN", weighted_mean(values, weights), expected)

# 示例 3：确定性结果验证（硬编码期望值）
check("STATS.MEAN.ZERO", mean([0.0, 0.0, 0.0]), 0.0)
