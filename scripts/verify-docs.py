#!/usr/bin/env python3
"""
verify-docs.py — 文档一致性验证

功能（新项目初始化后按需扩展）：
  1. 检查全部文档（动态发现：根治理文件 / docs/ / skills/ / templates/ / examples/ /
     scripts/（README）/ .github/）中相对链接指向的文件是否存在
     —— 动态发现取代硬编码清单：新增文档自动纳入检查，防「加了文档忘登记即漏检」
  2. 检查 project-structure.md 目录树中声明的顶层目录是否真实存在
  3. 校验 AGENTS.md 与 project-structure.md 的顶层目录集合一致（双目录树防漂移）
  4. 检查目录树中未声明的文件/目录（可选，--strict）
  5. 语义交叉检查：裸 catch/except、文档 TODO/FIXME 残留、CI 脚本裸 input 调用（防门禁挂起）
  6. 反引号路径检查：`skills/xxx.md` 等非 markdown 链接的失效引用
  7. 版本一致性门禁：.release-please-manifest.json == pyproject.toml == CHANGELOG 最新发布版本
     （存在 version.txt / 包 __init__.py 的 __version__ 时一并纳入对账，来源：ExcelAddin 函数库）
  8. 宪法副本一致性：CLAUDE.md 与 AGENTS.md 逐字节一致（副本存在时才校验，来源：本仓实测漂移）
  9. 悬空引用登记两向校验：第三方（vendored）技能子树内新悬空引用必须登记，登记表不得陈旧
     （来源：工程分析套件 skills/README「已知差异」表）
 10. 豁免到期门禁：docs/governance/review-exemptions.md 中已到期条目必须复查（来源：本仓实测
     P2 条目到期 v0.2.0 而当前 v0.2.4 仍未被拦截）

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

# 排除目录集合 SSOT（2026-08 Max 审查 #8 收敛，此前多处重复定义且发散）
from _excluded_dirs import BASE_EXCLUDED_DIRS  # noqa: E402

# Windows GBK 控制台：强制 UTF-8 输出，避免中文说明乱码（[OK]/[FAIL] 标记保持 ASCII 兼容）
with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# 需检查链接的文档目录根（相对 ROOT，动态发现；2026-09 引入，此前为硬编码清单）
# 根目录 *.md 单独用 glob 展开；含第三方依赖/构建产物的目录由 _DOC_EXCLUDED_DIRS 排除
_DOC_SCAN_DIRS = ("docs", "skills", "templates", "examples", "scripts", ".github")
# 链接检查排除的目录名（非项目文档：依赖、构建产物、缓存）
_DOC_EXCLUDED_DIRS = frozenset(BASE_EXCLUDED_DIRS) | {
    "node_modules",
    "site",
    "dist",
    ".venv",
    "venv",
    "htmlcov",
}
# 链接/反引号检查排除的路径前缀：第三方 Superpowers 技能（上游原样分发，不做本地改写）。
# 其内部链接可能指向上游未 vendored 的兄弟技能（如 requesting-code-review），
# 反引号相对路径按技能目录而非仓库根解析 → 纳入检查只会产生恒定误报。
_DOC_EXCLUDED_PREFIXES = (
    "skills/brainstorming/",
    "skills/writing-plans/",
    "skills/test-driven-development/",
    "skills/subagent-driven-development/",
    "skills/systematic-debugging/",
    "skills/verification-before-completion/",
)


def _discover_docs() -> list[str]:
    """动态发现需检查链接的 markdown 文档（防硬编码清单漂移）。

    覆盖：根目录 *.md + _DOC_SCAN_DIRS 递归 *.md；排除依赖/产物目录与第三方技能子树。
    返回 ROOT 相对路径（正斜杠），排序稳定。
    """
    found: set[str] = set()
    for p in ROOT.glob("*.md"):
        found.add(p.name)
    for sub in _DOC_SCAN_DIRS:
        base = ROOT / sub
        if not base.is_dir():
            continue
        for p in base.rglob("*.md"):
            rel = p.relative_to(ROOT)
            rel_posix = rel.as_posix()
            if any(part in _DOC_EXCLUDED_DIRS for part in rel.parts):
                continue
            if rel_posix.startswith(_DOC_EXCLUDED_PREFIXES):
                continue
            found.add(rel_posix)
    return sorted(found)


# 需要检查链接的文档（相对 ROOT）——动态发现，新增文档自动纳入
DOC_FILES = _discover_docs()

# 顶层目录检查：从 project-structure.md 目录树解析（唯一定义处，随规模裁剪自动适配）
# 注：logs/ 为运行时目录（.gitignore 排除、init-project 复制时跳过），不检查；
#     .git/ 为 git 内部目录，无需声明；
#     .claude/.codegraph/.qoder/.zcode/ 为 AI 工具本地目录
#     （.gitignore 已忽略、init-project 复制时跳过）
EXCLUDED_DIRS = set(BASE_EXCLUDED_DIRS)


# 目录树 SSOT 唯一路径（目录树即契约；2026-09 随 rules/ 并入 docs/ 迁移至 docs/governance/）
STRUCTURE_DOC = ROOT / "docs" / "governance" / "project-structure.md"


def _parse_top_dirs() -> list[str]:
    """从 project-structure.md 目录树解析顶层目录（目录树即契约）。"""
    path = STRUCTURE_DOC
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
    path = STRUCTURE_DOC
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
# 补充 check_undeclared 只查根级的盲区：子目录新增文件（如新 docs/spec/*.md）
# 之前可静默通过 --strict，现在必须登记目录树。
# 二级目录（docs/governance 等）为 opt-in：仅显式列出的才逐文件核对，
# tests/unit、scripts/git-hooks 等未列出的既有子目录不受影响
# （docs/ 分类子目录于 2026-09 随 rules/ 并入 docs/ 而新增）。
_SUBDIR_CHECK = (
    "docs",
    "docs/governance",
    "docs/spec",
    "docs/design",
    "docs/pitfalls",
    "docs/methodology",
    "skills",
    "scripts",
    ".github",
    "templates",
    "examples",
)


def _parse_nested_files() -> dict[str, set[str]]:
    """解析 project-structure.md 目录树中的直属文件条目（两层深度）。

    返回键为相对仓库根的目录路径：顶层目录（如 "docs"）与其下声明的二级目录
    （如 "docs/governance"），值为该目录直属文件名集合。
    树形前缀按 4 字符单元格（"│   " / "    "）计深，兼容末子节点前缀（"│       "）。
    """
    path = STRUCTURE_DOC
    result: dict[str, set[str]] = {}
    current: str | None = None
    current_sub: str | None = None
    in_block = False
    # 单元格捕获组：n 个完整 4 字符前缀 → 深度 n
    depth_re = re.compile(r"^((?:│   |    )*)[├└]──\s+(\S+)")
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.rstrip()
        if s.strip().startswith("```"):
            in_block = not in_block
            continue
        if not in_block:
            continue
        m = depth_re.match(s)
        if not m:
            continue
        depth = len(m.group(1)) // 4
        raw = m.group(2)
        if depth == 0:
            if raw.endswith("/") and "/" not in raw.rstrip("/"):
                current = raw.rstrip("/")
                current_sub = None
                result.setdefault(current, set())
            else:
                current = None
                current_sub = None
            continue
        if current is None:
            continue
        if depth == 1:
            if raw.endswith("/") and "/" not in raw.rstrip("/"):
                # 顶层下的二级目录（如 docs/ 下的 governance/）
                current_sub = raw.rstrip("/")
                result.setdefault(f"{current}/{current_sub}", set())
            elif raw == "..." or "/" in raw:
                # 省略号或 workflows/ci.yml 式"目录/文件"合并条目：非直属文件
                current_sub = None
            else:
                result[current].add(raw)
        elif depth == 2 and current_sub is not None and "/" not in raw and raw != "...":
            key = f"{current}/{current_sub}"
            result[key].add(raw.rstrip("/"))
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
    "scripts/",
    "rules/",
    "skills/",
    "templates/",
    ".github/",
    "docs/",
    "tests/",
    "src/",
    "tools/",
    "build/",
)
_BACKTICK_SKIP_MARKERS = (
    "xxx",
    "nnn",
    "{{",
    "{",
    "}",
    "<",
    ">",
    "*",
    "...",  # 占位符 / 模式串
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
            # 剥离 pytest node-id 后缀（如 tests/x.py::TestY::test_z）：引用具体用例是正常
            # 文档写法，门禁只需校验文件路径本身（2026-10-11 实证误报）
            probe = target.split("::", 1)[0].rstrip("/")
            if not probe:
                continue
            # 依次尝试仓库根与文档所在目录（技能/子目录文档常引用同目录相对路径）
            if not (ROOT / probe).exists() and not (path.parent / probe).exists():
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
            problems.append("[配置错误] 无法从 AGENTS.md 目录树解析顶层目录（格式异常？）")
        return problems
    for d in sorted(ps_dirs - agents_dirs):
        problems.append(
            f"[目录树漂移] project-structure.md 声明 {d}/，AGENTS.md 未收录（请同步 AGENTS.md）"
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
                f"[未声明目录] {p.name}/（请同步 project-structure.md 目录树，或裁剪时同步删除）"
            )
    return problems


def check_subdir_undeclared(strict: bool) -> list[str]:
    """（可选 --strict）检查 SSOT 关键子目录内文件是否在目录树中登记。

    补充 check_undeclared 只查根级的盲区：docs/、scripts/ 等子目录新增文件
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
            problems.append(f"[未声明文件] {sub}/{p.name}（请同步 project-structure.md 目录树）")
    return problems


