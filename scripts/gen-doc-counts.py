#!/usr/bin/env python3
"""
gen-doc-counts.py — 文档计数自动注入（AUTO_COUNTS 标记）

背景（来自 cross-project-synthesis.md 高频修复模式「文档数字漂移 6+」）：
  函数计数/模块计数在多处硬编码，更新时遗漏。本脚本把"文档中的数字"变成
  由源代码自动推导的标记块，从根上消除手工同步。

用法：
  python scripts/gen-doc-counts.py            # 用当前值就地更新文档中的标记块
  python scripts/gen-doc-counts.py --check    # 仅比对（不写入）；不一致则退出码 1
  python scripts/gen-doc-counts.py --config x.json

文档中的标记语法：
  <!-- AUTO_COUNTS:KEY_START -->
  <当前值将被替换>
  <!-- AUTO_COUNTS:KEY_END -->

配置格式（scripts/doc-counts.json）：
  {
    "counts": {
      "tests":   {"type": "regex_count", "pattern": "^def test_", "glob": "tests/**/*.py"},
      "scripts": {"type": "file_count",  "glob": "scripts/*.py"},
      "placeholders": {"type": "json_keys",
                       "path": "scripts/placeholders.json", "key_path": "placeholders"}
    },
    "docs": ["docs/architecture.md", "README.md"]
  }

counts 类型：
  - file_count  统计 glob 匹配的文件数
  - regex_count 统计 glob 匹配文件中的正则命中总数
  - json_keys   统计 JSON 对象键数（key_path 点分隔）

退出码：0 = 一致/更新完成；1 = --check 模式下发现不一致
"""
import argparse
import contextlib
import json
import re
import sys
from pathlib import Path

with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# AUTO_COUNTS 标记（纯文档内嵌）
_MARK_START = re.compile(r"<!-- AUTO_COUNTS:([A-Z0-9_]+)_START -->")
_MARK_END = re.compile(r"<!-- AUTO_COUNTS:([A-Z0-9_]+)_END -->")
_DEFAULT_CONFIG = str(ROOT / "scripts" / "doc-counts.json")


def _compute(key: str, spec: dict) -> int:
    """按 spec 计算一个计数源的当前值。"""
    ctype = spec.get("type", "file_count")
    if ctype == "file_count":
        files = list(ROOT.glob(spec.get("glob", "")))
        return len(files)
    if ctype == "regex_count":
        # 逐行匹配需 MULTILINE；`^\s*` 允许缩进（类内测试方法）
        pattern = re.compile(spec.get("pattern", ""), re.MULTILINE)
        total = 0
        for p in ROOT.glob(spec.get("glob", "")):
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            total += len(pattern.findall(text))
        return total
    if ctype == "json_keys":
        path = ROOT / spec.get("path", "")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return -1
        node = data
        for seg in spec.get("key_path", "").split("."):
            if not seg:
                break
            if isinstance(node, dict) and seg in node:
                node = node[seg]
            else:
                return -1
        return len(node) if isinstance(node, dict) else -1
    return -1


def compute_counts(counts: dict) -> dict[str, int]:
    """计算全部计数源的当前值。返回 {key: value}。"""
    return {key: _compute(key, spec) for key, spec in counts.items()}


