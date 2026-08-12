---
description: "Python 编码技能 — falsy 陷阱、异常处理、pandas/scipy/matplotlib 陷阱、架构分层、新增函数流程。修改 .py 前必读。"
name: "Python 编码技能"
argument-hint: "[修改的 .py 文件/模块] [--context 新增分析函数 | 修复缺陷 | 重构]"
---

# Python 编码技能

> 从 EngSmartSuite + DocAudit 历史 diff 中提炼的 Python 易错点与最佳实践。修改 .py 前必读。
> **SSOT 防御契约**：无效输入返回什么（NaN 哨兵 vs 异常）见 [rules/sentinel-contract.md](../rules/sentinel-contract.md)。

## 1. Falsy 陷阱（最高频错误）

> **SSOT**：完整检查清单（核心规则/正反例/高风险变量名/历史案例）见 [falsy-pitfalls.md](../rules/falsy-pitfalls.md)，此处只列最小示例。

```python
# ❌ 0、空字符串、空列表都是 falsy
if value:  # value=0 时为 False！
    result = compute(value)

# ✅ 显式检查 None（0 是有效值时）
if value is not None:
    result = compute(value)
```

## 2. 异常处理

```python
# ❌ 裸 except 吞掉一切（包括 KeyboardInterrupt）
try:
    result = risky_op()
except:
    result = None

# ✅ 捕获具体异常
try:
    result = risky_op()
except (ValueError, TypeError) as e:
    logger.warning(f"输入异常: {e}")
    result = None

# ❌ 暴露 traceback 给用户
except Exception as e:
    return {"error": traceback.format_exc()}

# ✅ 用户友好的错误信息
except Exception as e:
    logger.exception("内部错误")  # 日志保留完整信息
    return {"error": f"分析失败：{type(e).__name__}"}  # 用户看简要
```

## 3. pandas 陷阱

```python
# ❌ FutureWarning: sum(axis=None) 语义变更
df.sum(axis=None)  # 旧版返回标量，新版返回 Series

# ✅ 明确意图
df.sum().sum()  # 全表求和
df.sum(axis=1)  # 按行求和

# ❌ StringDtype 与 one-hot 编码冲突
pd.get_dummies(df["col"])  # StringDtype 列可能产生意外结果

# ✅ 先转 str
pd.get_dummies(df["col"].astype(str))

# ❌ 中位数填充产生新 NaN（仅填充强制转换产生的）
df.fillna(df.median())  # 非数值列变 NaN

# ✅ 仅填充数值列
num_cols = df.select_dtypes(include=[np.number]).columns
df[num_cols] = df[num_cols].fillna(df[num_cols].median())
```

## 4. scipy/statsmodels 兼容性

```python
# ❌ 字符串分布名在新版 scipy 中不兼容
from scipy.stats import kstest
kstest(data, 'norm')  # 新版可能报 ndtr 签名错误

# ✅ 使用 frozen distribution
from scipy import stats
dist = stats.norm(loc=mu, scale=sigma)
kstest(data, dist.cdf)

# ❌ statsmodels 警告含 'failed' 单词被误判为失败
if 'failed' in result_output:  # 误判！
    raise Error("分析失败")

# ✅ 检查实际返回码/异常，不检查字符串内容
```

## 5. matplotlib 陷阱

```python
# ❌ 在 engine 设置 Agg 后端前导入 pyplot
import matplotlib.pyplot as plt  # 文件顶部导入 → 后端已锁定

# ✅ 延迟导入
def plot_chart(data):
    import matplotlib
    matplotlib.use('Agg')  # CLI 模式无 GUI
    import matplotlib.pyplot as plt
    # ...

# ✅ 或使用条件后端
import matplotlib
if not os.environ.get('DISPLAY'):
    matplotlib.use('Agg')
```

## 6. 架构分层（EngSmartSuite 模式）

```
core/       ← ① 数据契约层：零依赖，仅 dataclass
engine/     ← ③ 分析引擎层：纯 Python，零 xlwings/flask 依赖
services/   ← ② 应用服务层：唯一桥接层
web/        ← Web 层：依赖 services/，不直接依赖 engine/
```

- ✅ 引擎函数签名统一：`(AnalysisRequest) -> AnalysisResult`
- ✅ 每个分析函数返回 `summary` 字段（中文工艺语言结论）
- ❌ engine/ 不导入 flask/xlwings
- ❌ web/ 不直接导入 engine/（通过 orchestrator 间接调用）

## 7. 新增分析函数 11 步清单

1. 引擎文件中实现 `(AnalysisRequest) -> AnalysisResult`
2. `engine/__init__.py` 导出
3. `services/orchestrator.py` → `TASK_REGISTRY` 注册
4. `DEFAULT_PARAMS` 添加默认参数
5. `TASK_LABELS` + `TASK_GROUPS` 添加条目
6. `web/static/app.js` → `TASK_PARAMS` 添加参数默认值
7. `templates/` 创建 YAML 模板
8. 测试：`test_correctness.py` + `test_invariants.py` 必做
9. 更新 `api-reference.md`
10. 更新 `python-SKILL.md` 决策树（如引入新场景）
11. 更新 `user-manual.md`

## 8. 依赖管理

```python
# ❌ 版本上限导致安装冲突
# requirements.txt: numpy<=1.24, scipy<=1.10

# ✅ 仅保留下限
# requirements.txt: numpy>=1.21, scipy>=1.7
```

## 8.5 Pydantic v2 陷阱

```python
# ❌ Pydantic v2 不兼容位置参数（静默/报错取决于模型配置）
req = AnalysisRequest(data_df, alpha)

# ✅ 必须使用关键字参数
req = AnalysisRequest(data=data_df, alpha=alpha)

# ❌ v1 遗留写法（validator 装饰器等）
# ✅ v2 使用 @field_validator / model_config
```

> Pydantic v2 默认禁止位置参数构造（v1 可部分兼容）。所有模型实例化必须显式关键字。

## 9. 跨平台兼容

```python
# ❌ Windows 专用 API 未捕获
import winreg  # Linux 上 ImportError

# ✅ 条件导入 + 降级
try:
    import winreg
except ImportError:
    winreg = None  # 非 Windows 环境降级

# ❌ 路径硬编码反斜杠
path = "C:\\Users\\data"

# ✅ pathlib
from pathlib import Path
path = Path.home() / "data"
```

## 9.5 变量作用域初始化

```python
# ❌ 循环内依赖未初始化变量（首次迭代可能不存在）
for grp in groups:
    if cond:
        violations = detect(grp)   # 变量在此分支才初始化
    report(violations)             # 未命中分支时 NameError / 引用上次残留

# ✅ 循环外显式初始化
violations = []
for grp in groups:
    if cond:
        violations = detect(grp)
    report(violations)
```

## 10. 提交前必检

- [ ] `ruff check src/` 零错误
- [ ] `pytest tests/ -x -q` 全绿
- [ ] 无裸 `except:` 或 `except Exception:` 不记录日志
- [ ] 新增函数已注册到 TASK_REGISTRY（如适用）
- [ ] 新增 Public 接口已同步 api-reference.md
- [ ] 数值结果有交叉验证（与 scipy/numpy 独立计算比对）
