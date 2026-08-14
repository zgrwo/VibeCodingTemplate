// ============================================================================
// mod.rs — 统计均值计算核心层（Rust 示例）
// 对应模板：templates/NewModule/{Name}Core.rs.template
// 设计原则（见 skills/rust-SKILL.md）：
//   - 哨兵值 NaN：0 是有效值，用 NaN 表示"无效"
//   - 零 panic：无效输入返回 NaN，不 panic
// ============================================================================

/// Mean 计算算术均值。空切片/全无效返回 NaN。
///
/// 与 Go/Python/TypeScript 实现对齐：逐元素过滤 NaN/Inf，分母为有效值计数。
pub fn mean(values: &[f64]) -> f64 {
    if values.is_empty() {
        return f64::NAN;
    }
    let mut sum = 0.0;
    let mut count = 0usize;
    for &v in values {
        if v.is_nan() || v.is_infinite() {
            continue;
        }
        sum += v;
        count += 1;
    }
    if count == 0 {
        return f64::NAN;
    }
    let result = sum / count as f64;
    if result.is_infinite() || result.is_nan() {
        return f64::NAN;
    }
    result
}

/// WeightedMean 计算加权均值。空/长度不匹配/权重全零返回 NaN。
///
/// 与 Mean 对齐：逐对过滤非有限（NaN/Inf）值及其配对权重，否则 NaN 会毒化整个结果。
pub fn weighted_mean(values: &[f64], weights: &[f64]) -> f64 {
    if values.is_empty() || weights.is_empty() || values.len() != weights.len() {
        return f64::NAN;
    }
    let mut total_weight = 0.0;
    let mut sum = 0.0;
    for (&v, &w) in values.iter().zip(weights.iter()) {
        if v.is_nan() || v.is_infinite() || w.is_nan() || w.is_infinite() {
            continue;
        }
        total_weight += w;
        sum += v * w;
    }
    if total_weight == 0.0 {
        return f64::NAN;
    }
    let result = sum / total_weight;
    if result.is_infinite() || result.is_nan() {
        return f64::NAN;
    }
    result
}
