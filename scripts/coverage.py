#!/usr/bin/env python3
"""
coverage.py — 覆盖率门禁入口（跨平台）

职责（三要素，来源：ExcelAddin coverage.ps1 / ci-pipeline-SKILL C14）：
  1. 运行前清理旧覆盖率产物（.coverage / coverage.xml / htmlcov/）——防读旧报告假绿
  2. 运行 pytest-cov，范围与阈值读取 pyproject.toml 的 [tool.coverage] 配置（SSOT）
  3. 退出码即门禁结果；覆盖率数据缺失/工具未装时显式失败，不静默通过

pyproject.toml 配置示例（唯一真相源）：
  [tool.coverage.run]
  source = ["scripts"]        # 覆盖率范围（模板仓库为 scripts；下游项目通常为 ["src"]）
  [tool.coverage.report]
  fail_under = 80             # 阈值（建议低于实测基线 ~5 点留余量）

用法：
  python scripts/coverage.py                    # 按 pyproject 配置运行
  python scripts/coverage.py --source src --fail-under 85
  python scripts/coverage.py --xml              # 额外产出 coverage.xml（CI 构件）
  python scripts/coverage.py --html             # 额外产出 htmlcov/（本地查看）

退出码：0 = 达标；非 0 = 未达标 / 工具缺失 / 无测试收集（pytest 退出码透传）
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Windows GBK 控制台：强制 UTF-8 输出，避免中文说明乱码（[OK]/[FAIL] 标记保持 ASCII 兼容）
with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# pyproject.toml 解析（正则而非 tomllib：保持 Python 3.10 兼容，且只取两个简单字段）
_SOURCE_RE = re.compile(r"^\s*source\s*=\s*\[([^\]]*)\]", re.MULTILINE)
_FAIL_UNDER_RE = re.compile(r"^\s*fail_under\s*=\s*([0-9]+(?:\.[0-9]+)?)", re.MULTILINE)

# 清理的旧产物（相对 ROOT）
_STALE_ARTIFACTS = (".coverage", "coverage.xml", "htmlcov")


def read_pyproject_config(path: Path) -> tuple[list[str], float | None]:
    """从 pyproject.toml 读取 [tool.coverage] 的 source 与 fail_under。

    解析失败/字段缺失时返回 ([], None)，由调用方回退默认值（不静默猜测阈值）。
    """
    if not path.exists():
        return [], None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return [], None
    sources: list[str] = []
    m = _SOURCE_RE.search(text)
    if m:
        sources = list(re.findall(r'"([^"]+)"', m.group(1)))
    m2 = _FAIL_UNDER_RE.search(text)
    fail_under = float(m2.group(1)) if m2 else None
    return sources, fail_under


def clean_artifacts(root: Path) -> list[str]:
    """清理旧覆盖率产物，返回被清理项名称（防读旧报告假绿）。"""
    removed: list[str] = []
    for name in _STALE_ARTIFACTS:
        p = root / name
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
            removed.append(name + "/")
        elif p.exists():
            with contextlib.suppress(OSError):
                p.unlink()
                removed.append(name)
    return removed


def build_pytest_cmd(
    python: str, sources: list[str], fail_under: float | None, xml: bool, html: bool
) -> list[str]:
    """构造 pytest-cov 命令（可单测的纯函数）。"""
    cmd = [python, "-m", "pytest", "tests/", "-q"]
    for src in sources:
        cmd.append(f"--cov={src}")
    cmd.append("--cov-report=term-missing")
    if fail_under is not None:
        cmd.append(f"--cov-fail-under={fail_under:g}")
    if xml:
        cmd.append("--cov-report=xml")
    if html:
        cmd.append("--cov-report=html")
    return cmd


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="覆盖率门禁（pyproject [tool.coverage] 为 SSOT）")
    parser.add_argument(
        "--source", action="append", default=[], help="覆盖率范围（可重复；默认读 pyproject）"
    )
    parser.add_argument(
        "--fail-under", type=float, default=None, help="覆盖率阈值（默认读 pyproject）"
    )
    parser.add_argument("--xml", action="store_true", help="额外产出 coverage.xml")
    parser.add_argument("--html", action="store_true", help="额外产出 htmlcov/")
    args = parser.parse_args(argv)

    if importlib.util.find_spec("pytest_cov") is None:
        print('[FAIL] pytest-cov 未安装 — 运行: pip install -e ".[dev]"')
        return 1

    configured_sources, configured_fail_under = read_pyproject_config(ROOT / "pyproject.toml")
    sources = args.source or configured_sources or ["src"]
    fail_under = args.fail_under if args.fail_under is not None else configured_fail_under

    removed = clean_artifacts(ROOT)
    if removed:
        print(f"[OK] 已清理旧覆盖率产物: {', '.join(removed)}")

    cmd = build_pytest_cmd(sys.executable, sources, fail_under, args.xml, args.html)
    print(f"[RUN] {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=ROOT)
    except OSError as e:
        print(f"[FAIL] 覆盖率运行失败（工具未找到: {e}）")
        return 1
    if result.returncode != 0:
        print(
            f"[FAIL] 覆盖率门禁未通过（退出码 {result.returncode}；"
            "检查阈值/未覆盖分支/是否有测试被收集）"
        )
        return result.returncode
    threshold_desc = f"{fail_under:g}" if fail_under is not None else "未设"
    print(f"[OK] 覆盖率门禁通过（范围: {', '.join(sources)}；阈值: {threshold_desc}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
