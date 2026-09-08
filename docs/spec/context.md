# 领域术语表

> 本文件是所有领域术语的**唯一定义**。代码、文档、注释中使用的术语必须与此处一致。

## 通用术语

| 术语 | 定义 | 备注 |
|------|------|------|
| SSOT (Single Source of Truth) | 信息只在一处定义 | 项目核心原则 |
| 哨兵值 (Sentinel) | 不可转换值的类型零值替代（NaN/0/false/""） | 不抛异常，静默返回 |
| 防御编程 (Defensive Programming) | 对每个输入假设其可能为 null/空/越界/NaN | 守卫前置 |
| 闭环验证 (Closed-Loop Verification) | 用独立实现交叉比对，禁止自校验 | 至少两路独立计算 |
| 交叉验证 (CrossVal) | 用 Python/scipy 等独立计算结果与项目输出比对 | 非机器学习中的交叉验证 |
| 黄金测试 (Golden Test) | 已知正确输入的固定期望输出测试 | 回归防护 |
| 差分测试 (Differential Testing) | 同一输入经不同路径（CLI/Web/API）产生相同输出 | 一致性保证 |

## 架构术语

| 术语 | 定义 |
|------|------|
| UDF 层 (UDF Layer) | 用户可见函数入口，仅做分发与适配，不含业务逻辑 |
| Core 层 (Core Layer) | 纯逻辑实现，零外部框架依赖 |
| Engine 层 (Engine Layer) | 纯计算引擎，零依赖（无 IO/无状态），可独立单元测试 |
| Service 层 (Service Layer) | 业务编排层，有状态/有事务/有外部依赖，协调 Engine 与 Data |
| Foundation/共享层 (Foundation / Shared Layer) | 跨模块复用的基础工具（类型转换、数组操作、错误包装） |
| 桥接层 (Services) | 连接引擎与 UI 的唯一通道 |
| 契约 (Contract) | 数据对象定义（Request/Result），跨层通信协议 |

## 测试术语

| 术语 | 定义 |
|------|------|
| 数值正确性测试 (Numerical Correctness Test) | 与参考实现（scipy/numpy）对比，容差 1e-10 |
| 数学不变量测试 (Mathematical Invariant Test) | 验证数学约束（p∈[0,1]、R²≥0、Cpk≤Cp） |
| 模糊测试 (Fuzz Testing) | 空数据/单行/全NaN/常量列/共线/大样本 |
| E2E 测试 (End-to-End Test) | 端到端，模拟真实用户操作路径 |

## 项目专属术语

> 以下术语由各项目自行填充。

| 术语 | 定义 | 所属项目 |
|------|------|----------|
| `{{TERM_1}}` | {{DEFINITION_1}} | {{PROJECT_1}} |
| `{{TERM_2}}` | {{DEFINITION_2}} | {{PROJECT_2}} |
