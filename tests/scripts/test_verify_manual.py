"""test_verify_manual.py — verify-manual.py 自身测试套件

覆盖：
  - check() / cross_check() 的 PASS/FAIL 语义与容差
  - run_crossval() 的 crossval 缺失/为空 SKIP 路径
  - SELF_CHECK_RE 自校验模式检测
  - check_example_blocks 代码块标注/闭合检查
"""
import importlib.util
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

# 将 scripts/ 加入路径以导入 verify-manual
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location(
    "verify_manual_mod", SCRIPTS_DIR / "verify-manual.py"
)
vm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vm)
# 与 verify-manual.py 运行时一致：注册 verify_manual 别名，
# 使 crossval 测试脚本的 `from verify_manual import ...` 可解析
sys.modules.setdefault("verify_manual", vm)


class TestCheck:
    """确定性结果比对 check(name, actual, expected)。"""

    def setup_method(self):
        vm._PASS = 0
        vm._FAIL = 0

    def test_pass_on_equal(self):
        with redirect_stdout(io.StringIO()):
            vm.check("X.OK", 1.0, 1.0)
        assert vm._PASS == 1 and vm._FAIL == 0

    def test_fail_on_mismatch(self):
        with redirect_stdout(io.StringIO()):
            vm.check("X.BAD", 1.0, 2.0)
        assert vm._PASS == 0 and vm._FAIL == 1

    def test_zero_is_valid(self):
        """0 是有效值：check(X, 0, 0) 应为 PASS（非自校验，硬编码期望）。"""
        with redirect_stdout(io.StringIO()):
            vm.check("X.ZERO", 0, 0)
        assert vm._PASS == 1 and vm._FAIL == 0


class TestCrossCheck:
    """数值交叉验证 cross_check(name, actual, expected, tol)。"""

    def setup_method(self):
        vm._PASS = 0
        vm._FAIL = 0

    def test_within_tolerance_pass(self):
        with redirect_stdout(io.StringIO()):
            vm.cross_check("C.OK", 1.0 + 1e-12, 1.0, tol=1e-10)
        assert vm._PASS == 1 and vm._FAIL == 0

    def test_outside_tolerance_fail(self):
        with redirect_stdout(io.StringIO()):
            vm.cross_check("C.BAD", 1.0, 1.5, tol=1e-10)
        assert vm._PASS == 0 and vm._FAIL == 1

    def test_expected_none_is_fail(self):
        """期望值缺失（疑似自校验）必须 FAIL。"""
        with redirect_stdout(io.StringIO()):
            vm.cross_check("C.NONE", 1.0, None)
        assert vm._PASS == 0 and vm._FAIL == 1

    def test_scale_tolerance(self):
        """相对容差：大数值按 scale 放大容差。"""
        with redirect_stdout(io.StringIO()):
            vm.cross_check("C.SCALE", 1_000_000.0 + 1e-4, 1_000_000.0, tol=1e-10)
        assert vm._PASS == 1


class TestRunCrossval:
    """run_crossval() 的 SKIP 路径。"""

    def test_missing_dir_skips(self, tmp_path, monkeypatch):
        """crossval 目录缺失 → SKIP 且返回 True（不假装通过）。"""
        monkeypatch.setattr(vm, "CROSSVAL_DIR", tmp_path / "no-such-crossval")
        out = io.StringIO()
        with redirect_stdout(out):
            ok = vm.run_crossval()
        assert ok is True
        assert "[SKIP]" in out.getvalue()

    def test_empty_dir_skips(self, tmp_path, monkeypatch):
        """crossval 目录存在但为空 → SKIP。"""
        crossval = tmp_path / "crossval"
        crossval.mkdir()
        monkeypatch.setattr(vm, "CROSSVAL_DIR", crossval)
        out = io.StringIO()
        with redirect_stdout(out):
            ok = vm.run_crossval()
        assert ok is True
        assert "[SKIP]" in out.getvalue()

    def test_main_guard_script_fails(self, tmp_path, monkeypatch):
        """被 `if __name__ == "__main__"` 包裹的脚本产生 0 项校验 → 必须 FAIL（防门禁说谎）。"""
        crossval = tmp_path / "crossval"
        crossval.mkdir()
        (crossval / "bad.py").write_text(
            'from verify_manual import check\n'
            'if __name__ == "__main__":\n'
            '    check("G.BAD", 1.0, 2.0)\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(vm, "CROSSVAL_DIR", crossval)
        monkeypatch.setattr(vm, "_PASS", 0)
        monkeypatch.setattr(vm, "_FAIL", 0)
        out = io.StringIO()
        with redirect_stdout(out):
            ok = vm.run_crossval()
        assert ok is False
        assert "未产生任何校验项" in out.getvalue()

    def test_valid_script_passes(self, tmp_path, monkeypatch):
        """正常产生校验项的脚本 → PASS。"""
        crossval = tmp_path / "crossval"
        crossval.mkdir()
        (crossval / "good.py").write_text(
            'from verify_manual import check\n'
            'check("G.OK", 1.0, 1.0)\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(vm, "CROSSVAL_DIR", crossval)
        monkeypatch.setattr(vm, "_PASS", 0)
        monkeypatch.setattr(vm, "_FAIL", 0)
        out = io.StringIO()
        with redirect_stdout(out):
            ok = vm.run_crossval()
        assert ok is True
        assert "未产生任何校验项" not in out.getvalue()


class TestStaticChecks:
    """自校验模式与代码块检查。"""

    def test_self_check_regex_detects(self):
        """check(name, X, X) 模式必须被识别（自校验 = 永远 PASS）。"""
        assert vm.SELF_CHECK_RE.search('check("A.MEAN", mean, mean)') is not None

    def test_self_check_regex_ok_on_distinct(self):
        assert vm.SELF_CHECK_RE.search('check("A.MEAN", mean([1,2]), 1.5)') is None

    def test_check_example_blocks_balanced(self, tmp_path, monkeypatch):
        """合法手册（标注语言且闭合）→ 无问题。"""
        manual = tmp_path / "user-manual.md"
        manual.write_text(
            "```python\nx = 1\n```\n\n```vba\nDim i As Long\n```\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(vm, "MANUAL", manual)
        assert vm.check_example_blocks() == []

    def test_check_example_blocks_unclosed(self, tmp_path, monkeypatch):
        """未闭合代码块 → 报告问题。"""
        manual = tmp_path / "user-manual.md"
        manual.write_text("```python\nx = 1\n", encoding="utf-8")
        monkeypatch.setattr(vm, "MANUAL", manual)
        problems = vm.check_example_blocks()
        assert any("未闭合" in p for p in problems)

    def test_check_example_blocks_missing_lang(self, tmp_path, monkeypatch):
        """未标注语言的代码块 → 报告问题。"""
        manual = tmp_path / "user-manual.md"
        manual.write_text("```\nx = 1\n```\n", encoding="utf-8")
        monkeypatch.setattr(vm, "MANUAL", manual)
        problems = vm.check_example_blocks()
        assert any("未标注语言" in p for p in problems)


class TestMainCLI:
    """main() CLI 入口级测试：--check-only 与退出码。"""

    def test_check_only_returns_zero(self, monkeypatch):
        """--check-only 干净手册 → exit 0。"""
        import io
        from contextlib import redirect_stdout
        monkeypatch.setattr("sys.argv", ["verify-manual.py", "--check-only"])
        out = io.StringIO()
        with redirect_stdout(out):
            code = vm.main()
        assert code == 0
