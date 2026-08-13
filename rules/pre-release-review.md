# VibeCodingTemplate 发行前全量深度审查 Prompt

> 对本模板仓库执行发行前审查。分为 **min / med / max** 三级，
> 分别对应快速检查、标准审查、穷尽审计。根据发行风险选择级别。

## 项目背景（供审查 AI 理解上下文）

VibeCodingTemplate 是一个 **元项目模板**——不是具体应用，
而是克隆后初始化新项目的治理框架。核心机制：

- **AGENTS.md** = 项目宪法（AI 行为约束 + 目录树路由）
- **rules/** = 规范文档（SSOT 原则：每类信息唯一定义处）
- **skills/** = 5 语言编码陷阱 + 3 位审查专家
- **templates/** = 模块脚手架（占位符系统：`{{...}}` 项目级 / `{Pascal}` 模块级）
- **scripts/** = 验证脚本（AST 审计 + 文档一致性 + 手动验证 + 初始化）
- **.github/workflows/** = CI 分层门禁（quick/full/quality/template-self-test）
- **placeholders.json** = 占位符 SSOT 清单（init-project 读取，CI 校验）

关键约束：
- **模板自举检测**：CI 通过 `grep '{{' AGENTS.md` 区分模板/项目模式
- **双目录树防漂移**：AGENTS.md 与 project-structure.md 顶层目录必须一致
- **哨兵值契约**：NaN 表示无效（0 是有效值），不抛异常
- **Python 跨平台优先**：核心脚本 Python 实现，PowerShell 仅 Win 集成场景

---

## 审查级别

| 级别 | 适用场景 | 维度 | 预计耗时 |
|------|----------|------|----------|
| **Min** | 小修补后确认安全 | 5 | 10 min |
| **Med** | 功能迭代后标准审查 | 10 | 30 min |
| **Max** | 大版本发行前穷尽审计 | 18 | 60+ min |

---

# Min 审查（5 维度）

```
请对 VibeCodingTemplate 执行发行前最小审查，覆盖 5 个维度：

1. **门禁全绿**
   - 运行 `python scripts/verify-all.py`，确认全部步骤通过
   - 运行 `python -m ruff check scripts/ tests/`，确认零违规
   - 确认 `git status` 无未提交变更

2. **占位符 SSOT 完整性**
   - 运行 `python scripts/verify-docs.py --strict`，确认无未声明文件/目录
   - 检查 `placeholders.json` 中每个 `test` 值正确（非空、类型匹配）
   - 确认所有模板中 `{{...}}` 占位符均在 placeholders.json 中注册

3. **模板自举检测有效**
   - 确认 `grep '{{' AGENTS.md` 在模板仓库返回 true（含未替换占位符）
   - 确认 CI 中 `template-self-test` 使用相同检测逻辑（无 PROJECT_NAME 硬编码）

4. **关键文档无断链**
   - AGENTS.md / README.md / CONTRIBUTING.md 中所有相对链接目标存在
   - 技能表、占位符约定表中的反引号路径引用有效
   - 无占位符残留（如 `{{PROJECT_NAME}}` 未替换）在已发布文档中

5. **安全底线**
   - 无硬编码密钥/Token/连接串（检查 scripts/ 和 .github/）
   - CI 权限最小化（permissions 块显式声明，无 `write-all`）
   - 无 eval/exec 执行用户可控输入

输出格式：
- [P0] 阻塞发行 — 必须修复
- [P1] 建议修复 — 有风险但不阻塞
- [P2] 改善项 — 可记录到技术债
- 结论：🟢 可发行 / 🟡 修复 P0 后可发行
```

---

# Med 审查（10 维度）

```
请对 VibeCodingTemplate 执行发行前标准审查，覆盖 10 个维度：

## 1. 门禁全绿
- `python scripts/verify-all.py` 全部通过
- `python -m ruff check scripts/ tests/` 零违规
- `python -m pytest tests/ -v` 全部 169 项通过
- `git status` 干净

## 2. 占位符系统完整性
- placeholders.json 中每个条目有合法的 category（core/content/auto）
- core 类占位符有 prompt（说明含义）和 test（自测用值）
- auto 类占位符有 rule（today/year）
- template-self-test 的 `grep -rn "{{" templates/NewModule/` 无泄漏
- init-project.py 的 replace_placeholders 正确处理 binary/skip 文件

## 3. 模板完整性
- 5 语言 NewModule 模板（C#/Python/VBA/TypeScript/Go）均存在
- 每个 Core 模板的 sentinel contract 完整（guard → validate → compute → result-guard）
- Go 模板可编译（`go build` 无 import 错误）
- C# 模板的 ROOT_NAMESPACE 占位符正确引用
- language/ 下构建配置模板覆盖所有支持语言

## 4. CI 管道正确性
- 4 级门禁（quick-check / full-check / quality-gate / template-self-test）触发条件正确
- 模板检测逻辑在 init 后不会反转（使用 `grep '{{'` 而非 `grep PROJECT_NAME`）
- security.yml 有 `contents: read` 权限
- Windows runner 上的 bash 步骤有 `shell: bash`
- 所有 action 引用的 SHA 真实存在
- release-please 配置与 Conventional Commits 规范一致

## 5. 文档一致性
- AGENTS.md 与 project-structure.md 顶层目录集合一致（双目录树防漂移）
- project-structure.md 目录树枚举了所有实际存在的根级文件/目录
- 技能表条目数量与实际 skills/ 文件数一致
- templates/README.md 占位符约定表与实际使用一致
- README / README.en.md 中功能计数准确
- 无断链（`verify-docs.py --strict` 通过）

## 6. Python 脚本质量
- 所有 Public 函数有类型注解
- 核心路径无 bare except（除已标记 noqa 的正当用例）
- subprocess 调用使用 list args（防注入）
- 路径操作使用 pathlib（非字符串拼接）
- 跨平台兼容（无 Windows-only 或 Linux-only 假设）
- 错误信息对用户有意义（中文/可操作）

## 7. 代码质量（跨语言示例）
- examples/src/stats/ 下的 Python/TypeScript/Go 示例功能一致
- 三个示例的 mean() 和 weightedMean() 行为对齐
- 哨兵值契约一致（NaN in Python/Go, NaN in TS via null guard）
- examples/tests/ 测试覆盖边界（空输入/NaN/Inf/负权重/溢出）

## 8. 测试完备性
- scripts/ 核心函数有测试覆盖（当前 169 tests）
- falsy-audit 的 AST 模式和正则兜底均有测试
- verify-docs 的各检查函数有行为测试（非仅 return type 检查）
- 关键错误路径有测试（文件不存在/JSON 解析失败/路径越界）

## 9. 安全审查
- CI Token 权限最小化
- init-project 目标路径验证（防路径穿越？）
- 无敏感信息在模板中硬编码
- CODEOWNERS 配置合理
- SECURITY.md 漏洞报告流程有效

## 10. 依赖与版本
- pyproject.toml 依赖版本使用下限约束（无上限冲突）
- pre-commit 钩子版本与 pyproject.toml 一致
- GitHub Actions 使用 commit SHA 锁定
- Python >=3.10 约束一致

输出格式：
对每个发现：
```
[P{0-3}] {文件}:{行号}
  问题：{描述}
  影响：{具体后果}
  修复：{具体建议}
```

最后：
- 统计：P0×N + P1×N + P2×N + P3×N
- 与上次审查对比（如有）：新增 N / 修复 N
- 结论：🟢 可发行 / 🟡 修复 P0+P1 后可发行 / 🔴 需返工
```

---

# Max 审查（18 维度）—— 发行前穷尽审计

```
请对 VibeCodingTemplate 执行发行前穷尽审计。本级别用于大版本
（如 1.0.0）发行前的最终质量门。覆盖 18 个维度，采用多轮对抗验证。

## 审查方法论

采用**多代理并行审查 + 对抗验证 + 交叉合成**模式：
1. 每个维度独立启动审查代理（并行）
2. 对 P0/P1 发现启动对抗验证代理（尝试反驳）
3. 对抗验证存活的发现进入修复队列
4. 修复后重新运行全部门禁
5. 合成最终审查报告

---

## 维度清单

### 1. 门禁全绿（基线确认）
- `verify-all.py` 全部通过
- `ruff check` 零违规（含 --unsafe-fixes 预览）
- `pytest tests/ -v --cov=scripts --cov-fail-under=35` 满足覆盖率底线
- `git status` 干净，无未追踪文件

### 2. 占位符 SSOT 穷尽审计
- 扫描全部文件（含 .github/ISSUE_TEMPLATE/ 的占位符类 yml 文件）
  找出所有 `{{...}}` 和 `{...}` 占位符
- 与 placeholders.json 交叉比对：
  - 双花括号 `{{...}}` → 必须在 placeholders.json 中注册（core/content/auto）
  - 单花括号 `{X}` → 为模块级手替换，不应由 init 替换
- 检查所有 `{{...}}` 占位符的特征：
  - 检测名 → `.*_(1|2|3)$` 是序列化检测名（占位符滥用嫌疑，报告 WARN）
  - 检测值 → test 字段是否语义合理（非明显占位值如 "TODO"/"..."）
- 检查 `test-template.ps1` 的占位符扫描是否覆盖全部声明条目

### 3. 模板穷尽审查
对 `templates/` 下全部文件（NewModule/ + language/ + monorepo/）：

- **编译检查**：每个语言模板能否通过该语言的基础编译
  - C#: `dotnet build`（语法有效 + ROOT_NAMESPACE 可替换）
  - Go: `go build`（import 完整，无未定义符号）
  - TypeScript: `npx tsc --noEmit`（类型正确）
  - Python: `python -m compileall`（语法有效）
  - VBA: 人工检查（无自动编译）
- **Contract 完整性**：每个 Core 模板含 4 步 sentinel contract
  (guard → validate → compute → result-guard)
- **占位符一致性**：模板内占位符类型正确（`{{ROOT_NAMESPACE}}` /
  `{Name}` / `{Module}` / `{module}` 区分准确）
- **测试模板配对**：每个 Core 模板有对应 test 模板
- **README 指令可执行**：templates/README.md 中每个语言流程可逐步执行

### 4. CI/CD 穷尽审计
- 每个 workflow 文件逐条审查：
  - 触发条件正确（push/pr/schedule/workflow_call）
  - 权限最小化（permissions 显式声明）
  - 每个 step 的 `if:` 条件逻辑正确
  - 每个 action 引用的 SHA 存在且与注释版本号匹配
- 跨平台兼容：ubuntu + windows runner 的 shell 差异已处理
- release-please：config.json 与分支/tag 模式一致
- dependabot：更新频率合理，assignees 有效

### 5. 文档穷尽审查
- AGENTS.md ↔ project-structure.md 双目录树一致
- 全部文档中相对链接可解析（含反引号路径引用）
- 计数型声明与实际数量一致：
  - skills/ 文件数
  - scripts/ 脚本数
  - templates/ 子目录数
  - 占位符条目数
  - rules/ 文件数
- README / README.en.md 同步（无英文版滞后）
- CHANGELOG.md 与 git tag 一致
- 所有 `{{...}}` 占位符在非模板文档中已替换（CHANGELOG/README 等）

### 6. Python 脚本深度审查
对 scripts/ 下全部 .py 文件：

- **类型安全**：所有 Public 函数有完整类型注解
- **异常安全**：无 bare except（已标记 noqa 的逐一审查合理性）
- **资源安全**：Path/文件句柄正确释放
- **并发安全**：无共享可变状态（如有 thread/process，检查锁）
- **跨平台**：路径/换行/编码正确处理
- **注入防护**：subprocess 使用 list args；无 os.system
- **性能**：无 O(N²) 可优化路径；无重复文件扫描
- **AST 审计准确性**：falsy-audit 覆盖全部检测变体
  （if/if not/while/or fallback + 类型注解感知 + 函数参数注解）
- **文档验证准确性**：verify-docs 的链接正则/目录树解析/反引号路径
  无已知漏检模式
- **手动验证准确性**：verify-manual 的 check/cross_check/section 逻辑正确

### 7. 代码质量穷尽审查
对全部源代码（scripts/ + tests/ + examples/）：

- 死代码检测：无未使用导入/函数/变量
- 命名一致性：同一概念同一名称（如 "哨兵值" 不另称 "标记值"）
- 注释质量：解释"为什么"而非"是什么"；无过期注释
- 魔法数字：全部替换为命名常量
- 复杂度：单函数不超过 50 行（合理拆解）
- 重复代码：识别跨脚本的重复模式并建议抽取

### 8. 测试穷尽审计
- 覆盖率报告：`pytest --cov=scripts --cov-fail-under=40`
  - 当前基线 79%，目标每次发行提升 5%
  - 识别覆盖率最低的模块并标记
- 边界测试完整性：
  - falsy-audit: --path 越界/SyntaxError/binary file
  - verify-docs: 断链/反引号失效/目录树漂移/未声明
  - init-project: JSON 解析失败/目标权限不足/空目录
- 漏洞测试：每个关键错误路径有对应测试
- 交叉验证：verify-manual 的 cross_check 有实际比对测试
- 示例测试：examples/tests/ 能通过 CI（当前未接入）

### 9. 安全穷尽审查
- 密钥检测：`grep -rnE '(password|secret|token|key|api_key)' --include='*.py' --include='*.yml'`
- 路径穿越：init-project 的 target 参数验证
- 代码注入：占位符替换是否可能注入代码（模板引擎安全）
- 信息泄漏：错误消息是否暴露内部路径/栈帧
- 依赖审计：`pip-audit` 或 `safety check`（如已安装）
- CI 安全：Token 权限审查、第三方 action 审计
- Supply chain：pre-commit 钩子来源、pip 源配置

### 10. 跨语言一致性穷尽审计
对比 5 个语言技能文件（skills/*-SKILL.md）：

- 结构一致：YAML frontmatter + 陷阱清单 + 设计约束 + 提交检查清单
- 内容覆盖：每个语言覆盖了该语言的核心陷阱
- 示例质量：代码示例可运行、注释清晰
- 术语一致：哨兵值/交叉验证/SSOT 等核心概念翻译一致

对比 examples/src/stats/ 三语言实现：
- 函数签名一致（mean/weightedMean 参数/返回类型语义相同）
- 哨兵契约一致（无效输入 → NaN/null）
- 边界处理一致（空输入/NaN/Inf/溢出）
- 测试覆盖对称（每语言测试用例数相近，覆盖相同边界）

### 11. 架构合规审查
- 层级依赖方向正确（scripts/ 不依赖 tests/；rules/ 不依赖 skills/）
- AGENTS.md 红线规则在全部代码中遵守
- SSOT 原则：每类信息唯一定义处，无重复定义
- 占位符系统：双语法约定（`{{...}}` / `{Pascal}`）一致使用

### 12. 反模式扫描
基于 AGENTS.md「高频修复模式」和 cross-project-synthesis.md 反模式库：

- 搜索「注册/同步遗漏」模式：新增文件是否在全部关联位置注册
- 搜索「文档数字漂移」：硬编码计数是否与 verify 结果一致
- 搜索「配置流断裂」：CI→脚本→模板 三层的配置传递是否连续
- 搜索「初始实现防御不足」：新模块的 sentinel contract 是否完整

### 13. 性能审查
- CI 管道耗时：最长 job 是否超过 5 min
- 脚本启动时间：verify-all.py 运行时间是否在合理范围
- 文件扫描效率：无不必要的重复 rglob/walk
- 内存使用：大文件处理是否流式

### 14. 兼容性审查
- Python 3.10/3.11/3.12/3.13/3.14 兼容（检查不使用新语法如 PEP 695 `type` 语句）
- Windows/Linux/macOS 兼容（路径分隔符/换行/编码）
- bash/PowerShell 双脚本 feature parity（init-project.py/ps1）
- Git 版本：pre-commit / CI 使用的 git 特性兼容

### 15. 国际化审查
- README.md ↔ README.en.md 内容同步
- 中文文档的关键术语有英文对应（方便非中文用户搜索）
- 错误消息的语言选择合理（脚本内部可用中文，API 错误用英文）

### 16. 发行准备审查
- CHANGELOG.md 是否更新到当前版本
- .release-please-manifest.json 版本号正确
- git tag 与 manifest 版本一致
- LICENSE 年份/作者信息准确
- CODE_OF_CONDUCT.md / SECURITY.md 联系信息有效

### 17. 对抗验证轮次
对 P0/P1 发现启动独立验证代理：
- 每个 P0/P1 发现由 3 个独立代理尝试反驳
- 反驳存活（≥2/3 确认）的发现进入修复队列
- 修复后重新运行全部门禁
- 记录每个驳倒的发现及其驳倒原因

### 18. 知识库更新
- 将本次审查发现的新反模式记录到 AGENTS.md「高频修复模式」
- 将新发现的工具坑位记录到 rules/tooling-pitfalls.md
- 更新 rules/cross-project-synthesis.md 反模式库
- 如发现需要豁免的项，登记到 `.claude/exemptions.md`

---

## 输出格式

### 总报告结构

```
# VibeCodingTemplate 发行前审查报告

**审查级别**: Max (18 维度)
**审查日期**: YYYY-MM-DD
**审查基线**: <commit SHA>
**目标版本**: <version>

## 执行摘要
- 总发现数: N
- P0 (阻塞): N
- P1 (高风险): N
- P2 (改善): N
- P3 (建议): N
- 对抗验证驳回: N
- 结论: 🟢/🟡/🔴

## 各维度结果

### 维度 N: {名称} — 🟢/🟡/🔴
- [P0] ... (如有)
- [P1] ...
...

## 修复后验证
- 门禁重跑: ✅/❌
- 覆盖率变化: 35% → X%

## 知识库更新项
- [ ] AGENTS.md 高频修复模式
- [ ] tooling-pitfalls.md
- [ ] cross-project-synthesis.md
- [ ] exemptions.md

## 签署
- 审查执行: Claude Code (max mode)
- 审查耗时: X min
- 最终结论: 🟢 可发行 / 🟡 条件发行 / 🔴 需返工
```

---

## 审查前置条件

- [ ] 已加载 AGENTS.md（了解红线规则和目录树）
- [ ] 已加载 rules/cross-project-synthesis.md（了解已知反模式）
- [ ] 已加载 rules/tooling-pitfalls.md（了解已知工具坑位）
- [ ] 已运行 `python scripts/verify-all.py`（基线确认）
- [ ] 已查看 `.claude/exemptions.md`（已知豁免清单）

## 豁免规则

- **P0 不可豁免**：阻塞发行的缺陷必须修复
- **P1 可豁免**：需在 exemptions.md 登记（含接受原因 + 到期版本）
- **豁免到期自动升级为 P0**：下次审查必须复查
