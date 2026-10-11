# 跨项目综合提炼

> 从 5 个项目（ExcelFormulaLabs / Excel-VBA-Libraries / EngSmartSuite / costsuite / DocAudit）的全量 commit 历史中提炼的共性经验。
>
> **定位（SSOT 声明）**：本文件只承载**真实案例库**与**方法论索引**。设计原则、红线规则、流程类内容一律不在此重复——它们在 AGENTS.md / skills/ / docs/ 有唯一权威定义，本文件仅链接引用。
>
> 维护规则：新增条目必须附真实案例（出现次数 + 根因），禁止臆造；发现本文件与 AGENTS.md / skills/ 重复时，以权威文件为准，本文件只留链接。

---

## 一、反模式案例库（唯一权威内容）

> 以下 <!-- AUTO_COUNTS:ANTIPATTERNS_START -->18<!-- AUTO_COUNTS:ANTIPATTERNS_END --> 类问题在 5 个项目中反复出现。**出现次数与根因是本文件独有的验证数据**，对策则已固化为 AGENTS.md 红线或验证脚本，链接引用。

### 1. 注册/同步遗漏

**现象**：新增功能后忘记更新所有关联位置。
**案例**：
- DocAudit：新增 check_type 忘注册 _DISPATCH（3 次）
- VBA：新增函数忘更新 6 处文档（多次）
- EngSmartSuite：新增方法忘注册 TASK_REGISTRY
**对策**：→ 见 [AGENTS.md 开发流程](../../AGENTS.md)（提交前必检）与 [CONTRIBUTING.md](../../CONTRIBUTING.md)（文档同步步骤）

### 2. 文档数字漂移

**现象**：函数计数、模块计数在多处硬编码，更新时遗漏。
**对策**：→ 已固化为规则：数字仅在 [api-reference.md](../spec/api-reference.md) 维护，其余文档链接引用（本模板的 [specification.md](../spec/specification.md) 已按此收敛）。

### 3. 交叉验证自校验

**现象**：`check(name, X, X)` 永远 PASS，3 处 Bug 因此漏过。
**对策**：→ 已固化为 [AGENTS.md 闭环验证强制](../../AGENTS.md) + [verify-manual.py](../../scripts/verify-manual.py) 静态检测（自校验模式正则拦截）。

### 4. 配置流断裂（声明了但未生效）

**现象**：规则/参数在配置中声明，但链路某节点断裂导致功能静默失效。
**案例**：
- DocAudit：STR-004 `最大英文词数` 在 4 处断裂（解析无分支 / 不传递 / 不读取 / 硬编码）
- EngSmartSuite：新增方法忘注册 TASK_REGISTRY
**对策**：
- 配置链路全节点验证：声明 → 解析 → 传递 → 读取 → 使用（每步 grep 确认）
- 建议提供 `validate_dispatch()` 类方法在测试中验证注册表完整性

### 5. 双重执行 / 功能死代码

**现象**：
- 双重执行：同一检查被直接调用 + 委托调度各执行一次（仅靠去重掩盖）
- 功能死代码：引擎层实现了完整功能（如 accept.txt 白名单）但审计流程零调用
**对策**：
- 直接调用路径与注册表（_DISPATCH/TASK_REGISTRY）取交集查重
- 对引擎层公开方法 grep 确认调用链完整（零调用 = 删除或接入）

### 6. 初始实现防御不足

**现象**：每个项目都经历了 5-15 轮代码审查修复。
**根因**：初始实现只考虑正常路径，未系统性考虑退化输入。
**对策**：→ 已固化为 [AGENTS.md 防错三原则](../../AGENTS.md)（Standard 级别自查）。

### 7. 框架/版本兼容性

**案例**：
- IntelliSense net8.0 反复尝试 8 次才确认不可行
- scipy 新版 API 变更导致 kstest 失败
- winreg 在 Linux 上 ImportError
**对策**：→ 已固化为 [AGENTS.md 红线](../../AGENTS.md)（依赖跨平台确认）+ [tooling-pitfalls.md](../pitfalls/tooling-pitfalls.md)（平台 API 条件导入）。

### 8. 类型/封送问题

**案例**：
- VBA：`As String` 参数传 Range 时 #VALUE!
- C#：`long[]` 返回给 Excel-DNA 封送失败
- Python：falsy 陷阱（0 被当作 False）
**对策**：→ 已固化为 [skills/](../../skills/) 语言陷阱文件（修改代码前必须加载）。

