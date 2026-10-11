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

注意：--non-interactive 模式下，core 占位符若无 default 且未在 --values 中提供，脚本报错退出
（与 init-project.ps1 的 stdin 重定向 fail-fast 对齐），防止 CI 命令被静默替换成占位符名小写。

退出码：0 = 全部占位符已替换；1 = 存在未替换占位符
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 排除目录集合 SSOT（2026-08 Max 审查 #8 收敛）：复制语义取 BASE 子集——
# 缓存目录（__pycache__/.pytest_cache 等）复制后由 CLEANUP_DIRS 递归清理而非跳过
from _excluded_dirs import BASE_EXCLUDED_DIRS  # noqa: E402

# Windows GBK 控制台：强制 UTF-8 输出
with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDERS_JSON = TEMPLATE_ROOT / "scripts" / "placeholders.json"

# 复制时跳过的目录/文件
# 注意：与 init-project.ps1 对齐——仅跳过顶级目录，不递归跳过子目录中的同名目录
# build/ 在模板中是源目录（含 .gitkeep），仅在作为构建产物时才应跳过
SKIP_TOP_DIRS = {
    d
    for d in BASE_EXCLUDED_DIRS
    if d not in ("__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".coverage")
}
# 跳过的根级文件（运行产物，非模板内容；如 pytest-cov 生成的 .coverage）
SKIP_TOP_FILES = {".coverage"}
# 复制后清理的目录（递归，构建产物/缓存）
CLEANUP_DIRS = {
    "__pycache__",
    "bin",
    "obj",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "TestResults",
    "dist",
}
# 占位符扫描/替换时跳过的顶层目录：tests/ 内含 scanner 测试夹具（如 {{A}}/{{X1_}}），
# 这些 {{...}} 字面量是测试输入而非待替换占位符，替换会破坏生成项目的测试套件。
SKIP_PLACEHOLDER_DIRS = {"tests"}

# 交互模式下无默认值的 core 占位符最多重提示次数（超过则 fail-fast，防无 TTY/EOF 时死循环）
_MAX_CORE_PROMPT_ATTEMPTS = 3

# auto 规则计算
_AUTO_RULES = {
    "today": lambda: _dt.date.today().isoformat(),
    "year": lambda: str(_dt.date.today().year),
}


def load_manifest() -> dict[str, dict[str, str]]:
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
    """扫描文本中的 {{...}} 占位符，返回去重列表。

    与 init-project.ps1 / test-template.ps1 的 `[A-Z0-9_]+` 保持一致：
    仅识别大写占位符（{PascalCase} 模块级占位符不应被 init 匹配）。
    """
    return list(dict.fromkeys(m for m in re.findall(r"\{\{([A-Z0-9_]+)\}\}", text)))


def get_placeholder_value(
    name: str, manifest: dict[str, dict[str, str]], values: dict[str, str], interactive: bool
) -> str | None:
    """获取占位符替换值：values > interactive > auto > default > name.lower()。

    未登记 token（不在 manifest 且不在 values）→ 返回 None，保留原样，
    禁止 name.lower() 污染元文档引用（如教学用的 {{...}} 字面量），
    见 CHANGELOG H3 已修复缺陷回归。
    """
    # 1. 命令行 --values 优先
    if name in values:
        return values[name]

    entry = manifest.get(name)
    if entry is None:
        return None  # 未登记 → 保留原样，不计入 remaining
    category = entry.get("category", "content")

    # 2. auto 自动计算
    if category == "auto":
        rule = entry.get("rule", "")
        if rule in _AUTO_RULES:
            return _AUTO_RULES[rule]()
        print(f"[WARN] auto 占位符 {name} 未知 rule={rule!r}，回退 name.lower()")
        return name.lower()

    # 3. core 交互询问
    if category == "core":
        if not interactive and "default" not in entry:
            # 镜像 init-project.ps1：非交互且无默认值时 fail-fast，而非静默回退占位符名小写——
            # 否则 BUILD_CMD/TEST_CMD 等 CI 命令占位符被替换成 build_cmd/test_cmd，
            # 生成损坏的 .github/workflows/ci.yml（P5 审查修复）。
            raise SystemExit(
                f"[FATAL] 非交互模式下 core 占位符 {name} 无默认值："
                f'请通过 --values 提供（如 --values \'{{"{name}": "..."}}\'）'
            )
        if interactive:
            prompt = entry.get("prompt", name)
            default = entry.get("default")
            if default:
                return input(f"  {prompt}（Enter 用默认: {default}）: ").strip() or default
            # 无默认值的 core 占位符：空输入曾回退占位符名小写（BUILD_CMD → build_cmd），
            # 静默生成损坏的项目/CI 配置。改为重提示，超过 _MAX_CORE_PROMPT_ATTEMPTS 次仍未
            # 填写则 fail-fast（与非交互路径同语义，防静默传播；P2 豁免到期复查，2026-10-11 修复）。
            for _attempt in range(_MAX_CORE_PROMPT_ATTEMPTS):
                try:
                    answer = input(f"  {prompt}（必填，无默认值）: ").strip()
                except EOFError:
                    answer = ""
                if answer:
                    return answer
                print(
                    "  [WARN] 空输入会生成损坏的项目/CI 配置（如 BUILD_CMD → build_cmd），请填写。"
                )
            raise SystemExit(
                f"[FATAL] core 占位符 {name} 未填写：请通过 --values 提供"
                f'（如 --values \'{{"{name}": "..."}}\'）'
            )

    # 4. default（非交互 core 有默认值 / 交互 Enter 有默认值）
    if "default" in entry:
        return entry["default"]

    # 5. content → 占位符名小写（开发期再填）；交互 core Enter 且无默认值 → 同 ps1 回退小写
    return name.lower()


def copy_template(target: Path) -> list[str]:
    """复制模板到目标目录，返回实际复制的文件列表。

    与 init-project.ps1 对齐：
      - 跳过顶级目录（.git / logs / AI 工具目录）
      - 复制后递归清理构建产物/缓存目录
    """
    # 安全护栏：禁止复制到模板仓库自身内部（递归清理会摧毁模板源文件）。
    resolved_target = target.resolve()
    resolved_template = TEMPLATE_ROOT.resolve()
    if (
        resolved_target == resolved_template
        or resolved_template in resolved_target.parents
        or resolved_target in resolved_template.parents
    ):
        raise SystemExit(
            f"[FATAL] 目标目录 {target} 位于模板仓库内部或包含模板仓库，拒绝复制（防自删除）"
        )

    if target.exists():
        for item in target.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    target.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    # 仅跳过顶级目录/运行产物文件
    for item in TEMPLATE_ROOT.iterdir():
        if item.name in SKIP_TOP_DIRS:
            continue
        if item.name in SKIP_TOP_FILES:
            continue
        rel = item.relative_to(TEMPLATE_ROOT)
        dst = target / rel
        if item.is_dir():
            shutil.copytree(item, dst, dirs_exist_ok=True)
        elif item.is_file():
            shutil.copy2(item, dst)
            copied.append(str(rel))

    # 复制后单趟遍历：递归清理构建产物/缓存目录 + 收集实际复制文件
    # （原实现对每个 CLEANUP_DIRS 各做一次 rglob，O(13N)；合并为单趟 O(N)）
    for p in target.rglob("*"):
        if p.is_dir() and p.name in CLEANUP_DIRS:
            shutil.rmtree(p, ignore_errors=True)
        elif p.is_file():
            rel = p.relative_to(target)
            if str(rel) not in copied:
                copied.append(str(rel))

    return copied


def _in_skip_dirs(path: Path, target: Path) -> bool:
    """判断 path 是否位于 SKIP_PLACEHOLDER_DIRS 顶层目录内（如 tests/ 测试夹具）。"""
    try:
        rel = path.relative_to(target)
    except ValueError:
        return False
    return any(part in SKIP_PLACEHOLDER_DIRS for part in rel.parts)


def collect_placeholders(target: Path) -> set[str]:
    """扫描目标目录中全部 {{...}} 占位符（去重，跳过 tests/ 测试夹具目录）。"""
    all_placeholders: set[str] = set()
    for f in target.rglob("*"):
        if f.is_file() and not _in_skip_dirs(f, target):
            try:
                all_placeholders.update(scan_placeholders(f.read_text(encoding="utf-8")))
            except (UnicodeDecodeError, OSError):
                continue
    return all_placeholders


def build_replacements(
    target: Path, manifest: dict[str, dict[str, str]], values: dict[str, str], interactive: bool
) -> tuple[dict[str, str], set[str]]:
    """为全部占位符生成替换值，返回 (replacements, undeclared)。

    undeclared = 出现在文件中但未在 manifest/values 登记的占位符名集合——
    这类 token 是元文档引用（如 {{...}} 字面量），应保留原样不替换。

    非交互模式下先聚合全部"core 且无默认值且未提供"的占位符，一次性报错并给出
    --values 模板（镜像 init-project.ps1 的 fail-fast，但避免逐个报错往返 20 次，
    2026-08 Max 审查 P2 修复）。
    """
    names = sorted(collect_placeholders(target))
    if not interactive:
        missing_core = [
            name
            for name in names
            if name not in values
            and name in manifest
            and manifest[name].get("category") == "core"
            and "default" not in manifest[name]
        ]
        if missing_core:
            example = json.dumps(dict.fromkeys(missing_core, "..."))
            raise SystemExit(
                "[FATAL] 非交互模式下以下 core 占位符无默认值，请通过 --values 提供："
                + ", ".join(missing_core)
                + f"\n        示例 --values: {example}"
            )
    replacements: dict[str, str] = {}
    undeclared: set[str] = set()
    for name in names:
        value = get_placeholder_value(name, manifest, values, interactive)
        if value is None:
            undeclared.add(name)
        else:
            replacements[name] = value
    return replacements, undeclared


def replace_placeholders(
    target: Path, replacements: dict[str, str], undeclared: set[str] | None = None
) -> tuple[int, int]:
    """替换目标目录中所有文件内的占位符，返回（已替换文件数，剩余占位符数）。

    undeclared：未登记占位符名集合——这些 token 保留原样且不计入 remaining。
    """
    undeclared = undeclared or set()
    replaced_files = 0
    remaining = 0
    pattern = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

    # 替换值合法性检查（P3-21，纵深防御）：值由运行者本人提供（非权限边界），
    # 但含换行/花括号（含 GH Actions `${{ }}`）的值会直接改写生成项目的 CI 工作流或代码语义。
    for name, val in replacements.items():
        if ("\n" in val) or ("\r" in val) or ("{{" in val):
            print(
                f"[WARN] 占位符 {name} 的值含换行/花括号等特殊字符，"
                f"可能破坏目标文件语义: {val[:40]!r}"
            )

    for f in target.rglob("*"):
        if not f.is_file() or _in_skip_dirs(f, target):
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
            if name in replacements:
                return replacements[name]
            if name not in undeclared:
                _m.append(name)
            return m.group(0)

        new_content = pattern.sub(_replace, content)
        if new_content != content:
            f.write_bytes(new_content.encode("utf-8"))
            replaced_files += 1
        remaining += len(set(missing))

    return replaced_files, remaining


def _normalize_values(raw: dict) -> dict[str, str]:
    """归一化 --values 键：兼容带/不带 {{}} 两种写法（与 init-project.ps1 对齐）。"""
    return {k.strip().strip("{}"): v for k, v in raw.items()}


def _reset_changelog(target: Path) -> None:
    """将 CHANGELOG.md 重置为新项目初始态（模板自身变更历史不属于新项目）。

    与 init-project.ps1 对齐；拼接占位符键避免源文件内字面量被自扫描替换。
    """
    changelog = target / "CHANGELOG.md"
    if not changelog.exists():
        return
    init_text = (
        "# Changelog\n\n"
        "All notable changes to this project.\n\n"
        "格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)"
        " 与 [Semantic Versioning](https://semver.org/lang/zh-CN/)。\n\n"
        "## [Unreleased]\n\n"
        "> 新项目初始状态：首个功能落地后在此登记变更。\n"
    )
    changelog.write_text(init_text, encoding="utf-8", newline="\n")
    print("==> CHANGELOG.md 已重置为新项目初始态")


def _reset_release_manifest(target: Path, replacements: dict[str, str]) -> None:
    """将 .release-please-manifest.json 重置为新项目初始版本（模板自身发布版本不属于新项目）。

    与 _reset_changelog 同理（P4 审查修复）：模板仓库的 manifest 携带自身发布版本（如 0.1.2），
    直接复制会使新项目 manifest 与 pyproject.toml（version 占位符）版本漂移，
    触发 verify-docs.py 版本一致性门禁。
    """
    manifest_path = target / ".release-please-manifest.json"
    if not manifest_path.exists():
        return
    version = replacements.get("VERSION") or "0.1.0"
    manifest_path.write_text(
        json.dumps({".": version}, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"==> .release-please-manifest.json 已重置为版本 {version}")


def _slugify_package_name(name: str) -> str:
    """项目名 → 合法包名（PEP 508）：小写、非字母数字转连字符、折叠连续连字符。"""
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
    return slug.strip("-") or "my-project"


def _reset_pyproject_identity(target: Path, replacements: dict[str, str]) -> None:
    """重置复制进新项目的根 pyproject.toml：版本号 + [project] 身份（name/description）。

    根 pyproject.toml 是模板仓库自身开发配置（无占位符，init 不替换），直接复制会让新项目：
      - 版本与 .release-please-manifest.json（已重置为 VERSION）漂移（P4 修复）；
      - **包元数据仍是模板自己**（name = "vibe-coding-template"、description 讲的是治理模板），
        生成的项目执行 pip install -e . 会装出一个与项目无关的包名（2026-10-11 去伪修复）。
    """
    path = target / "pyproject.toml"
    if not path.exists():
        return
    version = replacements.get("VERSION") or "0.1.0"
    project_name = replacements.get("PROJECT_NAME") or ""
    description = replacements.get("ONE_LINE_DESCRIPTION") or ""
    text = path.read_text(encoding="utf-8")
    new_text = re.sub(
        r'^version\s*=\s*["\']([^"\']+)["\']',
        f'version = "{version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if project_name:
        new_text = re.sub(
            r'^name\s*=\s*["\'][^"\']*["\']',
            f'name = "{_slugify_package_name(project_name)}"',
            new_text,
            count=1,
            flags=re.MULTILINE,
        )
    if description:
        new_text = re.sub(
            r'^description\s*=\s*["\'][^"\']*["\']',
            "description = " + json.dumps(description, ensure_ascii=False),
            new_text,
            count=1,
            flags=re.MULTILINE,
        )
    if new_text != text:
        path.write_text(new_text, encoding="utf-8", newline="\n")
        print(
            f"==> pyproject.toml 已重置：版本 {version}"
            + (f"；包名 {_slugify_package_name(project_name)}" if project_name else "")
        )


def _prune_examples(target: Path) -> None:
    """默认不带 examples/：删除示例目录，并同源裁剪引用它的结构声明与 CI paths。

    不裁引用会让生成项目 verify-docs.py --strict 直接红（project-structure.md 的目录树
    仍声明 examples/ → check_dirs 报"缺失目录"；AGENTS.md 与它按顶层目录集合比对）。
    行级裁剪规则（模板仓库的树格式固定）：
      - project-structure.md：命中 "── examples/" 的行 + 其后连续的 "│" 续行
      - AGENTS.md / CLAUDE.md：命中 "── examples/" 的单行
      - ci.yml：整行为 - "examples/**" 的条目
    """
    examples_dir = target / "examples"
    if examples_dir.exists():
        shutil.rmtree(examples_dir, ignore_errors=True)

    def _strip_tree_block(path: Path) -> bool:
        if not path.is_file():
            return False
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        out: list[str] = []
        i = 0
        changed = False
        while i < len(lines):
            if "── examples/" in lines[i]:
                changed = True
                i += 1
                while i < len(lines) and lines[i].lstrip().startswith("│"):
                    i += 1
                continue
            out.append(lines[i])
            i += 1
        if changed:
            path.write_text("".join(out), encoding="utf-8", newline="\n")
        return changed

    _strip_tree_block(target / "docs" / "governance" / "project-structure.md")
    _strip_tree_block(target / "AGENTS.md")
    _strip_tree_block(target / "CLAUDE.md")

    ci_file = target / ".github" / "workflows" / "ci.yml"
    if ci_file.is_file():
        lines = ci_file.read_text(encoding="utf-8").splitlines(keepends=True)
        kept = [ln for ln in lines if ln.strip() != '- "examples/**"']
        if len(kept) != len(lines):
            ci_file.write_text("".join(kept), encoding="utf-8", newline="\n")
    print("==> examples/ 参考示例未复制（需要时用 --with-examples，或从模板仓库复制 examples/）")


def _refresh_doc_counts(target: Path) -> None:
    """运行生成项目的 gen-doc-counts.py 刷新 AUTO_COUNTS（manifest 裁剪后计数已变）。

    不刷新会让生成项目首次运行 `gen-doc-counts.py --check` / verify-all 必红
    （README 仍标注模板的占位符数，而 manifest 已裁剪——2026-09 模板自测实证）。
    与 init-project.ps1 的对等步骤保持行为一致（同源脚本，双实现各跑一次）。
    """
    script = target / "scripts" / "gen-doc-counts.py"
    if not script.exists():
        return
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(target),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        print(
            f"[WARN] 文档计数同步失败（退出码 {proc.returncode}）："
            f"{proc.stdout.strip() or proc.stderr.strip()[:200]}"
        )
    else:
        print("==> 文档计数标记已同步（AUTO_COUNTS）")


def _prune_placeholder_manifest(target: Path) -> None:
    """裁剪生成项目 scripts/placeholders.json：仅保留替换后仍被引用的条目。

    背景（2026-08 审查）：verify-registries.py 的死条目硬门禁要求 manifest 声明的条目必须被
    文件引用。初始化后全部已登记占位符都被替换（如 {{YEAR}} 在 LICENSE、{{WHEN_TO_USE}} 在
    user-manual.md），若 manifest 原样复制，生成项目每次跑 verify-registries 都会报大量死条目
    FAIL（下游 quality-gate 恒红，test-template.ps1 未跑该门禁故长期未被发现）。
    """
    path = target / "scripts" / "placeholders.json"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    manifest = data.get("placeholders", {})
    if not isinstance(manifest, dict):
        return
    referenced: set[str] = set()
    pattern = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
    for f in target.rglob("*"):
        if not f.is_file() or _in_skip_dirs(f, target):
            continue
        if f.suffix in (".pyc", ".dll", ".exe", ".xll", ".pdb"):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        referenced.update(pattern.findall(text))
    kept = {k: v for k, v in manifest.items() if k in referenced}
    if len(kept) == len(manifest):
        return
    data["placeholders"] = kept
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        f"==> scripts/placeholders.json 已裁剪：{len(manifest)} → {len(kept)} 个占位符"
        "（仅保留替换后仍被引用的条目）"
    )


_TEMPLATE_ONLY_START = b"<!-- TEMPLATE_ONLY_START -->"
_TEMPLATE_ONLY_END = b"<!-- TEMPLATE_ONLY_END -->"


def _trim_trailing_blank_lines(data: bytes) -> bytes:
    """裁掉文件尾部多余的空行，保留最后一行内容的行尾风格（CRLF/LF 不变）。"""
    base = data.rstrip(b" \t\r\n")
    if not base:
        return data  # 整文件为空白：原样返回，不动
    rest = data[len(base) :]  # 原文件尾部空白区（空格/换行）
    nl = rest.find(b"\n")
    if nl < 0:
        return base + b"\n"  # 尾部无换行：补一个 LF
    term = b"\r\n" if nl > 0 and rest[nl - 1 : nl] == b"\r" else b"\n"
    return base + term


def _strip_template_only_blocks(data: bytes) -> bytes:
    """删除 data 中被 TEMPLATE_ONLY 标记圈定的模板专属段落，字节级处理。

    模板仓库的 README 同时充当「下游项目模板」与「自身落地页」：落地页需要自我
    说明，但模板专属内容（如「从本模板初始化新项目」）不应被复制进新项目。
    - 删除 [START, END 行尾) 整段：保留 START 前一行（其行尾归前行所有，避免
      中间位置段落删除后相邻行并到一起），吞掉 END 标记所在行的行尾换行。
    - 配对 END 用深度计数：段内文档若引用了标记字面量（成对出现），视为嵌套
      而不当作真实段落边界，防说明文字把段落中途截断。
    - 删过段落后再裁掉文件尾部遗留的空行（模板专属段落常位于文件末尾）。
    - 遇到未闭合的 START（其后无 END）→ 停止处理并保留该段，防误删文件后半部分。
    """
    result = data
    removed = False
    while True:
        i = result.find(_TEMPLATE_ONLY_START)
        if i < 0:
            break
        # 从该 START 起做深度计数，找配对的真实 END
        depth = 1
        pos = i + len(_TEMPLATE_ONLY_START)
        end_pos = -1
        while depth > 0:
            next_s = result.find(_TEMPLATE_ONLY_START, pos)
            next_e = result.find(_TEMPLATE_ONLY_END, pos)
            if next_e < 0:
                break  # 未闭合
            if next_s >= 0 and next_s < next_e:
                depth += 1  # 段内出现的 START 字面量 → 深度 +1
                pos = next_s + len(_TEMPLATE_ONLY_START)
            else:
                depth -= 1  # END：深度回到 0 才视为真实段落边界
                end_pos = next_e
                pos = next_e + len(_TEMPLATE_ONLY_END)
        if end_pos < 0:
            break  # 未闭合 → 保留该段，停止处理
        removed = True
        j = end_pos + len(_TEMPLATE_ONLY_END)
        # 吞掉 END 标记所在行末尾的一个换行（CRLF/LF）
        if j < len(result) and result[j : j + 1] in (b"\r", b"\n"):
            j += 1
            if j < len(result) and result[j : j + 1] == b"\n":
                j += 1
        result = result[:i] + result[j:]
    if removed:
        return _trim_trailing_blank_lines(result)
    return result


def strip_template_only_sections(target: Path) -> int:
    """从目标目录全部 .md 文档删除 TEMPLATE_ONLY 标记段落，返回修改文件数。

    与 _reset_changelog 同属「复制后清理」：模板专属内容不进入新项目。
    字节级读写以保留原文件换行风格（CRLF/LF）；未闭合标记保留原样并告警。
    """
    modified = 0
    for f in target.rglob("*.md"):
        if _in_skip_dirs(f, target):
            continue
        try:
            raw = f.read_bytes()
        except OSError:
            continue
        new_raw = _strip_template_only_blocks(raw)
        if new_raw != raw:
            f.write_bytes(new_raw)
            modified += 1
        unclosed = (
            b"<!-- TEMPLATE_ONLY_START -->" in new_raw
            and b"<!-- TEMPLATE_ONLY_END -->" not in new_raw
        )
        if unclosed:
            try:
                rel = f.relative_to(target)
            except ValueError:
                rel = f
            print(f"[WARN] {rel} 含未闭合 TEMPLATE_ONLY 标记（仅 START），段落已保留")
    return modified


def _setup_git(target: Path) -> bool:
    """初始化 git 仓库并配置 commit-msg hook。成功返回 True。"""
    import subprocess

    print("\n==> 初始化 git 仓库")
    try:
        r = subprocess.run(["git", "init"], cwd=target, capture_output=True)
    except FileNotFoundError:
        print("[ERROR] git 不可用：请先安装 git 或去掉 --git-init")
        return False
    if r.returncode != 0:
        print(f"[ERROR] git init 失败: {r.stderr.decode('utf-8', 'replace').strip()}")
        return False
    hook_path = target / "scripts" / "git-hooks"
    r2 = subprocess.run(
        ["git", "config", "core.hooksPath", "scripts/git-hooks"], cwd=target, capture_output=True
    )
    if r2.returncode != 0:
        err = r2.stderr.decode("utf-8", "replace").strip()
        print(f"[WARN] git config core.hooksPath 失败: {err}")
        print(f"    生成的仓库可能不带 commit-msg 校验（hook 目录: {hook_path}）")
    else:
        print(f"    git init 完成（commit-msg hook 已配置: {hook_path}）")
    return True


def _create_compat_links(target: Path) -> None:
    """创建 CLAUDE.md 副本（Claude Code 兼容）。"""
    agents_md = target / "AGENTS.md"
    claude_md = target / "CLAUDE.md"
    if agents_md.exists():
        shutil.copy2(agents_md, claude_md)
        print("    已创建 CLAUDE.md（AGENTS.md 副本，供 Claude Code 读取）")
        print("    注意: AGENTS.md 更新后需重新创建 CLAUDE.md 副本")


def _is_reparse_point(p: Path) -> bool:
    """判断路径是否为重解析点（符号链接 / Windows junction）。

    Path.is_symlink() 对 Windows junction（mklink /J）返回 False（2026-08 Max 审查实证），
    需额外检测 FILE_ATTRIBUTE_REPARSE_POINT（0x400）位；3.12+ 可用 Path.is_junction()。
    与 init-project.ps1 的 ReparsePoint 拒绝语义对齐。
    """
    if p.is_symlink():
        return True
    try:
        if hasattr(p, "is_junction"):  # Python 3.12+
            return bool(p.is_junction())
        attrs = getattr(p.stat(), "st_file_attributes", 0)  # Windows 专属，非 Windows 为 0
        return bool(attrs & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT
    except (OSError, AttributeError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="从模板初始化新项目（跨平台 Python 版）")
    parser.add_argument("target", help="目标目录路径")
    parser.add_argument(
        "--values",
        default="",
        help='占位符值 JSON，如 \'{"PROJECT_NAME": "MyApp", "VERSION": "1.0.0"}\''
        "（注意：Windows PowerShell 5.1 会吞掉参数内的双引号导致 JSON 失效，"
        "该平台请改用 --values-file 或 init-project.ps1 的 -Values 哈希表）",
    )
    parser.add_argument(
        "--values-file",
        default="",
        help='从 JSON 文件读取占位符值（"-" 表示读 stdin）。'
        "脚本化/CI 首选：不受 shell 引号转义影响（Windows 与 POSIX 行为一致）",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="非交互模式（core 占位符用 default 填充；无默认值必须 --values 提供，"
        "否则报错退出——与 init-project.ps1 对齐，"
        "防生成 build_cmd 式损坏命令）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="覆盖已存在的非空目标目录（与 init-project.ps1 -Force 对齐）",
    )
    parser.add_argument(
        "--with-examples",
        action="store_true",
        help="带上 examples/ 参考示例（多语言 Core/CrossVal/测试闭环演示）。"
        "默认不带：新项目不需要 6 语言示例与 npm lockfile——需要时再加该开关，"
        "或直接从模板仓库复制 examples/",
    )
    parser.add_argument(
        "--git-init", action="store_true", help="初始化 git 仓库并配置 commit-msg hook"
    )
    parser.add_argument(
        "--create-compatibility-links",
        action="store_true",
        help="创建 CLAUDE.md 副本（Claude Code 兼容）",
    )
    args = parser.parse_args()

    # 目标自身是符号链接/junction（重解析点）时拒绝：resolve() 会解引用链接，copy_template 的
    # iterdir/rmtree 将穿透链接删除真实目录内容（镜像 init-project.ps1 的重解析点拒绝，
    # 2026-08 Max 审查 #7 修复；中间路径组件的 junction 由 resolve() 物理解析后
    # 由下方防自删除守卫覆盖）。注意 is_symlink() 对 Windows junction 返回 False，
    # 必须用 _is_reparse_point（含 FILE_ATTRIBUTE_REPARSE_POINT 位检测）。
    if _is_reparse_point(Path(args.target)):
        print(f"[ERROR] 目标路径是符号链接/junction: {args.target}（请使用实际目录，防穿透删除）")
        return 1
    target = Path(args.target).resolve()
    if target.exists():
        if not target.is_dir():
            print(f"[ERROR] 目标路径是文件，不是目录: {target}")
            return 1
        if any(target.iterdir()) and not args.force:
            print(f"[ERROR] 目标目录非空: {target}（如确需覆盖请加 --force）")
            return 1
    # target 不能在模板仓库内、等于模板根、或是模板仓库的祖先：copy_template 会先删除
    # target 自身内容，若目标是模板祖先会连模板仓库与同级项目一并删除（防自删除，P3-20）
    if (
        target == TEMPLATE_ROOT
        or target.is_relative_to(TEMPLATE_ROOT)
        or TEMPLATE_ROOT.is_relative_to(target)
    ):
        print(f"[ERROR] target 不能在模板仓库内、等于模板根或包含模板仓库: {target}")
        return 1

    print(f"==> 复制模板到 {target}")
    copied = copy_template(target)
    print(f"    复制了 {len(copied)} 个文件")
    if (target / "examples").exists():
        # P6 审查修复：examples/ 为参考示例，明确告知去向（不需要可删除，
        # 删除后需同步 project-structure.md/AGENTS.md 目录树，否则
        # verify-docs --strict 报未声明/缺失）
        print(
            "    [提示] examples/ 示例项目已复制（参考用途：演示多语言 Core/CrossVal/测试写法，"
            "不需要可整体删除；删除后请同步 docs/governance/project-structure.md"
            " 与 AGENTS.md 目录树）"
        )

    # 删除模板专属段落（README 的「从本模板初始化新项目」等不进入新项目；
    # 在占位符收集前执行，被删段落内的 {{...}} 示例不计入下游替换清单）
    stripped = strip_template_only_sections(target)
    if stripped:
        print(f"    删除了 {stripped} 个文件中的模板专属段落")

    # 加载占位符 manifest
    manifest = load_manifest()

    # 解析 --values / --values-file（键归一化：兼容 {{X}} 与 X 两种写法，键本身不进入替换扫描）
    values: dict[str, str] = {}
    raw_json = args.values
    if args.values_file:
        if args.values_file == "-":
            raw_json = sys.stdin.read()
        else:
            values_path = Path(args.values_file)
            if not values_path.is_file():
                print(f"[ERROR] --values-file 文件不存在: {values_path}")
                return 1
            raw_json = values_path.read_text(encoding="utf-8")
    if raw_json:
        try:
            values = _normalize_values(json.loads(raw_json))
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"[ERROR] 占位符值 JSON 解析失败: {e}")
            print(
                "        若是 Windows PowerShell，双引号会在传给原生命令时被吞掉——\n"
                "        改用 --values-file values.json（或 PowerShell 版 -Values @{...}）；\n"
                "        也可用 --values-file - 从 stdin 读取。"
            )
            return 1

    # 收集所有占位符并生成替换值
    # 交互询问按占位符决定（core 且未在 values 中才询问），不因传了任一 values 就整体关闭
    interactive = not args.non_interactive
    replacements, undeclared = build_replacements(target, manifest, values, interactive)

    # 执行替换
    replaced_files, remaining = replace_placeholders(target, replacements, undeclared)

    print("\n==> 占位符替换完成")
    print(f"    替换文件数: {replaced_files}")
    if undeclared:
        names = ", ".join(sorted(undeclared))
        print(
            f"    [WARN] {len(undeclared)} 个未登记占位符保留原样"
            f"（如需替换请登记 placeholders.json）: {names}"
        )
    if remaining:
        print(f"    [WARN] {remaining} 个占位符未替换（content 类，需开发期手动填充）")

    # 重置 CHANGELOG / 版本基线 / 版本号 / 占位符 manifest（与 ps1 对齐，
    # 避免新项目携带模板发布历史、版本漂移或死条目门禁 FAIL）
    if not args.with_examples:
        _prune_examples(target)

    _reset_changelog(target)
    _reset_release_manifest(target, replacements)
    _reset_pyproject_identity(target, replacements)
    _prune_placeholder_manifest(target)
    _refresh_doc_counts(target)

    # git init
    if args.git_init and not _setup_git(target):
        return 1

    # CLAUDE.md 兼容副本
    if args.create_compatibility_links:
        _create_compat_links(target)

    print("\n==> 初始化完成")
    return 0 if remaining == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
