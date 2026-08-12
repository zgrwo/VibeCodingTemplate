# VibeCodingTemplate 架构设计

> 本文档记录模板仓库自身的设计决策。初始化新项目后替换为项目架构文档。

## 设计目标

1. **治理幻觉**：AI 会编造 API、跨越架构边界。AGENTS.md 宪法 + 防幻觉铁律 + 闭环验证。
2. **文档漂移**：SSOT + verify-docs.py --strict CI 硬门禁。
3. **知识传承**：从 5 个真实项目提炼反模式案例库。

## 架构分层

```
.github/workflows/     CI/CD 分层门禁（quick/full/quality/template-self-test）
AGENTS.md              项目宪法（四条核心准则、红线规则、防幻觉铁律）
├── rules/             规范文档（documentation.md 为 SSOT 权威）
├── skills/            编码技能（5 语言 + 3 位重构专家）
├── templates/         模块脚手架（NewModule + language + monorepo）
├── scripts/           验证脚本（AST 审计 + 初始化 + commit 校验）
├── examples/          示例项目（Python/TypeScript/Go）
└── tests/             验证脚本自测（<!-- AUTO_COUNTS:TESTS_START -->164<!-- AUTO_COUNTS:TESTS_END --> tests，见 tests/scripts/）
```

## 演进计划

- **吸收计划**：`docs/absorption-plan-2026-08.md` 记录从 5 个子项目反哺模板的高价值点（多注册表门禁 / 文档计数注入 / 跨语言验证 runner / 环境医生 / 测试质量门禁等），是跨会话执行的唯一依据。

## 关键设计决策

### ADR-0001：占位符双语法
- `{{...}}` → 项目级，init-project 自动替换（正则 `\{\{(\w+)\}\}`）
- {PascalCase} → 模块级，开发者手动替换（不被 init 匹配，避免误伤）

### ADR-0002：模板自举检测
CI 通过 `grep -rq '{{' AGENTS.md` 区分模板/项目模式（含任意未替换占位符，
而非特定 `{{PROJECT_NAME}}`，避免初始化替换 PROJECT_NAME 后检测失效）。
模板仓库无构建系统，占位符命令无法执行→自举检测跳过。

### ADR-0003：Python 跨平台优先
核心验证脚本 Python 实现，PowerShell 仅 Win 集成场景。
init-project 保留双版本（Win 需 BOM/CRLF 处理）。

### ADR-0004：哨兵值优于异常
NaN 表示无效，不抛异常。来源 costsuite 性能回归教训。
