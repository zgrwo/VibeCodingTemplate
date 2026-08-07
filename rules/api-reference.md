# API 参考

> 本文件是所有 Public 函数签名的**唯一信源**。代码中的签名必须与此处一致。

## 模块概览

| 模块 | 函数数 | 说明 |
|------|--------|------|
| `{{MODULE_1}}` | {{COUNT_1}} | {{DESC_1}} |
| `{{MODULE_2}}` | {{COUNT_2}} | {{DESC_2}} |
| **总计** | **{{TOTAL}}** | |

---

## {{MODULE_1}}

### `{{FUNCTION_NAME}}`

```
{{FUNCTION_SIGNATURE}}
```

| 参数 | 类型 | 必选 | 默认值 | 说明 |
|------|------|------|--------|------|
| `{{PARAM_1}}` | {{TYPE_1}} | ✅ | — | {{PARAM_DESC_1}} |
| `{{PARAM_2}}` | {{TYPE_2}} | ❌ | {{DEFAULT_2}} | {{PARAM_DESC_2}} |

**返回值**：{{RETURN_TYPE}} — {{RETURN_DESC}}

**错误行为**：

| 条件 | 返回 |
|------|------|
| {{ERROR_CONDITION_1}} | `{{ERROR_VALUE_1}}` |
| 所有输入被过滤 | `{{EMPTY_ERROR}}` |

**示例与结果解读**：见 [user-manual.md](user-manual.md)（本文件只维护签名，不重复示例）。

---

## 错误参考

> 错误值由各模块实现定义（不同模块错误语义可能不同），以实际实现为准，**不在本文件硬编码**。

| 错误值 | 含义（示例） | 用户可修正 |
|--------|--------------|-----------|
| `{{ERROR_VALUE_1}}` | {{ERROR_MEANING_1}} | {{ERROR_FIXABLE_1}} |

---

## 调用约定

{{CALLING_CONVENTION_NOTES}}
