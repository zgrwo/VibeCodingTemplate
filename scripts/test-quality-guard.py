#!/usr/bin/env python3
"""
test-quality-guard.py — 测试质量守卫（弱断言/缺测/命名）

背景（来源：成本分析套件 tools/test-quality-guard.ps1 五阶段检测
      + 工程分析套件 test_quality_guard.py 恒真断言/自校验检测）：
  lint 与覆盖率只保证"测试存在"，不保证"测试有效"。本脚本检测五类测试质量问题：
    1. 弱断言：`assert x is not None` / `assert len(x) > 0` 等作为**唯一**断言的测试方法
       （验证了"不是空"，但没有验证具体值，任何非空结果都能通过——形同虚设）
    2. 恒真断言：`assert True` / `assert x == x` 等永远通过（FAIL 级，2026-09 对齐
       工程分析套件 test_quality_guard.py，补 AGENTS.md 红线 3.1 的全仓门禁）
    3. 自校验：`check(name, X, X)` 永远 PASS（FAIL 级，闭环验证红线 3.1 的静态检测，
       与 verify-manual.py 同源语义但覆盖全部 tests/）
    4. 缺测：src/ 下公共函数无对应测试引用（源码改动了测试没跟上）
    5. 命名：测试方法名非描述性（test_<数字> / test_caseN 等无意义名）

用法：
  python scripts/test-quality-guard.py            # 基础检查
  python scripts/test-quality-guard.py --src src --tests tests
  python scripts/test-quality-guard.py --max-warn 0   # WARN 预算零容忍（CI 硬门禁）

退出码：
  0 = 通过（弱断言 WARN 未超预算）
  1 = 存在 FAIL（恒真断言/自校验/缺测/命名）或 WARN 数量超过 --max-warn 预算
"""

import argparse
import ast
import contextlib
import re
import sys
from pathlib import Path

with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# 弱断言模式：只有这类断言，无具体值验证
_WEAK_ASSERT_RE = re.compile(
    r"assert\s+\w+\s+is\s+not\s+None"  # assert x is not None
    r"|assert\s+len\([^)]*\)\s*[><]=?\s*0"  # assert len(x) > 0
    r"|assert\s+\w+\s*!=\s*None"  # assert x != None
    r"|assert\s+bool\("  # assert bool(x)
)
# 真实断言（验证具体值）
# expr 支持下标/属性/方法调用（df["col"].sum() == 5）、len(...)==N/!=N 形式
# ReDoS 修复（CodeQL py/redos）：原 `\[.*?\]` / `\(.*?\)` 内嵌点星量词，
# 与分组外层 `*` 叠加形成嵌套量词 → 灾难性回溯。改用排除定界符的字符类
# `[^\]]*` / `[^)]*`（单层量词，无回溯），语义等价（单层下标/方法调用）。
_STRONG_ASSERT_RE = re.compile(
    r"assert\s+\w+(?:\[[^\]]*\]|\.\w+(?:\([^)]*\))?)*\s*[=!]=\s*\w+(?:\([^)]*\))?"
    r"|assert\s+\w+\s*in\s+"  # assert x in ...
    r"|assert\s+\w+(?:\[[^\]]*\]|\.\w+(?:\([^)]*\))?)*\s*[<>]=?\s*\w+(?:\([^)]*\))?"
    r"|assert\s+\w+\s*is\s+True"  # assert x is True
    r"|assert\s+\w+\s*is\s+False"
    r"|assert\s+len\([^)]*\)\s*[=!]=\s*\S+"  # assert len(x) == N / != N
    r"|pytest\.raises"  # 异常断言
)
# 无意义测试名：test_<纯数字/序号/caseN>
_BAD_NAME_RE = re.compile(r"test_(?:\d+|case\d+|test\d+|a|b|c|foo|bar|dummy)$")
# 自校验模式：check(name, X, X) —— 永远 PASS，无验证价值（与 verify-manual.py 同源）。
# 操作数用 [^\s,]+ 覆盖属性访问/下标/调用形态，否则此类自校验可绕过红线。
_SELF_CHECK_RE = re.compile(r"check\s*\(\s*['\"]?[^,]+['\"]?\s*,\s*([^\s,]+)\s*,\s*([^\s,]+)\s*\)")
# 常量操作数：check("X", 1.0, 1.0) 是对 check 辅助函数等值分支的合法单测，
# 不属于「同一变量算两次」的闭环验证红线，豁免（与 crossval 的真实自校验区分）。
_CONST_OPERAND_RE = re.compile(
    r"^(?:[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|['\"].*['\"]|True|False|None)$"
)


