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
└── tests/             验证脚本自测（<!-- AUTO_COUNTS:TESTS_START -->191<!-- AUTO_COUNTS:TESTS_END --> tests，见 tests/scripts/）
```

## 关键设计决策

### ADR-0001：占位符双语法
- `{{...}}` → 项目级，init-project 自动替换（正则 `\{\{([A-Z0-9_]+)\}\}`，仅匹配大写 token）
- {PascalCase} → 模块级，开发者手动替换（不被 init 匹配，避免误伤）

### ADR-0002：模板自举检测

CI 检测 `AGENTS.md` 中是否残留未替换的核心占位符 `PROJECT_NAME`（双花括号包裹）来区分模板/项目模式。
实现上刻意**检测特定占位符而非任意 `{{` 字面量**，原因有二：

1. **教学 token 残留**：`AGENTS.md`「历史经验」表按 H3 修复刻意保留教学 token（`X`/`UPPER`/`UPPER_CASE` 等
   未登记占位符原样保留），初始化后仍含双花括号字面量——若检测任意 `{{`，任何已初始化项目都会恒为
   "模板模式"，构建永被跳过。
2. **初始化不完整须显式失败**：特定 token 检测使"PROJECT_NAME 已替换但其他占位符残留"暴露为 CI 构建失败
   （占位符命令不可执行），而非静默跳过造成门禁假绿。

**grep 模式必须反斜杠转义**（`\{\{PROJECT_NAME\}\}`，grep BRE 中 `\{` 匹配字面 `{`）：若不转义，
`init-project` 会把 grep 模式里的占位符字面量一并替换成项目名，而生成项目 `AGENTS.md` 必然包含项目名
→ `is_template` 恒为 true，下游项目 CI 的构建/测试/质量门禁被永久跳过（2026-08 审查发现并修复的 P0 缺陷）。

实现：`.github/workflows/ci.yml`（quick-check / full-check / quality-gate / template-self-test 四处 detect 步骤）
与 `.github/workflows/detect-template.yml`（reusable workflow）统一使用上述转义模式。

（2026-08-14 审查修正：原 ADR 文字写的是 `grep -rq '{{'`，与实现不符，且该方案会被教学 token 反噬。）
模板仓库无构建系统，占位符命令无法执行→自举检测跳过。

### ADR-0003：Python 跨平台优先
核心验证脚本 Python 实现，PowerShell 仅 Win 集成场景。
init-project 保留双版本（Win 需 BOM/CRLF 处理）。

### ADR-0004：哨兵值优于异常
NaN 表示无效，不抛异常。来源 costsuite 性能回归教训。
