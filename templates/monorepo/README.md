# templates/monorepo/ — Monorepo 子项目脚手架

> 多子项目仓库（Monorepo）中新增子项目时的起点文件。

| 文件 | 用途 |
|------|------|
| `AGENTS.md.template` | 子目录级 AGENTS.md（子项目宪法，在根 AGENTS.md 基础上追加） |

## 何时使用

- 项目从单模块发展为多模块（5+ 子项目）
- 子项目有独立的语言/框架/构建系统
- 子项目间需要明确的依赖边界

## 使用方式

```bash
# 1. 复制 AGENTS.md.template 到子项目目录
cp templates/monorepo/AGENTS.md.template src/{子项目名}/AGENTS.md

# 2. 替换占位符
# {子项目名} → 子项目名（kebab-case）
# {子项目语言} → Go / TypeScript / Python / C#
# {子项目入口文件} → cmd/main.go / src/index.ts / __main__.py

# 3. 同步根目录文档
#    - rules/project-structure.md 目录树中新增子项目
#    - AGENTS.md 目录树中新增子项目
```

## Monorepo 架构约定

```
{{PROJECT_NAME}}/
├── AGENTS.md                # 根宪法（全局红线）
├── src/
│   ├── foundation/         # 共享层（类型转换/错误包装/数组操作）
│   ├── {子项目A}/          # 子项目 A
│   │   ├── AGENTS.md       # 子项目宪法（本模板生成）
│   │   ├── Core/
│   │   ├── Service/
│   │   └── go.mod / package.json / pyproject.toml
│   ├── {子项目B}/          # 子项目 B（❌ 不可直接 import A 的内部）
│   │   └── AGENTS.md
│   └── ...
├── tests/
│   ├── {子项目A}/
│   └── {子项目B}/
└── scripts/                # 统一验证脚本（所有子项目共用）
```

## 依赖规则

| 规则 | 说明 |
|------|------|
| 子项目 → foundation | ✅ 允许（foundation 是共享层） |
| 子项目 A → 子项目 B 内部 | ❌ 禁止（通过接口或 foundation 通信） |
| 子项目 → 根 rules/ | ✅ 允许（只读引用） |
| foundation → 任何子项目 | ❌ 禁止（共享层不感知子项目） |
