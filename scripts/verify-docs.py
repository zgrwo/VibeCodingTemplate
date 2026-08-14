#!/usr/bin/env python3
"""
verify-docs.py — 文档一致性验证

功能（新项目初始化后按需扩展）：
  1. 检查全部文档（根治理文件 / rules/ / skills/ / templates/ / docs/）中相对链接指向的文件是否存在
  2. 检查 project-structure.md 目录树中声明的顶层目录是否真实存在
  3. 校验 AGENTS.md 与 project-structure.md 的顶层目录集合一致（双目录树防漂移）
  4. 检查目录树中未声明的文件/目录（可选，--strict）
  5. 语义交叉检查：裸 catch/except、文档 TODO/FIXME 残留、CI 脚本裸 input 调用（防门禁挂起）
  6. 反引号路径检查：`skills/xxx.md` 等非 markdown 链接的失效引用
  7. 版本一致性门禁：.release-please-manifest.json == pyproject.toml == CHANGELOG 最新发布版本

规则：
  - 含 {{...}} 占位符的链接目标跳过（初始化替换前无法验证，打印提示）
  - logs/ 为运行时目录（.gitignore 排除，不入库），不参与目录存在性检查

用法：
  python scripts/verify-docs.py            # 基础检查
  python scripts/verify-docs.py --strict   # 含未声明文件检查

退出码：0 = 通过；1 = 发现断链/缺失
"""
import argparse
import contextlib
import json
import re
import sys
from pathlib import Path

# Windows GBK 控制台：强制 UTF-8 输出，避免中文说明乱码（[OK]/[FAIL] 标记保持 ASCII 兼容）
with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# 需要检查链接的文档（相对 ROOT）——覆盖全部含相对链接的文档
DOC_FILES = [
    # 根目录治理文件
    "README.md",
    "README.en.md",
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
    "rules/cross-project-synthesis.md",
    "rules/refactoring-plan.md",
    "rules/adr-template.md",
    "rules/falsy-pitfalls.md",
    "rules/tooling-pitfalls.md",
    "rules/sentinel-contract.md",
    # skills/ AI 技能文件
    "skills/csharp-SKILL.md",
    "skills/python-SKILL.md",
    "skills/vba-SKILL.md",
    "skills/typescript-SKILL.md",
    "skills/go-SKILL.md",
    "skills/rust-SKILL.md",
    "skills/architecture-reviewer-SKILL.md",
    "skills/refactoring-guardian-SKILL.md",
    "skills/project-plan-review-SKILL.md",
    # scripts/ 目录导航
    "scripts/README.md",
    # templates/ 与 docs/ 与 examples/
    "templates/README.md",
    "templates/monorepo/README.md",
    "docs/README.md",
    "docs/architecture.md",
    "examples/README.md",
]

# 顶层目录检查：从 project-structure.md 目录树解析（唯一定义处，随规模裁剪自动适配）
# 注：logs/ 为运行时目录（.gitignore 排除、init-project 复制时跳过），不检查；
#     .git/ 为 git 内部目录，无需声明；
#     .claude/.codegraph/.qoder/ 为 AI 工具本地目录（.gitignore 已忽略、init-project 复制时跳过）
EXCLUDED_DIRS = {
    "logs", ".git", ".claude", ".codegraph", ".qoder",
    ".pytest_cache", ".ruff_cache", "__pycache__", ".coverage",
}


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


def _parse_agents_top_entries() -> list[str]:
    """解析 AGENTS.md 目录树的顶层条目（目录 + 根级文件，用于文件级双树比对）。"""
    path = ROOT / "AGENTS.md"
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


# 需核对"目录内文件已登记"的 SSOT 关键子目录（目录树即契约，逐文件枚举）
# 补充 check_undeclared 只查根级的盲区：子目录新增文件（如新 rules/*.md）
# 之前可静默通过 --strict，现在必须登记目录树。
_SUBDIR_CHECK = ("rules", "skills", "scripts", "docs", ".github", "templates", "examples")


