"""test_stats.py — StatsCore 单元测试

覆盖路径：
  - 正常输入（正数/负数/混合）
  - 边界（空列表/单元素/全零）
  - Falsy 守卫（None → NaN，0 是有效值）
  - 异常输入（NaN/Inf 元素被过滤）
"""
import math

from src.stats.StatsCore import mean, weighted_mean


class TestMean:
    def test_normal_positive(self):
        assert mean([1.0, 2.0, 3.0, 4.0, 5.0]) == 3.0

    def test_normal_negative(self):
        assert mean([-1.0, -2.0, -3.0]) == -2.0

    def test_mixed_signs(self):
        assert mean([-1.0, 1.0]) == 0.0

    def test_all_zero_is_valid(self):
        """0 是有效值，均值=0 表示数据全零"""
        assert mean([0.0, 0.0, 0.0]) == 0.0

    def test_single_element(self):
        assert mean([42.0]) == 42.0

    def test_none_returns_nan(self):
        """None → NaN（哨兵契约）"""
        assert math.isnan(mean(None))

    def test_empty_returns_nan(self):
        """空列表 → NaN（哨兵契约）"""
        assert math.isnan(mean([]))

    def test_nan_elements_filtered(self):
        """NaN 元素被静默过滤"""
        assert mean([1.0, float("nan"), 3.0]) == 2.0

    def test_inf_elements_filtered(self):
        """Inf 元素被静默过滤"""
        assert mean([1.0, float("inf"), 3.0]) == 2.0

    def test_all_invalid_returns_nan(self):
        """全部无效 → NaN"""
        assert math.isnan(mean([float("nan"), float("inf")]))

    def test_overflow_returns_nan(self):
        """极大值求和溢出 → NaN（结果守卫，防 sum→inf 污染，2026-08 Max 审查补测）"""
        assert math.isnan(mean([1e308, 1e308]))


class TestWeightedMean:
    def test_normal(self):
        assert weighted_mean([1.0, 2.0, 3.0], [1.0, 1.0, 1.0]) == 2.0

    def test_weighted(self):
        assert weighted_mean([1.0, 2.0, 3.0], [0.0, 0.0, 1.0]) == 3.0

    def test_none_values(self):
        assert math.isnan(weighted_mean(None, [1.0, 2.0]))

    def test_none_weights(self):
        assert math.isnan(weighted_mean([1.0, 2.0], None))

    def test_length_mismatch(self):
        assert math.isnan(weighted_mean([1.0, 2.0], [1.0]))

    def test_zero_total_weight(self):
        """权重全零 → NaN"""
        assert math.isnan(weighted_mean([1.0, 2.0], [0.0, 0.0]))