### 9. 测试文件命名与框架 glob 不匹配

**现象**：测试文件命名不匹配测试框架默认发现规则，测试永不运行却静默通过。
**案例**：
- TypeScript：`test_Stats.ts` 不匹配 vitest/Jest 默认 glob `**/*.{test,spec}.*` → `npx vitest run tests/` 输出 "No test files found" 且 exit 0（本模板示例曾如此）
- 后果：CI 显示绿但测试从未执行，退化输入回归无检测
**对策**：→ 已固化为 [tooling-pitfalls.md](../pitfalls/tooling-pitfalls.md) #21（后缀用框架默认匹配，如 TS `.test.ts`；或显式配置 include）。

### 10. 文件命名分隔符不一致（连字符 vs 下划线）

**现象**：源文件用连字符（`gen-doc-counts.py`），测试文件用下划线（`test_gen_doc_counts.py`）；工具按命名约定做子串匹配映射时未归一化分隔符，映射静默失效。
**案例**：
- VibeCodingTemplate：run-affected-tests 对 4 个本有测试的连字符脚本全报"疑似缺测"（`verify-docs.py`→`test_verify_docs.py` 等），工具 docstring「防门禁说谎」自相矛盾
**对策**：→ 工具比较前统一 `replace('-', '_')` 再子串匹配；见 [tooling-pitfalls.md](../pitfalls/tooling-pitfalls.md) #24。

### 11. 双实现行为分叉（py/ps1 对等失效）

**现象**：同一逻辑维护 Python 与 PowerShell 双实现，修复只落在其中一个，两路径行为分叉且无测试拦截（CI 自测通常只覆盖单一实现）。
**案例**：
- VibeCodingTemplate（2026-08 Max 审查）：未登记占位符 token——init-project.py 返回 None 保留原样（H3 修复），init-project.ps1 仍替换为占位符名小写，Windows 初始化污染 AGENTS.md 教学 token；test-template.ps1 以 -Values 预置小写值全覆盖，使 ps1 未登记分支在 CI 自测中永不触发
**对策**：→ 双实现共享同一份行为规范文档 + 每侧各配回归守卫（ps1 侧用 test-template.ps1 存活断言）；见 [tooling-pitfalls.md](../pitfalls/tooling-pitfalls.md) #26。

### 12. 生成器/检测器字面量污染（init 替换检测模式）

**现象**：生成器（占位符替换/模板实例化）扫描全部文件，把检测逻辑自身引用的字面量（如 CI 检测"模板未替换"的 grep 模式）当作模板变量一并替换，导致检测器在生成产物中永久失效或恒真。
**案例**：
- VibeCodingTemplate（2026-08 审查 P0）：ci.yml/detect-template.yml 的 detect 步骤 `grep '{{PROJECT_NAME}}'` 被 init-project 替换成项目名，而生成项目 AGENTS.md 必含项目名 → `is_template` 恒 true，下游 CI 构建/测试/质量门禁被永久跳过（模板自身 CI 不执行生成项目 CI，长期未暴露）
**对策**：→ 检测器引用占位符字面量时反斜杠转义（grep BRE `\{` 匹配字面 `{`，init 正则不再匹配）；见 [tooling-pitfalls.md](../pitfalls/tooling-pitfalls.md) #25。

### 13. 门禁腐化 / 门禁说谎（治理工具自身失守）

**现象**：门禁脚本"看起来在检查"但实际失明——跳过路径静默计 PASS、校验项 0 命中仍 exit 0、声称计数与实现漂移。比"没有门禁"更危险：给出虚假安全感。
**案例**（2026-09 从两成熟项目提炼）：
- EngSmartSuite：`verify_manual_claims.py` 曾"永远 exit 0"；模板 task 键长期无门禁；`verify_consistency` 未执行项计 SKIP 而非合成 PASS；未声明文件检查只查一层
- ExcelAddin 函数库：`.pre-commit-config.yaml` 中 hook 名称写「文档一致性（19 项）」而 verify-docs 已扩到 20 项——**声称数字未随实现更新**（门禁自身无对账）
- VibeCodingTemplate 自身：`falsy-audit --path <文件>` 因 `rglob` 不迭代而静默输出"无发现"（见 #15）；run-affected-tests 对 4 个有测试的脚本误报缺测（见 #10）
**对策**：
- 每个门禁脚本配**负向注入自测**（`tests/scripts/test_*.py`：注入违规必须 FAIL 且点名，恢复必须绿）；SKIP 单独计数、不计 PASS
- 门禁中出现的数字/条数**必须自动推导或对账**（如 AUTO_COUNTS 标记注入），禁止手写后遗忘；`--strict` 检查默认全量递归
- 修改门禁后必须用**反例**验证一次（构造违规样本确认被拦截），而非只跑正例全绿