def _parse_nested_files() -> dict[str, set[str]]:
    """解析 project-structure.md 目录树中顶层目录下的直接文件条目。"""
    path = ROOT / "rules" / "project-structure.md"
    result: dict[str, set[str]] = {}
    current: str | None = None
    in_block = False
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.rstrip()
        if s.strip().startswith("```"):
            in_block = not in_block
            continue
        if not in_block:
            continue
        m = re.match(r"^[├└]──\s+([^/#\s]+)/", s)
        if m:
            current = m.group(1)
            result.setdefault(current, set())
            continue
        if current is not None and "│" in s:
            m2 = re.match(r"^│\s*[├└]──\s+([^#\s]+)", s)
            if m2:
                entry = m2.group(1).rstrip("/")
                if "/" not in entry and entry not in ("...",):
                    result[current].add(entry)
    return result


def check_dirs() -> list[str]:
    """检查目录树声明的顶层目录是否存在（裁剪后同步裁剪目录树即自动适配）。"""
    problems: list[str] = []
    declared = _parse_top_dirs()
    if not declared:
        problems.append(
            "[配置错误] 无法从 project-structure.md 目录树解析顶层目录（目录树格式异常？）"
        )
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
    link_re = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:\s+\"[^\"]*\")?\)")
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


# 反引号内相对路径检查：捕获 `skills/xxx.md` 这类非 markdown 链接的失效引用
# （技能表 / 占位符约定表多用反引号包路径，markdown link_re 不覆盖）
#
# 为控制误报，仅检查"以已知根目录前缀开头"的引用（语义明确指向仓库内路径），
# 并跳过：CHANGELOG（历史记录，引用已删文件属正常）、占位符/模式串、AI 工具本地目录。
_KNOWN_ROOT_PREFIXES = (
    "scripts/", "rules/", "skills/", "templates/", ".github/",
    "docs/", "tests/", "src/", "tools/", "build/",
)
_BACKTICK_SKIP_MARKERS = (
    "xxx", "nnn", "{{", "{", "}", "<", ">", "*", "...",  # 占位符 / 模式串
)
_BACKTICK_SKIP_PREFIXES = (".claude/", ".codegraph/", ".qoder/")  # AI 工具本地目录
# CHANGELOG 为历史记录，引用已删除/重建文件属正常，不做反引号路径校验
_BACKTICK_SKIP_DOCS = {"CHANGELOG.md"}


def _is_pattern_like(s: str) -> bool:
    """识别占位符/模式串（如 {{...}}、{Name}、<Module>、0001-xxx.md）——非真实路径，跳过。"""
    low = s.lower()
    return any(mk in low for mk in _BACKTICK_SKIP_MARKERS)


def check_backtick_paths() -> list[str]:
    """检查反引号内以已知根目录前缀开头的相对路径引用是否存在（防占位符替换成死路径后漏检）。"""
    problems: list[str] = []
    code_re = re.compile(r"`([^`\s]+)`")
    for doc in DOC_FILES:
        if doc in _BACKTICK_SKIP_DOCS:
            continue
        path = ROOT / doc
        if not path.exists():
            continue
        for m in code_re.finditer(path.read_text(encoding="utf-8")):
            raw = m.group(1)
            # 规范化 Windows 反斜杠路径 → 正斜杠（如 .\scripts\init-project.ps1）
            target = raw.replace("\\", "/")
            if target.startswith("./"):
                target = target[2:]
            if not target.startswith(_KNOWN_ROOT_PREFIXES):
                continue  # 非根目录路径：可能是示例文件名/命名规范，不校验
            if target.startswith(_BACKTICK_SKIP_PREFIXES):
                continue  # AI 工具本地目录（不入库）
            if _is_pattern_like(target):
                continue  # 占位符/模式串，替换前无法验证
            probe = target.rstrip("/")
            # 目录前缀路径按仓库根解析（如 `scripts/verify-docs.py` 指根下文件）
            resolved = (ROOT / probe).resolve()
            if not resolved.exists():
                problems.append(f"[反引号路径失效] {doc} -> `{raw}`（指向不存在的文件？）")
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
        if not agents_dirs:
            problems.append(
                "[配置错误] 无法从 AGENTS.md 目录树解析顶层目录（格式异常？）"
            )
        return problems
    for d in sorted(ps_dirs - agents_dirs):
        problems.append(
            f"[目录树漂移] project-structure.md 声明 {d}/，"
            f"AGENTS.md 未收录（请同步 AGENTS.md）"
        )
    for d in sorted(agents_dirs - ps_dirs):
        problems.append(
            f"[目录树漂移] AGENTS.md 声明 {d}/，"
            f"project-structure.md 未收录（请同步 project-structure.md）"
        )
    # 文件级双树比对：原检查只比较目录行，根级文件漂移（如 AGENTS.md 树漏 Makefile）
    # 永不被 CI 捕获。新增"根级文件集合"一致性校验。
    ps_entries = set(_parse_top_entries())
    agents_entries = set(_parse_agents_top_entries())
    if ps_entries and agents_entries:
        ps_files = ps_entries - set(ps_dirs)
        agents_files = agents_entries - set(agents_dirs)
        for f in sorted(ps_files - agents_files):
            problems.append(
                f"[目录树文件漂移] project-structure.md 声明 {f}，"
                f"AGENTS.md 未收录（请同步 AGENTS.md）"
            )
        for f in sorted(agents_files - ps_files):
            problems.append(
                f"[目录树文件漂移] AGENTS.md 声明 {f}，"
                f"project-structure.md 未收录（请同步 project-structure.md）"
            )
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
            problems.append(
                f"[未声明目录] {p.name}/（请同步 project-structure.md 目录树，"
                f"或裁剪时同步删除）"
            )
    return problems


