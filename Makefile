# ============================================================================
# Makefile — 跨平台全量验证入口
# 使用方式：make verify / make docs / make test / make init
# 适用于 Linux/macOS/WSL 环境（Windows 用户可用 verify-all.ps1）
# ============================================================================

.PHONY: verify docs test init clean help build lint format

PYTHON ?= python

help:
	@echo "用法："
	@echo "  make verify  — 全量验证（构建+测试+文档一致性）"
	@echo "  make docs    — 仅文档一致性验证"
	@echo "  make test    — 仅运行测试"
	@echo "  make build   — 构建项目"
	@echo "  make lint    — 代码风格检查（ruff + prettier）"
	@echo "  make format  — 自动格式化（ruff format + prettier）"
	@echo "  make init    — 初始化新项目（需 TARGET=路径）"
	@echo "  make clean   — 清理缓存"
	@echo ""
	@echo "变量："
	@echo "  PYTHON=$(PYTHON)  — Python 解释器路径"
	@echo "  TARGET=/path       — init 目标路径"

verify:
	$(PYTHON) scripts/verify-all.py

docs:
	$(PYTHON) scripts/verify-docs.py --strict
	$(PYTHON) scripts/verify-manual.py
	$(PYTHON) scripts/falsy-audit.py

test:
	$(PYTHON) scripts/verify-all.py --quick

init:
	@if [ -z "$(TARGET)" ]; then echo "用法: make init TARGET=/path/to/project"; exit 1; fi
	$(PYTHON) scripts/init-project.py $(TARGET) --git-init

build:
	@if [ -f pyproject.toml ]; then $(PYTHON) -m compileall -q src; fi
	@if [ -f go.mod ]; then go build ./...; fi

lint:
	@if command -v ruff >/dev/null 2>&1; then ruff check scripts/ tests/; fi
	@if command -v prettier >/dev/null 2>&1; then prettier --check "**/*.{md,yaml,yml,json}"; fi

format:
	@if command -v ruff >/dev/null 2>&1; then ruff format scripts/ tests/; fi
	@if command -v prettier >/dev/null 2>&1; then prettier --write "**/*.{md,yaml,yml,json}"; fi

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
