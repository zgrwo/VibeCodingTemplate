#!/usr/bin/env python3
"""
verify-all.py — 全量验证入口（跨平台 Python 版）

职责：一个命令完成「构建 + 测试 + 文档一致性」全量验证。

设计：
  - 构建/测试自动探测（*.sln → dotnet；pyproject.toml → Python）
  - 未检测到构建系统时显式 [跳过] 并提示，不假装通过
  - 文档一致性依赖 Python（verify-docs/verify-manual/falsy-audit）

与 verify-all.ps1 功能对等，适用于 Linux/macOS 或无 PowerShell 环境。

用法：
  python scripts/verify-all.py            # 全量验证
  python scripts/verify-all.py --quick    # 仅构建 + 测试（跳过文档检查）

退出码：0 = 通过；非 0 = 失败（CI 可直接调用）
"""
from __future__ import annotations

import argparse
import contextlib
import subprocess
import sys
from pathlib import Path

with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


def run_step(name: str, cmd: list[str], cwd: Path | None = None) -> bool:
    """运行一个验证步骤，返回是否成功。"""
    print(f"\n=== {name} ===")
    print(f"  命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd or ROOT)
    except OSError as e:
        print(f"  [FAIL] {name} 失败（工具未找到: {e}）")
        return False
    if result.returncode != 0:
        print(f"  [FAIL] {name} 失败 (退出码 {result.returncode})")
        return False
    print(f"  [OK] {name} 通过")
    return True


def detect_build_system() -> tuple[str | None, list[str], list[str]]:
    """探测构建系统，返回 (类型, 构建命令, 测试命令)。"""
    # .NET
    sln_files = list(ROOT.glob("*.sln"))
    if sln_files:
        return (
            ".NET",
            ["dotnet", "build", "-c", "Release", str(sln_files[0])],
            ["dotnet", "test", "-c", "Release", str(sln_files[0])],
        )

    # Python
    if (ROOT / "pyproject.toml").exists():
        return (
            "Python",
            [PYTHON, "-m", "compileall", "-q", "src"],
            [PYTHON, "-m", "pytest", "tests/", "-x", "-q"],
        )

    return None, [], []


def main() -> int:
    parser = argparse.ArgumentParser(description="全量验证入口")
    parser.add_argument("--quick", action="store_true",
                        help="仅构建 + 测试（跳过文档检查）")
    args = parser.parse_args()

    build_type, build_cmd, test_cmd = detect_build_system()

    steps: list[tuple[str, list[str]]] = []

    if build_type:
        steps.append((f"构建 ({build_type})", build_cmd))
        steps.append((f"测试 ({build_type})", test_cmd))
    else:
        print("[SKIP] 未检测到构建系统（*.sln / pyproject.toml），跳过构建与测试")

    if not args.quick:
        py = PYTHON
        steps.append(("文档一致性", [py, "scripts/verify-docs.py", "--strict"]))
        steps.append(("手册一致性", [py, "scripts/verify-manual.py"]))
        steps.append(("Falsy 审计", [py, "scripts/falsy-audit.py"]))
        steps.append(("注册表一致性", [py, "scripts/verify-registries.py"]))
        steps.append(("文档计数一致性", [py, "scripts/gen-doc-counts.py", "--check"]))
        steps.append(("测试质量守卫", [py, "scripts/test-quality-guard.py"]))
        # 模板自身治理脚本的"缺测"检测（默认 --src src 在模板仓库为空转；
        # 2026-08 Max 审查 #D8 修复：scripts/ 公共函数必须被 tests/scripts 引用）
        steps.append(("测试质量守卫（scripts 缺测）",
                      [py, "scripts/test-quality-guard.py",
                       "--src", "scripts", "--tests", "tests/scripts"]))

    all_passed = True
    for name, cmd in steps:
        if not run_step(name, cmd):
            all_passed = False
            break  # 任一步失败立即停止

    if all_passed:
        print("\n[OK] 全量验证通过")
        return 0
    else:
        print("\n[FAIL] 验证失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