def update_doc(path: Path, values: dict[str, int], check_only: bool) -> list[str]:
    """更新单个文档中的 AUTO_COUNTS 标记块。返回问题列表。"""
    if not path.exists():
        return [f"[配置错误] 文档不存在: {path}"]
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"[错误] 无法读取 {path}: {e}"]

    problems: list[str] = []
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    changed = False
    while i < len(lines):
        line = lines[i]
        m = _MARK_START.search(line)
        if not m:
            out.append(line)
            i += 1
            continue
        key = m.group(1)
        # 内联形态：START 与 END 同行（可能一行含多个标记对，须循环处理全部）。
        # 逐对替换并保留行内前后缀，直到行内无剩余 START。
        if _MARK_END.search(line):
            # 关键：替换生成的 `<!-- AUTO_COUNTS:X_START -->` 文本本身也匹配 _MARK_START，
            # 若从行首重新搜索会死循环。改用 pos 游标，每次从替换处之后继续搜索。
            new_line = line
            pos = 0
            while True:
                sm = _MARK_START.search(new_line, pos)
                if not sm:
                    break
                em = _MARK_END.search(new_line, sm.end())
                if not em:
                    problems.append(
                        f"[错误] {path} 内联 {sm.group(1)}_START 无对应 END（未闭合标记）"
                    )
                    break
                seg = new_line[sm.end():em.start()]
                expected = values.get(sm.group(1))
                if expected is None or expected < 0:
                    problems.append(
                        f"[配置错误] 文档引用未定义的计数源 `{sm.group(1)}`"
                    )
                    # 值未定义：跳过该对标记（保留原样），从 em.end() 后继续
                    pos = em.end()
                    continue
                if seg != str(expected):
                    changed = True
                replacement = (
                    f"<!-- AUTO_COUNTS:{sm.group(1)}_START -->"
                    + str(expected)
                    + f"<!-- AUTO_COUNTS:{sm.group(1)}_END -->"
                )
                new_line = new_line[:sm.start()] + replacement + new_line[em.end():]
                pos = sm.start() + len(replacement)
            out.append(new_line)
            i += 1
            continue
        # 块状形态：START 单独一行，END 在后续行。保留 START 行前导缩进与前缀文本，
        # 值行沿用相同缩进，避免破坏所在代码块/列表结构。
        j = i + 1
        block_lines: list[str] = []
        found_end = False
        while j < len(lines):
            if _MARK_END.search(lines[j]):
                found_end = True
                break
            block_lines.append(lines[j])
            j += 1
        if not found_end:
            problems.append(f"[错误] {path} 中 {key}_START 无对应 END（未闭合标记）")
            out.extend(lines[i:])
            break
        expected = values.get(key)
        if expected is None or expected < 0:
            problems.append(f"[配置错误] 文档引用未定义的计数源 `{key}`")
            out.extend(lines[i:j + 1])
        else:
            current_text = "".join(block_lines).strip()
            if current_text != str(expected):
                changed = True
            # 提取 START 行的缩进与前缀（`    <!-- AUTO_COUNTS:X_START --> 文字`）
            indent_match = re.match(r"^(\s*)", line)
            indent = indent_match.group(1) if indent_match else ""
            prefix = line[:m.start()]  # START 前文本（含缩进）
            suffix = line[m.end():].split("-->", 1)[1] if "-->" in line[m.end():] else ""
            # 沿用原行尾（CRLF/LF），避免混合行尾触发 eol=lf / mixed-line-ending 门禁
            term = "\r\n" if line.endswith("\r\n") else "\n"
            out.append(f"{prefix}<!-- AUTO_COUNTS:{key}_START -->{suffix}{term}")
            out.append(f"{indent}{expected}{term}")
            out.append(f"{indent}<!-- AUTO_COUNTS:{key}_END -->{term}")
        i = j + 1

    if check_only:
        if changed:
            problems.append(
                f"[FAIL] {path} 的 AUTO_COUNTS 计数已过时"
                "（运行 gen-doc-counts.py 更新）"
            )
    else:
        new_text = "".join(out)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            print(f"  [更新] {path} 计数已同步")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="文档计数自动注入")
    parser.add_argument("--check", action="store_true", help="仅比对不写入，不一致退出码 1")
    parser.add_argument("--config", default=_DEFAULT_CONFIG, help="计数源配置")
    args = parser.parse_args(argv)

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"[FAIL] 配置文件不存在: {cfg_path}")
        return 1
    try:
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[FAIL] 无法解析配置 {cfg_path}: {e}")
        return 1

    counts = config.get("counts", {})
    docs = config.get("docs", [])
    # 标记用大写 KEY（对齐占位符命名），配置用小写 key —— 建大写→小写映射
    values = {k.upper(): v for k, v in compute_counts(counts).items()}

    all_problems: list[str] = []
    for doc in docs:
        all_problems.extend(update_doc(ROOT / doc, values, args.check))

    if all_problems:
        for p in all_problems:
            print(p)
        return 1
    if args.check:
        print("[OK] 文档计数一致性验证通过")
    else:
        print("[OK] 文档计数更新完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
