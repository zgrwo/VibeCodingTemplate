#!/usr/bin/env python3
"""
init-project.py — 从模板初始化新项目（跨平台 Python 版）

职责：
  1. 复制模板到目标目录（跳过 .git / logs / __pycache__ / bin / obj / AI 工具目录）
  2. 扫描文档中的 {{...}} 占位符
  3. 交互式或 --values 参数式替换占位符
  4. 输出未替换占位符清单（防止遗漏导致文档断链）
  5. 可选：git init / 创建 CLAUDE.md 兼容副本

与 init-project.ps1 功能对等，适用于 Linux/macOS 或无 PowerShell 环境。
占位符清单读取 scripts/placeholders.json（唯一真相源）。

用法：
  python scripts/init-project.py /path/to/MyNewProject
  python scripts/init-project.py /path/to/MyNewProject \\
      --values '{"PROJECT_NAME": "MyNewProject", "VERSION": "1.0.0"}' \\
      --git-init --create-compatibility-links

退出码：0 = 全部占位符已替换；1 = 存在未替换占位符
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import json
import re
import shutil
import sys
from pathlib import Path

# Windows GBK 控制台：强制 UTF-8 输出
with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDERS_JSON = TEMPLATE_ROOT / "scripts" / "placeholders.json"

# 复制时跳过的目录/文件
# 注意：与 init-project.ps1 对齐——仅跳过顶级目录，不递归跳过子目录中的同名目录
# build/ 在模板中是源目录（含 .gitkeep），仅在作为构建产物时才应跳过
SKIP_TOP_DIRS = {
    ".git", "logs", ".claude", ".codegraph", ".qoder",
}
# 复制后清理的目录（递归，构建产物/缓存）
CLEANUP_DIRS = {
    "__pycache__", "bin", "obj", ".venv", "venv", "env", "node_modules",
    ".pytest_cache", ".ruff_cache", ".mypy_cache", "TestResults", "dist",
}

# auto 规则计算
_AUTO_RULES = {
    "today": lambda: _dt.date.today().isoformat(),
    "year": lambda: str(_dt.date.today().year),
}


def load_manifest() -> dict:
    """读取 placeholders.json；损坏时回退空 manifest（仅警告，不崩溃）。"""
    if not PLACEHOLDERS_JSON.exists():
        print(f"[WARN] placeholders.json 缺失: {PLACEHOLDERS_JSON}")
        return {}
    try:
        data = json.loads(PLACEHOLDERS_JSON.read_text(encoding="utf-8"))
        return data.get("placeholders", {})
    except (json.JSONDecodeError, OSError, AttributeError, TypeError) as e:
        print(f"[WARN] placeholders.json 解析失败: {e}")
        return {}


def scan_placeholders(text: str) -> list[str]:
    """扫描文本中的 {{NAME}} 占位符，返回去重列表。"""
    return list(dict.fromkeys(
        m for m in re.findall(r"\{\{(\w+)\}\}", text)
    ))


def get_placeholder_value(
    name: str, manifest: dict, values: dict, interactive: bool
) -> str | None:
    """获取占位符替换值：values > interactive > auto > default > name.lower()"""
    # 1. 命令行 --values 优先
    if name in values:
        return values[name]

    entry = manifest.get(name, {})
    category = entry.get("category", "content")

    # 2. auto 自动计算
    if category == "auto":
        rule = entry.get("rule", "")
        if rule in _AUTO_RULES:
            return _AUTO_RULES[rule]()
        print(f"[WARN] auto 占位符 {name} 未知 rule={rule!r}，回退 name.lower()")
        return name.lower()

    # 3. core 交互询问
    if category == "core" and interactive:
        prompt = entry.get("prompt", name)
        default = entry.get("default")
        hint = f"  {prompt}"
        if default:
            hint += f"（默认 {default}）"
        hint += ": "
        user_input = input(hint).strip()
        if user_input:
            return user_input
        if default:
            return default

    # 4. default
    if "default" in entry:
        return entry["default"]

    # 5. content → 占位符名小写（开发期再填）
    return name.lower()


def copy_template(target: Path) -> list[str]:
    """复制模板到目标目录，返回实际复制的文件列表。

    与 init-project.ps1 对齐：
      - 跳过顶级目录（.git / logs / AI 工具目录）
      - 复制后递归清理构建产物/缓存目录
    """
    if target.exists():
        for item in target.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    target.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    # 仅跳过顶级目录
    for item in TEMPLATE_ROOT.iterdir():
        if item.name in SKIP_TOP_DIRS:
            continue
        rel = item.relative_to(TEMPLATE_ROOT)
        dst = target / rel
        if item.is_dir():
            shutil.copytree(item, dst, dirs_exist_ok=True)
        elif item.is_file():
            shutil.copy2(item, dst)
            copied.append(str(rel))

    # 复制后递归清理构建产物/缓存目录
    for junk in CLEANUP_DIRS:
        for p in target.rglob(junk):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)

    # 收集所有实际复制的文件
    for f in target.rglob("*"):
        if f.is_file():
            rel = f.relative_to(target)
            if str(rel) not in copied:
                copied.append(str(rel))

    return copied


def replace_placeholders(target: Path, replacements: dict) -> tuple[int, int]:
    """替换目标目录中所有文件内的占位符，返回（已替换文件数，剩余占位符数）。"""
    replaced_files = 0
    remaining = 0
    pattern = re.compile(r"\{\{(\w+)\}\}")

    for f in target.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix in (".pyc", ".dll", ".exe", ".xll", ".pdb"):
            continue
        try:
            raw_bytes = f.read_bytes()
            content = raw_bytes.decode("utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        missing: list[str] = []

        def _replace(m: re.Match, _m: list = missing) -> str:
            name = m.group(1)
            if name in replacements and replacements[name] is not None:
                return replacements[name]
            _m.append(name)
            return m.group(0)

        new_content = pattern.sub(_replace, content)
        if new_content != content:
            f.write_bytes(new_content.encode("utf-8"))
            replaced_files += 1
        remaining += len(set(missing))

    return replaced_files, remaining


def main() -> int:
    parser = argparse.ArgumentParser(
        description="从模板初始化新项目（跨平台 Python 版）"
    )
    parser.add_argument("target", help="目标目录路径")
    parser.add_argument(
        "--values", default="",
        help='占位符值 JSON，如 \'{"PROJECT_NAME": "MyApp", "VERSION": "1.0.0"}\''
    )
    parser.add_argument("--non-interactive", action="store_true",
                        help="非交互模式（content 占位符用 name.lower() 填充）")
    parser.add_argument("--git-init", action="store_true",
                        help="初始化 git 仓库并配置 commit-msg hook")
    parser.add_argument("--create-compatibility-links", action="store_true",
                        help="创建 CLAUDE.md 副本（Claude Code 兼容）")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if target.exists():
        if not target.is_dir():
            print(f"[ERROR] 目标路径是文件，不是目录: {target}")
            return 1
        if any(target.iterdir()):
            print(f"[ERROR] 目标目录非空: {target}")
            return 1

    print(f"==> 复制模板到 {target}")
    copied = copy_template(target)
    print(f"    复制了 {len(copied)} 个文件")

    # 加载占位符 manifest
    manifest = load_manifest()

    # 解析 --values
    values: dict = {}
    if args.values:
        try:
            values = json.loads(args.values)
        except json.JSONDecodeError as e:
            print(f"[ERROR] --values JSON 解析失败: {e}")
            return 1

    # 收集所有占位符
    all_placeholders: set[str] = set()
    for f in target.rglob("*"):
        if f.is_file():
            try:
                all_placeholders.update(
                    scan_placeholders(f.read_text(encoding="utf-8"))
                )
            except (UnicodeDecodeError, OSError):
                continue

    # 获取替换值
    interactive = not args.non_interactive and not values
    replacements: dict[str, str | None] = {}
    for name in sorted(all_placeholders):
        val = get_placeholder_value(name, manifest, values, interactive)
        replacements[name] = val

    # 执行替换
    replaced_files, remaining = replace_placeholders(target, replacements)

    print("\n==> 占位符替换完成")
    print(f"    替换文件数: {replaced_files}")
    if remaining:
        print(f"    [WARN] {remaining} 个占位符未替换（content 类，需开发期手动填充）")

    # git init
    if args.git_init:
        import subprocess
        print("\n==> 初始化 git 仓库")
        subprocess.run(["git", "init"], cwd=target, capture_output=True)
        hook_path = target / "scripts" / "git-hooks"
        subprocess.run(
            ["git", "config", "core.hooksPath", "scripts/git-hooks"],
            cwd=target, capture_output=True
        )
        print(f"    git init 完成（commit-msg hook 已配置: {hook_path}）")

    # CLAUDE.md 兼容副本
    if args.create_compatibility_links:
        agents_md = target / "AGENTS.md"
        claude_md = target / "CLAUDE.md"
        if agents_md.exists():
            shutil.copy2(agents_md, claude_md)
            print("    已创建 CLAUDE.md（AGENTS.md 副本，供 Claude Code 读取）")
            print("    注意: AGENTS.md 更新后需重新创建 CLAUDE.md 副本")

    print("\n==> 初始化完成")
    return 0 if remaining == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
