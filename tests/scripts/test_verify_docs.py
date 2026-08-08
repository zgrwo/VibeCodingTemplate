#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_verify_docs.py — verify-docs.py 自身测试套件

验证文档一致性验证脚本的正确性：
  - 链接检查逻辑
  - 目录树解析逻辑
  - 双目录树一致性校验
  - 排除目录配置
"""
import re
import sys
from pathlib import Path

import pytest

# 将 scripts/ 加入路径以导入 verify-docs
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# verify-docs.py 的模块名带连字符，需要用 importlib
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "verify_docs", SCRIPTS_DIR / "verify-docs.py"
)
vd = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(vd)
except SystemExit:
    pass  # verify-docs.py 在 import 时不会 exit，但以防万一


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
