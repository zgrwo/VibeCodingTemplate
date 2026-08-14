---
description: "Rust 编码技能 — 所有权/借用、Option/Result、panic 陷阱、哨兵契约、unsafe 边界。修改 .rs 前必读。"
name: "Rust 编码技能"
argument-hint: "[修改的 .rs 文件/模块] [--context 新增功能 | 修复缺陷 | 重构]"
---

# Rust 编码技能

> 适用于 Rust edition 2021+（stable）。修改 .rs 前必读。

## 1. 所有权与借用（最高频错误）

Rust 用所有权模型在编译期保证内存安全。**先想借用，再想 clone**。

```rust
// ❌ 错误：move 后再使用
let s = String::from("hello");
let t = s;            // s 被 move
println!("{}", s);    // 编译错误：s 已失效

// ✅ 正确：借用（borrow）
let s = String::from("hello");
let t = &s;           // 不可变借用
println!("{}", s);    // OK

// ❌ 错误：可变借用与不可变借用同时存在
let mut v = vec![1, 2, 3];
let a = &v[0];        // 不可变借用
v.push(4);            // 可变借用 → 编译错误（a 仍在作用域）

// ✅ 正确：缩小借用作用域
let mut v = vec![1, 2, 3];
{
    let a = &v[0];
    println!("{}", a);
}
v.push(4);            // OK
```

### 借用决策树（何时借用 / 所有权 / clone）

| 场景 | 选择 | 理由 |
|------|------|------|
| 函数只读访问参数 | `&T`（借用） | 零拷贝，调用方仍拥有值 |
| 函数需修改参数 | `&mut T` | 唯一可变借用 |
| 函数需持有返回值 | 返回 `T`（move） | 转移所有权给调用方 |
| 值仅用一次且无借用冲突 | `T`（move） | 最简单 |
| 借用检查器报错，非性能热点 | 局部 `clone()` | 优先正确，再优化 |

> 规则：默认 `&T`；只有确认需转移所有权时才用 `T`；`clone()` 是最后手段而非首选。

## 2. Option / Result 处理（unwrap 陷阱）

```rust
// ❌ 错误：unwrap/expect 会 panic
let x = map.get("key").unwrap();     // 键不存在 → panic
let y: u32 = "abc".parse().unwrap(); // 解析失败 → panic

// ✅ 正确：用 match / ? / unwrap_or
let x = map.get("key").copied().unwrap_or(0);   // 缺省值
let x = match map.get("key") {
    Some(&v) => v,
    None => return f64::NAN,   // 哨兵：无效 → NaN
};

// ✅ 正确：? 传播错误（仅限返回 Result 的函数）
fn parse(s: &str) -> Result<u32, std::num::ParseIntError> {
    let n = s.parse::<u32>()?;   // 失败自动向上返回 Err
    Ok(n * 2)
}
```

### 决策：用 Option 还是 Result？

| 场景 | 返回类型 |
|------|----------|
| 值可能不存在（无错误原因） | `Option<T>` |
| 操作可能失败（有错误原因） | `Result<T, E>` |
| 数值计算"无效"（0 是有效值） | `f64::NAN` 哨兵（见 §4） |

> **`unwrap`/`expect` 只在证明不可能失败时用**（如刚 `contains_key` 检查后），否则用 `match`/`?`/`unwrap_or`。库代码禁止用 `unwrap` 处理可能失败的用户输入。

## 3. panic 陷阱

```rust
// ❌ 错误：切片索引越界 panic
let v = vec![1, 2, 3];
let x = v[10];   // panic: index out of bounds

// ✅ 正确：get 返回 Option
let x = v.get(10).copied().unwrap_or(0);

// ❌ 错误：库边界不守卫，让非法状态泄漏
pub fn div(a: f64, b: f64) -> f64 {
    a / b   // 除零 → inf，语义未守卫
}

// ✅ 正确：库边界用哨兵/Result，不用 panic
pub fn div(a: f64, b: f64) -> f64 {
    if b == 0.0 { return f64::NAN; }
    a / b
}
```

