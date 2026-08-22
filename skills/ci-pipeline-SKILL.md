---
description: "CI 管道与脚本技能 — GitHub Actions / PowerShell 脚本 / PR 与发版流程陷阱（从 ExcelFormulaLabs、costsuite、EngSmartSuite、DocAudit、Excel-VBA-Libraries 五项目 + 模板自身 2026-08 排障实证提炼）。修改 workflow、CI 脚本或走发版流程前必读。"
name: "CI 管道与脚本技能"
argument-hint: "[修改的 .github/workflows/*.yml 或 CI 脚本] [--context 新增 job | 修复 CI 失败 | 发版]"
---

# CI 管道与脚本技能

> 从 5 个子项目 + 模板自身的 2026-08 审查/排障/发版实证中提炼。**每条均有真实案例**（来源标注），
> 不是理论清单。修改 `.github/workflows/`、CI 脚本（PowerShell/Python/bash）或走发版流程前必读。
>
> **SSOT 链接**：通用工具坑位（PowerShell 编码/git 行为）见 [tooling-pitfalls.md](../rules/tooling-pitfalls.md)；
> 高频反模式（门禁静默失效/配置流断裂）见 [cross-project-synthesis.md](../rules/cross-project-synthesis.md) 与 AGENTS.md「历史经验」。

## 1. PowerShell / 脚本执行陷阱（Script）

| # | 陷阱 | 正确做法 | 来源 |
|---|------|---------|------|
| S1 | **`git describe --tags` 在浅克隆/无 tag 时 exit 128**，且 pwsh 步骤的 `$LASTEXITCODE` 残留 128 → **GitHub Actions pwsh 步骤末尾误判失败**（ZIP 已生成、脚本无报错仍 exit 1） | 捕获后显式重置：`$tag = git describe --tags --abbrev=0 2>$null; if (-not $tag) { $tag = "" }; $LASTEXITCODE = 0`；Actions 的 pwsh 步骤会在结束时检查 `$LASTEXITCODE` | costsuite 2026-08-16（`BomAddIn-v0.0.0-ci.12` 生成后 exit 1 实证） |
| S2 | **PS 5.1 `Set-Content -Encoding UTF8` 写文件带 BOM** → 用 `git commit -F 文件` 时 **commit subject 带 BOM 前缀** → 破坏 Conventional Commits 校验（CI 提交规范检查拦截） | 提交消息文件用 Python `write_text(encoding='utf-8')` 或 `[System.Text.UTF8Encoding]::new($false)` 写入；提交后 `git show -s --format=%B \| xxd` 验证无 `EF BB BF` | 模板自身 2026-08（release-prep 提交 BOM 实证） |
| S3 | **`.ps1` 含中文注释必须 UTF-8 with BOM**（PS 5.1 按 ANSI 解析注释 → 乱码/解析失败） | 编辑 .ps1 后检查 BOM；无 BOM 补 `\xEF\xBB\xBF` 前缀（详见 tooling-pitfalls #3） | costsuite sign.ps1 2026-08 |
| S4 | **grep BRE 转义 `\{` 依赖 grep 版本宽容行为**（新版 GNU grep 3.11 报 `Invalid content of \{\}` exit 2）→ 检测逻辑静默翻转 | 检测/校验一律用 `grep -F` 固定串匹配（无正则解析，版本无关）；关键分支**不要 `2>/dev/null` 吞错误**（详见 tooling-pitfalls #25b） | 模板 detect 步骤 2026-08-15（release PR 全红实证） |
| S5 | **`git commit` 提交整个 index** → 分组提交时未跟踪/残留 stage 混入，或消息文件被提交 | 分组提交前先 `git reset`（unstage 全部）再按组 `git add <精确路径>`；每组提交后检查 `git status` 仅含该组 | 模板自身 2026-08（commit 分组事故实证） |
| S6 | **Windows 大小写不敏感文件系统**：`git mv agents.md AGENTS.md` 后 `git status` 不显示 rename；`Path.exists()` 对 `agents.md`/`AGENTS.md` 都返回 True（假阳性） | 以 `git ls-files` 精确核对大小写；CI（Linux）是大小写敏感的——本地验证与 CI 结果可能不一致 | costsuite/EngSmartSuite 2026-08-16（AGENTS.md 对齐实证） |
| S7 | **`.gitignore` 对已跟踪文件无效** → 仅加 gitignore 无法出库 | 出库需 `git rm -r --cached <路径>` + gitignore 双管齐下；`git add -A <路径>` 会被 ignore 拒绝（提示用 -f，别用） | 5 仓库 .qoder 出库 2026-08（ExcelFormulaLabs/costsuite/EngSmartSuite/DocAudit/VBA 共 5 处实证） |
| S8 | **Windows 控制台 GBK 乱码**：Python 脚本打印中文 → UnicodeEncodeError；`python -c "多行中文"` 引号地狱 | 脚本内 `sys.stdout.reconfigure(encoding='utf-8', errors='replace')`；多行代码写脚本文件执行，不用 `-c` | 模板/审查工具 2026-08（多次实证） |
| S9 | **Windows 无 bash**：POSIX 脚本（validate-commit-msg.sh 等）本地无法直接验证 | 本地跳过、由 CI（ubuntu）验证；或装 Git Bash 后以 `& 'D:\Program Files\Git\usr\bin\grep.exe'` 方式调用 | 模板 2026-08（commit 校验本地空转实证） |
| S10 | **`git mv` 前先确认目标不存在**；重命名后**全仓引用同步**（`grep -rn "旧名"` 复查，含大小写变体——Linux CI 上 404） | 重命名后跑链接/引用门禁（见 R5） | VBA `README_EN.md → README.en.md`、costsuite `agents.md → AGENTS.md` 2026-08 |

