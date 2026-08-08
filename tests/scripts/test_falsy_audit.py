#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_falsy_audit.py — falsy-audit.py 自身测试套件

验证 Falsy 陷阱审计脚本的正确性：
  - 变量名匹配逻辑
  - HIGH/LOW 分级
  - AST 模式 + 正则兜底
  - 各检测模式（if x / if not x / while x / x or default）
  - 类型注解感知（bool/collection 安全）
"""
import sys
import tempfile
from pathlib import Path

import pytest

# 将 scripts/ 加入路径以导入 falsy-audit
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# falsy-audit.py 文件名含连字符，需要用 importlib 导入
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "falsy_audit", SCRIPTS_DIR / "falsy-audit.py"
)
fa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fa)


class TestClassify:
    """测试变量名分类逻辑。"""

    def test_high_risk_statistical(self):
        assert fa._classify("mean") == "HIGH"
        assert fa._classify("count") == "HIGH"
        assert fa._classify("threshold") == "HIGH"
        assert fa._classify("correlation") == "HIGH"
        assert fa._classify("sigma") == "HIGH"
        assert fa._classify("effect_size") == "HIGH"

    def test_high_risk_patterns(self):
        assert fa._classify("weibull_shape") == "HIGH"
        assert fa._classify("dist_scale") == "HIGH"

    def test_low_risk(self):
        assert fa._classify("error_rate") == "LOW"
        assert fa._classify("pass_rate") == "LOW"

    def test_safe_names(self):
        assert fa._classify("name") == ""
        assert fa._classify("message") == ""
        assert fa._classify("flag") == ""


class TestASTAudit:
    """测试 AST 模式审计。"""

    def test_clean_file_no_warnings(self, tmp_path):
        """无 falsy 问题的文件不应产生警告。"""
        f = tmp_path / "clean.py"
        f.write_text(
            "def compute(value):\n"
            "    if value is not None:\n"
            "        return value * 2\n"
            "    return None\n"
        )
        results = fa.audit_file(f, use_ast=True)
        assert len(results) == 0

    def test_if_truthy_detected(self, tmp_path):
        """if count: 应被检测。"""
        f = tmp_path / "risky.py"
        f.write_text(
            "def process(count):\n"
            "    if count:\n"
            "        return count\n"
        )
        results = fa.audit_file(f, use_ast=True)
        assert len(results) >= 1
        assert results[0][0] == "HIGH"  # level
        assert "count" in results[0][1]  # var

    def test_if_not_truthy_detected(self, tmp_path):
        """if not count: 应被检测。"""
        f = tmp_path / "risky.py"
        f.write_text(
            "def process(count):\n"
            "    if not count:\n"
            "        return 0\n"
        )
        results = fa.audit_file(f, use_ast=True)
        assert len(results) >= 1

    def test_while_truthy_detected(self, tmp_path):
        """while count: 应被检测。"""
        f = tmp_path / "risky.py"
        f.write_text(
            "def process(count):\n"
            "    while count:\n"
            "        count -= 1\n"
        )
        results = fa.audit_file(f, use_ast=True)
        assert len(results) >= 1

    def test_or_fallback_detected(self, tmp_path):
        """threshold or 0.05 应被检测。"""
        f = tmp_path / "risky.py"
        f.write_text(
            "def process(threshold):\n"
            "    result = threshold or 0.05\n"
            "    return result\n"
        )
        results = fa.audit_file(f, use_ast=True)
        assert len(results) >= 1
        assert "threshold" in results[0][1]

    def test_return_or_detected(self, tmp_path):
        """return count or 0 应被检测。"""
        f = tmp_path / "risky.py"
        f.write_text(
            "def process(count):\n"
            "    return count or 0\n"
        )
        results = fa.audit_file(f, use_ast=True)
        assert len(results) >= 1

    def test_is_not_none_safe(self, tmp_path):
        """if x is not None: 不应被报告。"""
        f = tmp_path / "safe.py"
        f.write_text(
            "def process(count):\n"
            "    if count is not None:\n"
            "        return count\n"
        )
        results = fa.audit_file(f, use_ast=True)
        assert len(results) == 0

    def test_compare_safe(self, tmp_path):
        """if count > 0: 不应被报告。"""
        f = tmp_path / "safe.py"
        f.write_text(
            "def process(count):\n"
            "    if count > 0:\n"
            "        return count\n"
        )
        results = fa.audit_file(f, use_ast=True)
        assert len(results) == 0

    def test_attribute_access_detected(self, tmp_path):
        """self.count 应被检测。"""
        f = tmp_path / "attr.py"
        f.write_text(
            "class Foo:\n"
            "    def bar(self):\n"
            "        if self.count:\n"
            "            return self.count\n"
        )
        results = fa.audit_file(f, use_ast=True)
        assert len(results) >= 1

    def test_bool_annotation_safe(self, tmp_path):
        """flag: bool → if flag: 安全，不报告。"""
        f = tmp_path / "safe_bool.py"
        f.write_text(
            "def process(flag: bool) -> None:\n"
            "    if flag:\n"
            "        print('yes')\n"
        )
        results = fa.audit_file(f, use_ast=True)
        assert len(results) == 0

    def test_collection_annotation_safe(self, tmp_path):
        """data: list → if data: 安全，不报告。"""
        f = tmp_path / "safe_collection.py"
        f.write_text(
            "def process(data: list) -> int:\n"
            "    if data:\n"
            "        return len(data)\n"
            "    return 0\n"
        )
        results = fa.audit_file(f, use_ast=True)
        assert len(results) == 0


class TestRegexFallback:
    """测试正则兜底模式。"""

    def test_regex_if_detected(self, tmp_path):
        """正则模式下 if count: 应被检测。"""
        f = tmp_path / "risky.py"
        f.write_text(
            "def process(count):\n"
            "    if count:\n"
            "        return count\n"
        )
        results = fa.audit_file(f, use_ast=False)
        assert len(results) >= 1

    def test_regex_clean_file(self, tmp_path):
        f = tmp_path / "clean.py"
        f.write_text(
            "def compute(value):\n"
            "    if value is not None:\n"
            "        return value * 2\n"
        )
        results = fa.audit_file(f, use_ast=False)
        assert len(results) == 0

    def test_ast_fallback_on_syntax_error(self, tmp_path):
        """语法错误的文件 → AST 失败，不应崩溃，正则兜底。"""
        f = tmp_path / "broken.py"
        f.write_text(
            "def process(count:\n"  # 语法错误：缺右括号
            "    if count:\n"
            "        return count\n"
        )
        # AST 应失败，正则兜底；不应崩溃
        results = fa.audit_file(f, use_ast=True)
        # 正则兜底应该捕获 if count:
        assert len(results) >= 1
