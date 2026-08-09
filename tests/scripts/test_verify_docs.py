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
import re
import sys
from pathlib import Path

# 将 scripts/ 加入路径以导入 verify-docs
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location(
    "verify_docs", SCRIPTS_DIR / "verify-docs.py"
)
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


class TestCheckFunctionsDetection:
    """检出型测试：构造破坏场景 → 断言问题被检出（非仅 return type）。"""

    def test_agents_tree_drift_detected(self, monkeypatch):
        """单边漂移：AGENTS.md 多声明一个目录 → 必须被 check_agents_tree 检出。"""
        monkeypatch.setattr(
            vd, "_parse_top_dirs", lambda: ["src", "tests"]
        )
        monkeypatch.setattr(
            vd, "_parse_agents_top_dirs", lambda: ["src", "tests", "drifted"]
        )
        problems = vd.check_agents_tree()
        assert any("目录树漂移" in p and "drifted" in p for p in problems)

    def test_agents_tree_clean_no_problems(self, monkeypatch):
        """双树一致 → 无目录树漂移问题。"""
        monkeypatch.setattr(
            vd, "_parse_top_dirs", lambda: ["src", "tests"]
        )
        monkeypatch.setattr(
            vd, "_parse_agents_top_dirs", lambda: ["src", "tests"]
        )
        problems = vd.check_agents_tree()
        assert not any("目录树漂移" in p for p in problems)
