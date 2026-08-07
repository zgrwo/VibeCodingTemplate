#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-docs.py — 文档一致性验证

功能（新项目初始化后按需扩展）：
  1. 检查 readme.md / agents.md / CONTRIBUTING.md / rules/*.md 中相对链接指向的文件是否存在
  2. 检查 project-structure.md 目录树中声明的顶层目录是否真实存在
  3. 检查目录树中未声明的新增文件（可选，--strict）

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

ROOT = Path(__file__).resolve().parent.parent

# 需要检查链接的文档（相对 ROOT）——覆盖全部含相对链接的文档
DOC_FILES = [
    # 根目录治理文件
    "readme.md",
    "agents.md",
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
]

# project-structure.md 中声明的顶层目录（缺失则报错）
# 注：logs/ 为运行时目录（.gitignore 排除、init-project 复制时跳过），不检查
REQUIRED_DIRS = [
    "src", "tests", "rules", "skills", "tools",
    "build", "docs", "scripts", "templates", ".github",
]


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


def check_dirs() -> list[str]:
    """检查目录树声明的顶层目录是否存在。"""
    problems: list[str] = []
    for d in REQUIRED_DIRS:
        if not (ROOT / d).exists():
            problems.append(f"[缺失目录] {d}/（project-structure.md 已声明）")
    return problems


def check_undeclared(strict: bool) -> list[str]:
    """（可选）检查 ROOT 下是否有目录树未声明的新文件。"""
    if not strict:
        return []
    problems: list[str] = []
    declared = {
        "agents.md", "readme.md", "CONTRIBUTING.md", "CHANGELOG.md",
        "SECURITY.md", "CODE_OF_CONDUCT.md", "LICENSE", ".gitignore",
        ".gitattributes", ".editorconfig", ".pre-commit-config.yaml",
    }
    for p in ROOT.iterdir():
        if p.is_file() and p.name not in declared:
            problems.append(f"[未声明文件] {p.name}（请同步 project-structure.md）")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="文档一致性验证")
    parser.add_argument("--strict", action="store_true", help="含未声明文件检查")
    args = parser.parse_args()

    problems = check_links() + check_dirs() + check_undeclared(args.strict)
    if problems:
        print("[FAIL] 发现以下问题：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("[OK] 文档一致性验证通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