def _check_bare_handlers() -> list[str]:
    """向量 1：裸异常捕获（src/ 生产代码 + scripts/ 治理脚本；跳过注释/docstring 行防自误报）。

    模板红线"无裸 catch/except"原为提交前 grep（ci.yml 同步扫描 src/ scripts/）。
    逐行扫描并跳过注释/docstring 行（正则需冒号；跳过是为防未来 docstring/注释出现
    `except:` 字面量时自误报，2026-08 Max 审查拆分加固）。
    """
    problems: list[str] = []
    bare_patterns = [
        (r"catch\s*\{", "{csharp} 裸 catch {", {".cs"}),
        (r"except\s*:", "{python} 裸 except 捕获", {".py"}),
    ]
    for pattern, label, suffixes in bare_patterns:
        for root in ("src", "scripts"):
            base = ROOT / root
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if not p.is_file() or p.suffix.lower() not in suffixes:
                    continue
                if any(part in EXCLUDED_DIRS for part in p.relative_to(ROOT).parts):
                    continue
                try:
                    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
                except OSError:
                    continue
                in_docstring = False
                in_block_comment = False  # C# /* */ 块注释状态（下游 .cs 项目防误报）
                for i, line in enumerate(lines, 1):
                    stripped = line.split("#", 1)[0]
                    if suffixes == {".cs"}:
                        # C#：剥离 // 行注释（含 /// XML 注释）与 /* */ 块注释
                        stripped = stripped.split("//", 1)[0]
                        if in_block_comment:
                            if "*/" in stripped:
                                stripped = stripped.split("*/", 1)[1]
                                in_block_comment = False
                            else:
                                continue
                        if "/*" in stripped:
                            parts = stripped.split("/*", 1)
                            stripped = parts[0]
                            # 同行闭合（/* ... */）不残留块注释状态（2026-08 Max 审查修正）
                            in_block_comment = "*/" not in parts[1]
                    # docstring 状态：按行内三引号出现次数奇偶翻转（单行 docstring
                    # 成对出现为偶数 → 不翻转但该行跳过；2026-08 Max 审查 P1 修复，
                    # 原实现每行只翻转一次导致单行 docstring 后真实代码被跳过漏检）
                    q = stripped.count('"""') + stripped.count("'''")
                    if q:
                        if q % 2 == 1:
                            in_docstring = not in_docstring
                        continue
                    if in_docstring:
                        continue
                    if re.search(pattern, stripped):
                        problems.append(
                            f"[语义检查] {label} 残留于 {p.relative_to(ROOT)}:{i}"
                            "（防错三原则：统一排除不可恢复异常，禁止裸捕获）"
                        )
    return problems