def check_subdir_undeclared(strict: bool) -> list[str]:
    """（可选 --strict）检查 SSOT 关键子目录内文件是否在目录树中登记。

    补充 check_undeclared 只查根级的盲区：rules/、scripts/ 等子目录新增文件
    之前可静默通过 --strict，导致新规则文档孤儿化（无注册、无链接校验）。
    """
    if not strict:
        return []
    problems: list[str] = []
    nested = _parse_nested_files()
    for sub in _SUBDIR_CHECK:
        base = ROOT / sub
        if not base.exists():
            continue
        declared = nested.get(sub, set())
        for p in sorted(base.iterdir()):
            if p.is_dir():
                continue
            if p.name == ".gitkeep":  # 空目录占位文件，非 SSOT 契约对象
                continue
            if p.name in declared:
                continue
            problems.append(
                f"[未声明文件] {sub}/{p.name}（请同步 project-structure.md 目录树）"
            )
    return problems


def check_semantic_consistency() -> list[str]:
    """语义交叉检查（来源：ExcelAddin verify-docs.sh 8 向量中语言无关部分）。

    模板的红线规则要求"无裸 catch/except"，但该自检原为提交前 grep，不属
    verify-docs 硬门禁。此处将最易遗漏的 3 个语言无关向量纳入 CI：
      1. 源码无裸 `catch {`（C#）/ 无裸 `except:`（Python）
      2. 文档无未闭合 TODO/FIXME 残留（易被误以为已处理）
      3. scripts/*.py 无裸 `input()`（CI 无 TTY 时挂起）
    """
    problems: list[str] = []

    # 向量 1：裸异常捕获（仅扫 src/ 生产代码；tests/ 常含教学字符串会被误判，
    # 且模板红线"grep catch{ src/" 本就只扫 src/）
    bare_patterns = [
        (r"catch\s*\{", "{csharp} 裸 catch {", ("src",)),
        (r"except\s*:", "{python} 裸 except:", ("src",)),
    ]
    for pattern, label, roots in bare_patterns:
        for root in roots:
            base = ROOT / root
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if not p.is_file() or p.suffix.lower() not in {".cs", ".py"}:
                    continue
                if any(part in EXCLUDED_DIRS for part in p.relative_to(ROOT).parts):
                    continue
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if re.search(pattern, text):
                    problems.append(
                        f"[语义检查] {label} 残留于 {p.relative_to(ROOT)}"
                        "（防错三原则：统一排除不可恢复异常，禁止裸捕获）"
                    )

    # 向量 2：文档中的 TODO/FIXME 残留（未闭合的待办易被当作已完成）
    for doc in DOC_FILES:
        p = ROOT / doc
        if not p.exists():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # 仅匹配行首待办标记（如 "- TODO: ..."），排除教学性提及
        # （如审查规则里"注释说 TODO: 未来优化"作为反模式示例）
        for m in re.finditer(r"^\s*(?:[-*]?\s*)?(TODO|FIXME)\s*[:：]", text, re.MULTILINE):
            problems.append(
                f"[语义检查] {doc} 含未闭合 {m.group(1)} 待办（第 "
                f"{text[:m.start()].count(chr(10)) + 1} 行）——已完成请移除，未完成请登记"
            )

    # 向量 3：CI 调用的验证脚本禁裸 input()（CI 无 TTY 时挂起）。
    # 仅扫非交互验证脚本（verify-* / falsy-audit / gen-doc-counts），
    # init-project.* 本为交互工具且有 --non-interactive，不在 CI 直跑，豁免。
    ci_scripts = [
        p for p in (ROOT / "scripts").glob("*.py")
        if p.name.startswith(("verify-", "falsy-", "gen-doc-"))
    ]
    for p in sorted(ci_scripts):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # 仅匹配真正的调用：跳过注释/docstring 行（docstring 教学文字如「裸 input() 调用」
        # 会误报），且跳过含正则模式字面量的行（检查逻辑自身，如本函数里 `input|raw_input`
        # 是正则串而非调用）。2026-08 Max 审查加固：新增 docstring 状态跟踪。
        in_docstring = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.split("#", 1)[0]
            if "input|raw_input" in stripped or "re.search" in stripped:
                continue
            if '"""' in stripped or "'''" in stripped:
                in_docstring = not in_docstring  # 单行 docstring 成对出现，两次翻转抵消
                continue
            if in_docstring:
                continue
            call = re.search(r"(?:^|\s)(input|raw_input)\s*\(", stripped)
            if call:
                problems.append(
                    f"[语义检查] {p.name} 第 {line_no} 行含裸 {call.group(1)} 调用"
                    "——CI 无交互环境会挂起，请改为参数/环境变量/--non-interactive"
                )

    return problems


