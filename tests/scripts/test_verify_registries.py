#!/usr/bin/env python3
"""
test_verify_registries.py — verify-registries.py 自身测试套件

验证多注册表一致性门禁脚本的正确性：
  - collect_keys 三类来源（json_keys / placeholder_scan / regex_extract）
  - check_group 死条目 FAIL / 未声明 WARN 语义
  - main CLI 退出码（纯 WARN→0，含 FAIL→1，配置缺失→1）
"""

import importlib.util
import json
import sys
from pathlib import Path

# 将 scripts/ 加入路径以导入 verify-registries
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location(
    "verify_registries", SCRIPTS_DIR / "verify-registries.py"
)
vr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vr)


class TestCollectKeys:
    """测试各类 registry 来源的键提取。"""

    def test_json_keys_valid(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text('{"placeholders": {"A": 1, "B": 2}}', encoding="utf-8")
        keys, errs = vr.collect_keys(
            {"type": "json_keys", "path": f.as_posix(), "key_path": "placeholders"}
        )
        assert errs == []
        assert keys == {"A", "B"}

    def test_json_keys_missing_file(self, tmp_path):
        keys, errs = vr.collect_keys(
            {"type": "json_keys", "path": str(tmp_path / "nope.json"), "key_path": "x"}
        )
        assert keys == set()
        assert any("[配置错误]" in e for e in errs)

    def test_json_keys_bad_key_path(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text('{"a": {"b": 1}}', encoding="utf-8")
        keys, errs = vr.collect_keys(
            {"type": "json_keys", "path": f.as_posix(), "key_path": "nope"}
        )
        assert keys == set()
        assert any("key_path" in e for e in errs)

    def test_placeholder_scan_finds_tokens(self, tmp_path):
        # 在临时目录建文件，绕过 EXCLUDED_DIRS
        f = tmp_path / "sample.md"
        f.write_text("参考 {{FOOX}} 与 {{BAR}} 两个占位符", encoding="utf-8")
        keys, errs = vr.collect_keys({"type": "placeholder_scan", "roots": [tmp_path.as_posix()]})
        assert errs == []
        assert keys == {"FOOX", "BAR"}

    def test_placeholder_scan_excludes_teaching_tokens(self, tmp_path):
        # 教学转义 token（A/B/FOO/NAME/X 等）不计入已使用集合，避免恒定 WARN 噪声（P3-2）
        f = tmp_path / "sample.md"
        f.write_text("参考 {{FOO}}、{{NAME}}、{{B}}、{{BAR}} 四个占位符", encoding="utf-8")
        keys, errs = vr.collect_keys({"type": "placeholder_scan", "roots": [tmp_path.as_posix()]})
        assert errs == []
        assert "FOO" not in keys
        assert "NAME" not in keys
        assert "B" not in keys  # B 来自 init-project.ps1 扫描注释（P3 补录，防恒定 WARN）
        assert keys == {"BAR"}

    def test_unknown_type(self):
        keys, errs = vr.collect_keys({"type": "bogus"})
        assert keys == set()
        assert any("未知" in e for e in errs)


class TestCheckGroup:
    """测试组对比的死条目/未声明语义。"""

    def _make_registry(self, tmp_path, keys: list[str], name: str) -> dict:
        f = tmp_path / f"{name}.json"
        f.write_text(json.dumps({"keys": dict.fromkeys(keys, 1)}), encoding="utf-8")
        return {"name": name, "type": "json_keys", "path": f.as_posix(), "key_path": "keys"}

    def test_consistent_group_no_problems(self, tmp_path):
        group = {
            "name": "G",
            "registries": [
                self._make_registry(tmp_path, ["A", "B"], "r1"),
                self._make_registry(tmp_path, ["A", "B"], "r2"),
            ],
        }
        assert vr.check_group(group) == []

    def test_dead_entry_is_fail(self, tmp_path):
        group = {
            "name": "G",
            "registries": [
                self._make_registry(tmp_path, ["A", "B"], "r1"),
                self._make_registry(tmp_path, ["A"], "r2"),
            ],
        }
        problems = vr.check_group(group)
        assert any(p.startswith("[FAIL]") and "B" in p for p in problems)

    def test_undeclared_is_warn(self, tmp_path):
        group = {
            "name": "G",
            "registries": [
                self._make_registry(tmp_path, ["A"], "r1"),
                self._make_registry(tmp_path, ["A", "C"], "r2"),
            ],
        }
        problems = vr.check_group(group)
        assert any(p.startswith("[WARN]") and "C" in p for p in problems)
        assert not any(p.startswith("[FAIL]") for p in problems)

    def test_single_registry_is_config_error(self, tmp_path):
        group = {"name": "G", "registries": [self._make_registry(tmp_path, ["A"], "r1")]}
        assert any("[配置错误]" in p for p in vr.check_group(group))


class TestMainCLI:
    """测试 CLI 入口退出码。"""

    def test_missing_config_returns_one(self, tmp_path):
        assert vr.main(["--config", str(tmp_path / "nope.json")]) == 1

    def test_single_registry_config_returns_one(self, tmp_path):
        cfg = tmp_path / "r.json"
        cfg.write_text(
            json.dumps(
                {
                    "groups": [
                        {
                            "name": "G",
                            "registries": [
                                {"name": "a", "type": "json_keys", "path": "x", "key_path": "k"},
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        # 单 registry → 配置错误 → 返回 1（配置错误硬失败）
        assert vr.main(["--config", cfg.as_posix()]) == 1

    def test_valid_placeholder_group_returns_zero(self):
        # 用真实默认配置跑一遍（应只有 WARN，无 FAIL → 0）
        assert vr.main([]) == 0