### 14. 产物新鲜度缺失（陈旧二进制交叉验证假绿）

**现象**：交叉验证/黄金测试调用的被测产物（编译二进制、生成的数据文件）是旧版本，源码已改而验证仍对照旧行为，一致通过但毫无意义。
**案例**：
- ExcelAddin 函数库（2026-09）：CrossValRunner 交叉验证依赖构建产物；审查发现需在跑 cross_check 前校验产物构建时间/哈希，否则"验证通过"对应当前源码不成立
- VBA 库 v2.1.1（2026-08）：Release 附带的 xlsm 构建时间早于 CHANGELOG 固化时间，构件与版本代码不一致
**对策**：
- 验证流程做**产物新鲜度阶梯**：源码 mtime/hash 变化 → 强制重建 → 断言产物时间戳晚于源码；或验证前无条件重建（慢但可靠）
- 发布检查清单加「构件重建 + 版本代码一致性核对」（见 [ci-pipeline-SKILL.md](../../skills/ci-pipeline-SKILL.md) R7）

### 15. 双宿主脚本分叉（pwsh 7 vs Windows PowerShell 5.1）

**现象**：治理脚本在 CI 的 pwsh 7（Linux/Windows runner）通过，却在本机 PS 5.1 失败（或反之）——编码、`Get-ChildItem -Recurse -Force` 隐藏目录递归、`Split-Path -LiteralPath` 参数集、路径分隔符等行为差异。
**案例**：
- ExcelAddin 函数库（2026-09）：其治理自测脚本以双宿主（pwsh7 + PS5.1）扫描运行全部 PowerShell 自测，并设 Skip 上限；期间实证 pwsh 7 不递归隐藏目录导致漏扫 `.github`（见 tooling-pitfalls #28 同类）
- EngSmartSuite（2026-09）：pre-commit 排除 `.ps1` 的 end-of-file-fixer 以保留 CRLF+BOM，与 .ps1 双宿主约束配套
**对策**：
- 治理脚本改动后在**两个宿主各跑一次**；CI 矩阵覆盖 windows-latest（PS 5.1 可显式 `powershell.exe` 调用）
- 脚本内统一 UTF-8 输出 + `-Force` 递归 + 避免参数集歧义 API（详见 [tooling-pitfalls.md](../pitfalls/tooling-pitfalls.md) #3/#28）

### 16. 审查豁免无到期 = 永久遗忘

**现象**：审查发现的问题以"已知/暂缓"豁免后不再被跟踪，随着代码演进风险放大却无人复查。
**案例**：
- ExcelAddin 函数库（2026-09）：`review-exemptions.md` 建立 P0 不可豁免 / P1 登记制 + **到期必查清单**；EngSmartSuite 的 `progress.md` 对 deferred/out-of-scope 显式登记（而非口头跳过）
- **VibeCodingTemplate（2026-10-11 实证）：登记表写了"到期：v0.2.0 复查"，仓库已到 v0.2.4 仍无人复查——到期只是文档里的一句话，没有门禁读它**。复查后按建议修复（交互式 init 空输入曾静默回退占位符名小写，生成损坏的 CI 配置），并把"到期"变成硬检查
**对策**：
- 豁免必须**登记 + 设到期条件**（版本/日期/触发事件），到期未复查视为新问题；见 [review-exemptions.md](../governance/review-exemptions.md)（本模板已内置登记表）
- **到期条件必须可机械校验**：`scripts/verify-docs.py` 的「豁免到期」向量比对"到期版本 vs 当前版本"，过期即 FAIL（划删除线=已关闭才跳过）。人工承诺 + 无门禁 = 一定会烂
- 引用清单文件时**写段落名不写行号**：本表曾以 `.gitignore:73`/`:67` 定位，两次改动后行号全部失真（数字型引用必须可自动对账，否则迟早说谎）

