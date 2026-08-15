#!/usr/bin/env python3
"""
test_retry.py — retry.py 自身测试套件

验证瞬态错误重试装饰器的正确性：
  - 瞬态错误自动重试后成功
  - 非瞬态错误立即重抛（不重试）
  - 超过上限抛最后一次异常
  - 自定义分类器
"""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location("retry_mod", SCRIPTS_DIR / "retry.py")
retry_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(retry_mod)


class TestRetryTransient:
    def test_retries_transient_then_success(self):
        calls = {"n": 0}

        @retry_mod.retry_transient(max_attempts=4, delay=0.01)
        def flaky() -> str:
            calls["n"] += 1
            if calls["n"] < 3:
                raise ConnectionError("瞬时断连")
            return "ok"

        assert flaky() == "ok"
        assert calls["n"] == 3

    def test_non_transient_raises_immediately(self):
        calls = {"n": 0}

        @retry_mod.retry_transient(max_attempts=5, delay=0.01)
        def bad() -> None:
            calls["n"] += 1
            raise ValueError("业务错误，不可重试")

        with pytest.raises(ValueError):
            bad()
        assert calls["n"] == 1  # 只调用一次，不重试

    def test_exhausts_attempts(self):
        calls = {"n": 0}

        @retry_mod.retry_transient(max_attempts=3, delay=0.01)
        def always_fail() -> None:
            calls["n"] += 1
            raise ConnectionError("一直失败")

        with pytest.raises(ConnectionError):
            always_fail()
        assert calls["n"] == 3

    def test_custom_classifier(self):
        class MyError(Exception):
            pass

        calls = {"n": 0}

        @retry_mod.retry_transient(
            max_attempts=3, delay=0.01, classifier=lambda e: isinstance(e, MyError)
        )
        def flaky() -> str:
            calls["n"] += 1
            if calls["n"] < 2:
                raise MyError("自定义瞬态")
            return "done"

        assert flaky() == "done"
        assert calls["n"] == 2

    def test_preserves_wraps(self):
        @retry_mod.retry_transient(max_attempts=1)
        def documented() -> str:
            """docstring 保留"""
            return "x"

        assert documented.__name__ == "documented"
        assert documented.__doc__ == "docstring 保留"
