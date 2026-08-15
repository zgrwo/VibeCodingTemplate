"""共享排除目录集合（SSOT，2026-08 Max 审查 #8 收敛）。

此前 verify-docs / verify-registries / init-project 各自维护 EXCLUDED_DIRS /
SKIP_TOP_DIRS 且集合已发散（如 verify-docs 缺 build/benchmarks/tests、registries
缺 .mypy_cache）。此处定义统一基线，各工具叠加用途专属项：
  - BASE_EXCLUDED_DIRS：任何语义下都不应处理的目录（VCS 内部 / AI 工具本地目录 /
    运行时产物 / 缓存）
  - 用途专属：verify-registries 追加 build/benchmarks（扫描排除模板资产目录）与
    tests/（占位符扫描夹具）；init-project 的复制语义取 BASE 子集（缓存目录改为
    复制后递归清理，build/ 等模板资产必须复制）

注意：init-project.ps1 的跳过/清理清单为 PowerShell 实现，修改 BASE 后需同步
（见 scripts/init-project.ps1 步骤 2 注释）。
"""
BASE_EXCLUDED_DIRS = frozenset({
    ".git", ".claude", ".codegraph", ".qoder",
    "logs", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    ".coverage",
})
