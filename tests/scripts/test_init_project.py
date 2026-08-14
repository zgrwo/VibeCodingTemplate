"""test_init_project.py — init-project.py 自身测试套件

覆盖：
  - load_manifest()：有效 / 缺失 / JSON 损坏回退
  - scan_placeholders()：仅识别大写占位符
  - get_placeholder_value()：values > auto > default > name.lower() 优先级
  - copy_template()：跳过 .git/.coverage、清理缓存目录
  - replace_placeholders()：字节级替换保留 CRLF、跳过 binary 后缀
  - build_replacements()：全量占位符生成
  - _strip_template_only_blocks() / strip_template_only_sections()：TEMPLATE_ONLY 段落裁剪
"""
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location(
    "init_project_mod", SCRIPTS_DIR / "init-project.py"
)
ip = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ip)


class TestLoadManifest:
    def test_valid(self, tmp_path, monkeypatch):
        manifest = tmp_path / "placeholders.json"
        manifest.write_text(
            '{"placeholders": {"PROJECT_NAME": {"category": "core", "test": "App"}}}',
            encoding="utf-8",
        )
        monkeypatch.setattr(ip, "PLACEHOLDERS_JSON", manifest)
        assert ip.load_manifest() == {
            "PROJECT_NAME": {"category": "core", "test": "App"}
        }

    def test_missing_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ip, "PLACEHOLDERS_JSON", tmp_path / "nope.json")
        assert ip.load_manifest() == {}

    def test_corrupt_returns_empty(self, tmp_path, monkeypatch):
        manifest = tmp_path / "placeholders.json"
        manifest.write_text("{ not valid json", encoding="utf-8")
        monkeypatch.setattr(ip, "PLACEHOLDERS_JSON", manifest)
        assert ip.load_manifest() == {}


class TestScanPlaceholders:
    def test_finds_uppercase_only(self):
        """{{PROJECT_NAME}} 识别；{Name} 与 {{name}}（小写）不应被匹配。"""
        text = "a {{PROJECT_NAME}} b {Name} c {{name}} d {{X1_}}"
        assert ip.scan_placeholders(text) == ["PROJECT_NAME", "X1_"]

    def test_dedup(self):
        assert ip.scan_placeholders("{{A}} {{A}} {{B}}") == ["A", "B"]


class TestGetPlaceholderValue:
    MANIFEST = {
        "CORE_A": {"category": "core", "prompt": "?", "default": "dflt"},
        "AUTO_D": {"category": "auto", "rule": "year"},
        "CONT": {"category": "content"},
        "ONLY_DEFAULT": {"category": "core", "default": "def"},
    }

    def test_values_priority(self):
        got = ip.get_placeholder_value("CORE_A", self.MANIFEST, {"CORE_A": "given"}, False)
        assert got == "given"

    def test_auto_rule(self):
        val = ip.get_placeholder_value("AUTO_D", self.MANIFEST, {}, False)
        assert len(val) == 4 and val.isdigit()  # year → 4 位数字

    def test_default(self):
        assert ip.get_placeholder_value("ONLY_DEFAULT", self.MANIFEST, {}, False) == "def"

    def test_content_falls_back_to_lower(self):
        assert ip.get_placeholder_value("CONT", self.MANIFEST, {}, False) == "cont"


class TestCopyTemplate:
    def _make_template(self, tmp_path):
        """构造小型模板夹具：文件 + 跳过项 + 缓存目录。"""
        tpl = tmp_path / "tpl"
        tpl.mkdir()
        (tpl / "README.md").write_text("hi", encoding="utf-8")
        (tpl / ".git").mkdir()  # 应跳过
        (tpl / "src").mkdir()
        (tpl / "src" / "main.py").write_text("x", encoding="utf-8")
        (tpl / "src" / "__pycache__").mkdir()  # 应清理
        (tpl / ".coverage").write_text("x", encoding="utf-8")  # 应跳过
        return tpl

    def test_skips_git_and_coverage_cleans_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ip, "TEMPLATE_ROOT", self._make_template(tmp_path))
        target = tmp_path / "out"
        copied = ip.copy_template(target)
        assert "README.md" in copied
        assert any(p.replace("\\", "/") == "src/main.py" for p in copied)
        assert not (target / ".git").exists()
        assert not (target / ".coverage").exists()
        assert not (target / "src" / "__pycache__").exists()

    def test_rejects_inside_target(self, tmp_path, monkeypatch):
        """target 位于模板仓库内部 → 拒绝（防自删除）。"""
        tpl = self._make_template(tmp_path)
        monkeypatch.setattr(ip, "TEMPLATE_ROOT", tpl)
        with pytest.raises(SystemExit):
            ip.copy_template(tpl / "subdir")

    def test_rejects_ancestor_target(self, tmp_path, monkeypatch):
        """target 是模板仓库的祖先 → 拒绝（防递归删除模板与同级项目）。"""
        tpl = self._make_template(tmp_path)
        monkeypatch.setattr(ip, "TEMPLATE_ROOT", tpl)
        with pytest.raises(SystemExit):
            ip.copy_template(tmp_path)  # tmp_path 是 tpl 的父目录


