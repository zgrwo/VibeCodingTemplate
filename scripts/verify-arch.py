#!/usr/bin/env python3
"""
verify-arch.py — 架构边界门禁（配置驱动，Python AST）

背景（来源：AGENTS.md 架构分层红线 + ExcelAddin / EngSmartSuite 分层守卫实践）：
  "禁止跨层调用或反向依赖"写进了宪法，但分层规则是项目特定的——本脚本把"声明"
  变成可执行断言：读取 scripts/architecture.json，扫描源码 import，命中即 FAIL。

配置格式（scripts/architecture.json，示例见 scripts/README.md）：
  {
    "schema_version": 1,
    "rules": [
      {
        "name": "核心层零框架依赖",
        "source": ["src/core/**/*.py"],
        "forbid_imports": ["flask", "streamlit"],
        "exclude": ["**/vendor/**"],
        "reason": "核心计算必须可独立单测"
      }
    ]
  }

规则语义：
  - 目标文件：source 中每个 glob 匹配的文件（相对仓库根；** 递归），再剔除 exclude
  - 违规判定：`import X` / `import X.Y` / `from X import ...` 的模块名等于
    forbid_imports 中任一项，或以 "项." 为前缀
  - 防门禁说谎：规则 source 未匹配任何文件 → 配置错误（FAIL），不静默通过
  - rules 为空 → **[SKIP] 未检查**（不是通过）：退出码 0 以便新项目首日不红，但输出与
    verify-all 的其余门禁区分开——"0 条规则"时声称"架构边界验证通过"属于门禁说谎
    （cross-project-synthesis #13；2026-10-11 由 [OK] 改为 [SKIP]）

用法：
  python scripts/verify-arch.py
  python scripts/verify-arch.py --config scripts/architecture.json

退出码：0 = 无违规；1 = 存在违规或配置错误
"""

import argparse
import ast
import contextlib
import json
import sys
from pathlib import Path

# Windows GBK 控制台：强制 UTF-8 输出，避免中文说明乱码（[OK]/[FAIL] 标记保持 ASCII 兼容）
with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = "scripts/architecture.json"


def _match_module(module: str, forbidden: str) -> bool:
    """模块名是否命中禁用项（相等或以 "禁用项." 为前缀）。"""
    return module == forbidden or module.startswith(forbidden + ".")


def _iter_targets(rule: dict) -> list[Path]:
    """展开规则的目标文件：source globs 并集减去 exclude globs。"""
    sources = rule.get("source") or []
    if isinstance(sources, str):
        sources = [sources]
    excludes = rule.get("exclude") or []
    if isinstance(excludes, str):
        excludes = [excludes]
    excluded: set[Path] = set()
    for pattern in excludes:
        excluded.update(p for p in ROOT.glob(pattern) if p.is_file())
    targets: set[Path] = set()
    for pattern in sources:
        targets.update(p for p in ROOT.glob(pattern) if p.is_file() and p.suffix == ".py")
    return sorted(targets - excluded)


def load_config(path: Path) -> tuple[dict | None, list[str]]:
    """读取并校验架构配置。返回 (config, 配置错误列表)。"""
    if not path.exists():
        return None, [
            f"[配置错误] 架构配置不存在: {path}（空规则示例见 scripts/architecture.json）"
        ]
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return None, [f"[配置错误] 无法解析 {path}: {e}"]
    if not isinstance(config, dict):
        return None, [f"[配置错误] {path} 顶层必须是对象"]
    if config.get("schema_version") != 1:
        return None, [f"[配置错误] {path} schema_version 必须为 1"]
    rules = config.get("rules")
    if not isinstance(rules, list):
        return None, [f"[配置错误] {path} 的 rules 必须是数组"]
    errors: list[str] = []
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"[配置错误] rules[{i}] 必须是对象")
            continue
        if not rule.get("name"):
            errors.append(f"[配置错误] rules[{i}] 缺少 name")
        forbid = rule.get("forbid_imports")
        if not isinstance(forbid, list) or not forbid:
            errors.append(f"[配置错误] rules[{i}]（{rule.get('name', '?')}）缺 forbid_imports")
        elif not all(isinstance(x, str) and x for x in forbid):
            errors.append(f"[配置错误] rules[{i}] forbid_imports 必须是非空字符串数组")
        source = rule.get("source")
        if not source:
            errors.append(f"[配置错误] rules[{i}]（{rule.get('name', '?')}）缺 source")
    return config, errors


def check_rule(rule: dict) -> list[str]:
    """检查单条规则，返回问题列表（含配置错误与违规）。"""
    problems: list[str] = []
    name = rule.get("name", "未命名规则")
    reason = rule.get("reason", "")
    forbid_imports = [x for x in rule.get("forbid_imports", []) if isinstance(x, str)]
    targets = _iter_targets(rule)
    if not targets:
        return [
            f"[配置错误] 规则「{name}」的 source 未匹配任何 .py 文件"
            "（路径拼写错误？空规则会静默通过，故显式失败）"
        ]
    for p in targets:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue  # 非 Python / 语法错误文件由其他门禁负责，此处不误判
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                modules = [node.module]
            for module in modules:
                for forbidden in forbid_imports:
                    if _match_module(module, forbidden):
                        rel = p.relative_to(ROOT).as_posix()
                        detail = f"（{reason}）" if reason else ""
                        problems.append(
                            f"[FAIL] 架构违规: {rel}:{node.lineno} `{module}` 命中规则"
                            f"「{name}」禁用项 `{forbidden}`{detail}"
                        )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="架构边界门禁（配置驱动）")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help=f"架构配置路径（默认 {DEFAULT_CONFIG}）",
    )
    args = parser.parse_args(argv)

    config, errors = load_config(ROOT / args.config)
    if config is None:
        for e in errors:
            print(e)
        return 1
    if errors:
        for e in errors:
            print(e)
        return 1

    rules = config.get("rules", [])
    if not rules:
        print(
            "[SKIP] 架构边界：未检查（scripts/architecture.json 的 rules 为空）\n"
            "       这不是通过——请按项目实际分层填写规则，例如：\n"
            '       {"name": "核心层零框架依赖", "source": ["src/core/**/*.py"],\n'
            '        "forbid_imports": ["flask", "streamlit"], "reason": "核心计算须可独立单测"}\n'
            "       填写后本门禁才真正生效（当前状态：架构红线只有声明，没有断言）"
        )
        return 0

    problems: list[str] = []
    for rule in rules:
        problems.extend(check_rule(rule))

    if problems:
        print("[FAIL] 发现以下架构问题：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"[OK] 架构边界验证通过（{len(rules)} 条规则）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
