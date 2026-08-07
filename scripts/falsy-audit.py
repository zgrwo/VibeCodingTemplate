#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
falsy-audit.py — Falsy 陷阱静态审计

背景：Python 中 `if x:` 对 0/0.0/""/[]/{} 判假。
统计代码中 0 是有效值（效应量=0、均值=0、计数=0），必须用 `if x is not None:`。

检测变体：
  - `if x:`          —— 真值判断（HIGH 名单变量 = 高风险）
  - `if not x:`      —— 取反真值判断（数值 0 时同样误判）
  - `while x:`       —— 循环条件
  - `x or <default>` —— or 回退模式（threshold=0 时被默认值覆盖）
  - 变量名支持属性访问（`self.count` / `obj.offset`）与 `return x or <default>`

输出 HIGH（疑似 falsy 误判，必须修复）与 LOW（需人工确认）两级警告。

用法：
  python scripts/falsy-audit.py                 # 默认扫描 src/
  python scripts/falsy-audit.py --path tests/   # 指定目录

验收标准：零 HIGH 风险警告（CI quality-gate 硬门禁）。
详见 rules/falsy-pitfalls.md（检查清单唯一定义处）。
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
DEFAULT_SCOPE = "src"

# 高风险变量名模式：统计量/参数/阈值，0 是有效值（rules/falsy-pitfalls.md 唯一定义）
HIGH_RISK_PATTERNS = [
    r"\b(?:effect_size|statistic|threshold|tolerance|alpha|sigma|mean|std|var)\b",
    r"\b(?:cp|cpk|ppm|correlation|coefficient|offset|shift|count)\b",
    r"\b\w*_shape\b",
    r"\b\w*_scale\b",
]

# 低风险（需人工确认）：0 可能是有效值的领域量
LOW_RISK_PATTERNS = [
    r"\b\w*_(?:ratio|rate|index|level|num|size|weight|percent|pct)\b",
    r"\b(?:ratio|rate|score|score_value)\b",
]

# 真值判断变体（排除 is None / is not None）；变量名支持 self.x / obj.attr
IF_TRUTHY_RE = re.compile(r"^\s*if\s+(not\s+)?([\w.]+)\s*:")
WHILE_TRUTHY_RE = re.compile(r"^\s*while\s+(not\s+)?([\w.]+)\s*:")
OR_FALLBACK_RE = re.compile(r"(?:=\s*|return\s+)([\w.]+)\s+or\s+")

HIGH_RISK_RE = [re.compile(p) for p in HIGH_RISK_PATTERNS]
LOW_RISK_RE = [re.compile(p) for p in LOW_RISK_PATTERNS]


def _classify(var: str) -> str:
    """返回 'HIGH' / 'LOW' / ''（名单外）。"""
    for pattern in HIGH_RISK_RE:
        if pattern.search(var):
            return "HIGH"
    for pattern in LOW_RISK_RE:
        if pattern.search(var):
            return "LOW"
    return ""


def audit_file(path: Path) -> list[tuple[str, str, int, str, str]]:
    """返回 [(级别, 变量, 行号, 代码, 变体)]。"""
    findings: list[tuple[str, str, int, str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return findings

    def probe(line: str, regex: re.Pattern, kind: str, i: int) -> None:
        m = regex.match(line)
        if not m:
            return
        var = m.group(2) if m.lastindex == 2 else m.group(1)
        level = _classify(var)
        if level:
            findings.append((level, var, i, line.strip(), kind))

    for i, line in enumerate(lines, 1):
        probe(line, IF_TRUTHY_RE, "if", i)
        probe(line, WHILE_TRUTHY_RE, "while", i)
        if not line.strip().startswith(("#", "'", '"')):
            m = OR_FALLBACK_RE.search(line)
            if m:
                level = _classify(m.group(1))
                if level:
                    findings.append((level, m.group(1), i, line.strip(), "or 回退"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Falsy 陷阱审计")
    parser.add_argument("--path", default=DEFAULT_SCOPE, help="扫描目录")
    args = parser.parse_args()

    scope = ROOT / args.path
    if not scope.exists():
        print(f"[FAIL] 目录不存在: {scope}")
        return 1

    high: list = []
    low: list = []
    for p in sorted(scope.rglob("*.py")):
        for level, var, lineno, code, kind in audit_file(p):
            target = (high if level == "HIGH" else low)
            target.append((str(p.relative_to(ROOT)), var, lineno, code, kind))

    if high:
        print(f"[FAIL] 发现 {len(high)} 个 HIGH 风险（falsy 误判，必须修复）：")
        for path, var, lineno, code, kind in high:
            print(f"  {path}:{lineno} [{kind}] {code} — 数值 0 可能被误判为 False，"
                  f"应改为 `is not None`")
    if low:
        print(f"[WARN] {len(low)} 个 LOW 风险（需人工确认 0 是否为有效值）：")
        for path, var, lineno, code, kind in low:
            print(f"  {path}:{lineno} [{kind}] {code} — 变量 `{var}` 在名单内")
    if not high and not low:
        print("[OK] 未发现 falsy 高风险模式")
    return 1 if high else 0


if __name__ == "__main__":
    sys.exit(main())
