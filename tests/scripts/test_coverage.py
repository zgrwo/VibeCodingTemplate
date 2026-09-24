#!/usr/bin/env python3
"""
test_coverage.py — coverage.py 自身测试套件

验证覆盖率门禁入口的正确性：
  - pyproject [tool.coverage] 配置解析（source / fail_under / 缺失回退）
  - 旧产物清理（.coverage / coverage.xml / htmlcov）
  - pytest-cov 命令构造（纯函数）
  - main CLI：配置注入、CLI 覆盖、工具缺失显式失败、退出码透传
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location("coverage_guard", SCRIPTS_DIR / "coverage.py")
cv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cv)


def _write_pyproject(tmp_path, source='["mysrc"]', fail_under="42"):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.coverage.run]\n"
        f"source = {source}\n"
        "\n"
        "[tool.coverage.report]\n"
        f"fail_under = {fail_under}\n",
        encoding="utf-8",
    )


class TestReadPyprojectConfig:
    """配置解析。"""

    def test_reads_source_and_threshold(self, tmp_path):
        _write_pyproject(tmp_path)
        sources, fail_under = cv.read_pyproject_config(tmp_path / "pyproject.toml")
        assert sources == ["mysrc"]
        assert fail_under == 42.0

    def test_multiple_sources(self, tmp_path):
        _write_pyproject(tmp_path, source='["src", "lib"]')
        sources, _ = cv.read_pyproject_config(tmp_path / "pyproject.toml")
        assert sources == ["src", "lib"]

    def test_missing_file_returns_defaults(self, tmp_path):
        sources, fail_under = cv.read_pyproject_config(tmp_path / "nope.toml")
        assert sources == []
        assert fail_under is None

    def test_no_coverage_section_returns_defaults(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
        sources, fail_under = cv.read_pyproject_config(tmp_path / "pyproject.toml")
        assert sources == []
        assert fail_under is None


class TestCleanArtifacts:
    """旧产物清理。"""

    def test_removes_all_stale_artifacts(self, tmp_path):
        (tmp_path / ".coverage").write_text("stale", encoding="utf-8")
        (tmp_path / "coverage.xml").write_text("stale", encoding="utf-8")
        (tmp_path / "htmlcov").mkdir()
        (tmp_path / "htmlcov" / "index.html").write_text("stale", encoding="utf-8")
        removed = cv.clean_artifacts(tmp_path)
        assert sorted(removed) == [".coverage", "coverage.xml", "htmlcov/"]
        assert not (tmp_path / ".coverage").exists()
        assert not (tmp_path / "htmlcov").exists()

    def test_clean_when_nothing_to_remove(self, tmp_path):
        assert cv.clean_artifacts(tmp_path) == []


class TestBuildPytestCmd:
    """命令构造（纯函数）。"""

    def test_includes_sources_and_threshold(self):
        cmd = cv.build_pytest_cmd("py", ["scripts"], 80, xml=False, html=False)
        assert "--cov=scripts" in cmd
        assert "--cov-fail-under=80" in cmd
        assert "--cov-report=term-missing" in cmd

    def test_multiple_sources_each_get_cov_flag(self):
        cmd = cv.build_pytest_cmd("py", ["src", "lib"], 85, xml=False, html=False)
        assert "--cov=src" in cmd
        assert "--cov=lib" in cmd

    def test_optional_reports(self):
        cmd = cv.build_pytest_cmd("py", ["src"], None, xml=True, html=True)
        assert "--cov-report=xml" in cmd
        assert "--cov-report=html" in cmd
        assert not any(c.startswith("--cov-fail-under") for c in cmd)

    def test_fractional_threshold_formatted(self):
        cmd = cv.build_pytest_cmd("py", ["src"], 87.5, xml=False, html=False)
        assert "--cov-fail-under=87.5" in cmd


class TestMainCLI:
    """main 编排：配置注入 / CLI 覆盖 / 失败路径。"""

    def _patch_run(self, monkeypatch, returncode):
        captured = {}

        def fake_run(cmd, cwd=None):
            captured["cmd"] = cmd
            captured["cwd"] = cwd
            return subprocess.CompletedProcess(cmd, returncode)

        monkeypatch.setattr(cv.subprocess, "run", fake_run)
        return captured

    def test_pyproject_config_drives_command(self, tmp_path, monkeypatch):
        _write_pyproject(tmp_path)
        monkeypatch.setattr(cv, "ROOT", tmp_path)
        captured = self._patch_run(monkeypatch, 0)
        assert cv.main([]) == 0
        assert "--cov=mysrc" in captured["cmd"]
        assert "--cov-fail-under=42" in captured["cmd"]
        assert captured["cwd"] == tmp_path

    def test_cli_overrides_pyproject(self, tmp_path, monkeypatch):
        _write_pyproject(tmp_path)
        monkeypatch.setattr(cv, "ROOT", tmp_path)
        captured = self._patch_run(monkeypatch, 0)
        assert cv.main(["--source", "src", "--fail-under", "99"]) == 0
        assert "--cov=src" in captured["cmd"]
        assert "--cov-fail-under=99" in captured["cmd"]

    def test_failure_exit_code_passthrough(self, tmp_path, monkeypatch):
        _write_pyproject(tmp_path)
        monkeypatch.setattr(cv, "ROOT", tmp_path)
        self._patch_run(monkeypatch, 1)
        assert cv.main([]) == 1

    def test_missing_pytest_cov_fails_explicitly(self, monkeypatch, capsys):
        monkeypatch.setattr(cv.importlib.util, "find_spec", lambda name: None)
        assert cv.main([]) == 1
        assert "pytest-cov 未安装" in capsys.readouterr().out
