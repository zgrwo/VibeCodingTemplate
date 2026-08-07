#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-manual.py — 手册一致性验证 + CrossVal 执行器

职责：
  1. 静态检查：自校验模式 check(X, X)、示例代码块语言标注、未闭合代码块
  2. 数值比对（可选）：执行 scripts/crossval/*.py（独立实现 vs 被测实现）
  3. 提供 cross_check() / check() / section() 辅助 API，供 CrossVal 脚本 import

规则（防错三原则之闭环验证）：
  - 禁止自校验 check(name, X, X) —— 永远 PASS，无验证价值
  - 数值型必须 cross_check()（与独立参考实现 scipy/numpy 比对）
  - crossval 目录缺失时输出 SKIP（显式说明未验证），不假装通过

用法：
  python scripts/verify-manual.py              # 静态检查 + 执行 crossval
  python scripts/verify-manual.py --check-only # 仅静态检查

退出码：0 = 通过（crossval 缺失时 SKIP 不算失败）；1 = 发现不一致
"""
import argparse
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANUAL = ROOT / "rules" / "user-manual.md"
CROSSVAL_DIR = ROOT / "scripts" / "crossval"

# 自校验模式：check(name, X, X) —— 永远 PASS，无验证价值
SELF_CHECK_RE = re.compile(
    r"check\s*\(\s*['\"]?[^,]+['\"]?\s*,\s*(\w+)\s*,\s*\1\s*\)"
)

# ============================================================================
# CrossVal 辅助 API（供 scripts/crossval/*.py 脚本 import）
# ============================================================================
_PASS = 0
_FAIL = 0


def section(name: str, count: int) -> None:
    """打印模块测试分节标题。"""
    print(f"\n=== {name} — {count} 项 ===")


def cross_check(name: str, actual: float, expected: float, tol: float = 1e-10) -> None:
    """数值交叉验证：被测实现结果 vs 独立参考实现结果（两路独立计算）。

    禁止自校验：actual 与 expected 必须来自两条独立路径
    （如 Python/scipy 独立实现 vs C#/VBA 被测实现的 CLI 输出）。
    """
    global _PASS, _FAIL
    if expected is None:
        _FAIL += 1
        print(f"  [FAIL] {name}: 期望值缺失（疑似自校验或无参考实现）")
        return
    scale = max(1.0, abs(float(expected)))
    if abs(float(actual) - float(expected)) <= tol * scale:
        _PASS += 1
        print(f"  [OK] {name}: {actual} ≈ {expected} (tol={tol})")
    else:
        _FAIL += 1
        print(f"  [FAIL] {name}: {actual} != {expected} (tol={tol})")


def check(name: str, actual, expected) -> None:
    """确定性结果比对：actual vs 硬编码期望值（非自校验）。"""
    global _PASS, _FAIL
    if actual == expected:
        _PASS += 1
        print(f"  [OK] {name}: {actual}")
    else:
        _FAIL += 1
        print(f"  [FAIL] {name}: {actual!r} != {expected!r}")


def run_crossval() -> bool:
    """执行 scripts/crossval/ 下所有 .py 脚本；目录缺失时 SKIP。"""
    global _PASS, _FAIL
    if not CROSSVAL_DIR.exists():
        print("[SKIP] 未发现 scripts/crossval/，数值比对待项目初始化实现"
              "（将 {Name}CrossVal 模板放入该目录后自动执行）")
        return True
    scripts = sorted(CROSSVAL_DIR.glob("*.py"))
    if not scripts:
        print("[SKIP] scripts/crossval/ 为空，数值比对待项目初始化实现")
        return True
    # CrossVal 脚本通过 `from verify_manual import check, cross_check, section` 使用辅助 API
    sys.path.insert(0, str(ROOT / "scripts"))
    for s in scripts:
        print(f"\n>>> 执行 {s.relative_to(ROOT)}")
        try:
            spec = importlib.util.spec_from_file_location(s.stem, s)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:  # noqa: BLE001 —— 隔离单个脚本失败，继续执行其余
            _FAIL += 1
            print(f"  [FAIL] {s.name} 执行失败: {type(e).__name__}: {e}")
    return _FAIL == 0


# ============================================================================
# 静态检查
# ============================================================================
def check_self_validation() -> list[str]:
    """检查手册与 CrossVal 脚本中是否存在自校验模式。"""
    problems: list[str] = []
    targets: list[Path] = []
    if MANUAL.exists():
        targets.append(MANUAL)
    if CROSSVAL_DIR.exists():
        targets.extend(sorted(CROSSVAL_DIR.glob("*.py")))
    for path in targets:
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if SELF_CHECK_RE.search(line):
                problems.append(f"[自校验] {path.name}:{i} check(X, X) 永远 PASS")
    return problems


def check_example_blocks() -> list[str]:
    """检查示例代码块是否标注语言（```python / ```csharp / ```vba）且全部闭合。"""
    problems: list[str] = []
    if not MANUAL.exists():
        return problems
    lines = MANUAL.read_text(encoding="utf-8").splitlines()
    in_block = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            if in_block:
                in_block = False
            elif lang:
                in_block = True
            else:
                problems.append(
                    f"[未标注语言] {MANUAL.name}:{i} 代码块必须标注语言"
                )
    if in_block:
        problems.append(f"[未闭合代码块] {MANUAL.name} 结尾存在未闭合的代码块")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="手册一致性验证")
    parser.add_argument("--check-only", action="store_true",
                        help="仅检查自校验模式与代码块标注，不执行数值比对")
    args = parser.parse_args()

    problems = check_self_validation() + check_example_blocks()
    if problems:
        print("[FAIL] 发现以下问题：")
        for p in problems:
            print(f"  - {p}")
        return 1

    if args.check_only:
        print("[OK] 静态检查通过（数值比对已跳过）")
        return 0

    ok = run_crossval()
    if _FAIL:
        print(f"\n[FAIL] 手册一致性验证失败：{_PASS} 项通过 / {_FAIL} 项失败")
        return 1
    print(f"\n[OK] 手册一致性验证通过（静态 + {_PASS} 项数值比对）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