> **规则**：库（library）代码不 panic；`panic!` 只用于不可恢复的编程错误（如内部不变量破坏）。业务边界用 `Result`/哨兵。

## 4. 哨兵契约（NaN 表示无效）

> 术语统一：SSOT 定义为「哨兵契约」（见 [rules/sentinel-contract.md](../rules/sentinel-contract.md)，L1-L5 各语言落地映射）。与 Go/Python 对齐：**0 是有效值，NaN 表示无效**。

```rust
/// Mean 计算算术均值。空切片/全无效返回 NaN。
pub fn mean(values: &[f64]) -> f64 {
    if values.is_empty() {
        return f64::NAN;   // 哨兵：空输入 → NaN
    }
    let (sum, count) = values.iter().fold((0.0, 0usize), |(s, c), &v| {
        if v.is_nan() || v.is_infinite() {
            (s, c)            // 静默过滤无效值
        } else {
            (s + v, c + 1)    // 分母是有效值计数，不是 len
        }
    });
    if count == 0 {
        return f64::NAN;      // 全部无效 → NaN
    }
    sum / count as f64
}

// ❌ 错误：用 Option<f64> 表示"计算结果为 0"
// pub fn mean(values: &[f64]) -> Option<f64> {
//     let r = ...;
//     if r == 0.0 { return None; }   // 0 是有效值！
//     Some(r)
// }
```

> **NaN 守卫清单**：输入 NaN/Inf → NaN；空集合 → NaN；全无效 → NaN；结果 Inf/NaN → NaN。0 恒为有效值。

## 5. 集合与切片陷阱

```rust
// ❌ 错误：迭代中修改 Vec（不可变借用与可变借用冲突）
let mut v = vec![1, 2, 3];
for &x in &v {
    v.push(x * 2);   // 编译错误
}

// ✅ 正确：先 collect 再修改
let doubled: Vec<i32> = v.iter().map(|&x| x * 2).collect();
v.extend(doubled);

// ✅ 正确：iterator 优先于手动索引循环
let sum: i32 = v.iter().sum();
```

## 6. unsafe 边界

```rust
// ❌ 错误：无必要地使用 unsafe（绕过借用检查，易 UB）
unsafe { *ptr }

// ✅ 正确：unsafe 最小化 + 封装在安全 API 后
// 仅在与 C 库交互（FFI）/ 性能热点确需绕过借用检查时才用，
// 必须：① 最小作用域；② 封装在 safe 函数后；③ SAFETY 注释说明不变式；
//      ④ cargo miri / sanitizer 验证。
```

> **规则**：默认不用 `unsafe`。确需时遵守「最小作用域 + SAFETY 注释 + 安全封装」三原则。

## 7. 测试约定

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compute() {
        // table-driven（Rust 惯例：Vec<(name, input, want)>）
        let cases = [
            ("normal positive", 5.0, 10.0, false),
            ("zero is valid", 0.0, 0.0, false),   // 0 是有效值
            ("NaN returns NaN", f64::NAN, f64::NAN, true),
        ];
        for (name, input, want, want_nan) in cases {
            let got = compute(input);
            if want_nan {
                assert!(got.is_nan(), "{name}: got {got}, want NaN");
            } else {
                assert_eq!(got, want, "{name}");
            }
        }
    }
}
```

> **浮点断言**：精确值（0.0、整数倍）可用 `assert_eq!`；非精确浮点用 `approx` crate 的 `assert_relative_eq!`。
> **属性测试**（proptest，可选）：对"任意输入都不 panic 且 NaN/Inf 守卫成立"这类性质用 `proptest!` 生成随机输入验证，比手写边界用例更全面。

## 8. 提交前必检

- [ ] `cargo fmt --check` 零差异
- [ ] `cargo clippy -- -D warnings` 零警告
- [ ] `cargo test` 全绿
- [ ] 无 `unwrap`/`expect`（有则附注释说明不可能失败）
- [ ] 无 `unsafe`（有则 SAFETY 注释 + 最小作用域）
- [ ] 数值函数遵循哨兵契约（0 有效值，NaN 无效）
- [ ] 库代码无 panic
- [ ] 新增 Public 接口已同步 api-reference.md
