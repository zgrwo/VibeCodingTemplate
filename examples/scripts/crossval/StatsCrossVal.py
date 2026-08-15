#!/usr/bin/env python3
"""StatsCrossVal.py — 统计模块交叉验证

使用方式（两处自动发现，无需手动执行）：
  - 模板仓库：位于 examples/scripts/crossval/，由 scripts/verify-manual.py 自动发现并执行
    （模板自举闭环验证：verify-manual.py 同时扫描 scripts/crossval/ 与 examples/scripts/crossval/）
  - 新项目：复制到 scripts/crossval/StatsCrossVal.py，由 scripts/verify-manual.py 自动发现并执行
  - 独立运行（演示/调试）：python examples/scripts/crossval/StatsCrossVal.py
    （校验失败时退出码 1，可供脚本化调用）

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

# verify-manual.py 以 `python scripts/verify-manual.py` 运行时会把自身注册为
# verify_manual 模块别名（文件名含连字符无法直接 import）。独立运行（直接执行
# 本文件）时无此别名：向上查找仓库根 scripts/verify-manual.py 并以 spec 加载。
try:
    import verify_manual as _vm  # noqa: E402
    from verify_manual import check, cross_check, section  # noqa: E402
except ModuleNotFoundError:
    import importlib.util as _ilu

    _root = Path(__file__).resolve().parent
    while _root.parent != _root and not (_root / "scripts" / "verify-manual.py").exists():
        _root = _root.parent
    _spec = _ilu.spec_from_file_location("verify_manual", _root / "scripts" / "verify-manual.py")
    _vm = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_vm)
    sys.modules["verify_manual"] = _vm
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

# 独立运行（__main__）时按校验结果退出：失败 → 1。
# verify-manual.py 以 spec 加载时 __name__ 恒为模块 stem，本守卫不会误触执行器。
if __name__ == "__main__" and _vm._FAIL:
    sys.exit(1)
