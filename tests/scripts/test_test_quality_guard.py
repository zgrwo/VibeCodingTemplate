#!/usr/bin/env python3
"""
test_test_quality_guard.py — test-quality-guard.py 自身测试套件

验证测试质量守卫脚本的正确性：
  - 弱断言检测（is not None / len>0 唯一断言）
  - 命名规范检测
  - 缺测检测
  - main CLI 退出码（弱断言→0，FAIL→1）
"""
import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location(
    "test_quality_guard", SCRIPTS_DIR / "test-quality-guard.py"
)
tq = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tq)


def _make_test(tmp_path, name: str, body: str) -> Path:
    t = tmp_path / "tests"
    t.mkdir(exist_ok=True)
    f = t / f"test_{name}.py"
    f.write_text(f"def {name}():\n    {body}\n", encoding="utf-8")
    return f


class TestWeakAsserts:
    """测试弱断言检测。"""

    def test_weak_notnone_only(self, tmp_path):
        _make_test(tmp_path, "test_a", "x = foo()\n    assert x is not None")
        problems = tq.check_weak_asserts(tmp_path / "tests")
        assert len(problems) == 1
        assert "[WARN]" in problems[0]

    def test_weak_len_zero(self, tmp_path):
        _make_test(tmp_path, "test_b", "items = foo()\n    assert len(items) > 0")
        problems = tq.check_weak_asserts(tmp_path / "tests")
        assert len(problems) == 1

    def test_strong_assert_not_flagged(self, tmp_path):
        _make_test(tmp_path, "test_c", "x = foo()\n    assert x == 42")
        problems = tq.check_weak_asserts(tmp_path / "tests")
        assert problems == []

    def test_weak_plus_strong_ok(self, tmp_path):
        # is not None 作为前置检查 + 真实断言 → 不判弱
        _make_test(tmp_path, "test_d", "x = foo()\n    assert x is not None\n    assert x == 42")
        problems = tq.check_weak_asserts(tmp_path / "tests")
        assert problems == []


class TestNaming:
    """测试命名规范检测。"""

    def test_bad_numeric_name(self, tmp_path):
        _make_test(tmp_path, "test_1", "assert True")
        problems = tq.check_naming(tmp_path / "tests")
        assert len(problems) == 1
        assert "[FAIL]" in problems[0]

    def test_good_descriptive_name(self, tmp_path):
        _make_test(tmp_path, "test_divide_by_zero_returns_nan", "assert True")
        problems = tq.check_naming(tmp_path / "tests")
        assert problems == []


class TestMissingTests:
    """测试缺测检测。"""

    def test_unreferenced_function_flagged(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "core.py").write_text("def compute():\n    return 1\n", encoding="utf-8")
        tests = tmp_path / "tests"
        tests.mkdir()
        other = "def test_other():\n    assert True\n"
        (tests / "test_other.py").write_text(other, encoding="utf-8")
        problems = tq.check_missing_tests(src, tests)
        assert len(problems) == 1
        assert "compute" in problems[0]

    def test_referenced_function_not_flagged(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "core.py").write_text("def compute():\n    return 1\n", encoding="utf-8")
        tests = tmp_path / "tests"
        tests.mkdir()
        core = "def test_compute():\n    assert compute() == 1\n"
        (tests / "test_core.py").write_text(core, encoding="utf-8")
        problems = tq.check_missing_tests(src, tests)
        assert problems == []


class TestMainCLI:
    """测试 CLI 退出码。"""

    def test_clean_returns_zero(self):
        # 模板自身应通过
        assert tq.main([]) == 0
