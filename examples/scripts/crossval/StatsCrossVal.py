#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""StatsCrossVal.py — 统计模块交叉验证

使用方式：
  复制到 scripts/crossval/StatsCrossVal.py
  由 scripts/verify-manual.py 自动发现并执行

原则（防错三原则之闭环验证）：
  - 禁止自校验 check(name, X, X) —— 永远 PASS，无验证价值
  - 数值型必须 cross_check()（与 scipy 独立比对）
"""
import numpy as np
from scipy import stats as sp_stats

# 确保可导入 verify_manual（CI 在 scripts/ 下执行，本地在项目根执行）
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from verify_manual import check, cross_check, section

from src.stats.StatsCore import mean, weighted_mean

# ========================================================================
# Stats — 2 UDFs
# ========================================================================
section("Stats — 均值计算", 2)

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
