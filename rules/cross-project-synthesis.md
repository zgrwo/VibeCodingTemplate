# 跨项目综合提炼

> 从 5 个项目（ExcelFormulaLabs / Excel-VBA-Libraries / EngSmartSuite / costsuite / DocAudit）的全量 commit 历史中提炼的共性经验。
>
> **定位（SSOT 声明）**：本文件只承载**真实案例库**与**方法论索引**。设计原则、红线规则、流程类内容一律不在此重复——它们在 AGENTS.md / skills/ / rules/ 有唯一权威定义，本文件仅链接引用。
>
> 维护规则：新增条目必须附真实案例（出现次数 + 根因），禁止臆造；发现本文件与 AGENTS.md / skills/ 重复时，以权威文件为准，本文件只留链接。

---

## 一、反模式案例库（唯一权威内容）

> 以下 8 类问题在 5 个项目中反复出现。**出现次数与根因是本文件独有的验证数据**，对策则已固化为 AGENTS.md 红线或验证脚本，链接引用。

### 1. 注册/同步遗漏

**现象**：新增功能后忘记更新所有关联位置。
**案例**：
- DocAudit：新增 check_type 忘注册 _DISPATCH（3 次）
- VBA：新增函数忘更新 6 处文档（多次）
- EngSmartSuite：新增方法忘注册 TASK_REGISTRY
**对策**：→ 见 [AGENTS.md 开发流程](../AGENTS.md)（提交前必检）与 [CONTRIBUTING.md](../CONTRIBUTING.md)（文档同步步骤）

### 2. 文档数字漂移

**现象**：函数计数、模块计数在多处硬编码，更新时遗漏。
**对策**：→ 已固化为规则：数字仅在 [api-reference.md](api-reference.md) 维护，其余文档链接引用（本模板的 [specification.md](specification.md) 已按此收敛）。

### 3. 交叉验证自校验

**现象**：`check(name, X, X)` 永远 PASS，3 处 Bug 因此漏过。
**对策**：→ 已固化为 [AGENTS.md 闭环验证强制](../AGENTS.md) + [verify-manual.py](../scripts/verify-manual.py) 静态检测（自校验模式正则拦截）。

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
**对策**：→ 已固化为 [AGENTS.md 防错三原则](../AGENTS.md) 与 [code-review-prompt.md](code-review-prompt.md)（Standard 级别自查）。

### 7. 框架/版本兼容性

**案例**：
- IntelliSense net8.0 反复尝试 8 次才确认不可行
- scipy 新版 API 变更导致 kstest 失败
- winreg 在 Linux 上 ImportError
**对策**：→ 已固化为 [AGENTS.md 红线](../AGENTS.md)（依赖跨平台确认）+ [tooling-pitfalls.md](tooling-pitfalls.md)（平台 API 条件导入）。

### 8. 类型/封送问题

**案例**：
- VBA：`As String` 参数传 Range 时 #VALUE!
- C#：`long[]` 返回给 Excel-DNA 封送失败
- Python：falsy 陷阱（0 被当作 False）
**对策**：→ 已固化为 [skills/](../skills/) 语言陷阱文件（修改代码前必须加载）。

---

## 二、过度设计反模式案例（costsuite）

| 过度设计 | 问题 | 正确做法 |
|---------|------|----------|
| 19 commits 用 6 层架构 | 原型不需要 | 4 层（UI→Service→Engine→Data） |
| MediatR 事件总线 | 零消费者 | 删除，有需求再加（YAGNI） |
| Polly 重试 | 离线系统无网络调用 | 删除 |
| AES-256 加密 | 本地 SQLite 无安全威胁 | 删除 |
| NLog + AOP 审计 | 原型无审计需求 | Console/Debug 日志即可 |
| 规格文档写未验证功能 | ERP/gRPC/审批流 | 仅写已验证功能 |

**判断准则（YAGNI 四问）**：→ 见 [architecture-reviewer.md](../skills/architecture-reviewer.md)（唯一权威定义处）。
**架构简化 ≠ 降低质量**：简化的是**未使用的复杂度**，保留的是**有实际价值的分离**（如 Engine 层纯计算独立于 Service 层，可独立测试）。

---

## 三、重构方法论（跨项目验证过）

> 重构方法论由 5 个项目验证提炼（见第一节反模式案例）。**执行模板**用 [refactoring-plan.md](refactoring-plan.md)，**每 Phase 守卫**用 [refactoring-guardian.md](../skills/refactoring-guardian.md)。

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
| 设计原则（SSOT/配置驱动/YAGNI/优雅降级） | [AGENTS.md 核心准则](../AGENTS.md) + [specification.md](specification.md) |
| 架构层级与单向依赖 | [project-structure.md](project-structure.md) |
| 闭环验证体系（交叉验证/黄金测试/差分测试） | [AGENTS.md 闭环验证强制](../AGENTS.md) + [verify-manual.py](../scripts/verify-manual.py) |
| 防御编程（哨兵契约/异常过滤器/NaN 守卫） | [AGENTS.md 防错三原则](../AGENTS.md) + [skills/csharp-SKILL.md](../skills/csharp-SKILL.md) |
| 文档职责体系 | [documentation.md](documentation.md)（唯一权威） |
| 会话管理（5 文件/20 轮/跨会话接力） | [AGENTS.md 会话管理](../AGENTS.md) |
| 版本管理（SemVer + 发版流程） | [CONTRIBUTING.md 发版规范](../CONTRIBUTING.md) + [release.yml](../.github/workflows/release.yml)（release-please 自动） |
| 工程化基础设施优先级 | [CONTRIBUTING.md](../CONTRIBUTING.md)（CI/模板/徽章清单已并入） |