def _check_unclosed_todos() -> list[str]:
    """向量 2：文档中的 TODO/FIXME 残留（未闭合的待办易被当作已完成）。"""
    problems: list[str] = []
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
                f"{text[: m.start()].count(chr(10)) + 1} 行）——已完成请移除，未完成请登记"
            )
    return problems


def _check_bare_input_calls() -> list[str]:
    """向量 3：CI 调用的验证脚本禁裸 input()（CI 无 TTY 时挂起）。

    仅扫非交互验证脚本（verify-* / falsy-audit / gen-doc-counts），
    init-project.* 本为交互工具且有 --non-interactive，不在 CI 直跑，豁免。
    """
    problems: list[str] = []
    ci_scripts = [
        p
        for p in (ROOT / "scripts").glob("*.py")
        if p.name.startswith(("verify-", "falsy-", "gen-doc-"))
    ]
    for p in sorted(ci_scripts):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # 仅匹配真正的调用：跳过注释/docstring 行（docstring 教学文字如「裸 input() 调用」
        # 会误报），且跳过含正则模式字面量的行（检查逻辑自身，如本函数里 `input|raw_input`
        # 是正则串而非调用）。docstring 状态按行内三引号出现次数奇偶翻转（2026-08 Max 审查
        # P1 修复：原实现每行只翻转一次，单行 docstring 后真实代码被跳过导致漏检）。
        in_docstring = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.split("#", 1)[0]
            if "input|raw_input" in stripped or "re.search" in stripped:
                continue
            q = stripped.count('"""') + stripped.count("'''")
            if q:
                if q % 2 == 1:
                    in_docstring = not in_docstring
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


