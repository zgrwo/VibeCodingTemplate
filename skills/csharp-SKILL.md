---
description: "C# 编码技能 — Excel-DNA 黄金法则、防错三原则、封送陷阱、依赖管理。修改 .cs 前必读。"
name: "C# 编码技能"
argument-hint: "[修改的 .cs 文件/模块] [--context 新增 UDF | 修复缺陷 | 重构]"
---

# C# 编码技能

> 从 ExcelFormulaLabs + costsuite 历史 diff 中提炼的 C# 易错点与最佳实践。修改 .cs 前必读。

## 1. Excel-DNA 黄金法则

### 1.1 UDF 声明规范

```csharp
// ✅ 正确：所有参数 object，返回 object
[ExcelFunction(Name = "STATS.MEAN", Description = "计算均值")]
public static object StatsMean(
    [ExcelArgument(Name = "data", Description = "数据范围")] object data,
    [ExcelArgument(Name = "[hasHeaders]", Description = "是否含表头")] object hasHeaders = null)
{
    return WrapError(() => StatsCore.Mean(ToDoubles(data), ToBool(hasHeaders, false)));
}

// ❌ 错误：强类型参数（Excel 传入 ExcelMissing/ExcelEmpty 时崩溃）
public static double StatsMean(double[] data)
```

### 1.2 ExplicitExports 必须开启

```xml
<!-- ❌ 未设置：MathNet/Foundation 公共方法被注册为 UDF -->
<ExternalLibrary Path="Analytics.dll" />

<!-- ✅ 正确：仅导出标记了 [ExcelFunction] 的方法 -->
<ExternalLibrary Path="Analytics.dll" ExplicitExports="true" />
```

### 1.3 纯依赖库用 Reference 而非 ExternalLibrary

```xml
<!-- ❌ ExternalLibrary 会扫描公共方法 -->
<ExternalLibrary Path="MathNet.Numerics.dll" />

<!-- ✅ 纯依赖用 Reference -->
<Reference Path="MathNet.Numerics.dll" />
```

## 2. 防错三原则

### 2.1 静默传播阻断

```csharp
// ❌ NaN 静默传播到最终结果
double sum = values.Sum();  // 如果 values 含 NaN，sum = NaN

// ✅ 显式守卫
var clean = values.Where(v => !double.IsNaN(v) && !double.IsInfinity(v)).ToArray();
if (clean.Length == 0) return ExcelError.ExcelErrorValue;
```

### 2.2 异常过滤器统一

```csharp
// ❌ 裸 catch 吞掉一切
catch { return ExcelError.ExcelErrorValue; }

// ✅ 异常过滤器排除不可恢复异常
catch (Exception ex) when (ex is not OutOfMemoryException
                        and not StackOverflowException
                        and not AccessViolationException)
{
    return ExcelError.ExcelErrorValue;
}
```

### 2.3 哨兵契约（InputNormalizer）

| 目标类型 | 不可转换时返回 | 不抛异常 |
|----------|---------------|----------|
| double | NaN | ✅ |
| long/int | 0 | ✅ |
| bool | false | ✅ |
| DateTime | MinValue | ✅ |
| string | "" | ✅ |
| 未知类型 | **throw** | ❌ 禁止 `return default(T)` |

## 3. 双 TFM 兼容（net48 + net8.0）

```csharp
// ✅ 条件编译仅限内部实现
#if NET48
    // net48 特定实现
#else
    // net8.0 特定实现
#endif

// ❌ 禁止在方法签名/参数上使用条件编译
// ❌ 禁止引入单框架 NuGet 包
```

### IntelliSense 隔离

```csharp
// ✅ net48 启用 IntelliSense
#if NET48
    ExcelDna.IntelliSense.IntelliSenseServer.Install();
#endif

// ❌ net8.0 禁止添加 IntelliSense 代码（Excel-DNA Issue #343）
```

### IsExternalInit polyfill（net48 + record）

```csharp
// ❌ .NET Framework 4.8 编译期错误：record 需要 IsExternalInit 类型
public record AnalysisResult(double Mean, double Std);

// ✅ net48 需自行声明 polyfill（或避免使用 record）
#if NETFRAMEWORK
namespace System.Runtime.CompilerServices
{
    internal static class IsExternalInit { }
}
#endif
```

## 4. 架构分层

```
UDF 层 (public static, [ExcelFunction])  ← 仅分发与适配
  ↓ MapOver / MapOverMulti / V() 分发
Core 层 (internal static, 纯逻辑)       ← 零 Excel 依赖
  ↓ 依赖
Foundation (共享工具)                    ← InputNormalizer, ElementWiseMapper, OutputWrapper
```

- ✅ UDF 不包含业务逻辑
- ✅ Core 不引用 `ExcelDna.Integration`
- ❌ 禁止跨层直接调用或反向依赖

## 5. 表头行契约

```csharp
// ✅ 所有接受 object[,] 的 Core 方法必须含 hasHeaders 参数
internal static double[] Mean(object[,] table, bool hasHeaders = true)
{
    int startRow = hasHeaders ? 1 : 0;  // 跳过表头
    // ...
}
```

## 6. 常见数值陷阱

| 陷阱 | 后果 | 修复 |
|------|------|------|
| 除以零未守卫 | NaN/Infinity 传播 | 前置 `if (denominator == 0)` |
| 空集合 `.First()` | InvalidOperationException | 前置 `.Any()` 检查 |
| `double[]` 返回给 Excel-DNA | 封送失败 | 返回 `object` 或 `object[,]` |
| `long[]` 返回 | 封送失败 | 转为 `double[]` |
| 相关矩阵 rows<2 | 除零 | 前置守卫返回 #VALUE! |

## 7. 安全防御

```csharp
// 路径沙箱
internal static string ValidatePath(string path)
{
    var full = Path.GetFullPath(path);
    if (SandboxRoot != null && !full.StartsWith(SandboxRoot, StringComparison.OrdinalIgnoreCase))
        throw new UnauthorizedAccessException("路径超出沙箱范围");
    // 逐段检查重解析点（junction/symlink）
    return full;
}

// SQL 参数化
// ❌ $"SELECT * FROM t WHERE col = '{userInput}'"
// ✅ cmd.Parameters.AddWithValue("@p0", userInput)

// 正则超时
Regex.Match(input, pattern, RegexOptions.None, TimeSpan.FromSeconds(5))
```

## 8. 提交前必检

- [ ] `grep -rn "catch\s*{" src/ --include="*.cs"` 返回空（无裸 catch）
- [ ] 新增 UDF 有 `[ExcelFunction]` + `[ExcelArgument]` 属性
- [ ] 返回类型兼容 Excel-DNA 封送（object / object[,] / double[]）
- [ ] `dotnet build` 双 TFM 均通过
- [ ] `dotnet test` 全绿
- [ ] 新增函数已同步 api-reference.md
