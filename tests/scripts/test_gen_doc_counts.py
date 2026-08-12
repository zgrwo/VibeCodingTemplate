#!/usr/bin/env python3
"""
test_gen_doc_counts.py — gen-doc-counts.py 自身测试套件

验证文档计数注入脚本的正确性：
  - _compute 三类计数源（file_count / regex_count / json_keys）
  - update_doc 内联与块状标记的更新/比对
  - main CLI 退出码（check 一致→0，过时→1，配置缺失→1）
"""
import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location(
    "gen_doc_counts", SCRIPTS_DIR / "gen-doc-counts.py"
)
gdc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gdc)


class TestCompute:
    """测试计数源计算。"""

    def test_file_count(self):
        assert gdc._compute("scripts", {"type": "file_count", "glob": "scripts/*.py"}) >= 1

    def test_regex_count_multiline_and_indent(self):
        # 类内缩进的测试方法应被统计（^\s* 允许缩进）
        v = gdc._compute(
            "tests",
            {"type": "regex_count", "pattern": "^\\s*def test_", "glob": "tests/**/*.py"},
        )
        assert v >= 60

    def test_json_keys(self):
        v = gdc._compute(
            "placeholders",
            {"type": "json_keys", "path": "scripts/placeholders.json", "key_path": "placeholders"},
        )
        assert v >= 100

    def test_unknown_type_returns_neg(self):
        assert gdc._compute("x", {"type": "bogus"}) == -1


class TestUpdateDoc:
    """测试标记块的更新与比对。"""

    def _doc(self, tmp_path, content: str) -> Path:
        p = tmp_path / "doc.md"
        p.write_text(content, encoding="utf-8")
        return p

    def test_inline_marker_update(self, tmp_path):
        p = self._doc(tmp_path, "（<!-- AUTO_COUNTS:X_START -->1<!-- AUTO_COUNTS:X_END --> 项）\n")
        problems = gdc.update_doc(p, {"X": 42}, check_only=False)
        assert problems == []
        assert "42" in p.read_text(encoding="utf-8")

    def test_inline_marker_check_passes_when_match(self, tmp_path):
        p = self._doc(tmp_path, "（<!-- AUTO_COUNTS:X_START -->42<!-- AUTO_COUNTS:X_END --> 项）\n")
        problems = gdc.update_doc(p, {"X": 42}, check_only=True)
        assert problems == []

    def test_inline_marker_check_fails_when_stale(self, tmp_path):
        p = self._doc(tmp_path, "（<!-- AUTO_COUNTS:X_START -->1<!-- AUTO_COUNTS:X_END --> 项）\n")
        problems = gdc.update_doc(p, {"X": 42}, check_only=True)
        assert any("已过时" in pr for pr in problems)

    def test_block_marker_update(self, tmp_path):
        p = self._doc(tmp_path, "<!-- AUTO_COUNTS:Y_START -->\n1\n<!-- AUTO_COUNTS:Y_END -->\n")
        problems = gdc.update_doc(p, {"Y": 7}, check_only=False)
        assert problems == []
        assert "7\n" in p.read_text(encoding="utf-8")

    def test_unclosed_marker_reports_error(self, tmp_path):
        p = self._doc(tmp_path, "<!-- AUTO_COUNTS:Z_START -->\n1\n")
        problems = gdc.update_doc(p, {"Z": 7}, check_only=False)
        assert any("无对应 END" in pr for pr in problems)

    def test_undefined_source_reports_error(self, tmp_path):
        marker = "<!-- AUTO_COUNTS:NOPE_START -->\n1\n<!-- AUTO_COUNTS:NOPE_END -->\n"
        p = self._doc(tmp_path, marker)
        problems = gdc.update_doc(p, {"X": 7}, check_only=False)
        assert any("未定义" in pr for pr in problems)

    def test_missing_doc(self, tmp_path):
        problems = gdc.update_doc(tmp_path / "nope.md", {"X": 1}, check_only=False)
        assert any("不存在" in pr for pr in problems)


class TestMainCLI:
    """测试 CLI 退出码。"""

    def test_missing_config(self, tmp_path):
        assert gdc.main(["--config", str(tmp_path / "nope.json")]) == 1

    def test_check_consistent_returns_zero(self):
        # 真实配置下所有标记块应一致（前一步已 update）
        assert gdc.main(["--check"]) == 0


class TestInlineMultiMarker:
    """测试一行含多个内联标记对（档 C 修复 6：避免只处理第一个）。"""

    def test_two_inline_markers_checked(self, tmp_path):
        p = tmp_path / "doc.md"
        p.write_text(
            "<!-- AUTO_COUNTS:A_START -->5<!-- AUTO_COUNTS:A_END --> "
            "<!-- AUTO_COUNTS:B_START -->7<!-- AUTO_COUNTS:B_END -->",
            encoding="utf-8",
        )
        # B 漂移为 9 → --check 必须检出（不能静默跳过第二个标记）
        problems = gdc.update_doc(p, {"A": 5, "B": 9}, check_only=True)
        assert any("已过时" in pr for pr in problems)

    def test_two_inline_markers_both_updated(self, tmp_path):
        p = tmp_path / "doc.md"
        p.write_text(
            "<!-- AUTO_COUNTS:A_START -->5<!-- AUTO_COUNTS:A_END --> "
            "<!-- AUTO_COUNTS:B_START -->7<!-- AUTO_COUNTS:B_END -->",
            encoding="utf-8",
        )
        gdc.update_doc(p, {"A": 5, "B": 9}, check_only=False)
        out = p.read_text(encoding="utf-8")
        assert "A_START -->5<!--" in out
        assert "B_START -->9<!--" in out
