"""conftest.py — 使 pytest 从仓库根可直接运行 examples/tests/。

示例模块位于 examples/src/stats/（与仓库根 src/ 布局不同），
不加本文件时 `pytest examples/tests/test_stats.py -v`（仓库根执行）会
ModuleNotFoundError: No module named 'src.stats'。
本文件将 examples/ 加入模块搜索路径，使 `from src.stats...` 可从 examples/ 解析，
文档化的运行命令直接可用。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
