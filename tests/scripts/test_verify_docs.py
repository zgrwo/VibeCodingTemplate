#!/usr/bin/env python3
"""
test_verify_docs.py — verify-docs.py 自身测试套件

验证文档一致性验证脚本的正确性：
  - 链接检查逻辑
  - 目录树解析逻辑
  - 双目录树一致性校验
  - 排除目录配置
"""

import contextlib
import importlib.util
import json
import re
import sys
from pathlib import Path

# 将 scripts/ 加入路径以导入 verify-docs
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location("verify_docs", SCRIPTS_DIR / "verify-docs.py")
vd = importlib.util.module_from_spec(_spec)
with contextlib.suppress(SystemExit):
    _spec.loader.exec_module(vd)  # verify-docs.py 在 import 时不会 exit，但以防万一


class TestExcludedDirs:
    """测试排除目录配置。"""

    def test_git_excluded(self):
        assert ".git" in vd.EXCLUDED_DIRS

    def test_logs_excluded(self):
        assert "logs" in vd.EXCLUDED_DIRS

    def test_ai_tool_dirs_excluded(self):
        assert ".claude" in vd.EXCLUDED_DIRS
        assert ".codegraph" in vd.EXCLUDED_DIRS
        assert ".qoder" in vd.EXCLUDED_DIRS


class TestLinkRegex:
    """测试 Markdown 链接正则。"""

    def test_standard_link_extracted(self):
        text = "see [docs](rules/context.md)"
        link_re = re.compile(r"\[[^\]]*\]\(([^)#]+)\)")
        matches = link_re.findall(text)
        assert "rules/context.md" in matches

    def test_external_link(self):
        text = "see [GitHub](https://github.com)"
        link_re = re.compile(r"\[[^\]]*\]\(([^)#]+)\)")
        matches = link_re.findall(text)
        assert "https://github.com" in matches

    def test_placeholder_link(self):
        text = "see [{{MODULE}}](rules/{{MODULE}}.md)"
        link_re = re.compile(r"\[[^\]]*\]\(([^)#]+)\)")
        matches = link_re.findall(text)
        assert "rules/{{MODULE}}.md" in matches


class TestTreeParsing:
    """测试目录树解析。"""

    def test_parse_top_dirs(self):
        """_parse_top_dirs 应从 project-structure.md 解析顶层目录。"""
        dirs = vd._parse_top_dirs()
        # 这些目录在实际项目结构中应该存在
        assert isinstance(dirs, list)
        # src 和 tests 应在目录树中
        if dirs:  # 如果 project-structure.md 存在
            assert "src" in dirs

    def test_parse_agents_top_dirs(self):
        """_parse_agents_top_dirs 应从 AGENTS.md 解析顶层目录。"""
        dirs = vd._parse_agents_top_dirs()
        assert isinstance(dirs, list)

    def test_trees_consistent(self):
        """project-structure.md 和 AGENTS.md 的顶层目录集应一致。"""
        ps_dirs = set(vd._parse_top_dirs())
        agents_dirs = set(vd._parse_agents_top_dirs())
        # 两棵树应该一致（双目录树防漂移）
        if ps_dirs and agents_dirs:
            assert ps_dirs == agents_dirs, (
                f"目录树不一致: project-structure={ps_dirs - agents_dirs}, "
                f"agents={agents_dirs - ps_dirs}"
            )


class TestCheckFunctions:
    """测试检查函数的返回类型。"""

    def test_check_dirs_returns_list(self):
        result = vd.check_dirs()
        assert isinstance(result, list)

    def test_check_links_returns_list(self):
        result = vd.check_links()
        assert isinstance(result, list)

    def test_check_backtick_paths_returns_list(self):
        result = vd.check_backtick_paths()
        assert isinstance(result, list)

    def test_check_agents_tree_returns_list(self):
        result = vd.check_agents_tree()
        assert isinstance(result, list)


