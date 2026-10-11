# 仓库现场整理（5S）

> 面向 AI 助手与维护者：把「仓库也是一处现场」变成可执行的整理清单 + 可复制的命令。
> 本文件只定义**整理动作与判定**——产物清单的唯一信源是 [.gitignore](../../.gitignore)，
> 文件用途的唯一信源是 [project-structure.md](project-structure.md)，二者都不在此重复。

## 5S 与本仓的对应

| 5S | 日文 | 在本仓的含义 | 主要手段 |
|----|------|--------------|----------|
| 整理 | Seiri | 现场只留需要的：构建产物 / 缓存 / 会话状态不入库 | .gitignore + 巡检命令（见第一节） |
| 整顿 | Seiton | 每样东西都有定位：新增文件必须登记目录树与索引 | verify-docs.py --strict（硬门禁） |
| 清扫 | Seiso | 把脏东西擦掉：断链 / 副本漂移 / 计数漂移 / 格式 | verify-all 全套门禁 |
| 清洁 | Seiketsu | 把清扫制度化：每类漂移都有门禁，不靠自觉 | 第四节「漂移类别 → 门禁」对照表 |
| 素养 | Shitsuke | 持续执行：定期整理 + 每次大改后回归 | 第五节维护触发 |

---

## 一、整理（Seiri）：不该在仓库里的东西，清出去

```bash
# 1) 有哪些「被忽略但实际存在」的产物（占本地现场，未入库）
git status --porcelain --ignored | grep '^!!'

# 2) 有没有产物混进了版本库（最危险：缓存/覆盖率/egg-info 被误提交）
git ls-files | grep -E '(__pycache__|\.egg-info|\.coverage$|\.pytest_cache|node_modules|/logs/|\.opencode-goal/)'
#    期望：零输出。有输出 = 立即 git rm --cached <路径> 并从 .gitignore 补齐规则

# 3) 清本地产物
python scripts/doctor.py     # 先诊断环境就绪性
make clean                   # 跨平台清理缓存（Windows 用 verify-all.ps1 同款清理步骤）
```

**判定**：第 2 条命令必须**零输出**（已入库的产物 = 污染信源）；第 1 条列出的目录可以存在（本地运行需要），
但**不得**出现在 `git ls-files` 中。产物清单增删 → 只改 [.gitignore](../../.gitignore)，不在本文件重复列名。

## 二、整顿（Seiton）：每样东西都有定位

| 新增了什么 | 必须登记到 |
|------------|-----------|
| 任意文件（新增/删除/移动） | [project-structure.md](project-structure.md) 目录树——`verify-docs.py --strict` 强制，未登记即 FAIL |
| 文档 | [docs/README.md](../README.md) 分类导航；高入口文档另登 [docs/index.md](../index.md) |
| 治理脚本 | [scripts/README.md](../../scripts/README.md) + [templates/README.md](../../templates/README.md)「治理脚本速查」 |
| 技能 | [skills/README.md](../../skills/README.md)（第三方技能另登悬空引用表） |
| 根文档 | 无（`ci.yml` 的 `*.md` 通配已自动纳入门禁） |
| 反模式案例 / 坑位条目 | 目标文档自身；条数由 AUTO_COUNTS 自动注入，**禁止手写** |

**判定**：`python scripts/verify-docs.py --strict` 全绿。

## 三、清扫（Seiso）：把脏东西擦掉

