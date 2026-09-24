# {{PROJECT_NAME}}

{{ONE_LINE_DESCRIPTION}}

> 本页由 [mkdocs](https://www.mkdocs.org/) 构建发布（站点配置：仓库根 `mkdocs.yml`）。
> 仓库内根文档（README / AGENTS.md / CONTRIBUTING）不在站点导航，请直接在仓库查看。

## 快速入口

| 入口 | 内容 |
|------|------|
| [项目规格](spec/specification.md) | 项目做什么、功能范围与业务规则（唯一信源） |
| [API 参考](spec/api-reference.md) | 全部 Public 签名、参数与错误行为（唯一信源） |
| [用户手册](spec/user-manual.md) | 面向使用者的示例与结果解读 |
| [术语表](spec/context.md) | 领域术语唯一定义 |
| [文档职责](governance/documentation.md) | 各文档分工、SSOT 原则与维护规则 |
| [哨兵契约](pitfalls/sentinel-contract.md) | 无效输入返回值约定（L1-L5）与 NaN/Inf 守卫 |
| [陷阱清单](pitfalls/tooling-pitfalls.md) | 工具/脚本坑位（含真实案例） |

## 本地预览

```bash
pip install mkdocs-material
mkdocs serve          # http://127.0.0.1:8000
mkdocs build --strict # 与 CI 同口径构建（警告即失败）
```