class TestPatternLike:
    """测试模式串识别（反引号路径检查的辅助函数）。"""

    def test_placeholder_is_pattern(self):
        assert vd._is_pattern_like("{{MODULE}}")

    def test_normal_path_not_pattern(self):
        assert not vd._is_pattern_like("rules/context.md")

    def test_name_pattern_is_pattern(self):
        assert vd._is_pattern_like("0001-xxx.md")


class TestMainCLI:
    """main() CLI 入口级测试：--strict 接线与退出码。"""

    def test_main_returns_zero_on_clean(self, monkeypatch):
        """全绿时 main() 返回 0。"""
        import io
        from contextlib import redirect_stdout

        monkeypatch.setattr("sys.argv", ["verify-docs.py", "--strict"])
        out = io.StringIO()
        with redirect_stdout(out):
            code = vd.main()
        assert code == 0

    def test_check_bare_handlers_flag_clean(self, monkeypatch):
        """--check-bare-handlers 对仓库自身（docstring 教学文字）返回 0 不误报。"""
        import io
        from contextlib import redirect_stdout

        monkeypatch.setattr("sys.argv", ["verify-docs.py", "--check-bare-handlers"])
        out = io.StringIO()
        with redirect_stdout(out):
            code = vd.main()
        assert code == 0
        assert "无裸 catch / bare except" in out.getvalue()

    def test_check_bare_handlers_flag_detects(self, tmp_path, monkeypatch):
        """--check-bare-handlers 对含真实裸 except 的目录返回 1（检出）。"""
        import io
        from contextlib import redirect_stdout

        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "verify-x.py").write_text(
            "def f():\n    try:\n        pass\n    except:\n        pass\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        monkeypatch.setattr("sys.argv", ["verify-docs.py", "--check-bare-handlers"])
        out = io.StringIO()
        with redirect_stdout(out):
            code = vd.main()
        assert code == 1
        assert "裸 except" in out.getvalue()


class TestCheckFunctionsDetection:
    """检出型测试：构造破坏场景 → 断言问题被检出（非仅 return type）。"""

    def test_agents_tree_drift_detected(self, monkeypatch):
        """单边漂移：AGENTS.md 多声明一个目录 → 必须被 check_agents_tree 检出。"""
        monkeypatch.setattr(vd, "_parse_top_dirs", lambda: ["src", "tests"])
        monkeypatch.setattr(vd, "_parse_agents_top_dirs", lambda: ["src", "tests", "drifted"])
        problems = vd.check_agents_tree()
        assert any("目录树漂移" in p and "drifted" in p for p in problems)

    def test_agents_tree_clean_no_problems(self, monkeypatch):
        """双树一致 → 无目录树漂移问题。"""
        monkeypatch.setattr(vd, "_parse_top_dirs", lambda: ["src", "tests"])
        monkeypatch.setattr(vd, "_parse_agents_top_dirs", lambda: ["src", "tests"])
        problems = vd.check_agents_tree()
        assert not any("目录树漂移" in p for p in problems)


class TestSemanticConsistency:
    """测试语义交叉检查（档 A-A3：裸 catch / TODO / input 向量）。"""

    def test_bare_catch_detected(self, tmp_path, monkeypatch):
        """src/ 下含裸 catch { 的 C# 文件必须被检出。"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "bad.cs").write_text("try {} catch {}", encoding="utf-8")
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        problems = vd.check_semantic_consistency()
        assert any("裸 catch" in p and "bad.cs" in p for p in problems)

    def test_todo_in_doc_detected(self, tmp_path, monkeypatch):
        """文档中行首 TODO: 待办必须被检出。"""
        doc = tmp_path / "README.md"
        doc.write_text("# 标题\n\n- TODO: 未完成事项\n", encoding="utf-8")
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        monkeypatch.setattr(vd, "DOC_FILES", ["README.md"])
        problems = vd.check_semantic_consistency()
        assert any("TODO" in p for p in problems)

    def test_input_in_ci_script_detected(self, tmp_path, monkeypatch):
        """CI 验证脚本中裸 input() 必须被检出。"""
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "verify-x.py").write_text('x = input(">")', encoding="utf-8")
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        problems = vd.check_semantic_consistency()
        assert any("input" in p for p in problems)

    def test_single_line_docstring_does_not_hide_bare_except(self, tmp_path, monkeypatch):
        """单行 docstring 后跟裸 except: 必须检出（2026-08 Max 审查 P1 回归：
        原 docstring 状态机每行只翻转一次，单行 `\"\"\"...\"\"\"` 后真实代码被跳过漏检）。"""
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "verify-x.py").write_text(
            '"""module doc."""\ndef f():\n    try:\n        pass\n    except:\n        pass\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        problems = vd.check_semantic_consistency()
        assert any("裸 except" in p for p in problems)

    def test_docstring_mentions_except_not_flagged(self, tmp_path, monkeypatch):
        """docstring 教学文字含 except: 不误报（跳过 docstring 的加固点）。"""
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "verify-y.py").write_text(
            '"""禁止裸 except: 捕获（教学文字）。"""\nx = 1\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        problems = vd.check_semantic_consistency()
        assert not any("裸 except" in p for p in problems)

    def test_cs_comment_catch_not_flagged(self, tmp_path, monkeypatch):
        """C# 注释内 catch { 不误报（// 与 /* */ 剥离）；真实裸 catch {} 仍检出。"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "ok.cs").write_text(
            "// catch { 教学文字\n"
            "/* 块注释 catch { 教学 */\n"
            "class C { void M() { try {} catch {} } }\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        problems = vd.check_semantic_consistency()
        assert any("裸 catch" in p for p in problems)  # 第 3 行真实裸 catch
        assert not any(p.endswith(":1") for p in problems)  # 行注释不误报
        assert not any(p.endswith(":2") for p in problems)  # 块注释不误报


class TestVersionConsistency:
    """版本号 SSOT 一致性门禁（P4 修复：防 manifest/pyproject/CHANGELOG 漂移）。"""

    def _setup(self, tmp_path, monkeypatch, manifest_ver, pyproject_ver, changelog_ver):
        (tmp_path / ".release-please-manifest.json").write_text(
            json.dumps({".": manifest_ver}), encoding="utf-8"
        )
        (tmp_path / "pyproject.toml").write_text(
            f'[project]\nversion = "{pyproject_ver}"\n', encoding="utf-8"
        )
        if changelog_ver:
            (tmp_path / "CHANGELOG.md").write_text(
                f"## [Unreleased]\n\n## [{changelog_ver}](https://github.com/x/y)\n",
                encoding="utf-8",
            )
        monkeypatch.setattr(vd, "ROOT", tmp_path)

    def test_consistent_versions_pass(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, "0.1.2", "0.1.2", "0.1.2")
        assert vd.check_version_consistency() == []

    def test_manifest_pyproject_mismatch_detected(self, tmp_path, monkeypatch):
        """manifest 0.1.2 vs pyproject 0.1.0 → 检出（曾真实发生的漂移形态）。"""
        self._setup(tmp_path, monkeypatch, "0.1.2", "0.1.0", "0.1.2")
        problems = vd.check_version_consistency()
        assert any("版本漂移" in p and "pyproject.toml" in p for p in problems)

    def test_manifest_changelog_mismatch_detected(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, "0.1.2", "0.1.2", "0.1.1")
        problems = vd.check_version_consistency()
        assert any("版本漂移" in p and "CHANGELOG" in p for p in problems)

    def test_missing_manifest_skips(self, tmp_path, monkeypatch):
        """无 release-please manifest（未接入/非发布项目）→ 不强制。"""
        (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1.0"\n', encoding="utf-8")
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        assert vd.check_version_consistency() == []

    def test_missing_pyproject_skips(self, tmp_path, monkeypatch):
        """非 Python 项目（无 pyproject.toml）→ 不强制。"""
        (tmp_path / ".release-please-manifest.json").write_text('{".": "0.1.2"}', encoding="utf-8")
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        assert vd.check_version_consistency() == []


class TestHardGateDetection:
    """CI 硬门禁的检出行为测试（2026-08 Max 审查 P2 补测：
    此前断链/反引号/未声明仅弱断言 isinstance(list)）。"""

    def _setup(self, tmp_path, monkeypatch, doc_name, doc_content):
        (tmp_path / doc_name).write_text(doc_content, encoding="utf-8")
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        monkeypatch.setattr(vd, "DOC_FILES", [doc_name])

    def test_check_links_detects_broken_link(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, "README.md", "see [x](missing.md)")
        problems = vd.check_links()
        assert any("[断链]" in p and "missing.md" in p for p in problems)

    def test_check_links_clean(self, tmp_path, monkeypatch):
        (tmp_path / "target.md").write_text("", encoding="utf-8")
        self._setup(tmp_path, monkeypatch, "README.md", "see [x](target.md)")
        assert vd.check_links() == []

    def test_check_backtick_paths_detects_dead_path(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, "README.md", "用 `scripts/nope.py` 做 X")
        problems = vd.check_backtick_paths()
        assert any("反引号路径失效" in p and "nope.py" in p for p in problems)

    def test_check_backtick_paths_clean(self, tmp_path, monkeypatch):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "ok.py").write_text("", encoding="utf-8")
        self._setup(tmp_path, monkeypatch, "README.md", "用 `scripts/ok.py` 做 X")
        assert vd.check_backtick_paths() == []

    def test_check_undeclared_detects_root_file(self, tmp_path, monkeypatch):
        (tmp_path / "extra.txt").write_text("", encoding="utf-8")
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        monkeypatch.setattr(vd, "_parse_top_entries", lambda: ["src", "tests"])
        problems = vd.check_undeclared(strict=True)
        assert any("未声明文件" in p and "extra.txt" in p for p in problems)

    def test_check_undeclared_non_strict_skips(self, tmp_path, monkeypatch):
        (tmp_path / "extra.txt").write_text("", encoding="utf-8")
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        monkeypatch.setattr(vd, "_parse_top_entries", lambda: ["src", "tests"])
        assert vd.check_undeclared(strict=False) == []

    def test_check_subdir_undeclared_detects_child(self, tmp_path, monkeypatch):
        rules = tmp_path / "rules"
        rules.mkdir()
        (rules / "orphan.md").write_text("", encoding="utf-8")
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        monkeypatch.setattr(vd, "_parse_nested_files", lambda: {"rules": {"known.md"}})
        problems = vd.check_subdir_undeclared(strict=True)
        assert any("未声明文件" in p and "orphan.md" in p for p in problems)

    def test_check_dirs_detects_missing_declared(self, tmp_path, monkeypatch):
        monkeypatch.setattr(vd, "ROOT", tmp_path)
        monkeypatch.setattr(vd, "_parse_top_dirs", lambda: ["src", "ghost"])
        problems = vd.check_dirs()
        assert any("[缺失目录]" in p and "ghost" in p for p in problems)


class TestExcludedDirsSSOT:
    """EXCLUDED_DIRS 与 _excluded_dirs.py 基线的收敛断言（2026-08 Max 审查：防 SSOT 回归）。"""

    def test_verify_docs_equals_base(self):
        from _excluded_dirs import BASE_EXCLUDED_DIRS

        assert set(BASE_EXCLUDED_DIRS) == vd.EXCLUDED_DIRS

    def test_registries_base_plus_purpose_extras(self):
        import contextlib as _ctx
        import importlib.util as _ilu

        from _excluded_dirs import BASE_EXCLUDED_DIRS

        _spec = _ilu.spec_from_file_location(
            "verify_registries", SCRIPTS_DIR / "verify-registries.py"
        )
        _vr = _ilu.module_from_spec(_spec)
        with _ctx.suppress(SystemExit):
            _spec.loader.exec_module(_vr)
        assert set(BASE_EXCLUDED_DIRS) | {"build", "benchmarks", "tests"} == _vr.EXCLUDED_DIRS