| 脏东西 | 命令 | 判定 |
|--------|------|------|
| 文档断链 / 文件未登记 | `python scripts/verify-docs.py --strict` | `[OK]` |
| 宪法副本（CLAUDE.md）漂移 | 同上（含「宪法副本一致性」向量） | `[OK]`；漂移则重建副本 |
| 上游悬空引用未登记 / 登记陈旧 | 同上（含「悬空引用登记」向量） | `[OK]` |
| 审查豁免到期未复查 | 同上（含「豁免到期」向量） | `[OK]` |
| 文档计数漂移 | `python scripts/gen-doc-counts.py --check` | `[OK]`；不一致就跑不带 `--check` 的版本刷新 |
| 代码风格 / 格式 | `python -m ruff check scripts/ tests/ examples/` + `python -m ruff format --check scripts/ tests/ examples/` | 0 错误 |
| 裸 except / 裸 catch | `python scripts/verify-docs.py --check-bare-handlers` | `[OK]` |
| 弱断言 / 自校验 / 缺测 | `python scripts/test-quality-guard.py --max-warn 0` | 0 FAIL / 0 WARN |
| 覆盖率低于阈值 | `python scripts/coverage.py` | ≥ pyproject `[tool.coverage]` |
| 生成物带 UTF-8 BOM | `pwsh -File scripts/test-template.ps1`（生成物无 BOM 断言，字节级判定） | 通过 |
| 缓存目录残留（`__pycache__` 等） | 目录扫描后手工删除 | 非门禁（不入库即可） |

> 一次跑完全部：`python scripts/verify-all.py`（跨平台）或 `.\scripts\verify-all.ps1`（Windows）。

## 四、清洁（Seiketsu）：把清扫制度化（漂移类别 → 门禁）

> **原则：能被自动对账的事实，绝不靠人自觉。** 下表是「本仓实证过的漂移 → 现在由谁看守」对照，
> 新增一类漂移时**必须同时补一条门禁**，否则这张表就是下一次事故的清单。

| 漂移类别（本仓实证） | 看守它的门禁 |
|----------------------|--------------|
| 文档断链 / 目录树未登记 | `verify-docs.py --strict`（CI quality-gate 硬门禁） |
| CLAUDE.md 与 AGENTS.md 不一致 | `verify-docs.py`「宪法副本一致性」（2026-10 新增：此前靠人工提醒，实测漂移 5 行） |
| 第三方技能子树悬空引用无人知晓 | `verify-docs.py`「悬空引用登记」两向校验（2026-10 新增） |
| 审查豁免到期未复查 | `verify-docs.py`「豁免到期」（2026-10 新增：实测过期 4 个版本） |
| 文档计数手写漂移 | `gen-doc-counts.py --check` + AUTO_COUNTS 标记 |
| 版本号多处不一致 | `verify-docs.py` 版本向量（manifest / pyproject / CHANGELOG / version.txt / `__version__`） |
| 全量验证步骤清单多实现分叉 | `tests/scripts/test_verify_all.py::TestFullVerifyStepParity`（py / ps1 / Makefile 三方比对） |
| 覆盖率低于阈值 | `coverage.py`（阈值读 pyproject，清旧产物防假绿） |
| 弱断言 / 恒真断言 / 自校验 | `test-quality-guard.py --max-warn 0` |
| 跨层依赖 | `verify-arch.py`（规则见 `scripts/architecture.json`） |
| 改了被守护文件却不触发 CI | `ci.yml` 的 `paths`（根文档用 `*.md` 通配；push 与 PR 的清单逐条一致，由 `test_ci_triggers.py` 强制，见 [案例 17](../methodology/cross-project-synthesis.md)） |
| 生成物带 BOM 使解析器拒绝 | `test-template.ps1` 生成物无 BOM 断言（2026-10 新增：此前生成项目 pytest 退出码 4、覆盖率门禁必红；见 [tooling-pitfalls #32](../pitfalls/tooling-pitfalls.md)） |

## 五、素养（Shitsuke）：什么时候做一次

| 触发 | 动作 |
|------|------|
| 每个功能点提交前 | 第三节「一次跑完全部」（`verify-all`） |
| 大改 / 重构后 | 第一节 + 第二节（重点看被误提交产物与未登记文件） |
| 每季度 / 发版前 | 本文件全表巡检；核对 [review-exemptions.md](review-exemptions.md) 到期项 |
| 发现新一类漂移 | **先补门禁再修数据**，并同步第四节对照表 |

> 判定标准一句话：**新人 clone 下来，`verify-all` 全绿，且 `git status --ignored` 之外没有未登记文件，现场就是合格的。**