# ---------------------------------------------------------------------------
# 向量 8：宪法副本一致性（AGENTS.md ↔ CLAUDE.md）
# ---------------------------------------------------------------------------
# Claude Code 只读 CLAUDE.md，需 AGENTS.md 的静态副本（AGENTS.md「AGENTS.md 生态兼容」）。
# 副本靠人工 Copy-Item 维护、原先无任何门禁 → 实测漂移（2026-10-11：AGENTS.md 257 行 vs
# CLAUDE.md 252 行，缺 ROADMAP.md / benchmarks/ / mkdocs.yml / review-checklist.md 四处登记，
# 且 quality-gate 描述停留在旧版）。只比对副本存在的情形：下游项目不使用 Claude Code 时
# 删除 CLAUDE.md 即自动跳过（不强制创建副本）。
_RULE_COPY_PAIRS = (("AGENTS.md", "CLAUDE.md"),)


def _check_rule_copies() -> list[str]:
    """宪法副本必须与主文件内容一致（忽略换行符差异，防 autocrlf 误报）。"""
    problems: list[str] = []
    for src_name, copy_name in _RULE_COPY_PAIRS:
        src = ROOT / src_name
        copy = ROOT / copy_name
        if not src.is_file() or not copy.is_file():
            continue  # 副本未创建 → 该项目不使用 Claude Code，不强制
        src_text = src.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        copy_text = copy.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        if src_text == copy_text:
            continue
        src_lines = src_text.splitlines()
        copy_lines = copy_text.splitlines()
        src_set, copy_set = set(src_lines), set(copy_lines)
        detail = f"{src_name} {len(src_lines)} 行 vs {copy_name} {len(copy_lines)} 行"
        only_src = [line for line in src_lines if line not in copy_set]
        only_copy = [line for line in copy_lines if line not in src_set]
        if only_src:
            detail += f"；仅 {src_name} 有「{only_src[0].strip()[:50]}」"
        if only_copy:
            detail += f"；仅 {copy_name} 有「{only_copy[0].strip()[:50]}」"
        problems.append(
            f"[宪法副本漂移] {copy_name} 与 {src_name} 内容不一致（{detail}）"
            f"——重建副本：Copy-Item {src_name} {copy_name}"
        )
    return problems


