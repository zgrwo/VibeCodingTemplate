# build/ — 构建配置

> 存放项目实际构建配置与产物（按需裁剪）。结构唯一定义见 [project-structure.md](../rules/project-structure.md)。

## 用途

- 项目实际构建辅助配置（区别于 `templates/language/` 的语言级构建模板）
- 编译产物输出目录（`build/output/`，.gitignore 已排除）

## 约定

- 语言级构建配置模板放 `templates/language/`，本目录放项目实际构建配置
- 单文件脚本/小型项目通常无需本目录（YAGNI，见 project-structure.md「规模适配」）
- 空目录仅保留本 README 说明用途