class TestReplacePlaceholders:
    def test_replaces_and_preserves_crlf(self, tmp_path):
        """字节级替换：CRLF 换行必须原样保留（Windows 模板文件）。"""
        f = tmp_path / "AGENTS.md"
        f.write_bytes(b"# {{PROJECT_NAME}}\r\nsecond line {{PROJECT_NAME}}\r\n")
        replaced, remaining = ip.replace_placeholders(
            tmp_path, {"PROJECT_NAME": "MyApp"}
        )
        assert replaced == 1
        assert remaining == 0
        raw = f.read_bytes()
        assert raw == b"# MyApp\r\nsecond line MyApp\r\n"

    def test_binary_suffix_skipped(self, tmp_path):
        """.pyc 后缀文件不参与替换（防损坏二进制）。"""
        f = tmp_path / "data.pyc"
        f.write_bytes(b"{{PROJECT_NAME}}")
        replaced, remaining = ip.replace_placeholders(
            tmp_path, {"PROJECT_NAME": "MyApp"}
        )
        assert replaced == 0
        assert remaining == 0
        assert f.read_bytes() == b"{{PROJECT_NAME}}"

    def test_missing_placeholder_counts_remaining(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("{{NOT_PROVIDED}}", encoding="utf-8")
        replaced, remaining = ip.replace_placeholders(tmp_path, {})
        assert replaced == 0
        assert remaining == 1


class TestBuildReplacements:
    def test_returns_mapping_for_registered(self, tmp_path):
        (tmp_path / "f.txt").write_text("{{PROJECT_NAME}} {{CONT}}", encoding="utf-8")
        repl, undeclared = ip.build_replacements(
            tmp_path, {"PROJECT_NAME": {"category": "core", "test": "App"}}, {}, False
        )
        assert repl["PROJECT_NAME"] == "project_name"  # 无默认值 core → name.lower()
        # CONT 未登记 → 归入 undeclared，保留原样（防元占位符污染）
        assert "CONT" not in repl
        assert "CONT" in undeclared

    def test_undeclared_preserved_not_replaced(self, tmp_path):
        """未登记占位符必须保留原样：init 生成的文档中 {{UPPER}}/{{X}} 不被污染。"""
        (tmp_path / "f.txt").write_text("{{UPPER}} {{PROJECT_NAME}}", encoding="utf-8")
        repl, undeclared = ip.build_replacements(
            tmp_path, {"PROJECT_NAME": {"category": "core", "test": "App"}}, {}, False
        )
        assert "UPPER" in undeclared
        assert "UPPER" not in repl
        replaced, remaining = ip.replace_placeholders(tmp_path, repl, undeclared)
        # UPPER 保留原样且不计入 remaining；PROJECT_NAME 被替换
        assert remaining == 0
        assert "{{UPPER}}" in (tmp_path / "f.txt").read_text(encoding="utf-8")


class TestStripTemplateOnly:
    """TEMPLATE_ONLY 标记段落裁剪：模板专属内容不进入新项目。"""

    def test_midfile_block_removed_preserves_surrounding(self):
        data = (
            b"# keep\n\n"
            b"<!-- TEMPLATE_ONLY_START -->\n"
            b"## drop me\n"
            b"- [ ] template only\n"
            b"<!-- TEMPLATE_ONLY_END -->\n"
            b"# after\n"
        )
        assert ip._strip_template_only_blocks(data) == b"# keep\n\n# after\n"

    def test_eof_block_trims_leftover_blank_line(self):
        """模板专属段落位于文件末尾时，删除后裁剪遗留的空行。"""
        data = (
            b"keep\n"
            b"\n"
            b"<!-- TEMPLATE_ONLY_START -->\n"
            b"## some template-only section\n"
            b"- [ ] x\n"
            b"<!-- TEMPLATE_ONLY_END -->\n"
        )
        assert ip._strip_template_only_blocks(data) == b"keep\n"

    def test_preserves_crlf(self):
        """CRLF 文件：删除段落且不把收尾换行归一化为 LF。"""
        data = (
            b"keep\r\n"
            b"<!-- TEMPLATE_ONLY_START -->\r\n"
            b"drop\r\n"
            b"<!-- TEMPLATE_ONLY_END -->\r\n"
            b"after\r\n"
        )
        assert ip._strip_template_only_blocks(data) == b"keep\r\nafter\r\n"

    def test_unclosed_marker_preserved(self):
        """未闭合标记（有 START 无 END）→ 整段保留，防误删文件后半部分。"""
        data = b"keep\n<!-- TEMPLATE_ONLY_START -->\ndrop\n"
        assert ip._strip_template_only_blocks(data) == data

    def test_marker_literals_in_note_do_not_split_section(self):
        """段内说明引用标记字面量：深度计数把成对字面量当嵌套，不中途截断段落。"""
        data = (
            b"keep\n"
            b"<!-- TEMPLATE_ONLY_START -->\n"
            b"> note quotes <!-- TEMPLATE_ONLY_START --> and <!-- TEMPLATE_ONLY_END -->\n"
            b"## drop\n"
            b"<!-- TEMPLATE_ONLY_END -->\n"
            b"after\n"
        )
        assert ip._strip_template_only_blocks(data) == b"keep\nafter\n"

    def test_multiple_blocks_all_removed(self):
        data = (
            b"a\n"
            b"<!-- TEMPLATE_ONLY_START -->\n"
            b"x\n"
            b"<!-- TEMPLATE_ONLY_END -->\n"
            b"b\n"
            b"<!-- TEMPLATE_ONLY_START -->\n"
            b"y\n"
            b"<!-- TEMPLATE_ONLY_END -->\n"
            b"c\n"
        )
        assert ip._strip_template_only_blocks(data) == b"a\nb\nc\n"

    def test_no_markers_unchanged(self):
        data = b"a\nb\n"
        assert ip._strip_template_only_blocks(data) == data

    def test_strip_sections_walks_md_only(self, tmp_path):
        """strip_template_only_sections 只处理 .md，且跳过 tests/ 夹具目录。"""
        (tmp_path / "README.md").write_bytes(
            b"keep\n<!-- TEMPLATE_ONLY_START -->\ndrop\n<!-- TEMPLATE_ONLY_END -->\n"
        )
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "README.md").write_bytes(
            b"keep\n<!-- TEMPLATE_ONLY_START -->\ndrop\n<!-- TEMPLATE_ONLY_END -->\n"
        )
        (tmp_path / "data.py").write_bytes(
            b"keep\n<!-- TEMPLATE_ONLY_START -->\ndrop\n<!-- TEMPLATE_ONLY_END -->\n"
        )
        modified = ip.strip_template_only_sections(tmp_path)
        assert modified == 1
        assert (tmp_path / "README.md").read_bytes() == b"keep\n"
        assert (tests / "README.md").read_bytes().startswith(
            b"keep\n<!-- TEMPLATE_ONLY_START -->"
        )
        assert b"<!-- TEMPLATE_ONLY_START -->" in (tmp_path / "data.py").read_bytes()


