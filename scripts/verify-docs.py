#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-docs.py — 文档一致性验证

功能（新项目初始化后按需扩展）：
  1. 检查全部文档（根治理文件 / rules/ / skills/ / templates/ / docs/）中相对链接指向的文件是否存在
  2. 检查 project-structure.md 目录树中声明的顶层目录是否真实存在
  3. 校验 AGENTS.md 与 project-structure.md 的顶层目录集合一致（双目录树防漂移）
  4. 检查目录树中未声明的文件/目录（可选，--strict）

规则：
  - 含 {{...}} 占位符的链接目标跳过（初始化替换前无法验证，打印提示）
  - logs/ 为运行时目录（.gitignore 排除，不入库），不参与目录存在性检查

用法：
  python scripts/verify-docs.py            # 基础检查
  python scripts/verify-docs.py --strict   # 含未声明文件检查

退出码：0 = 通过；1 = 发现断链/缺失
"""
import argparse
import re
import sys
from pathlib import Path

# Windows GBK 控制台：强制 UTF-8 输出，避免中文说明乱码（[OK]/[FAIL] 标记保持 ASCII 兼容）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent

# 需要检查链接的文档（相对 ROOT）——覆盖全部含相对链接的文档
DOC_FILES = [
    # 根目录治理文件
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    # rules/ 规范文档
    "rules/context.md",
    "rules/documentation.md",
    "rules/project-structure.md",
    "rules/specification.md",
    "rules/api-reference.md",
    "rules/user-manual.md",
    "rules/code-review-prompt.md",
    "rules/cross-project-synthesis.md",
    "rules/refactoring-plan.md",
    "rules/adr-template.md",
    "rules/falsy-pitfalls.md",
    "rules/tooling-pitfalls.md",
    # skills/ AI 技能文件
    "skills/csharp-SKILL.md",
    "skills/python-SKILL.md",
    "skills/vba-SKILL.md",
    "skills/architecture-reviewer.md",
    "skills/refactoring-guardian.md",
    "skills/project-plan-review.md",
    # templates/ 与 docs/
    "templates/README.md",
    "docs/README.md",
]

# 顶层目录检查：从 project-structure.md 目录树解析（唯一定义处，随规模裁剪自动适配）
# 注：logs/ 为运行时目录（.gitignore 排除、init-project 复制时跳过），不检查；
#     .git/ 为 git 内部目录，无需声明；
#     .claude/.codegraph/.qoder/ 为 AI 工具本地目录（.gitignore 已忽略、init-project 复制时跳过）
EXCLUDED_DIRS = {"logs", ".git", ".claude", ".codegraph", ".qoder"}


def _parse_top_dirs() -> list[str]:
    """从 project-structure.md 目录树解析顶层目录（目录树即契约）。"""
    path = ROOT / "rules" / "project-structure.md"
    if not path.exists():
        return []
    dirs: list[str] = []
    in_block = False
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_block = not in_block
            continue
        if not in_block:
            continue
        m = re.match(r"^[├└]──\s+([^/#\s]+)/", s)
        if m:
            dirs.append(m.group(1))
    return dirs


def _parse_top_entries() -> list[str]:
    """从 project-structure.md 目录树解析顶层条目（目录 + 根级文件）。"""
    path = ROOT / "rules" / "project-structure.md"
    if not path.exists():
        return []
    entries: list[str] = []
    in_block = False
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_block = not in_block
            continue
        if not in_block:
            continue
        m = re.match(r"^[├└]──\s+([^#\s]+)", s)
        if m:
            entries.append(m.group(1).rstrip("/"))
    return entries


def _parse_agents_top_dirs() -> list[str]:
    """解析 AGENTS.md 目录树的顶层目录（仅目录，用于双目录树一致性校验）。"""
    path = ROOT / "AGENTS.md"
    if not path.exists():
        return []
    dirs: list[str] = []
    in_block = False
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_block = not in_block
            continue
        if not in_block:
            continue
        m = re.match(r"^[├└]──\s+([^/#\s]+)/", s)
        if m:
            dirs.append(m.group(1))
    return dirs


def check_dirs() -> list[str]:
    """检查目录树声明的顶层目录是否存在（裁剪后同步裁剪目录树即自动适配）。"""
    problems: list[str] = []
    declared = _parse_top_dirs()
    if not declared:
        problems.append("[配置错误] 无法从 project-structure.md 目录树解析顶层目录（目录树格式异常？）")
        return problems
    for d in declared:
        if d in EXCLUDED_DIRS:
            continue
        if not (ROOT / d).exists():
            problems.append(f"[缺失目录] {d}/（project-structure.md 已声明）")
    return problems


def check_links() -> list[str]:
    """检查文档内相对链接的目标是否存在。含 {{...}} 占位符的链接跳过（打印提示）。"""
    problems: list[str] = []
    skipped: list[str] = []
    link_re = re.compile(r"\[[^\]]*\]\(([^)#]+)\)")
    for doc in DOC_FILES:
        path = ROOT / doc
        if not path.exists():
            problems.append(f"[缺失文档] {doc}")
            continue
        for m in link_re.finditer(path.read_text(encoding="utf-8")):
            target = m.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if "{{" in target:
                # 占位符链接：初始化替换前无法验证
                skipped.append(f"{doc} -> {target}")
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                problems.append(f"[断链] {doc} -> {target}")
    for s in skipped:
        print(f"  [SKIP] [占位符链接] {s}（初始化替换后自动验证）")
    return problems


def check_agents_tree() -> list[str]:
    """校验 AGENTS.md 与 project-structure.md 顶层目录集合一致（双目录树防漂移）。

    AGENTS.md 与 project-structure.md 各有一份目录树，新增/删除目录必须双处同步，
    本检查在 CI 中强制两者一致。
    """
    problems: list[str] = []
    ps_dirs = set(_parse_top_dirs())
    agents_dirs = set(_parse_agents_top_dirs())
    if not ps_dirs or not agents_dirs:
        return problems  # 目录树解析失败由 check_dirs 报告
    for d in sorted(ps_dirs - agents_dirs):
        problems.append(f"[目录树漂移] project-structure.md 声明 {d}/，AGENTS.md 未收录（请同步 AGENTS.md）")
    for d in sorted(agents_dirs - ps_dirs):
        problems.append(f"[目录树漂移] AGENTS.md 声明 {d}/，project-structure.md 未收录（请同步 project-structure.md）")
    return problems


def check_undeclared(strict: bool) -> list[str]:
    """（可选 --strict）检查 ROOT 下是否有目录树未声明的文件/目录。

    声明集合从 project-structure.md 目录树解析（目录树即契约），
    新增根级文件/目录必须登记，删除时同步裁剪。
    """
    if not strict:
        return []
    problems: list[str] = []
    declared = set(_parse_top_entries())
    if not declared:
        problems.append("[配置错误] 无法从 project-structure.md 解析顶层条目（目录树格式异常？）")
        return problems
    for p in ROOT.iterdir():
        if p.name in declared or p.name in EXCLUDED_DIRS:
            continue
        if p.is_file():
            problems.append(f"[未声明文件] {p.name}（请同步 project-structure.md 目录树）")
        elif p.is_dir():
            problems.append(f"[未声明目录] {p.name}/（请同步 project-structure.md 目录树，或裁剪时同步删除）")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="文档一致性验证")
    parser.add_argument("--strict", action="store_true", help="含未声明文件检查")
    args = parser.parse_args()

    problems = check_links() + check_dirs() + check_agents_tree() + check_undeclared(args.strict)
    if problems:
        print("[FAIL] 发现以下问题：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("[OK] 文档一致性验证通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
