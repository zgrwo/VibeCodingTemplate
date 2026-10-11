# {{PROJECT_NAME}} 架构设计

<!-- TEMPLATE_ONLY_START -->
> 本文档记录模板仓库自身的设计决策。初始化新项目后替换为项目架构文档。

## 设计目标

1. **治理幻觉**：AI 会编造 API、跨越架构边界。AGENTS.md 宪法 + 防幻觉铁律 + 闭环验证。
2. **文档漂移**：SSOT + verify-docs.py --strict CI 硬门禁。
3. **知识传承**：从 5 个真实项目提炼反模式案例库。

## 架构分层

```
.github/workflows/     CI/CD 分层门禁（quick/full/quality/template-self-test）
AGENTS.md              项目宪法（四条核心准则、红线规则、防幻觉铁律）
├── docs/              文档中心（governance/spec/design/pitfalls/methodology 五分类，documentation.md 为 SSOT 权威）
├── skills/            编码技能（6 语言 + 3 位重构专家 + CI 管道技能）
├── templates/         模块脚手架（NewModule + language + monorepo）
├── scripts/           验证脚本（AST 审计 + 架构边界 + 覆盖率 + 初始化 + commit 校验）
├── benchmarks/        性能基准（非门禁，趋势观测；基准约定见其 README）
├── examples/          示例项目（Python/TypeScript/Go/Rust）
└── tests/             验证脚本自测（<!-- AUTO_COUNTS:TESTS_START -->320<!-- AUTO_COUNTS:TESTS_END --> tests，见 tests/scripts/）
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

**grep 模式必须防 init 替换 + 兼容所有 grep 版本**：检测串在运行时拼装（`open='{{'` / `close='}}'` +
`grep -Fq "${open}PROJECT_NAME${close}"`），文件内不出现可被 init 匹配的字面占位符——否则
`init-project` 会把 grep 模式里的占位符字面量一并替换成项目名，而生成项目 `AGENTS.md` 必然包含项目名
→ `is_template` 恒为 true，下游项目 CI 的构建/测试/质量门禁被永久跳过（2026-08 审查发现并修复的 P0 缺陷）。
**不可用 BRE 转义 `\{\{PROJECT_NAME\}\}`**：`\{` 是区间表达式起始符，旧版 GNU grep 对"`\{` 后非数字"宽容
处理为字面量，新版（3.11，runner 镜像 20260810.271.1 实证）直接报 `Invalid content of \{\}`（exit 2），
且原实现 `2>/dev/null` 吞掉错误 → `is_template` 恒 false、模板模式跳过逻辑静默失效（2026-08-15 发行阻塞，
见 docs/pitfalls/tooling-pitfalls.md #25）；`grep -F` 固定串匹配无正则解析，版本无关。

实现：`.github/workflows/ci.yml`（quick-check / full-check / quality-gate / template-self-test 四处 detect 步骤）
与 `.github/workflows/detect-template.yml`（reusable workflow）统一使用上述运行时拼装 + `grep -F` 模式。

（2026-08-14 审查修正：原 ADR 文字写的是 `grep -rq '{{'`，与实现不符，且该方案会被教学 token 反噬。）
模板仓库无构建系统，占位符命令无法执行→自举检测跳过。

### ADR-0003：Python 跨平台优先
核心验证脚本 Python 实现，PowerShell 仅 Win 集成场景。
<!-- TEMPLATE_ONLY_END -->

---

## 本项目架构（待填写）

> 上一节是**模板仓库自身**的设计说明（初始化时已被裁剪，不会出现在生成项目里）。
> 请在下面写出本项目的分层、模块职责与关键决策；写完可删除这段提示。

### 分层

```
（例：UI → Services → Core → Foundation，单向依赖）
```

- ✅ 上层不包含业务逻辑；下层不引用上层依赖
- ❌ 禁止跨层直接调用或反向依赖（用 [verify-arch.py](../../scripts/verify-arch.py) + `scripts/architecture.json` 规则固化）

### 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| （待填） | | |

### 关键决策（ADR）

> 一个决策一个文件：`docs/design/adr/NNNN-xxx.md`（模板见 [ADR 模板](adr-template.md)，格式与「何时必须写 ADR」判定见该文件）。
init-project 保留双版本（Win 需 BOM/CRLF 处理）。

### ADR-0004：哨兵值优于异常
NaN 表示无效，不抛异常。来源 costsuite 性能回归教训。

### ADR-0005：配置驱动架构门禁（2026-09）

- **背景**：AGENTS.md 声明"禁止跨层调用或反向依赖"，但分层因项目而异，模板无法硬编码；
  两个成熟参考项目用 guards 目录下的 AST 测试执行该红线，语言/框架耦合较强。
- **决策**：`scripts/verify-arch.py` 读取 `scripts/architecture.json` 规则（source glob +
  forbid_imports + exclude），Python AST 扫描 import 命中即 FAIL；空规则显式通过并提示填写；
  **source 未匹配任何文件按配置错误处理**（防"空规则静默通过"的门禁说谎）。
- **代价与边界**：只覆盖 Python；下游可在此之上叠加语言特定 guards（二者不冲突）。
- **备选未采纳**：在模板内固化 guards 测试示例——模板 `src/` 为空，固化测试会空转，
  且不同语言项目的 guards 形态不同（YAGNI）。