### 17. 门禁触发/覆盖盲区（门禁正确，却从未在改动上运行）

**现象**：门禁逻辑本身没坏，但**触发条件或覆盖范围**把它挡在门外——改了被守护文件却不触发 CI；子树被有意排除出检查却无登记，盲区无人知晓。比 #13（门禁说谎）更隐蔽：门禁每次跑都是绿的，因为它根本没跑。
**案例**：
- EngSmartSuite（2026-10-09 R2/G-10）：`quality.yml` 的 `paths` 未含 `pyproject.toml` / `CHANGELOG.md` / `.release-please-manifest.json` / `AGENTS.md` / `templates/**` / `mkdocs.yml` / `docs/governance/**`，而这些恰是该 job 里版本链断言与目录树登记所守护的文件——**改模板数、改版本号都不跑门禁，门禁反复变红而改动者从未看到**
- EngSmartSuite（同上）：`quality.yml` 只有 `pull_request` 触发，release-please 自动提交与维护者直推 main 完全不过门禁 → 补 `push: branches: [main]`
- VibeCodingTemplate（2026-10-11 实证）：`ci.yml` 仅 `pull_request` + `workflow_dispatch` 触发（无 `push: main`）；`paths` 按文件名逐个列举，漏 `CLAUDE.md` / `tools/**` / `build/**`；同时 `verify-docs.py` 的 `_DOC_EXCLUDED_PREFIXES` 把 6 个第三方技能子树排除出链接检查，而子树内实际存在悬空引用且**全仓没有任何地方登记它**（读者只能自己撞上）
**对策**：
- **凡被某个 job 校验的文件，必须出现在该 job 的 `paths` 里**；根文档用 `*.md` 通配而非逐个列名（新增文档自动纳入）。不确定时，宁可在 main 上不加 `paths` 过滤——最后一道防线不设窄门
- **`push: branches: [main]` 必须与 PR 同等门禁**：PR 事件覆盖不到 auto-commit 与直推；其 `paths` 与 PR 的 `paths`
  逐条一致（用守卫测试强制，别靠人同步——两份清单总会分叉），既省掉重复运行又不留盲区
- **主动缩小的检查范围必须有登记表 + 两向门禁**：新盲区未登记 → FAIL；登记条目已失效 → FAIL（防登记表陈旧）。参考实现见 `skills/README.md` 的 VENDORED_DANGLING_REFS 表与 `scripts/verify-docs.py` 的「悬空引用登记」向量
- 定期问一句：**"这个门禁上次真正拦下问题是什么时候？"** 答不出来就说明它可能在盲区里

---

### 18. 模板初始化摩擦与生成物身份错配（"模板不像自己的项目"）

**现象**：模板仓库治理做得好，但**生成的项目**带着模板的影子与无关负担，外人第一次试用就卡住——三个典型症状：
① 必填项错配（把只在可选模板文件里出现的占位符标成"初始化必填"）；② 生成物仍自称模板；③ 空门禁声称"通过"。