# ---------------------------------------------------------------------------
# 向量 9：第三方（vendored）技能子树悬空引用登记
# ---------------------------------------------------------------------------
# _DOC_EXCLUDED_PREFIXES 内的子树（Superpowers 原样分发）不做链接检查——其相对链接可能指向
# 上游未 vendored 的兄弟技能。但「不检查」不等于「无需登记」：实测
# skills/subagent-driven-development/SKILL.md 引用 ../requesting-code-review/code-reviewer.md，
# 本地无此文件，读者只能自己撞上（来源：工程分析套件 skills/README「已知差异」表）。
# 门禁两向校验：① 新出现的悬空引用未登记 → FAIL；② 登记表条目已不复存在 → FAIL（防陈旧）。
# 覆盖范围（写实，不含糊）：markdown 链接 + 反引号仓库路径，且跳过围栏代码块内的文本；
# mermaid 图与示例代码块中的引用不被扫描，需人工补登。
_VENDORED_REF_REGISTRY_DOC = "skills/README.md"
_VENDORED_REGISTRY_START = "<!-- VENDORED_DANGLING_REFS_START -->"
_VENDORED_REGISTRY_END = "<!-- VENDORED_DANGLING_REFS_END -->"
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_BACKTICK_TOKEN_RE = re.compile(r"`([^`\s]+)`")


def _iter_lines_outside_fences(text: str):
    """逐行产出 (1-based 行号, 行文本)，跳过围栏代码块内的行（示例文本非引用）。"""
    fence_char = ""
    fence_len = 0
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped[:1] in ("`", "~"):
            ch = stripped[0]
            run = len(stripped) - len(stripped.lstrip(ch))
            if run >= 3:
                if fence_len == 0:
                    fence_char, fence_len = ch, run
                elif ch == fence_char and run >= fence_len:
                    fence_char, fence_len = "", 0
                continue
        if fence_len == 0:
            yield lineno, line


def _iter_vendored_docs() -> list[Path]:
    """第三方技能子树内的全部 markdown 文档。"""
    docs: list[Path] = []
    for prefix in _DOC_EXCLUDED_PREFIXES:
        base = ROOT / prefix
        if base.is_dir():
            docs.extend(sorted(base.rglob("*.md")))
    return docs


