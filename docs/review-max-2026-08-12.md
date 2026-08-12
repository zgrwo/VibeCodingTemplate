# VibeCodingTemplate 发行前 Max 审查报告

**审查级别**: Max (18 维度，多代理并行 + 对抗验证)
**审查日期**: 2026-08-12
**审查基线**: 22a2eca (HEAD)
**目标版本**: 0.2.0

## 执行摘要

- 总发现数: 59
- P1 (高风险): 12
- P2 (改善): 19
- P3 (建议): 28
- 对抗验证驳回: 0 (12 项 P1 全部 CONFIRMED)
- 基线门禁: verify-all 全绿 · ruff 零违规 · 164 tests · 覆盖率 80%
- 结论: 🟡 修复 9 项 P1 后条件发行

## P1 修复清单（全部经对抗验证存活）

| # | 文件 | 问题 | 修复方向 |
|---|------|------|---------|
| P1-1 | templates/NewModule/{Name}Core.Tests.cs.template:20 | 测试模板 Compute_normal_input 调用 Should().Be(/* {期望值} */)，期望值整个被 | 把 `Be(/* {期望值} */)` 改为带具体值的断言，如 `Be(2.0)`（模板内 compute(1.0)=2.0 的语义一致）；或在 {期望值} 前补默认值，保证占位符替换后 Be() 有实参。 |
| P1-2 | templates/language/offline-setup.py.template:14 | docstring 与 README 宣传的干跑用法 `python offline-setup.py install  | 把 --print-cmd 挪到子命令之前（如 `python offline-setup.py --print-cmd install --src wheels/`）并同步修正 docstring 第 12-14 行三 |
| P1-3 | templates/NewModule/{Name}VariantKit.bas.template:23 | NormalizeInput 的 Range 分支只处理 IsArray(arr) 的展平，未把单格 Range 的标量 | 在 Range 分支 `If IsArray(arr)` 之后补 `If Not IsArray(arr) Then`：把标量包成 0 To 0 单元素数组（与 Else 分支同构），或复用第 39-41 行的单值包装逻 |
| P1-4 | templates/language/tsconfig.json.template:28 | tsconfig 使用已被 TypeScript 6/7 移除的 baseUrl，且 paths 目标值 src/{Mo | 删除 `"baseUrl": "."`，把 paths 目标改为 `"./src/{Module}/*"`（相对路径）；如需兼容 TS 5.x 旧版可加注释说明 baseUrl 已废弃。 |
| P1-5 | .github/workflows/ci.yml:168 | quality-gate job 设了 setup-python（137-139 行）却没有任何依赖安装步骤，LINT_ | 在 quality-gate 的 LINT/COVERAGE 之前增加依赖安装步骤（Python: `python -m pip install -e ".[dev]"`；.NET: 增加 actions/setup-d |
| P1-6 | D:/Workspace/zgrwo/Harmonization/VibeCodingTemplate/CHANGELOG.md:7 | v0.1.2 已发布（本地 refs/tags/v0.1.2 与远程 origin/main fa5c61c 均存在）， | 发版前先合并/变基 origin/main（纳入 25decc8 'release 0.1.2' 与 fa5c61c 合并提交），.release-please-manifest.json 同步为 0.1.2，再触发 r |
| P1-7 | scripts/falsy-audit.py:208 | _check_or_fallback 在遇到第一个"可命名但未命中风险名单"的操作数时无条件 break，漏检其后真正的 | 把 line 208 的 `break` 移到 `if level:` 分支内部，未命中名单的变量操作数继续扫描后续操作数（与函数调用操作数 `continue` 的行为一致），直到找到已分类操作数或链尾。 |
| P1-8 | scripts/run-affected-tests.py:93 | find_tests_for() 子串匹配未归一化连字符：kebab-case 脚本（verify-docs.py/ge | 匹配前把连字符归一为下划线：`stem_n = stem.lower().replace("-", "_")`，对 `test_*.py` 与 `*Tests.cs` 两个分支均用 `stem_n in p.name.l |
| P1-9 | scripts/init-project.ps1:151 | init-project.ps1 与 init-project.py 功能不对等：ps1 在占位符扫描/替换/未替换检查 | 与 py 版对齐：在 ps1 扫描（第 151 行 Where-Object）、替换（第 234 行 $files 构造）、未替换检查（第 279 行）三处加入跳过条件 `$_.FullName -notmatch "[ |

## 知识库更新项（维度18）

- [ ] AGENTS.md 高频修复模式：登记「run-affected-tests 连字符匹配回归」（本轮修复1引入）
- [ ] tooling-pitfalls.md：登记「TS baseUrl 已移除」「C# 测试模板 Be() 空参」「VBA 单格 Range 标量」
- [ ] cross-project-synthesis.md：补「模板占位符替换后不可编译」反模式
- [ ] exemptions.md：无豁免项

*报告生成: Claude Code (max mode, 12 代理: 9 维度审查 + 对抗验证)*