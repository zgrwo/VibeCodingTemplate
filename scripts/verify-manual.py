#!/usr/bin/env python3
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
import contextlib
import importlib.util
import re
import sys
from pathlib import Path

# Windows GBK 控制台：强制 UTF-8 输出，避免中文说明乱码（[OK]/[FAIL] 标记保持 ASCII 兼容）
with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
MANUAL = ROOT / "rules" / "user-manual.md"
CROSSVAL_DIR = ROOT / "scripts" / "crossval"

# 自校验模式：check(name, X, X) —— 永远 PASS，无验证价值。
# 操作数用 [^\s,]+ 而非 \w+：须覆盖 self.mean / obj.attr / d["k"] / mean(...)
# 等属性访问、下标、调用形态，否则此类自校验可绕过「禁止自校验」红线。
SELF_CHECK_RE = re.compile(
    r"check\s*\(\s*['\"]?[^,]+['\"]?\s*,\s*([^\s,]+)\s*,\s*\1\s*\)"
)


def _display(path: Path) -> str:
    """输出脚本相对路径；位于仓库外时回退绝对路径（防 relative_to ValueError）。"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _is_comment_or_docstring(line: str) -> bool:
    """判断是否为注释/docstring 行（自校验扫描应跳过，避免文档反例被误判）。"""
    stripped = line.lstrip()
    return stripped.startswith(("#", "\"", "'"))

# ============================================================================
# CrossVal 辅助 API（供 scripts/crossval/*.py 脚本 import）
# ============================================================================
_PASS = 0
_FAIL = 0


def section(name: str, count: int) -> None:
    """打印模块测试分节标题。"""
    print(f"\n=== {name} — {count} 项 ===")


def cross_check(
    name: str, actual: float | None, expected: float | None, tol: float = 1e-10
) -> None:
    """数值交叉验证：被测实现结果 vs 独立参考实现结果（两路独立计算）。

    禁止自校验：actual 与 expected 必须来自两条独立路径
    （如 Python/scipy 独立实现 vs C#/VBA 被测实现的 CLI 输出）。

    tol 支持分层语义（来源：ExcelVBA build_common.py 容差分层）：
      精确 1e-10 基本运算 / 数值 1e-6 迭代算法 / 宽松 1e-5 SVD /
      统计 1e-2 高阶矩 / 物理 0.1 物理常数。调用方可按算法类型选档。
    """
    global _PASS, _FAIL
    if expected is None:
        _FAIL += 1
        print(f"  [FAIL] {name}: 期望值缺失（疑似自校验或无参考实现）")
        return
    if actual is None:
        _FAIL += 1
        print(f"  [FAIL] {name}: 实际值为 None（被测实现未返回有效结果）")
        return
    scale = max(1.0, abs(float(expected)))
    if abs(float(actual) - float(expected)) <= tol * scale:
        _PASS += 1
        print(f"  [OK] {name}: {actual} ≈ {expected} (tol={tol})")
    else:
        _FAIL += 1
        print(f"  [FAIL] {name}: {actual} != {expected} (tol={tol})")


# 容差分层常量（来源：ExcelVBA build_common.py）——供 crossval 脚本按算法类型选档
TOLERANCE_TIERS = {
    "exact": 0.0,        # 精确：字符串/布尔结果
    "standard": 1e-10,   # 基本运算/排序/数组操作
    "numeric": 1e-6,     # 迭代算法（PolyFit/矩阵分解）
    "loose": 1e-5,       # SVD 奇异值（迭代收敛）
    "stats": 1e-2,       # 高阶矩（偏度/峰度）
    "physical": 0.1,     # 物理常数（分子量/单位换算）
}


def compare(name: str, actual: object, expected: object, tol: float = 1e-10) -> None:
    """分类型比较器：按结果类型选择比对策略（数组/标量/字符串/字典键）。

    来源：ExcelVBA build_common.py 分类型比较器。crossval 脚本用它验证
    非标量结果（数组、字典、字符串列表）的一致性。
    """
    import math

    global _PASS, _FAIL
    if actual is None or expected is None:
        _FAIL += 1
        print(f"  [FAIL] {name}: actual/expected 含 None")
        return
    # 数组/序列：逐元素比对，任一分量超差即 FAIL
    if isinstance(expected, (list, tuple)) and not isinstance(expected, str):
        try:
            if len(actual) != len(expected):
                _FAIL += 1
                print(f"  [FAIL] {name}: 长度 {len(actual)} != {len(expected)}")
                return
            for i, (a, e) in enumerate(zip(actual, expected, strict=True)):
                if isinstance(e, (int, float)) and not isinstance(e, bool):
                    scale = max(1.0, abs(float(e)))
                    try:
                        a_f = float(a)
                    except (TypeError, ValueError):
                        _FAIL += 1
                        print(f"  [FAIL] {name}[{i}]: 类型不匹配——期望数值 {e!r}，"
                              f"实际 {a!r} 无法转数值")
                        return
                    if not math.isfinite(a_f) or abs(a_f - float(e)) > tol * scale:
                        _FAIL += 1
                        print(f"  [FAIL] {name}[{i}]: {a} != {e} (tol={tol})")
                        return
                elif a != e:
                    _FAIL += 1
                    print(f"  [FAIL] {name}[{i}]: {a!r} != {e!r}")
                    return
            _PASS += 1
            print(f"  [OK] {name}: 序列一致 ({len(actual)} 项)")
        except TypeError:
            _FAIL += 1
            print(f"  [FAIL] {name}: actual 非序列（{type(actual).__name__}）")
        return
    # 字典：比对键集合一致
    if isinstance(expected, dict):
        if isinstance(actual, dict) and set(actual.keys()) == set(expected.keys()):
            _PASS += 1
            print(f"  [OK] {name}: 字典键集合一致 ({len(expected)} 键)")
        else:
            _FAIL += 1
            print(f"  [FAIL] {name}: 字典键集合不一致")
        return
    # 数值标量：走 cross_check 语义
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        cross_check(name, actual, expected, tol)
        return
    # 其余（字符串/布尔）：确定性相等
    if actual == expected:
        _PASS += 1
        print(f"  [OK] {name}: {actual}")
    else:
        _FAIL += 1
        print(f"  [FAIL] {name}: {actual!r} != {expected!r}")


def check(name: str, actual: object, expected: object) -> None:
    """确定性结果比对：actual vs 硬编码期望值（非自校验）。"""
    global _PASS, _FAIL
    if actual == expected:
        _PASS += 1
        print(f"  [OK] {name}: {actual}")
    else:
        _FAIL += 1
        print(f"  [FAIL] {name}: {actual!r} != {expected!r}")


# 手册声称值标记：`<!-- CLAIM:NAME --><值><!-- /CLAIM:NAME -->`
# 值定义在 user-manual.md（SSOT），crossval 脚本用 manual_check() 实跑代码比对。
_CLAIM_RE = re.compile(
    r"<!--\s*CLAIM:([A-Z0-9_]+)\s*-->\s*"
    r"([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*"
    r"<!--\s*/CLAIM:\1\s*-->"
)


def load_claims() -> dict[str, float]:
    """从 user-manual.md 提取全部手册声称值，返回 {NAME: 数值}。"""
    claims: dict[str, float] = {}
    if not MANUAL.exists():
        return claims
    text = MANUAL.read_text(encoding="utf-8")
    for name, value in _CLAIM_RE.findall(text):
        try:
            claims[name] = float(value)
        except ValueError:
            continue
    return claims


# CLAIM 声称值缓存：manual_check 多次调用时避免每次重读重扫 user-manual.md（P3-12）
_CLAIMS_CACHE: dict[str, float] | None = None


def manual_check(name: str, actual: float | None, tol: float = 1e-10) -> None:
    """实跑比对：将实际计算结果与 user-manual.md 中声称值（CLAIM:NAME 标记）比对。

    防文档数字漂移：手册里写的数值（effect size、阈值、均值等）由真实运行验证，
    而非静态核对文本。声称值来源 SSOT（user-manual.md），crossval 脚本不硬编码。
    """
    global _PASS, _FAIL, _CLAIMS_CACHE
    if _CLAIMS_CACHE is None:
        _CLAIMS_CACHE = load_claims()
    claims = _CLAIMS_CACHE
    expected = claims.get(name)
    if expected is None:
        _FAIL += 1
        print(f"  [FAIL] {name}: user-manual.md 无对应 `<!-- CLAIM:{name} -->` 声称值"
              "（请先在手册标注该数值）")
        return
    cross_check(name, actual, expected, tol)


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
    # 让 `from src.stats.StatsCore import ...` 等仓库包导入可解析（CrossVal 位于 scripts/crossval/）
    sys.path.insert(0, str(ROOT))
    # 本脚本以 `python scripts/verify-manual.py` 运行时，模块名是 __main__ 而非
    # verify_manual（文件名含连字符无法直接 import）。
    # 为 __main__ 注册别名，避免 CrossVal 脚本 ModuleNotFoundError。
    sys.modules.setdefault("verify_manual", sys.modules.get("__main__"))
    for s in scripts:
        print(f"\n>>> 执行 {_display(s)}")
        try:
            spec = importlib.util.spec_from_file_location(s.stem, s)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:  # noqa: BLE001 —— 隔离单个脚本失败，继续执行其余
            _FAIL += 1
            print(f"  [FAIL] {s.name} 执行失败: {type(e).__name__}: {e}")
    # 防门禁说谎：crossval 脚本若被 `if __name__ == "__main__"` 包裹则不会执行任何校验
    # （spec_from_file_location 加载时 __name__ 恒为模块 stem），0 PASS/0 FAIL 必须显式失败。
    if _PASS + _FAIL == 0:
        print("[FAIL] crossval 脚本未产生任何校验项（检查是否误用了 "
              "`if __name__ == '__main__':` 守卫，它会被 spec 加载绕过）")
        _FAIL += 1
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
            # 跳过注释/docstring 行：文档中的反例教学文字
            # （如「禁止自校验 check(name, X, X)」）不应被误判为真实自校验
            if _is_comment_or_docstring(line):
                continue
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

    run_crossval()
    if _FAIL:
        print(f"\n[FAIL] 手册一致性验证失败：{_PASS} 项通过 / {_FAIL} 项失败")
        return 1
    print(f"\n[OK] 手册一致性验证通过（静态 + {_PASS} 项数值比对）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
