#!/usr/bin/env python3
"""
verify-registries.py — 多注册表一致性门禁

背景（来自 cross-project-synthesis.md 高频修复模式「注册/同步遗漏 6+」）：
  registry-driven 架构（插件、分发器、路由表）最常见的坑是"加了一个函数却忘了
  某个注册点"，导致配置流静默断裂。本脚本把"N 个注册表必须键集一致"变成可执行断言。

用法：
  python scripts/verify-registries.py                    # 使用 scripts/registries.json 默认配置
  python scripts/verify-registries.py --config xxx.json  # 自定义注册表对

配置格式（scripts/registries.json）：
  {
    "schema_version": 1,
    "groups": [
      {
        "name": "占位符注册表",          # 组名（对比失败时展示）
        "registries": [
          {"name": "manifest", "type": "json_keys",
           "path": "scripts/placeholders.json", "key_path": "placeholders"},
          {"name": "模板文件引用", "type": "placeholder_scan", "roots": ["."]}
        ]
      }
    ]
  }

registry 来源类型：
  - json_keys        从 JSON 对象取键（key_path 用点分隔，如 "placeholders"）
  - placeholder_scan 扫描文件中的 {{NAME}} 元占位符（大写 token）
  - regex_extract    正则提取（如 Python 常量/字典键），pattern 必填

语义（对齐 test-template.ps1 的双向漂移守卫）：
  - 死条目（manifest 有但文件不用）→ FAIL（退出码 1）
  - 未声明（文件用但 manifest 无）→ WARN（教学性 {{...}} 转义合法，不硬失败）

退出码：0 = 通过；1 = 任一组存在死条目/缺失
"""
import argparse
import contextlib
import json
import re
import sys
from pathlib import Path

# Windows GBK 控制台：强制 UTF-8 输出，避免中文说明乱码
with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# placeholder_scan 默认跳过目录（AI 工具本地目录 / 运行时产物，不入库）
EXCLUDED_DIRS = {
    ".git", ".claude", ".codegraph", ".qoder",
    "logs", "build", "benchmarks",
    "__pycache__", ".pytest_cache", ".ruff_cache",
    # tests/ 含教学/夹具 token（{{FOO}}/{{A}} 等）——计入"已使用"会：
    #   (a) 每次运行输出大量未声明 WARN 淹没真实信号
    #   (b) 夹具引用使死条目被误判为已使用，削弱 FAIL 检测
    "tests",
}

_PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

# 教学转义 token 白名单：源码注释/docstring 示例与 AGENTS.md 教学文字中的占位符
# （{{A}}/{{B}}/{{FOO}}/{{NAME}}/{{X}} 等），不计入"未声明" WARN——否则每次运行
# 恒定输出噪声，淹没真实未登记占位符信号（与 EXCLUDED_DIRS 排除 tests/ 的设计理由一致）。
# B 来自 scripts/init-project.ps1 的扫描注释（{{A}}/{{B}}/{{FOO}}，2026-08 审查 P3 补录）。
TEACHING_TOKENS = {
    "A", "B", "FOO", "NAME", "UPPER", "UPPER_CASE", "X", "X1_",
}


def _iter_files(roots: list[str]) -> list[Path]:
    """展开 roots（相对 ROOT）为文件列表，跳过排除目录与二进制。"""
    files: list[Path] = []
    for root in roots:
        base = (ROOT / root).resolve() if root != "." else ROOT
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if any(part in EXCLUDED_DIRS for part in p.relative_to(base).parts):
                continue
            if p.suffix.lower() in {".pyc", ".exe", ".dll", ".7z", ".zip", ".png", ".jpg", ".ico"}:
                continue
            files.append(p)
    return files


def collect_keys(reg: dict) -> tuple[set[str], list[str]]:
    """从单个 registry 定义提取键集。返回 (keys, 配置错误)。"""
    problems: list[str] = []
    rtype = reg.get("type", "json_keys")
    if rtype == "json_keys":
        path = ROOT / reg.get("path", "")
        if not path.exists():
            return set(), [f"[配置错误] registry 文件不存在: {path}"]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return set(), [f"[配置错误] 无法解析 {path}: {e}"]
        node = data
        for seg in reg.get("key_path", "").split("."):
            if not seg:
                break
            if isinstance(node, dict) and seg in node:
                node = node[seg]
            else:
                return set(), [f"[配置错误] key_path 无效: {reg.get('key_path')} in {path}"]
        if not isinstance(node, dict):
            return set(), [f"[配置错误] {path} 的 {reg.get('key_path')} 不是对象"]
        return set(node.keys()), problems

    if rtype == "placeholder_scan":
        found: set[str] = set()
        for p in _iter_files(reg.get("roots", ["."])):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            found.update(_PLACEHOLDER_RE.findall(text))
        # 剔除教学转义 token（见 TEACHING_TOKENS），避免恒定 WARN 噪声
        return found - TEACHING_TOKENS, problems

    if rtype == "regex_extract":
        pattern = re.compile(reg.get("pattern", ""))
        # 多捕获组时 findall 返回 tuple（与 json_keys 的字符串键比较产生垃圾输出）：
        # 统一只取第 1 个捕获组，无捕获组则取整段匹配。
        groups = pattern.groups
        found: set[str] = set()
        for p in _iter_files(reg.get("roots", ["."])):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in pattern.finditer(text):
                if groups == 0:
                    found.add(m.group(0))
                elif m.group(1) is not None:
                    found.add(m.group(1))
        return found, problems

    return set(), [f"[配置错误] 未知 registry 类型: {rtype}"]


def check_group(group: dict) -> list[str]:
    """对比组内所有 registry 的键集，返回差异问题。"""
    problems: list[str] = []
    name = group.get("name", "未命名组")
    regs = group.get("registries", [])
    if len(regs) < 2:
        return [f"[配置错误] 组 '{name}' 需至少 2 个 registry 才能对比"]
    collected = []
    for reg in regs:
        keys, errs = collect_keys(reg)
        problems.extend(errs)
        collected.append((reg.get("name", "?"), keys))
    if problems:
        return problems
    base_name, base_keys = collected[0]
    for other_name, other_keys in collected[1:]:
        for k in sorted(base_keys - other_keys):
            problems.append(
                f"[FAIL] 死条目: {name} — {base_name} 声明 `{k}` 但 {other_name} 未收录"
            )
        for k in sorted(other_keys - base_keys):
            problems.append(
                f"[WARN] 未声明: {name} — {other_name} 引用 `{k}` 但 {base_name} 未登记"
                "（教学性 {{...}} 转义请保留；新增占位符请登记 manifest）"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="多注册表一致性门禁")
    parser.add_argument(
        "--config", default=str(ROOT / "scripts" / "registries.json"),
        help="注册表对配置文件（默认 scripts/registries.json）",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[FAIL] 配置文件不存在: {config_path}")
        return 1
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[FAIL] 无法解析配置 {config_path}: {e}")
        return 1

    all_problems: list[str] = []
    for group in config.get("groups", []):
        all_problems.extend(check_group(group))

    for p in all_problems:
        print(p)
    # 语义对齐 falsy-audit：仅 FAIL（死条目/配置错误）硬失败；纯 WARN（教学性转义）通过
    if any(p.startswith("[FAIL]") or p.startswith("[配置错误]") for p in all_problems):
        return 1
    if all_problems:
        print("[OK] 注册表一致性验证通过（仅未声明教学性转义，已 WARN）")
        return 0
    print("[OK] 注册表一致性验证通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