def _iter_relative_refs(line: str):
    """产出该行中疑似「仓库内相对引用」的目标（markdown 链接 + 反引号路径）。"""
    for m in _MD_LINK_RE.finditer(line):
        target = m.group(1).split("#")[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:", "/")):
            continue
        if "{{" in target:
            continue
        yield target
    for m in _BACKTICK_TOKEN_RE.finditer(line):
        target = m.group(1)
        if not target.startswith(_KNOWN_ROOT_PREFIXES):
            continue
        if _is_pattern_like(target):
            continue
        yield target


def _vendored_ref_exists(doc: Path, target: str) -> bool:
    """相对引用能否解析——先按文档所在目录（上游写法），再按仓库根（本仓惯例）。"""
    for candidate in (doc.parent / target, ROOT / target):
        try:
            if candidate.exists():
                return True
        except OSError:
            continue  # 非法路径字符（Windows）→ 视为不存在
    return False


def scan_vendored_dangling_refs() -> dict[str, list[str]]:
    """扫描第三方技能子树，返回 {悬空引用: ["文件:行号", ...]}。"""
    found: dict[str, list[str]] = {}
    for doc in _iter_vendored_docs():
        rel_doc = doc.relative_to(ROOT).as_posix()
        text = doc.read_text(encoding="utf-8", errors="replace")
        for lineno, line in _iter_lines_outside_fences(text):
            for target in _iter_relative_refs(line):
                if not _vendored_ref_exists(doc, target):
                    found.setdefault(target, []).append(f"{rel_doc}:{lineno}")
    return found


def _read_vendored_ref_registry() -> set[str]:
    """读取 skills/README.md 登记表（HTML 标记圈定的表格，取每行首个反引号 token）。"""
    doc = ROOT / _VENDORED_REF_REGISTRY_DOC
    if not doc.is_file():
        return set()
    inside = False
    registered: set[str] = set()
    for line in doc.read_text(encoding="utf-8", errors="replace").splitlines():
        if _VENDORED_REGISTRY_START in line:
            inside = True
            continue
        if _VENDORED_REGISTRY_END in line:
            break
        if not inside:
            continue
        m = _BACKTICK_TOKEN_RE.search(line)
        if m:
            registered.add(m.group(1))
    return registered


def check_vendored_refs_registry() -> list[str]:
    """两向校验悬空引用登记表：未登记的悬空引用 FAIL，已失效的登记条目 FAIL。"""
    problems: list[str] = []
    if not _iter_vendored_docs():
        return problems  # 未引入第三方技能子树（下游常见）→ 不强制
    dangling = scan_vendored_dangling_refs()
    registered = _read_vendored_ref_registry()
    for target, spots in sorted(dangling.items()):
        if target not in registered:
            problems.append(
                f"[悬空引用未登记] {target}（{', '.join(spots)}）在本地不存在"
                f"——请在 {_VENDORED_REF_REGISTRY_DOC} 的 VENDORED_DANGLING_REFS 登记表补一行"
                "（上游原样分发不改写，登记即责任）"
            )
    for target in sorted(registered - set(dangling)):
        problems.append(
            f"[悬空引用登记陈旧] {_VENDORED_REF_REGISTRY_DOC} 登记的 {target} 已不再悬空"
            "——请删除该行（登记表须与实测一致）"
        )
    return problems


# ---------------------------------------------------------------------------
# 向量 10：豁免登记到期（docs/governance/review-exemptions.md）
# ---------------------------------------------------------------------------
# 「登记即责任——豁免项进入下次审查必查清单」原为人工承诺。实测：P2 条目写明「到期：v0.2.0
# 复查」，而仓库已到 v0.2.4 仍无人复查、无门禁拦截（2026-10-11）。本向量把「到期」变成硬检查：
# 条目声明的到期版本 <= 当前版本 → FAIL，必须复查后关闭/修复，或改写到期版本并留下复查结论。
_EXEMPTIONS_DOC = "docs/governance/review-exemptions.md"
_EXPIRY_RE = re.compile(r"到期：\s*v?(\d+)\.(\d+)\.(\d+)")
_VERSION_RE = re.compile(r'^version\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)


def _read_current_version() -> str:
    """当前版本号：release-please manifest 优先，其次 pyproject.toml；均缺失返回空串。"""
    manifest_path = ROOT / ".release-please-manifest.json"
    if manifest_path.is_file():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            version = str(data.get(".", "")).strip()
            if version:
                return version
        except (json.JSONDecodeError, OSError, AttributeError):
            pass
    pyproject_path = ROOT / "pyproject.toml"
    if pyproject_path.is_file():
        m = _VERSION_RE.search(pyproject_path.read_text(encoding="utf-8", errors="replace"))
        if m:
            return m.group(1).strip()
    return ""


def check_exemption_expiry() -> list[str]:
    """豁免登记表中已到期的条目必须复查（划删除线 = 已关闭，跳过）。"""
    doc = ROOT / _EXEMPTIONS_DOC
    if not doc.is_file():
        return []
    current = _read_current_version()
    m_cur = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", current)
    if not m_cur:
        return []  # 无版本锚点（未接入发版）→ 无「到期版本」可比，不强制
    cur = tuple(int(x) for x in m_cur.groups())
    problems: list[str] = []
    text = doc.read_text(encoding="utf-8", errors="replace")
    for lineno, line in _iter_lines_outside_fences(text):
        if "~~" in line:
            continue  # 已关闭条目（划删除线）
        m = _EXPIRY_RE.search(line)
        if not m:
            continue
        exp = tuple(int(x) for x in m.groups())
        if exp <= cur:
            exp_text = ".".join(str(x) for x in exp)
            problems.append(
                f"[豁免到期] {_EXEMPTIONS_DOC}:{lineno} 声明到期 v{exp_text}，当前 v{current}"
                "——请复查后关闭条目（划删除线 + 复查结论）或改写到期版本并说明复查依据"
            )
    return problems


def check_semantic_consistency() -> list[str]:
    """语义交叉检查（来源：ExcelAddin verify-docs.sh 8 向量中语言无关部分）。

    模板的红线规则要求"无裸 catch/except"，但该自检原为提交前 grep，不属
    verify-docs 硬门禁。此处将最易遗漏的 3 个语言无关向量纳入 CI：
      1. 源码无裸 catch {（C#）/ 无裸 except 捕获（Python）
      2. 文档无未闭合 TODO/FIXME 残留（易被误以为已处理）
      3. scripts/*.py 无裸 input 调用（CI 无 TTY 时挂起）
    """
    return _check_bare_handlers() + _check_unclosed_todos() + _check_bare_input_calls()


def check_version_consistency() -> list[str]:
    """版本号 SSOT 一致性：manifest 根版本 == pyproject 版本 == CHANGELOG 最新发布版本。

    来源（2026-08 审查 P4）：release-please 只自动维护 manifest/CHANGELOG/tag，语言版本文件
    （pyproject.toml）是否被自动管理取决于 release-type——若配置不当，pyproject 版本会与
    已发布版本脱节（曾出现 manifest 0.1.2 vs pyproject 0.1.0），且无门禁拦截。
    非 Python 项目（无 pyproject.toml）或未接入 release-please（无 manifest）时不强制。

    可选锚点（存在才校验，2026-09 对齐 ExcelAddin 函数库四重版本向量）：
      - version.txt          独立版本锚点（C#/非 Python 项目常用）
      - src/<pkg>/__init__.py 的 __version__（Python 包内版本）
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
    # 可选锚点 1：version.txt（单一版本锚点文件）
    version_txt = ROOT / "version.txt"
    if manifest_version and version_txt.exists():
        vt_version = version_txt.read_text(encoding="utf-8", errors="replace").strip()
        if vt_version and vt_version != manifest_version:
            problems.append(
                f"[版本漂移] .release-please-manifest.json {manifest_version} != "
                f"version.txt {vt_version}（发版后需同步版本锚点）"
            )
    # 可选锚点 2：src/<pkg>/__init__.py 的 __version__（Python 包内版本）
    src_dir = ROOT / "src"
    if manifest_version and src_dir.is_dir():
        for init_py in sorted(src_dir.glob("*/__init__.py")):
            m3 = re.search(
                r'^__version__\s*=\s*["\']([^"\']+)["\']',
                init_py.read_text(encoding="utf-8", errors="replace"),
                re.MULTILINE,
            )
            if m3 and m3.group(1).strip() != manifest_version:
                rel = init_py.relative_to(ROOT).as_posix()
                problems.append(
                    f"[版本漂移] .release-please-manifest.json {manifest_version} != "
                    f"{rel} __version__ {m3.group(1).strip()}"
                )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="文档一致性验证")
    parser.add_argument("--strict", action="store_true", help="含未声明文件检查")
    parser.add_argument(
        "--check-bare-handlers",
        action="store_true",
        help="仅执行向量 1：裸 catch/bare except 检查（quick-check 提交前自检调用；"
        "注释/docstring 感知，防教学文字自误报）",
    )
    args = parser.parse_args()

    if args.check_bare_handlers:
        problems = _check_bare_handlers()
        if problems:
            print("[FAIL] 发现裸 catch / bare except：")
            for p in problems:
                print(f"  - {p}")
            return 1
        print("[OK] 无裸 catch / bare except")
        return 0

    problems = (
        check_links()
        + check_backtick_paths()
        + check_dirs()
        + check_agents_tree()
        + check_semantic_consistency()
        + check_version_consistency()
        + _check_rule_copies()
        + check_vendored_refs_registry()
        + check_exemption_expiry()
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