def check_version_consistency() -> list[str]:
    """版本号 SSOT 一致性：manifest 根版本 == pyproject 版本 == CHANGELOG 最新发布版本。

    来源（2026-08 审查 P4）：release-please 只自动维护 manifest/CHANGELOG/tag，语言版本文件
    （pyproject.toml）是否被自动管理取决于 release-type——若配置不当，pyproject 版本会与
    已发布版本脱节（曾出现 manifest 0.1.2 vs pyproject 0.1.0），且无门禁拦截。
    非 Python 项目（无 pyproject.toml）或未接入 release-please（无 manifest）时不强制。
    """
    problems: list[str] = []
    manifest_path = ROOT / ".release-please-manifest.json"
    pyproject_path = ROOT / "pyproject.toml"
    if not manifest_path.exists() or not pyproject_path.exists():
        return problems
    try:
        manifest_version = str(
            json.loads(manifest_path.read_text(encoding="utf-8")).get(".", "")
        ).strip()
    except (json.JSONDecodeError, OSError):
        manifest_version = ""
    m = re.search(
        r'^version\s*=\s*["\']([^"\']+)["\']',
        pyproject_path.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    pyproject_version = m.group(1).strip() if m else ""
    if manifest_version and pyproject_version and manifest_version != pyproject_version:
        problems.append(
            f"[版本漂移] .release-please-manifest.json 版本 {manifest_version} != "
            f"pyproject.toml 版本 {pyproject_version}"
            "（发版后需同步；或确认 release-please release-type 能自动管理 pyproject.toml）"
        )
    # CHANGELOG 最新已发布版本（首个 `## [x.y.z]` 段，Unreleased 不匹配数字版本）
    changelog_path = ROOT / "CHANGELOG.md"
    if changelog_path.exists():
        m2 = re.search(
            r"^##\s*\[(\d+\.\d+\.\d+)\]",
            changelog_path.read_text(encoding="utf-8", errors="replace"),
            re.MULTILINE,
        )
        changelog_version = m2.group(1) if m2 else ""
        if manifest_version and changelog_version and manifest_version != changelog_version:
            problems.append(
                f"[版本漂移] .release-please-manifest.json {manifest_version} != "
                f"CHANGELOG 最新发布版本 {changelog_version}"
            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="文档一致性验证")
    parser.add_argument("--strict", action="store_true", help="含未声明文件检查")
    args = parser.parse_args()

    problems = (
        check_links()
        + check_backtick_paths()
        + check_dirs()
        + check_agents_tree()
        + check_semantic_consistency()
        + check_version_consistency()
        + check_subdir_undeclared(args.strict)
        + check_undeclared(args.strict)
    )
    if problems:
        print("[FAIL] 发现以下问题：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("[OK] 文档一致性验证通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
