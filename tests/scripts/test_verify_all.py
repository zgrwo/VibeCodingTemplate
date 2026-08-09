"""test_verify_all.py — verify-all.py 自身测试套件

覆盖：
  - detect_build_system()：.NET / Python / 无构建系统三分支
  - run_step()：成功 / 非零退出 / 工具缺失失败
"""
import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location(
    "verify_all_mod", SCRIPTS_DIR / "verify-all.py"
)
va = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(va)


class TestDetectBuildSystem:
    def test_python_repo(self, tmp_path, monkeypatch):
        """含 pyproject.toml 且无 .sln → Python 构建命令。"""
        (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        monkeypatch.setattr(va, "ROOT", tmp_path)
        build_type, build_cmd, test_cmd = va.detect_build_system()
        assert build_type == "Python"
        assert build_cmd[0] == va.PYTHON
        assert "-m" in build_cmd and "compileall" in build_cmd
        assert "pytest" in test_cmd

    def test_dotnet_repo(self, tmp_path, monkeypatch):
        """含 .sln → .NET 构建命令（优先于 pyproject.toml）。"""
        (tmp_path / "App.sln").write_text("", encoding="utf-8")
        (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        monkeypatch.setattr(va, "ROOT", tmp_path)
        build_type, build_cmd, test_cmd = va.detect_build_system()
        assert build_type == ".NET"
        assert build_cmd[0] == "dotnet"
        assert "build" in build_cmd
        assert "Release" in build_cmd  # 与 verify-all.ps1 对齐（-c Release）
        assert any("App.sln" in c for c in build_cmd)

    def test_no_build_system(self, tmp_path, monkeypatch):
        """无 .sln / pyproject.toml → None, [], []（显式跳过不假装通过）。"""
        monkeypatch.setattr(va, "ROOT", tmp_path)
        assert va.detect_build_system() == (None, [], [])


class TestRunStep:
    def test_success(self):
        assert va.run_step("示例", [va.PYTHON, "-c", "pass"]) is True

    def test_nonzero_exit_fails(self):
        assert va.run_step("失败示例", [va.PYTHON, "-c", "import sys; sys.exit(3)"]) is False

    def test_missing_tool_fails(self):
        """工具不存在 → FileNotFoundError 被捕获并返回 False。"""
        assert va.run_step("缺失工具", ["definitely-not-a-real-cmd-xyz"]) is False
