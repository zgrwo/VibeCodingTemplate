---
description: "TypeScript 编码技能 — 类型陷阱、strict 模式、异步错误处理、模块边界。修改 .ts/.tsx 前必读。"
name: "TypeScript 编码技能"
argument-hint: "[修改的 .ts/.tsx 文件/模块] [--context 新增功能 | 修复缺陷 | 重构]"
---

# TypeScript 编码技能

> 适用于 TypeScript 5.x + Node.js 18+。修改 .ts/.tsx 前必读。

## 1. strict 模式强制

```typescript
// tsconfig.json 必须开启 strict
// "strict": true 包含：noImplicitAny / strictNullChecks / strictFunctionTypes / strictPropertyInitialization

// ❌ 错误：隐式 any
function process(data) { /* ... */ }

// ✅ 正确：显式类型
function process(data: unknown): void { /* ... */ }

// ❌ 错误：忽略 null/undefined
function getName(user: User): string {
  return user.name; // user.name 可能是 null | undefined
}

// ✅ 正确：null 安全
function getName(user: User): string {
  return user.name ?? "Unknown";
}
```

## 2. 类型守卫与收窄

```typescript
// ❌ 错误：类型断言绕过检查
const len = (value as string).length;

// ✅ 正确：类型守卫
function getLength(value: string | string[]): number {
  if (typeof value === "string") {
    return value.length; // 收窄为 string
  }
  return value.length;   // 收窄为 string[]
}

// ✅ 自定义类型谓词
function isUser(obj: unknown): obj is User {
  return typeof obj === "object" && obj !== null && "name" in obj;
}
```

## 3. 异步错误处理

```typescript
// ❌ 错误：未捕获的 Promise rejection
async function fetchUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  return res.json(); // 网络错误/非 200 会 unhandled rejection
}

// ✅ 正确：显式错误边界
async function fetchUser(id: string): Promise<Result<User, AppError>> {
  try {
    const res = await fetch(`/api/users/${id}`);
    if (!res.ok) {
      return err({ kind: "http_error", status: res.status });
    }
    const data = await res.json() as unknown;
    if (!isUser(data)) {
      return err({ kind: "parse_error" });
    }
    return ok(data);
  } catch (e) {
    return err({ kind: "network_error", cause: e });
  }
}

// Result 模式
type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };
const ok = <T>(value: T): Result<T, never> => ({ ok: true, value });
const err = <E>(error: E): Result<never, E> => ({ ok: false, error: error });
```

## 4. 枚举陷阱

```typescript
// ❌ 避免：数字枚举（不安全，可从数字反向映射）
enum Status { Active, Inactive }

// ✅ 推荐：字符串枚举或联合类型
type Status = "active" | "inactive";
// 或
const Status = {
  Active: "active",
  Inactive: "inactive",
} as const;
type Status = typeof Status[keyof typeof Status];
```

## 5. 模块边界与导入

```typescript
// ❌ 错误：跨层导入（UI 直接访问数据层）
import { Database } from "./data/database";

// ✅ 正确：通过 Service 层
import { UserService } from "./services/user-service";

// ❌ 错误： barrel 导入导致 tree-shaking 失效
import { Utils } from "./utils"; // barrel file

// ✅ 正确：按需导入
import { formatDate } from "./utils/date";
```

## 6. Record / Map 选择

```typescript
// 小规模固定键 → Record
type Config = Record<"host" | "port", string>;

// 大规模动态键 → Map（有序遍历、性能更好）
const cache = new Map<string, Data>();

// ❌ 避免用对象做动态键映射（原型链污染风险）
const cache: Record<string, Data> = {};
cache["__proto__"]; // 不安全

// ✅ Map 无原型链问题
cache.get("__proto__"); // 安全
```

## 7. 不可变性与只读

```typescript
// 配置/常量用 as const
const ROLES = ["admin", "user", "guest"] as const;
type Role = typeof ROLES[number]; // "admin" | "user" | "guest"

// 接口暴露只读
interface User {
  readonly id: string;
  name: string;
}

// ❌ 避免直接变异
config.timeout = 5000;

// ✅ 展开/结构更新
const newConfig = { ...config, timeout: 5000 };
```

## 8. 测试约定

```typescript
// 使用 vitest / jest
import { describe, it, expect } from "vitest";

describe("processData", () => {
  it("正常输入返回正确结果", () => {
    expect(processData([1, 2, 3])).toBe(6);
  });

  it("空数组返回 0（有效值）", () => {
    expect(processData([])).toBe(0);
  });

  it("null 输入抛出 TypeError", () => {
    expect(() => processData(null as unknown as number[]))
      .toThrow(TypeError);
  });
});
```

## 9. 提交前必检

- [ ] `npx tsc --noEmit` 零错误
- [ ] `npx vitest run`（或 `npx jest`）全绿
- [ ] 无 `as any` / `as unknown` 滥用（有则附注释说明原因）
- [ ] 无 `@ts-ignore` / `@ts-expect-error` 未配说明
- [ ] 新增 Public 接口已同步 api-reference.md
- [ ] 异步函数有错误边界（try/catch 或 Result 模式）
- [ ] 无跨层导入（UI → Data 直连）
