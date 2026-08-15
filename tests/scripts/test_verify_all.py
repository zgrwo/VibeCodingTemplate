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

_spec = importlib.util.spec_from_file_location("verify_all_mod", SCRIPTS_DIR / "verify-all.py")
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


class TestMainCLI:
    """main() 编排逻辑（2026-08 Max 审查 P2 补测：--quick 语义 / 失败即停 / 无构建系统）。"""

    def _run_main(self, monkeypatch, argv, run_step_results=None):
        import io
        from contextlib import redirect_stdout

        calls: list[list[str]] = []

        def fake_run_step(name, cmd, cwd=None):
            calls.append(cmd)
            if run_step_results is None:
                return True
            return run_step_results.pop(0) if run_step_results else True

        monkeypatch.setattr(va, "run_step", fake_run_step)
        monkeypatch.setattr(
            va,
            "detect_build_system",
            lambda: ("Python", ["python", "-m", "compileall", "-q", "src"], ["pytest-cmd"]),
        )
        monkeypatch.setattr("sys.argv", ["verify-all.py"] + argv)
        out = io.StringIO()
        with redirect_stdout(out):
            code = va.main()
        return code, calls, out.getvalue()

    def test_full_runs_all_doc_steps(self, monkeypatch):
        code, calls, _ = self._run_main(monkeypatch, [])
        assert code == 0
        flat = " ".join(" ".join(c) for c in calls)
        assert "pytest" in flat
        assert "verify-docs.py" in flat
        assert "verify-manual.py" in flat
        assert "falsy-audit.py" in flat
        assert "verify-registries.py" in flat

    def test_quick_skips_doc_steps(self, monkeypatch):
        code, calls, _ = self._run_main(monkeypatch, ["--quick"])
        assert code == 0
        flat = " ".join(" ".join(c) for c in calls)
        assert "pytest" in flat
        assert "verify-docs.py" not in flat

    def test_first_failure_stops_and_returns_one(self, monkeypatch):
        code, calls, _ = self._run_main(monkeypatch, [], run_step_results=[False])
        assert code == 1
        assert len(calls) == 1  # 任一步失败立即停止（break-on-first-failure）

    def test_no_build_system_skips_but_runs_docs(self, monkeypatch):
        import io
        from contextlib import redirect_stdout

        calls: list[list[str]] = []
        monkeypatch.setattr(va, "run_step", lambda name, cmd, cwd=None: calls.append(cmd) or True)
        monkeypatch.setattr(va, "detect_build_system", lambda: (None, [], []))
        monkeypatch.setattr("sys.argv", ["verify-all.py"])
        out = io.StringIO()
        with redirect_stdout(out):
            code = va.main()
        assert code == 0
        assert "[SKIP]" in out.getvalue()
        flat = " ".join(" ".join(c) for c in calls)
        assert "pytest" not in flat
        assert "verify-docs.py" in flat