## 2. GitHub Actions CI 陷阱

| # | 陷阱 | 正确做法 | 来源 |
|---|------|---------|------|
| C1 | **提交规范检查需要完整历史**：浅克隆（fetch-depth:1）下 `git rev-list base..HEAD` 拿不到 PR 基线 | checkout 补 `fetch-depth: 0`（代价：大仓库变慢，可接受） | 模板/costsuite/VBA ci.yml 2026-08 |
| C2 | **覆盖率门禁无阈值 = 门禁不会红**：`pytest --cov` 不配 `--cov-fail-under`，覆盖率下降 CI 照绿 | 必须 `--cov-fail-under=N`；"覆盖率数据缺失时显式失败而非静默通过" | EngSmartSuite 2026-08-15 审查（P1-⑤） |
| C3 | **多层 job 相互掩盖失败**：Build 失败 → Test/后续步骤全部不跑，每修一层暴露下一层（模板 release PR 曾连爆 3 层：detect → 提交前自检 → 示例测试） | 修完一层**必须重跑全链路**，直到全部 job 绿；不要只看当前失败点 | 模板 2026-08-15（release PR 全红三层实证） |
| C4 | **checkout 默认浅克隆**：`git describe`/tag 比对/历史审计在默认配置下不可用 | 需要 tag/历史/基线时显式 `fetch-depth: 0` | costsuite Package job 2026-08-16（S1 同源） |
| C5 | **actions 用 `@vN` tag 引用**（供应链：tag 可变）；**dependabot 对同一 action 的多个 action 文件（如 codeql-action 的 init/autobuild/analyze）分别发 PR，部分合并即版本混用**（init@4.37.7 + autobuild@4.37.6 → autobuild 步骤 30-49s 快速失败） | 固定 commit SHA + 注释版本号；**同一 action 多处引用一次性统一升级 SHA 并关闭 dependabot 分 PR**（security.yml 注释既有约定，两次实证） | 两仓库 2026-08-16 加固；模板 codeql-action 2026-08-22（3 个 dependabot PR 全部 autobuild fail，统一升级 v4.37.7 后关闭） |
| C6 | **Node 20 弃用**：setup-python@v5 等旧 action 被强制跑 Node 24（warning 非失败） | 升级到支持 Node 24 的大版本（setup-python v6+）；warning 是升级信号 | 模板/两仓库 2026-08-16（CI 日志 warning） |
| C7 | **`workflow_dispatch` 是诊断利器**：CI 只在 PR 上跑，main 直推无法触发 → 无法复现 | 临时分支改 workflow + `gh workflow run ci.yml --ref <branch>` 复现/验证，用完删分支（对照实验排除 PR 上下文因素） | 模板 detect 排障 2026-08-15（dispatch 对照实证） |
| C8 | **release-please force-push 与 pull_request 事件竞争**：可能产生 0s `action_required` 幽灵 run（无 job、无日志、PR checks 不附着） | **`gh run rerun <幽灵 run id>` 即可让 checks 正常附着**（CI/Security 双 workflow 各 rerun 一次，已验证成功）；以最新 run 与 PR statusCheckRollup 为准；幽灵 run 忽略 | 模板 release PR #12 2026-08-15（幽灵 run 实证）、#16/#17 2026-08-22（幽灵 run + rerun 处置成功两次） |
| C9 | **PR 事件 checkout 的是 `refs/pull/N/merge`（合并提交）**，不是 PR head | 涉及 base 比对/merge 语义的步骤按合并提交设计；本地复现用 `git fetch origin refs/pull/N/merge` | 模板 detect 排障 2026-08-15 |
| C10 | **模板仓库自身 CI 自举**：占位符命令（`{{BUILD_CMD}}` 等）在模板仓库不可执行 | is_template 检测（grep -F 运行时拼装，见 S4）+ 模板模式用**字面命令**门禁（pytest/ruff/链接检查直接写死） | 模板 ci.yml 2026-08（三层门禁实证） |
| C11 | **CodeQL autobuild 对无构建语言/模板仓库硬失败** | security.yml 只保留 extraction 型语言（python/javascript-typescript）；csharp/go 需可构建源码 | 模板 security.yml 2026-08 |
| C12 | **CI 步骤中文名 + GBK 控制台**：日志乱码不影响执行，但排查困难 | workflow 步骤名可用中文（Actions 日志 UTF-8），脚本输出统一 ASCII 标记 `[OK]/[FAIL]/[SKIP]` | 模板 2026-08（verify 脚本统一标记实证） |

