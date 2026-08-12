#!/usr/bin/env python3
"""
test_run_affected_tests.py — run-affected-tests.py 自身测试套件

验证影响范围测试路由脚本的正确性：
  - source_stem 提取
  - find_tests_for 命名映射
  - main --dry-run 退出码（有 src 变更→0，无→0）
"""
import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location(
    "run_affected_tests", SCRIPTS_DIR / "run-affected-tests.py"
)
rat = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rat)


class TestSourceStem:
    def test_py_stem(self):
        assert rat.source_stem("src/foo/bar.py") == "bar"

    def test_cs_stem(self):
        assert rat.source_stem("src/foo/Bar.cs") == "Bar"


class TestFindTestsFor:
    def test_matches_test_py(self, tmp_path):
        (tmp_path / "test_bar.py").write_text("", encoding="utf-8")
        (tmp_path / "test_other.py").write_text("", encoding="utf-8")
        found = rat.find_tests_for("src/foo/bar.py", tmp_path)
        assert any("test_bar.py" in f for f in found)
        assert not any("test_other.py" in f for f in found)

    def test_matches_tests_cs(self, tmp_path):
        (tmp_path / "BarTests.cs").write_text("", encoding="utf-8")
        found = rat.find_tests_for("src/foo/bar.cs", tmp_path)
        assert any("BarTests.cs" in f for f in found)

    def test_matches_kebab_case_py(self, tmp_path):
        # 连字符命名的源脚本须命中下划线命名的测试（P1-8/P1-11 回归防护）
        (tmp_path / "test_gen_doc_counts.py").write_text("", encoding="utf-8")
        found = rat.find_tests_for("scripts/gen-doc-counts.py", tmp_path)
        assert any("test_gen_doc_counts.py" in f for f in found)

    def test_no_match(self, tmp_path):
        found = rat.find_tests_for("src/foo/xyz.py", tmp_path)
        assert found == []

    def test_dunder_ignored(self, tmp_path):
        assert rat.find_tests_for("src/__init__.py", tmp_path) == []


class TestMainCLI:
    def test_dry_run_no_src_changes_returns_zero(self, monkeypatch):
        monkeypatch.setattr(rat, "get_changed_files", lambda base: ["tests/test_a.py"])
        assert rat.main(["--dry-run"]) == 0

    def test_unmatched_src_returns_one(self, monkeypatch):
        monkeypatch.setattr(rat, "get_changed_files", lambda base: ["src/zzz.py"])
        assert rat.main(["--dry-run"]) == 1
