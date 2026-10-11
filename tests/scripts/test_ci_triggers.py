#!/usr/bin/env python3
"""test_ci_triggers.py — CI 触发器配置守卫

背景（2026-10-11，来源：cross-project-synthesis 案例 17「门禁触发/覆盖盲区」）：
门禁本身正确，却可能因为"从未被触发"而失守。ci.yml 里 pull_request 与 push(main)
两处 paths 清单是**同一契约的两个副本**：只改一处会产生
「改了被守护文件却不触发门禁」的盲区，或者相反——无关变更在 main 上白跑一遍完整门禁。

覆盖：
  1. 解析器自身（合成 workflow 文本正确解析；缺 on: 区块显式报错而非静默返回空集）
  2. push(main) 必须声明 paths，且与 pull_request.paths 逐条相等
  3. 清单必须覆盖 quality-gate 实际校验的文件（语义断言，不锁定具体写法）

不引入 YAML 依赖：ci.yml 的 on: 区块结构固定（2 空格触发器 / 4 空格 paths / 6 空格条目），
行解析足够；结构被改坏时解析结果为空，会被第 2 组断言拦下。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"

# quality-gate 实际校验、因而必须进入 paths 的根配置（语义覆盖，允许通配或逐个列名）
GUARDED_ROOT_CONFIGS = (
    "pyproject.toml",
    ".release-please-manifest.json",
    ".pre-commit-config.yaml",
    "mkdocs.yml",
    "Makefile",
)
# 根文档：由 *.md 通配覆盖，或逐个列全（漏 CLAUDE.md 曾实证造成盲区）
GUARDED_ROOT_DOCS = ("AGENTS.md", "CLAUDE.md", "README.md", "ROADMAP.md", "CHANGELOG.md")


def parse_paths(text: str) -> dict[str, list[str]]:
    """解析 on: 区块里各触发器的 paths 清单；缺 on: 区块时显式报错。"""
    lines = text.splitlines()
    on_index = next((i for i, ln in enumerate(lines) if ln.rstrip() == "on:"), None)
    assert on_index is not None, "ci.yml 缺少顶层 on: 区块"

    result: dict[str, list[str]] = {}
    trigger: str | None = None
    in_paths = False
    for ln in lines[on_index + 1 :]:
        if ln and not ln[0].isspace():
            break  # 下一个顶层键（concurrency: / permissions: …）
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        indent = len(ln) - len(ln.lstrip())
        stripped = ln.strip()
        # 结构判定先剥行尾注释（paths: 后挂注释是常见写法，不剥会把触发器解析漏）
        code = stripped.split("#", 1)[0].strip()
        if indent == 2 and code.endswith(":"):
            trigger, in_paths = code[:-1], False
        elif indent == 4 and code == "paths:" and trigger is not None:
            in_paths = True
            result.setdefault(trigger, [])
        elif in_paths and indent == 6 and stripped.startswith("- "):
            quoted = re.match(r'^-\s*"([^"]+)"', stripped)
            value = quoted.group(1) if quoted else code[2:].strip().strip("'")
            result[trigger].append(value)
    return result


@pytest.fixture(scope="module")
def ci_paths() -> dict[str, list[str]]:
    return parse_paths(CI_YML.read_text(encoding="utf-8"))


class TestParser:
    """解析器自身（防「解析出空集 → 断言恒真」的空心通过）。"""

    SYNTHETIC = (
        "name: X\n"
        "on:\n"
        "  pull_request:\n"
        "    paths:\n"
        '      - "src/**"\n'
        "  push:\n"
        "    branches: [main]\n"
        "    paths:\n"
        '      - "src/**"  # 行尾注释\n'
        "      - 'docs/**'\n"
        "concurrency:\n"
        "  group: g\n"
    )

    def test_parses_both_triggers(self):
        assert parse_paths(self.SYNTHETIC) == {
            "pull_request": ["src/**"],
            "push": ["src/**", "docs/**"],
        }

    def test_missing_on_block_raises(self):
        with pytest.raises(AssertionError):
            parse_paths("name: X\nconcurrency:\n  group: g\n")

    def test_inline_comment_on_paths_key_is_tolerated(self):
        """paths: 后挂行尾注释是常见写法——不剥注释会把整个触发器解析漏（2026-10-11 实证）。"""
        text = (
            "name: X\n"
            "on:\n"
            "  pull_request:\n"
            "    paths:            # 与 push 一致\n"
            '      - "src/**"\n'
            "  push:\n"
            "    branches: [main]\n"
            "    paths:\n"
            '      - "src/**"\n'
        )
        assert parse_paths(text) == {"pull_request": ["src/**"], "push": ["src/**"]}

    def test_ignores_text_after_next_top_level_key(self):
        """区块边界：concurrency: 之后的同形文本不得被误收。"""
        text = self.SYNTHETIC + '  pull_request:\n    paths:\n      - "ghost/**"\n'
        assert "ghost/**" not in parse_paths(text).get("push", [])


class TestCiPathsParity:
    def test_push_declares_paths(self, ci_paths):
        """push(main) 必须带 paths：避免无关变更在 main 上重复跑一遍完整门禁。"""
        assert "push" in ci_paths, "ci.yml 的 push 触发器缺少 paths 清单"
        assert len(ci_paths["push"]) >= 10, "paths 清单过短（疑似解析失败或被删窄）"

    def test_push_paths_equal_pull_request_paths(self, ci_paths):
        pr_paths, push_paths = ci_paths["pull_request"], ci_paths["push"]
        only_pr = sorted(set(pr_paths) - set(push_paths))
        only_push = sorted(set(push_paths) - set(pr_paths))
        assert pr_paths == push_paths, (
            f"两份 paths 分叉：仅 PR 有 {only_pr}；仅 push 有 {only_push}"
        )

    def test_guarded_root_configs_covered(self, ci_paths):
        """quality-gate 校验的根配置必须进入清单（案例 17 的直接断言）。"""
        missing = [f for f in GUARDED_ROOT_CONFIGS if f not in ci_paths["pull_request"]]
        assert not missing, f"以下被门禁校验的文件未进入 paths：{missing}"

    def test_root_docs_covered(self, ci_paths):
        """根文档须由 *.md 通配覆盖或逐个列全（漏 CLAUDE.md 曾造成盲区）。"""
        paths = set(ci_paths["pull_request"])
        assert "*.md" in paths or set(GUARDED_ROOT_DOCS) <= paths, (
            "根文档未被 paths 覆盖：改用 *.md 通配或逐个列全"
        )
