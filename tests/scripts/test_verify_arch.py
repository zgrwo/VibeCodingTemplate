#!/usr/bin/env python3
"""
test_verify_arch.py — verify-arch.py 自身测试套件

验证架构边界门禁的正确性：
  - 配置加载/校验（缺文件、坏 JSON、schema 版本、字段缺失）
  - 规则检查（import / from import / 模块前缀 / exclude / 空匹配防说谎）
  - main CLI 退出码（空规则通过、违规失败）
"""

import importlib.util
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_spec = importlib.util.spec_from_file_location("verify_arch", SCRIPTS_DIR / "verify-arch.py")
va = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(va)


def _write_config(tmp_path, rules):
    cfg = tmp_path / "architecture.json"
    cfg.write_text(
        json.dumps({"schema_version": 1, "rules": rules}, ensure_ascii=False),
        encoding="utf-8",
    )
    return cfg


def _write_src(tmp_path, rel: str, body: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


class TestLoadConfig:
    """配置加载与校验。"""

    def test_missing_file_returns_error(self, tmp_path):
        config, errors = va.load_config(tmp_path / "nope.json")
        assert config is None
        assert any("不存在" in e for e in errors)

    def test_invalid_json_returns_error(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        config, errors = va.load_config(bad)
        assert config is None
        assert any("无法解析" in e for e in errors)

    def test_wrong_schema_version_returns_error(self, tmp_path):
        cfg = tmp_path / "v2.json"
        cfg.write_text(json.dumps({"schema_version": 2, "rules": []}), encoding="utf-8")
        config, errors = va.load_config(cfg)
        assert config is None
        assert any("schema_version" in e for e in errors)

    def test_empty_rules_valid(self, tmp_path):
        config, errors = va.load_config(_write_config(tmp_path, []))
        assert config["schema_version"] == 1
        assert len(errors) == 0

    def test_rule_missing_forbid_imports_detected(self, tmp_path):
        cfg = _write_config(tmp_path, [{"name": "x", "source": ["src/**/*.py"]}])
        _config, errors = va.load_config(cfg)
        assert any("forbid_imports" in e for e in errors)


class TestCheckRule:
    """规则检查行为。"""

    def test_forbidden_import_detected(self, tmp_path, monkeypatch):
        _write_src(tmp_path, "src/core/a.py", "import flask\n")
        monkeypatch.setattr(va, "ROOT", tmp_path)
        problems = va.check_rule(
            {"name": "核心零框架", "source": ["src/core/**/*.py"], "forbid_imports": ["flask"]}
        )
        assert any("架构违规" in p and "flask" in p for p in problems)

    def test_forbidden_from_import_detected(self, tmp_path, monkeypatch):
        _write_src(tmp_path, "src/core/b.py", "from flask import Blueprint\n")
        monkeypatch.setattr(va, "ROOT", tmp_path)
        problems = va.check_rule(
            {"name": "核心零框架", "source": ["src/**/*.py"], "forbid_imports": ["flask"]}
        )
        assert len(problems) == 1

    def test_submodule_prefix_detected(self, tmp_path, monkeypatch):
        _write_src(tmp_path, "src/core/c.py", "import flask.helpers\n")
        monkeypatch.setattr(va, "ROOT", tmp_path)
        problems = va.check_rule(
            {"name": "核心零框架", "source": ["src/**/*.py"], "forbid_imports": ["flask"]}
        )
        assert len(problems) == 1

    def test_similar_name_not_false_positive(self, tmp_path, monkeypatch):
        # flasky 不以 "flask." 为前缀，不得误判
        _write_src(tmp_path, "src/core/d.py", "import flasky\n")
        monkeypatch.setattr(va, "ROOT", tmp_path)
        problems = va.check_rule(
            {"name": "核心零框架", "source": ["src/**/*.py"], "forbid_imports": ["flask"]}
        )
        assert problems == []

    def test_allowed_import_passes(self, tmp_path, monkeypatch):
        _write_src(tmp_path, "src/core/e.py", "import math\nfrom pathlib import Path\n")
        monkeypatch.setattr(va, "ROOT", tmp_path)
        problems = va.check_rule(
            {"name": "核心零框架", "source": ["src/**/*.py"], "forbid_imports": ["flask"]}
        )
        assert problems == []

    def test_exclude_glob_honored(self, tmp_path, monkeypatch):
        _write_src(tmp_path, "src/vendor/f.py", "import flask\n")
        _write_src(tmp_path, "src/core/g.py", "import flask\n")
        monkeypatch.setattr(va, "ROOT", tmp_path)
        problems = va.check_rule(
            {
                "name": "核心零框架",
                "source": ["src/**/*.py"],
                "forbid_imports": ["flask"],
                "exclude": ["src/vendor/**/*.py"],
            }
        )
        assert len(problems) == 1
        assert "src/core/g.py" in problems[0]

    def test_source_matching_nothing_fails(self, tmp_path, monkeypatch):
        """空匹配必须配置错误（防门禁静默通过/说谎）。"""
        monkeypatch.setattr(va, "ROOT", tmp_path)
        problems = va.check_rule(
            {"name": "幽灵层", "source": ["src/ghost/**/*.py"], "forbid_imports": ["flask"]}
        )
        assert any("未匹配任何" in p for p in problems)


class TestMainCLI:
    """CLI 退出码。"""

    def test_empty_rules_on_template_passes(self):
        # 模板仓库 architecture.json rules 为空 → 显式通过
        assert va.main([]) == 0

    def test_violation_returns_one(self, tmp_path, monkeypatch):
        _write_src(tmp_path, "src/core/h.py", "import flask\n")
        _write_config(
            tmp_path,
            [{"name": "核心零框架", "source": ["src/**/*.py"], "forbid_imports": ["flask"]}],
        )
        monkeypatch.setattr(va, "ROOT", tmp_path)
        assert va.main(["--config", "architecture.json"]) == 1

    def test_clean_returns_zero(self, tmp_path, monkeypatch):
        _write_src(tmp_path, "src/core/i.py", "import math\n")
        _write_config(
            tmp_path,
            [{"name": "核心零框架", "source": ["src/**/*.py"], "forbid_imports": ["flask"]}],
        )
        monkeypatch.setattr(va, "ROOT", tmp_path)
        assert va.main(["--config", "architecture.json"]) == 0
