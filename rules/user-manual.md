# 用户手册

> 面向最终用户的操作指南。每个函数/功能提供：场景说明 → 语法 → 参数 → 示例 → 结果解读。

## 手册数值声称值（CLAIM 标记）

> 手册中的**关键数值**（effect size、阈值、均值等）用 CLAIM 标记圈定，由
> `scripts/verify-manual.py` 的 `manual_check()` 实跑代码比对，防文档数字漂移
> （数值 SSOT 在本文档，CrossVal 脚本不硬编码）。语法：

```html
<!-- CLAIM:MEAN_DIFF -->0.42<!-- /CLAIM:MEAN_DIFF -->
```

- 标记名 `CLAIM:NAME` 须为大写 token（`[A-Z0-9_]+`），与 `manual_check("MEAN_DIFF", actual)` 的名称一一对应
- 标记值为十进制数（含小数/指数）；标记须成对闭合
- CrossVal 脚本用法：`from verify_manual import manual_check` →
  `manual_check("MEAN_DIFF", 实际值)`，实际值缺失/不匹配时 verify-manual 报 FAIL

## 快速开始

{{QUICK_START_GUIDE}}

---

## 目录

{{TABLE_OF_CONTENTS}}

---

## {{MODULE_1}}

### {{FUNCTION_NAME}}

**场景**：{{WHEN_TO_USE}}

**语法**：
```text
{{SYNTAX}}
```

**参数说明**：

| 参数 | 说明 | 示例值 |
|------|------|--------|
| `{{PARAM_1}}` | {{PARAM_DESC_1}} | {{PARAM_EXAMPLE_1}} |

**示例**：

输入数据：
```text
{{INPUT_DATA}}
```

公式：
```text
{{FORMULA}}
```

输出结果：
```text
{{OUTPUT_RESULT}}
```

**结果解读**：

{{INTERPRETATION_GUIDE}}

**注意事项**：
- {{CAVEAT_1}}
- {{CAVEAT_2}}

---

## 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| {{FAQ_Q1}} | {{FAQ_CAUSE1}} | {{FAQ_FIX1}} |

---

## 故障排查

{{TROUBLESHOOTING_GUIDE}}
