---
description: "VBA 编码技能 — 参数类型陷阱、错误处理三模式、数组陷阱、类型判断、模块依赖。修改 .bas/.cls 前必读。"
name: "VBA 编码技能"
argument-hint: "[修改的 .bas/.cls 文件/模块] [--context 新增 UDF | 修复缺陷 | 重构]"
---

# VBA 编码技能

> 从 5 个项目的历史 diff 中提炼的 VBA 易错点与最佳实践。修改 .bas/.cls 前必读。

## 1. 参数类型陷阱（最高频错误）

### 1.1 所有 UDF 参数必须 `As Variant`

```vba
' ❌ 错误：Range 传入时 #VALUE!
Public Function MyFunc(text As String) As Variant

' ✅ 正确：接受 Range 和直接值
Public Function MyFunc(text As Variant) As Variant
    Dim s As String
    If TypeOf text Is Range Then s = text.Value Else s = CStr(text)
```

### 1.2 Range vs 数组双路径

Public 函数必须同时处理 Range 对象和 Variant 数组：
```vba
' ✅ 使用 VariantKit.NormalizeInput 统一入口
Dim arr As Variant
arr = VariantKit.NormalizeInput(v, flattenColumn:=True)
```

## 2. 错误处理三模式

| 场景 | 模式 | 示例 |
|------|------|------|
| UDF（ worksheet 函数） | 返回 `CVErr(xlErrValue)` | 不抛异常，不中断公式 |
| VBA 内部函数 | `Err.Raise` + 有意义的 Source/Description | 调用方可捕获 |
| 资源操作 | `On Error GoTo Cleanup` + Finally 标签 | 确保释放 |

```vba
' ❌ 禁止：裸 On Error Resume Next 不检查 Err
On Error Resume Next
result = SomeRiskyOp()
' 忘了检查 Err.Number...

' ✅ 正确：
On Error Resume Next
result = SomeRiskyOp()
If Err.Number <> 0 Then
    Err.Raise Err.Number, "Module.Func", Err.Description
End If
On Error GoTo 0
```

## 3. 数组陷阱

### 3.1 0-based vs 1-based

```vba
' ❌ 假设所有数组都是 1-based
For i = 1 To UBound(arr)  ' 如果 arr 是 0-based 则跳过第一个元素

' ✅ 始终用 LBound
For i = LBound(arr) To UBound(arr)
```

### 3.2 空数组检测

```vba
' ❌ UBound 对未初始化数组抛异常
If UBound(arr) >= 0 Then  ' 崩溃！

' ✅ 安全检测
Function IsArrayEmpty(arr As Variant) As Boolean
    On Error Resume Next
    IsArrayEmpty = (UBound(arr) < LBound(arr)) Or (Err.Number <> 0)
    Err.Clear
End Function
```

### 3.3 ReDim Preserve 只能扩展最后一维

```vba
' ❌ ReDim Preserve arr(UBound(arr) + 1, 5)  ' 运行时错误
' ✅ 只能 Preserve 最后一维，或转置处理
```

## 4. 类型判断陷阱

### 4.0 Optional 数组参数不支持 ByRef

```vba
' ❌ 编译/运行错误：Optional ByRef 数组参数不被 VBA 支持
Public Function MyFunc(Optional ByRef arr() As Variant) As Variant

' ✅ Optional 数组参数必须 ByVal + 空数组检测
Public Function MyFunc(Optional ByVal arr As Variant = Empty) As Variant
    If IsArrayEmpty(arr) Then
        ' 使用默认逻辑
    End If
```

### 4.1 `And`/`Or` 不短路

```vba
' ❌ 即使 arr 为空，第二个条件仍会求值 → 崩溃
If Not IsEmpty(arr) And UBound(arr) > 0 Then

' ✅ 嵌套 If
If Not IsEmpty(arr) Then
    If UBound(arr) > 0 Then
```

### 4.2 IsArray 不可靠

```vba
' ❌ IsArray 对某些 Variant 包装返回 False
' ✅ 使用 UBound 错误探测
Function IsArrayValid(v As Variant) As Boolean
    On Error Resume Next
    Dim ub As Long: ub = UBound(v)
    IsArrayValid = (Err.Number = 0)
    Err.Clear
End Function
```

## 5. Err.Raise 常见拼写错误

```vba
' ❌ 历史高频错误：XxxErr.Raise（多了前缀）
StatsErr.Raise vbObjectError + 1, "StatsUtils", "msg"

' ✅ 正确
Err.Raise vbObjectError + 1, "StatsUtils", "msg"
```

## 6. 字符串与编码

```vba
' ❌ ChrW 中文字符在跨版本 Excel 中可能乱码
' ✅ 使用 ASCII 安全的分隔符，或 ChrW(&H4E2D) 显式 Unicode
```

## 7. COM 调用注意事项

- `Application.Run` 传参限制 30 个
- Range 对象跨线程访问 → 必须 `Application.OnTime` 或 `QueueAsMacro`
- 长时间 UDF 中禁止 `DoEvents`（重入风险）

## 8. 模块依赖顺序

```
VBA-Core: VariantKit → ArrayOps → DictProxy（导入时按此顺序）
RegressUtils 依赖 LinearUtils + StatsUtils（需先加载）
其余模块相互独立
```

## 8.5 模块常量集中声明（历史高频错误）

```vba
' ❌ 引用未定义常量（如 ERR_SINGULAR 未在模块声明）→ 过程级编译失败
' ✅ 所有错误码常量集中声明于模块顶部
```

> Err.Raise 拼写错误（`XxxErr.Raise`）见第 5 节，不在此重复。

## 9. 提交前必检

- [ ] 所有 Public UDF 参数为 `As Variant`
- [ ] 错误处理使用正确模式（CVErr / Err.Raise / Cleanup）
- [ ] 数组操作使用 LBound/UBound，不假设 1-based
- [ ] 无裸 `On Error Resume Next` 不检查 Err
- [ ] 新增函数已同步 API 文档 + 用户手册 + 交叉验证