**案例**（VibeCodingTemplate，2026-10-11 以外部使用者视角实测：init 一份再逐文件体检生成物）：
- **必填项错配**：20 个"core 且无默认值"占位符里有 9 个（APP_PORT / DB_NAME / DB_PASSWORD / BUILD_IMAGE /
  RUNTIME_IMAGE / ENTRY_CMD / IMAGE_NAME / FOUNDATION_PACKAGE 等）**只被 templates/** 与
  .github/workflows/*.yml.template 引用**（GitHub 根本不执行后者）→ 非交互初始化被迫索要数据库密码，
  交互初始化白问 9 个与项目无关的问题。批量核对"占位符 → 引用文件"后纠正为 content，必填从 20 降到 9（全是项目定义项）
- **生成物身份错配**：pyproject.toml 只重置了版本号，包名仍是 vibe-coding-template、描述仍是"治理模板" →
  生成项目 pip install -e . 装出与项目无关的包；doctor.py 打印模板名；README / README.en.md / CONTRIBUTING /
  architecture.md 的模板专属文案与 TEMPLATE_ONLY 标记原样进入生成项目
- **双实现分叉**（同轮发现）：同一份 values 输入下，Python 版初始版本 1.0.0、PowerShell 版 0.1.0
  （ps1 硬编码兜底、忽略 manifest 默认值），而 ROADMAP / README 文档写的初始态是 v0.1.0
- **空门禁说谎**：scripts/architecture.json 的 rules 为空时，verify-arch.py 输出"[OK] 架构边界验证通过"
  ——实际一条规则都没查（正是本文件 #13 的行为，只是发生在模板自身）
- **平台体验坑**：文档推荐的 --values '{"...":"..."}' 在 Windows PowerShell 5.1 下双引号被吞 → JSON 解析失败，
  而 README 把这条当主推路径

**对策**：
- **模板必须"以生成物为准"验收**：把初始化后的项目当交付物跑一遍（生成 → 逐文件体检 → 修 → 加断言）。
  模板仓库自身全绿 ≠ 生成项目可用
- **占位符分类按"引用位置"判定，不按直觉**：只有 templates/** 引用的 → content（不阻塞初始化）；活动文件需要
  但用户此刻拿不到的（如安全联系邮箱）→ 给**可执行的默认值**，而不是设为必填
- **生成物身份必须重置**：包名/描述/文档标题/工具横幅一律随项目走（占位符或运行时读取），并把"生成项目
  不得含模板自身标记/包名/初始版本"写成**自测断言**（本模板 test-template.ps1 已加：非模板包名 + 初始版本
  0.1.0 + 无 TEMPLATE_ONLY 残留 + 无 BOM）
- **空门禁只能输出 [SKIP] 未检查**，绝不能是"通过"；同时写进初始化收尾清单，让它有被填写的期限
- 脚本化入口用**文件读取**而非命令行内联 JSON（--values-file），并在文档里点名 Windows 引号陷阱

## 二、过度设计反模式案例（costsuite）

| 过度设计 | 问题 | 正确做法 |
|---------|------|----------|
| 19 commits 用 6 层架构 | 原型不需要 | 4 层（UI→Service→Engine→Data） |
| MediatR 事件总线 | 零消费者 | 删除，有需求再加（YAGNI） |
| Polly 重试 | 离线系统无网络调用 | 删除 |
| AES-256 加密 | 本地 SQLite 无安全威胁 | 删除 |
| NLog + AOP 审计 | 原型无审计需求 | Console/Debug 日志即可 |
| 规格文档写未验证功能 | ERP/gRPC/审批流 | 仅写已验证功能 |

**判断准则（YAGNI 四问）**：→ 见 [architecture-reviewer-SKILL.md](../../skills/architecture-reviewer-SKILL.md)（唯一权威定义处）。
**架构简化 ≠ 降低质量**：简化的是**未使用的复杂度**，保留的是**有实际价值的分离**（如 Engine 层纯计算独立于 Service 层，可独立测试）。

---

## 三、重构方法论（跨项目验证过）

> 重构方法论由 5 个项目验证提炼（见第一节反模式案例）。**执行模板**用 [refactoring-plan.md](refactoring-plan.md)，**每 Phase 守卫**用 [refactoring-guardian-SKILL.md](../../skills/refactoring-guardian-SKILL.md)。

### 1. Phase 0 审计模式（先测量再动手）

```
任何重构之前，必须先：
├─ 建立 baseline（当前测试通过率/覆盖率/性能数据）
├─ 审计实际问题（grep/手动检查，记录数量）
├─ 测量开发效率（模拟新增一个功能并计时）
└─ 设定回滚条件（如：测试失败 >N 个，先修复再重构）
```

**反模式**：没有 baseline 就开始重构 → 无法判断是否引入回归。

### 2. 小步快跑模式

| 原则 | 说明 |
|------|------|
| 每 Phase 1-2 周 | 不超过 2 周，避免大爆炸式重构 |
| 逐文件提交 | 每个修复独立 commit，可单独 revert |
| 分支开发 | 高风险修改在分支进行，验证后合入 |
| 新增优先 | 基础设施/测试/脚本是新增文件，不影响现有代码 |

### 3. 决策点模式（审计后分支）

```
Phase 0 审计结果 → 决策：
├─ 覆盖率 >60% → 仅补关键路径
├─ 覆盖率 <30% → 大规模补测试
├─ 组件零调用 → 直接删除
└─ 性能 <2s → 性能优化推迟
```

---

## 四、长期技术生命周期管理

> 跨项目共有的演进风险与退出策略（本文件独有，无权威定义处）。

| 项目 | 风险 | 策略 |
|------|------|------|
| Excel-VBA-Libraries | VBA 语言已停止演进（微软→Office Scripts） | 13 模块独立性 = 逐模块迁移路径 |
| ExcelFormulaLabs | Excel-DNA 版本兼容性 | 锁定版本 + 升级前完整回归 |
| EngSmartSuite | scipy API 变更 | 锁定版本下限 + 兼容性测试 |

**通用原则**：
```
保持模块独立性 = 保持未来迁移路径
├─ 模块间通过明确接口通信（不共享内部状态）
├─ 每个模块可独立测试（不依赖其他模块运行）
└─ 迁移时逐模块替换，而非一次性重写
```

---

## 五、对标项目清单

| 项目类型 | 对标 | 学习重点 |
|---------|------|----------|
| Excel Add-in (C#) | Excel-DNA 官方 / StatsCLR / NuGet 生态 | 包分发、异步 UDF、CI 矩阵 |
| VBA 库 | Rubberduck / VBA-JSON / VBA-Web (Tim Hall) | 静态分析、@注解、包管理 |
| 统计分析 (Python) | scipy / JASP / jamovi / statsmodels | Pydantic 验证、APA 合规、seed 管理 |
| BOM/制造业 (C#) | BOMManagementSoftware / Excel-DNA 企业级 | Closure Table、离线优先 |
| 文档审查 (Python) | markdownlint / proselint / retext | 规则独立化、--fix、SARIF 输出 |

---

## 六、最佳实践速查（索引表）

> 共性模式已在权威文件定义，此处只给链接，不重复内容。

| 主题 | 权威定义处 |
|------|-----------|
| 设计原则（SSOT/配置驱动/YAGNI/优雅降级） | [AGENTS.md 核心准则](../../AGENTS.md) + [specification.md](../spec/specification.md) |
| 架构层级与单向依赖 | [project-structure.md](../governance/project-structure.md) |
| 闭环验证体系（交叉验证/黄金测试/差分测试） | [AGENTS.md 闭环验证强制](../../AGENTS.md) + [verify-manual.py](../../scripts/verify-manual.py) |
| 分类型比较器 / 容差分层（数组/字典/标量） | [verify-manual.py compare](../../scripts/verify-manual.py) |
| 测试有效性（弱断言/缺测/命名守卫） | [test-quality-guard.py](../../scripts/test-quality-guard.py) |
| 影响范围测试路由（git diff → 受影响测试） | [run-affected-tests.py](../../scripts/run-affected-tests.py) |
| 防御编程（哨兵契约/异常过滤器/NaN 守卫） | [AGENTS.md 防错三原则](../../AGENTS.md) + [sentinel-contract.md](../pitfalls/sentinel-contract.md) + [skills/csharp-SKILL.md](../../skills/csharp-SKILL.md) |
| 环境就绪诊断（新开发者第一步） | [doctor.py](../../scripts/doctor.py) |
| 多注册表一致性（防注册遗漏） | [verify-registries.py](../../scripts/verify-registries.py) |
| 架构边界门禁（配置驱动分层依赖） | [verify-arch.py](../../scripts/verify-arch.py) + `scripts/architecture.json` |
| 覆盖率门禁（清旧产物 + 阈值 + 显式失败） | [coverage.py](../../scripts/coverage.py) + `pyproject.toml [tool.coverage]` |
| 文档计数自动注入（防数字漂移） | [gen-doc-counts.py](../../scripts/gen-doc-counts.py) |
| YAGNI 移除文档（为什么移除 X + git 引用） | [specification.md](../spec/specification.md) + [adr-template.md](../design/adr-template.md) |
| 文档职责体系 | [documentation.md](../governance/documentation.md)（唯一权威） |
| 会话管理（5 文件/20 轮/跨会话接力） | [AGENTS.md 会话管理](../../AGENTS.md) |
| 版本管理（SemVer + 发版流程） | [CONTRIBUTING.md 发版规范](../../CONTRIBUTING.md) + [release.yml](../../.github/workflows/release.yml)（release-please 自动） |
| 工程化基础设施优先级 | [CONTRIBUTING.md](../../CONTRIBUTING.md)（CI/模板/徽章清单已并入） |