## 3. PR 与发版流程陷阱

| # | 陷阱 | 正确做法 | 来源 |
|---|------|---------|------|
| R1 | **PR 模板 checklist 链接指向不存在的文件**（VBA PR 模板 4 处死链：skills/vba/SKILL.md、docs/VBA_LIB_Documentation.md 等） | PR/Issue 模板纳入文档链接门禁（见 R5）；模板内链接用真实路径 | VBA 2026-08-16（链接门禁 36 处漂移实证） |
| R2 | **release tag 与 CHANGELOG 语义错位**：tag 打在含 Unreleased 修复批的 HEAD → 标签混入未发布代码 | **发布前检查 CHANGELOG [Unreleased] 是否还有内容**；先固化版本段再打 tag；tag 必须指向与 CHANGELOG 版本一致的提交 | VBA v2.1.0 事故 2026-08-16（删除重发 v2.1.1） |
| R3 | **release-please 版本推导**：pre-1.0 下 `bump-patch-for-minor-pre-major` → feat 当 patch；BREAKING 当 minor；手动覆盖用 release PR commit body 加 `Release-As: x.y.z` | 合并 release PR 用 **rebase**（保留 release 提交）；合并后自动 tag + Release | 模板 v0.2.0 发版 2026-08-15 |
| R4 | **提交规范三层门禁**：本地 hook（core.hooksPath）+ CI PR step（validate-commit-msg.sh）+ release-please 依赖——缺一层则格式漂移无拦截 | 三层都配；校验规则唯一权威 = 一个脚本（避免多份规则漂移） | 模板/costsuite/VBA 2026-08 |
| R5 | **文档链接门禁**：Markdown 链接（相对文档目录）与反引号路径（**根相对**，仅校验已知根前缀：scripts/rules/skills/docs/tests/src/tools/.github 等；AI 本地目录 .claude/.codegraph/.qoder 豁免；占位符/模式串跳过）语义不同，混用导致漏检/误报 | 移植 `check-doc-links.py`（verify-docs 轻量版）入 CI；CI 首次接入必现一批历史漂移（两仓库 65 处实证），修完即全绿 | costsuite/VBA 2026-08-16（65 处漂移实证） |
| R6 | **PR 模板应要求验证记录**：构建/测试/全量验证三选一勾选，数值变更附交叉验证输出 | 模板 checklist 字段与仓库实际门禁一一对应（VBA「All parameters As Variant」「6 处同步」等仓库红线进模板） | VBA PR 模板（仓库红线 checklist 实证） |
| R7 | **release 构件**：发布前核对构件与版本代码一致（xlsm/zip 构建时间 vs CHANGELOG 固化时间）；**二进制重建需本机环境（Excel 等），CI 无法替代**——提前规划构建机器 | 发版 checklist 加「构件重建 + 上传」步骤；Release 资产列表发布后立即核对 | VBA v2.1.1 2026-08-16（xlsm 过期待重建实证） |

## 4. 诊断决策树（CI 失败时）

```
CI 失败
├── 步骤没跑 → 上层 job 失败被掩盖（C3）→ 修上层后重跑全链路
├── exit 127（command not found）→ 占位符命令在模板模式执行（C10）/ shell 缺失（S9）
├── exit 1 且脚本无报错 → pwsh 步骤 LASTEXITCODE 残留（S1）
├── grep 报 Invalid content → BRE 转义版本问题 → grep -F（S4）
├── 提交规范检查失败 → subject 带 BOM（S2）/ 格式不符（R4）
├── 覆盖率下降不红 → 无 --cov-fail-under（C2）
└── 链接检查报漂移 → 按 R5 语义逐条修（Markdown 链接文档相对 / 反引号根相对）
```

## 5. 发版前检查清单

- [ ] CHANGELOG [Unreleased] 已固化或确认无内容（R2）
- [ ] tag 指向与 CHANGELOG 版本一致的提交（R2）
- [ ] Release 构件已重建并上传（R7）
- [ ] 提交规范三层门禁在位（R4）
- [ ] 文档链接门禁全绿（R5）
- [ ] CI 全链路绿（非仅当前 job）（C3）
