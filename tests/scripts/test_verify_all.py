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


class TestFullVerifyStepParity:
    """全量验证入口三处实现的文档检查步骤集合必须一致（2026-10-11 新增）。

    背景：文档检查步骤清单同时存在于 `verify-all.py` / `verify-all.ps1` / `Makefile` 的
    `docs:` 目标（`.github/workflows/ci.yml` quality-gate 为第四处）。新增一个门禁脚本却只改一处
    即产生「本地绿、CI 红」或反向的静默分叉（tooling-pitfalls #26 py/ps1 双实现分叉）。本测试用
    三份独立产物互相比对 + 期望集合锚定（防三处同时为空导致的空心通过）。
    """

    EXPECTED = {
        "verify-docs.py",
        "verify-manual.py",
        "falsy-audit.py",
        "verify-registries.py",
        "verify-arch.py",
        "gen-doc-counts.py",
        "test-quality-guard.py",
    }

    def _py_doc_scripts(self, monkeypatch) -> set[str]:
        import io
        from contextlib import redirect_stdout

        calls: list[list[str]] = []
        monkeypatch.setattr(va, "run_step", lambda name, cmd, cwd=None: calls.append(cmd) or True)
        monkeypatch.setattr(va, "detect_build_system", lambda: (None, [], []))
        monkeypatch.setattr("sys.argv", ["verify-all.py"])
        with redirect_stdout(io.StringIO()):
            code = va.main()
        assert code == 0
        return {Path(cmd[1]).name for cmd in calls if len(cmd) > 1 and cmd[1].endswith(".py")}

    def _ps1_doc_scripts(self) -> set[str]:
        import re

        text = (SCRIPTS_DIR / "verify-all.ps1").read_text(encoding="utf-8")
        return set(re.findall(r"scripts\\([\w.\-]+\.py)", text))

    def _makefile_doc_scripts(self) -> set[str]:
        import re

        text = (SCRIPTS_DIR.parent / "Makefile").read_text(encoding="utf-8")
        block = re.search(r"^docs:\n((?:\t.*\n)+)", text, re.MULTILINE)
        assert block, "Makefile 缺少 docs: 目标（跨平台全量验证入口）"
        return set(re.findall(r"scripts/([\w.\-]+\.py)", block.group(1)))

    def test_expected_steps_present_in_python_entry(self, monkeypatch):
        assert self._py_doc_scripts(monkeypatch) >= self.EXPECTED

    def test_powershell_entry_matches_python_entry(self, monkeypatch):
        py_scripts = self._py_doc_scripts(monkeypatch)
        ps1_scripts = self._ps1_doc_scripts()
        only_py = sorted(py_scripts - ps1_scripts)
        only_ps1 = sorted(ps1_scripts - py_scripts)
        assert py_scripts == ps1_scripts, (
            f"verify-all.py 与 verify-all.ps1 步骤分叉：仅 py 有 {only_py}；仅 ps1 有 {only_ps1}"
        )

    def test_makefile_entry_matches_python_entry(self, monkeypatch):
        py_scripts = self._py_doc_scripts(monkeypatch)
        make_scripts = self._makefile_doc_scripts()
        assert py_scripts == make_scripts, (
            f"verify-all.py 与 Makefile docs: 目标分叉："
            f"仅 py 有 {sorted(py_scripts - make_scripts)}；"
            f"仅 Makefile 有 {sorted(make_scripts - py_scripts)}"
        )
