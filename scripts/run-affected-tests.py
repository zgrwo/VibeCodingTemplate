#!/usr/bin/env python3
"""
run-affected-tests.py — 影响范围测试路由（git-diff → 受影响测试）

背景（来源：ExcelAddin run-affected-tests.ps1）：
  全量测试在大型项目耗时数分钟，增量开发只该跑受影响的测试。本脚本用 git diff
  定位变更的源文件，按命名约定映射到对应测试，只运行受影响的部分（增量 CI 模式）。

映射约定（可参数化）：
  - `src/foo/bar.py`        → 测试目录下含 `bar` 的 `test_*.py`
  - `src/foo/bar.cs`        → 测试目录下含 `Bar` 的 `*Tests.cs` / `test_*.py`
  - 无匹配测试 → 提示"可能缺测"，不静默跳过（防门禁说谎）

用法：
  python scripts/run-affected-tests.py                # 默认：HEAD~1 变更
  python scripts/run-affected-tests.py --base main    # 对比 main..HEAD
  python scripts/run-affected-tests.py --dry-run      # 只打印将运行的测试

退出码：0 = 找到并（尝试）运行；1 = 无对应测试 / git 错误
"""
import argparse
import contextlib
import subprocess
import sys
from pathlib import Path

with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent


def get_changed_files(base: str) -> list[str]:
    """返回 base..HEAD 变更的文件相对路径列表。"""
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only", base, "HEAD"],
            capture_output=True, text=True, timeout=15, cwd=ROOT,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if r.returncode != 0:
        return []
    return [line.strip() for line in r.stdout.splitlines() if line.strip()]


def source_stem(path: str) -> str:
    """从源文件路径提取测试匹配基名（去扩展名、取最后段）。"""
    return Path(path).stem


def _rel(path: Path) -> str:
    """输出相对路径；位于仓库外时回退绝对路径（防 relative_to ValueError）。"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def find_tests_for(source: str, tests_dir: Path) -> list[str]:
    """按命名约定把源文件映射到测试文件。"""
    stem = source_stem(source)
    if not stem or stem.startswith("__"):
        return []
    candidates = []
    for p in tests_dir.rglob("test_*.py"):
        if stem.lower() in p.name.lower():
            candidates.append(_rel(p))
    for p in tests_dir.rglob("*Tests.cs"):
        if stem.lower() in p.name.lower():
            candidates.append(_rel(p))
    return candidates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="影响范围测试路由")
    parser.add_argument("--base", default="HEAD~1", help="对比基准（默认 HEAD~1）")
    parser.add_argument("--dry-run", action="store_true", help="只打印不运行")
    args = parser.parse_args(argv)

    changed = get_changed_files(args.base)
    src_changes = [f for f in changed if f.startswith("src/")]
    if not src_changes:
        print("[SKIP] 无 src/ 变更（影响范围测试路由无需运行）")
        return 0

    tests_dir = ROOT / "tests"
    target_tests: list[str] = []
    unmatched: list[str] = []
    for f in sorted(src_changes):
        found = find_tests_for(f, tests_dir)
        if found:
            target_tests.extend(found)
        else:
            unmatched.append(f)

    if not target_tests:
        print("[FAIL] 变更的源文件无对应测试——疑似缺测，请补测试：")
        for f in unmatched:
            print(f"  - {f}")
        return 1

    target_tests = sorted(set(target_tests))
    print(f"变更源文件 {len(src_changes)} 个 → 目标测试 {len(target_tests)} 个：")
    for t in target_tests:
        print(f"  {t}")
    if unmatched:
        print(f"（{len(unmatched)} 个源文件无测试映射，见上 FAIL 提示）")

    if args.dry_run:
        print("\n[dry-run] 完成，未实际运行")
        return 0

    r = subprocess.run([sys.executable, "-m", "pytest", *target_tests, "-q"], cwd=ROOT)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