def _rel(path: Path) -> str:
    """输出相对路径；位于仓库外时回退绝对路径（防 relative_to ValueError）。"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _extract_test_methods(path: Path) -> list[tuple[str, str]]:
    """解析 Python 测试文件，返回 [(方法名, 方法源码)]。"""
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except (OSError, SyntaxError):
        return []
    methods: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            src = ast.get_source_segment(text, node) or ""
            methods.append((node.name, src))
    return methods


def _method_has_strong_assert(src: str) -> bool:
    """方法体是否含真实断言（排除注释）。"""
    for line in src.splitlines():
        stripped = line.split("#", 1)[0]
        if _STRONG_ASSERT_RE.search(stripped):
            return True
    return False


def _method_is_weak_only(src: str) -> bool:
    """方法只有弱断言（且无强断言）→ 视为弱。"""
    # 与 _method_has_strong_assert 对齐：剔除注释后再判定，避免注释掉的弱断言误报
    code = "\n".join(line.split("#", 1)[0] for line in src.splitlines())
    return bool(_WEAK_ASSERT_RE.search(code)) and not _method_has_strong_assert(src)


# 自测夹具文件：刻意含弱断言以验证守卫逻辑，不应触发自 WARN（告警疲劳）
SELF_TEST_FILES = {"test_test_quality_guard.py"}


def check_weak_asserts(tests_dir: Path) -> list[str]:
    """检测弱断言测试方法。"""
    problems: list[str] = []
    if not tests_dir.is_dir():
        return problems
    for p in sorted(tests_dir.rglob("test_*.py")):
        if p.name in SELF_TEST_FILES:
            continue
        for name, src in _extract_test_methods(p):
            if _method_is_weak_only(src):
                rel = _rel(p)
                problems.append(
                    f"[WARN] {rel}:{name} 仅弱断言（is not None / len>0 / bool()），"
                    "不验证具体值——任何非空结果都能通过，请补真实断言"
                )
    return problems


def check_naming(tests_dir: Path) -> list[str]:
    """检测无意义测试命名。"""
    problems: list[str] = []
    if not tests_dir.is_dir():
        return problems
    for p in sorted(tests_dir.rglob("test_*.py")):
        for name, _ in _extract_test_methods(p):
            if _BAD_NAME_RE.search(name):
                rel = _rel(p)
                problems.append(
                    f"[FAIL] {rel}:{name} 无意义测试名——请改为描述性名称"
                    "（如 test_divide_by_zero_returns_nan）"
                )
    return problems


def _is_tautology(test: ast.expr) -> bool:
    """判断断言表达式是否恒真（永远通过）。

    覆盖形态：
      - `assert True` / `assert 1` / `assert "x"`（常量真值）
      - `assert not False` / `assert not 0`（常量假值取反）
      - `assert x == x` / `assert x is x`（比较两侧结构等价）
    """
    if isinstance(test, ast.Constant):
        return bool(test.value)
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        inner = test.operand
        return isinstance(inner, ast.Constant) and not inner.value
    if isinstance(test, ast.Compare) and len(test.ops) == 1 and len(test.comparators) == 1:
        left, right = test.left, test.comparators[0]
        same = ast.dump(left) == ast.dump(right)
        return same and isinstance(test.ops[0], (ast.Eq, ast.Is))
    return False


def check_tautological_asserts(tests_dir: Path) -> list[str]:
    """检测恒真断言（`assert True` / `assert x == x` 等永远通过的断言）。"""
    problems: list[str] = []
    if not tests_dir.is_dir():
        return problems
    for p in sorted(tests_dir.rglob("test_*.py")):
        if p.name in SELF_TEST_FILES:
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert) and _is_tautology(node.test):
                rel = _rel(p)
                problems.append(
                    f"[FAIL] {rel}:{node.lineno} 恒真断言 `assert {ast.unparse(node.test)}`"
                    "——永远通过，无验证价值，请改为验证具体值"
                )
    return problems


def check_self_validation(tests_dir: Path) -> list[str]:
    """检测测试中的自校验模式 check(name, X, X)（永远 PASS，闭环验证红线）。"""
    problems: list[str] = []
    if not tests_dir.is_dir():
        return problems
    for p in sorted(tests_dir.rglob("test_*.py")):
        if p.name in SELF_TEST_FILES:
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            # 跳过注释/docstring 行：反例教学文字（如「禁止自校验 check(X, X)」）不误判
            if line.lstrip().startswith(("#", '"', "'")):
                continue
            # 跳过守卫自身的测试夹具行（如 assert SELF_CHECK_RE.search('check(...)')）
            if any(tok in line for tok in ("SELF_CHECK_RE", "re.search", "re.compile")):
                continue
            m = _SELF_CHECK_RE.search(line)
            if not m:
                continue
            actual, expected = m.group(1), m.group(2)
            if actual != expected:
                continue
            # 常量等值（check("X", 1.0, 1.0)）是辅助函数单测，豁免
            if _CONST_OPERAND_RE.match(actual):
                continue
            rel = _rel(p)
            problems.append(
                f"[FAIL] {rel}:{i} 自校验 check(X, X) 永远 PASS"
                "（闭环验证红线：actual/expected 必须来自两条独立路径）"
            )
    return problems


def check_missing_tests(src_dir: Path, tests_dir: Path) -> list[str]:
    """src/ 公共函数 vs tests/ 测试引用对应检测（防"改代码没更测试"）。"""
    problems: list[str] = []
    if not src_dir.is_dir() or not tests_dir.is_dir():
        return problems
    tested: set[str] = set()
    for p in tests_dir.rglob("test_*.py"):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        tested.update(re.findall(r"\b(\w+)\(", text))
    for p in sorted(src_dir.rglob("*.py")):
        if p.name.startswith("__"):
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in tree.body:
            is_public = isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
            if is_public and node.name not in tested:
                rel = _rel(p)
                problems.append(f"[FAIL] {rel}:{node.name} 无对应测试引用——新增公共函数必须配测试")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="测试质量守卫")
    parser.add_argument("--src", default="src", help="源码目录（默认 src）")
    parser.add_argument("--tests", default="tests", help="测试目录（默认 tests）")
    parser.add_argument(
        "--max-warn",
        type=int,
        default=None,
        help="WARN 数量预算（0 = 零容忍）；超过预算按失败处理，默认不限制",
    )
    args = parser.parse_args(argv)

    src_dir = ROOT / args.src
    tests_dir = ROOT / args.tests

    problems: list[str] = []
    problems += check_weak_asserts(tests_dir)
    problems += check_tautological_asserts(tests_dir)
    problems += check_self_validation(tests_dir)
    problems += check_naming(tests_dir)
    problems += check_missing_tests(src_dir, tests_dir)

    warn_count = sum(1 for p in problems if p.startswith("[WARN]"))
    if not problems:
        print("[OK] 测试质量守卫通过")
        return 0
    for p in problems:
        print(p)
    if any(p.startswith("[FAIL]") for p in problems):
        return 1
    if args.max_warn is not None and warn_count > args.max_warn:
        print(f"[FAIL] WARN 数量 {warn_count} 超过预算 {args.max_warn}（--max-warn）")
        return 1
    print(f"[OK] 测试质量守卫通过（{warn_count} 条弱断言 WARN，未超预算）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