class TestMainCLI:
    """main() CLI 入口级测试：目标目录校验与 --force 对齐 ps1。"""

    def _run(self, monkeypatch, argv):
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        monkeypatch.setattr("sys.argv", ["init-project.py"] + argv)
        with redirect_stdout(out):
            code = ip.main()
        return code, out.getvalue()

    def test_nonempty_target_rejected(self, monkeypatch, tmp_path):
        """非空目标目录 → exit 1（防覆盖已存在项目）。"""
        target = tmp_path / "proj"
        target.mkdir()
        (target / "existing.txt").write_text("x", encoding="utf-8")
        code, out = self._run(monkeypatch, [str(target), "--non-interactive"])
        assert code == 1
        assert "目标目录非空" in out

    def test_force_overrides_nonempty(self, monkeypatch, tmp_path):
        """--force 允许覆盖非空目标（与 init-project.ps1 -Force 对齐）。"""
        target = tmp_path / "proj"
        target.mkdir()
        (target / "existing.txt").write_text("x", encoding="utf-8")
        code, _ = self._run(monkeypatch, [str(target), "--non-interactive", "--force"])
        assert code == 0
        assert (target / "AGENTS.md").exists()

    def test_rejects_file_target(self, monkeypatch, tmp_path):
        """文件目标 → exit 1（与 --force 无关，镜像 init-project.py 拒绝文件）。"""
        f = tmp_path / "important.md"
        f.write_text("precious", encoding="utf-8")
        code, out = self._run(monkeypatch, [str(f), "--non-interactive", "--force"])
        assert code == 1
        assert "文件" in out

    def test_rejects_ancestor_target(self, monkeypatch, tmp_path):
        """target 为模板仓库祖先 → exit 1（防递归删除模板）。"""
        monkeypatch.setattr(ip, "TEMPLATE_ROOT", tmp_path / "tpl")
        code, out = self._run(monkeypatch, [str(tmp_path), "--non-interactive"])
        assert code == 1
        assert "模板仓库" in out
