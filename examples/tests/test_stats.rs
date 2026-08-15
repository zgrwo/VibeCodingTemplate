// ============================================================================
// test_stats.rs — StatsCore 集成测试（Rust 示例）
// 对应模板：templates/NewModule/{Name}Core.rs.template（#[cfg(test)] 内联测试）
// 运行：cd examples && cargo test
// ============================================================================

use examples::stats::{mean, weighted_mean};

#[test]
fn test_mean() {
    let cases: [(&str, &[f64], f64, bool); 10] = [
        ("normal positive", &[1.0, 2.0, 3.0, 4.0, 5.0], 3.0, false),
        ("normal negative", &[-1.0, -2.0, -3.0], -2.0, false),
        ("mixed signs", &[-1.0, 1.0], 0.0, false),
        ("all zeros is valid", &[0.0, 0.0, 0.0], 0.0, false),
        ("single element", &[42.0], 42.0, false),
        ("empty returns NaN", &[], 0.0, true),
        ("NaN elements filtered", &[1.0, f64::NAN, 3.0], 2.0, false),
        ("Inf elements filtered", &[1.0, f64::INFINITY, 3.0], 2.0, false),
        ("all invalid returns NaN", &[f64::NAN, f64::INFINITY], 0.0, true),
        ("overflow returns NaN", &[1e308, 1e308], 0.0, true),
    ];
    for (name, input, want, want_nan) in cases {
        let got = mean(input);
        if want_nan {
            assert!(got.is_nan(), "{name}: mean() = {got}, want NaN");
        } else {
            assert_eq!(got, want, "{name}");
        }
    }
}

#[test]
fn test_weighted_mean() {
    let cases: [(&str, &[f64], &[f64], f64, bool); 6] = [
        ("equal weights", &[1.0, 2.0, 3.0], &[1.0, 1.0, 1.0], 2.0, false),
        ("weighted", &[1.0, 2.0, 3.0], &[0.0, 0.0, 1.0], 3.0, false),
        ("empty values", &[], &[1.0, 2.0], 0.0, true),
        ("empty weights", &[1.0, 2.0], &[], 0.0, true),
        ("length mismatch", &[1.0, 2.0], &[1.0], 0.0, true),
        ("zero total weight", &[1.0, 2.0], &[0.0, 0.0], 0.0, true),
    ];
    for (name, values, weights, want, want_nan) in cases {
        let got = weighted_mean(values, weights);
        if want_nan {
            assert!(got.is_nan(), "{name}: weighted_mean() = {got}, want NaN");
        } else {
            assert_eq!(got, want, "{name}");
        }
    }
}
