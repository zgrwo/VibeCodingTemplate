#!/usr/bin/env python3
"""
falsy-audit.py — Falsy 陷阱静态审计（AST 增强版）

背景：Python 中 `if x:` 对 0/0.0/""/[]/{} 判假。
统计代码中 0 是有效值（效应量=0、均值=0、计数=0），必须用 `if x is not None:`。

检测方式（AST 优先，正则兜底）：
  - AST 解析：精确识别 if/while/or 模式 + 类型注解感知（Optional[float] 等）
  - 正则兜底：AST 解析失败的文件（语法错误/非 Python）用正则补检

检测变体：
  - `if x:`          —— 真值判断（HIGH 名单变量 = 高风险）
  - `if not x:`      —— 取反真值判断（数值 0 时同样误判）
  - `while x:`       —— 循环条件
  - `x or <default>` —— or 回退模式（threshold=0 时被默认值覆盖）
  - 变量名支持属性访问（`self.count` / `obj.offset`）与 `return x or <default>`

AST 增强（相比纯正则）：
  - 类型注解感知：`count: Optional[int] = None` → count 可能是 None，`if count:` 更危险
  - `is None` / `is not None` 精确排除（正则版也能排除，但 AST 版零误报）
  - 布尔类型注解 `flag: bool` → `if flag:` 安全，不报告
  - 集合类型注解 `data: list[float]` → `if data:` 安全，不报告

输出 HIGH（疑似 falsy 误判，必须修复）与 LOW（需人工确认）两级警告。

用法：
  python scripts/falsy-audit.py                 # 默认扫描 src/
  python scripts/falsy-audit.py --path tests/   # 指定目录
  python scripts/falsy-audit.py --no-ast        # 禁用 AST（回退纯正则模式）

验收标准：零 HIGH 风险警告（CI quality-gate 硬门禁）。
详见 rules/falsy-pitfalls.md（检查清单唯一定义处）。
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import re
import sys
from pathlib import Path

# Windows GBK 控制台：强制 UTF-8 输出
with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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

# 正则模式（AST 兜底 + 非 Python 文件）
IF_TRUTHY_RE = re.compile(r"^\s*if\s+(not\s+)?([\w.]+)\s*:")
WHILE_TRUTHY_RE = re.compile(r"^\s*while\s+(not\s+)?([\w.]+)\s*:")
OR_FALLBACK_RE = re.compile(r"(?:=\s*|return\s+)([\w.]+)\s+or\s+")

HIGH_RISK_RE = [re.compile(p) for p in HIGH_RISK_PATTERNS]
LOW_RISK_RE = [re.compile(p) for p in LOW_RISK_PATTERNS]

# 安全类型注解：如果变量有这些类型注解，`if x:` 是安全的
SAFE_TYPES_BOOL = {"bool", "boolean"}
SAFE_TYPES_COLLECTION = {"list", "set", "dict", "frozenset", "deque", "tuple"}


def _classify(var: str) -> str:
    """返回 'HIGH' / 'LOW' / ''（名单外）。"""
    for pattern in HIGH_RISK_RE:
        if pattern.search(var):
            return "HIGH"
    for pattern in LOW_RISK_RE:
        if pattern.search(var):
            return "LOW"
    return ""


# ========== AST 审计器 ==========

class FalsyAuditor(ast.NodeVisitor):
    """AST 遍历器：检测 falsy 陷阱 + 类型注解感知。"""

    def __init__(self, filename: str):
        self.filename = filename
        self.findings: list[tuple[str, str, int, str, str]] = []
        # 变量 → 类型注解映射（从 AnnAssign 收集）
        self._type_hints: dict[str, str] = {}

    def _var_name(self, node: ast.expr) -> str | None:
        """提取变量名（支持 Name / Attribute / Constant）。"""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parts = []
            cur = node
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            return ".".join(reversed(parts))
        return None

    def _is_safe_type(self, var: str) -> bool:
        """检查变量是否有安全类型注解（bool/collection）。"""
        hint = self._type_hints.get(var, "")
        if not hint:
            return False
        low = hint.lower()
        # bool 类型：if flag: 安全
        if any(t in low for t in SAFE_TYPES_BOOL):
            return True
        # 集合类型：if data: 安全（空集合语义正确）
        return bool(any(t in low for t in SAFE_TYPES_COLLECTION))

    def _check_truthy(self, test: ast.expr, kind: str, lineno: int,
                      line_text: str) -> None:
        """检查 if/while 的条件是否为 falsy 风险。"""
        # 跳过：is None / is not None / 比较 / 逻辑运算
        if isinstance(test, (ast.Compare, ast.BoolOp)):
            return
        # not x → 解包内层
        if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            inner = test.operand
        else:
            inner = test

        var = self._var_name(inner)
        if not var:
            return

        level = _classify(var)
        if not level:
            return

        # 类型注解感知：bool/collection 类型安全
        base_var = var.split(".")[0] if "." in var else var
        if self._is_safe_type(base_var):
            return

        self.findings.append((level, var, lineno, line_text, kind))

    def _check_or_fallback(self, node: ast.AST, kind: str) -> None:
        """检查 x or default 模式。"""
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            for val in node.values:
                var = self._var_name(val)
                if var:
                    level = _classify(var)
                    if level:
                        base_var = var.split(".")[0] if "." in var else var
                        if not self._is_safe_type(base_var):
                            self.findings.append(
                                (level, var, node.lineno, kind, "or 回退")
                            )
                break  # 只检查第一个操作数

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """收集类型注解：var: Type = value"""
        if isinstance(node.target, ast.Name) and node.annotation:
            try:
                hint = ast.unparse(node.annotation)
                self._type_hints[node.target.id] = hint
            except Exception:
                pass
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """检查 if 条件。"""
        line_text = f"if {ast.unparse(node.test)}:" if hasattr(ast, 'unparse') else "if ...:"
        self._check_truthy(node.test, "if", node.lineno, line_text)
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        """检查 while 条件。"""
        line_text = f"while {ast.unparse(node.test)}:" if hasattr(ast, 'unparse') else "while ...:"
        self._check_truthy(node.test, "while", node.lineno, line_text)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """检查 result = x or default 模式。"""
        if node.value and isinstance(node.value, ast.BoolOp):
            self._check_or_fallback(node.value, "assign or")
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        """检查 return x or default 模式。"""
        if node.value and isinstance(node.value, ast.BoolOp):
            self._check_or_fallback(node.value, "return or")
        self.generic_visit(node)


def audit_file_ast(path: Path) -> list[tuple[str, str, int, str, str]] | None:
    """AST 模式审计一个文件。"""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return None  # AST 解析失败 → 返回 None 触发正则兜底

    auditor = FalsyAuditor(str(path))
    auditor.visit(tree)
    return auditor.findings


# ========== 正则兜底审计器 ==========

def audit_file_regex(path: Path) -> list[tuple[str, str, int, str, str]]:
    """正则兜底：AST 解析失败时使用。"""
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


def audit_file(path: Path, use_ast: bool = True) -> list[tuple[str, str, int, str, str]]:
    """审计一个文件：AST 优先，正则兜底。"""
    if use_ast:
        ast_findings = audit_file_ast(path)
        if ast_findings is not None:
            return ast_findings
    return audit_file_regex(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Falsy 陷阱审计（AST 增强版）")
    parser.add_argument("--path", default=DEFAULT_SCOPE, help="扫描目录")
    parser.add_argument("--no-ast", action="store_true", help="禁用 AST（回退纯正则模式）")
    args = parser.parse_args()

    scope = ROOT / args.path
    if not scope.exists():
        print(f"[FAIL] 目录不存在: {scope}")
        return 1

    use_ast = not args.no_ast
    high: list = []
    low: list = []
    for p in sorted(scope.rglob("*.py")):
        for level, var, lineno, code, kind in audit_file(p, use_ast=use_ast):
            target = (high if level == "HIGH" else low)
            target.append((str(p.relative_to(ROOT)), var, lineno, code, kind))

    if high:
        print(f"[FAIL] 发现 {len(high)} 个 HIGH 风险（falsy 误判，必须修复）：")
        for path, _var, lineno, code, kind in high:
            print(f"  {path}:{lineno} [{kind}] {code} — 数值 0 可能被误判为 False，"
                  f"应改为 `is not None`")
    if low:
        print(f"[WARN] {len(low)} 个 LOW 风险（需人工确认 0 是否为有效值）：")
        for path, var, lineno, code, kind in low:
            print(f"  {path}:{lineno} [{kind}] {code} — 变量 `{var}` 在名单内")
    if not high and not low:
        mode = "AST 增强模式" if use_ast else "纯正则模式"
        print(f"[OK] 未发现 falsy 高风险模式（{mode}）")
    return 1 if high else 0


if __name__ == "__main__":
    sys.exit(main())
