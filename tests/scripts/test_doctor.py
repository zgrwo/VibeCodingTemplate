#!/usr/bin/env python3
"""
test_doctor.py — doctor.py 自身测试套件

验证环境就绪性诊断脚本的正确性：
  - 各 check 函数（python/git/tool/dir/file/placeholders）
  - main CLI 退出码（全就绪→0，有失败→1）
"""
import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location("doctor", SCRIPTS_DIR / "doctor.py")
doc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(doc)


class TestChecks:
    """测试各检查函数。"""

    def test_python_ok(self):
        ok, _ = doc.check_python()
        assert ok is True  # 当前环境必然 >=3.10

    def test_git_ok(self):
        ok, _ = doc.check_git()
        # 模板仓库本身是 git 仓库
        assert ok is True

    def test_tool_missing(self):
        ok, msg = doc.check_tool("definitely_not_a_real_module_xyz", "fake")
        assert ok is False
        assert "未安装" in msg

    def test_dir_exists(self, tmp_path, monkeypatch):
        (tmp_path / "src").mkdir()
        monkeypatch.setattr(doc, "ROOT", tmp_path)
        ok, _ = doc.check_dir("src")
        assert ok is True

    def test_dir_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(doc, "ROOT", tmp_path)
        ok, _ = doc.check_dir("nope")
        assert ok is False

    def test_file_exists(self, tmp_path, monkeypatch):
        (tmp_path / "x.txt").write_text("", encoding="utf-8")
        monkeypatch.setattr(doc, "ROOT", tmp_path)
        ok, _ = doc.check_file("x.txt")
        assert ok is True

    def test_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(doc, "ROOT", tmp_path)
        ok, _ = doc.check_file("nope.txt")
        assert ok is False

    def test_placeholders_valid(self):
        # 用真实 placeholders.json（模板自身应可解析）
        ok, msg = doc.check_placeholders()
        assert ok is True
        assert "可解析" in msg

    def test_placeholders_broken_json(self, tmp_path, monkeypatch):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        p = scripts / "placeholders.json"
        p.write_text("{invalid json", encoding="utf-8")
        monkeypatch.setattr(doc, "ROOT", tmp_path)
        ok, msg = doc.check_placeholders()
        assert ok is False
        assert "解析失败" in msg

    def test_placeholders_empty_ok(self, tmp_path, monkeypatch):
        """生成项目 manifest 被 init 裁剪为空 → 仍视为就绪（2026-08 审查修复）。"""
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        p = scripts / "placeholders.json"
        p.write_text('{"schema_version": 1, "placeholders": {}}', encoding="utf-8")
        monkeypatch.setattr(doc, "ROOT", tmp_path)
        ok, msg = doc.check_placeholders()
        assert ok is True
        assert "0 个占位符" in msg


class TestMainCLI:
    """测试 CLI 退出码。"""

    def test_main_returns_zero_on_ready(self):
        # 模板自身环境应全就绪
        assert doc.main([]) == 0
