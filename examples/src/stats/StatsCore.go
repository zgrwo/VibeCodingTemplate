// ============================================================================
// StatsCore.go — 统计均值计算核心层（Go 示例）
// 对应模板：templates/NewModule/{Name}Core.go.template
// 设计原则（见 skills/go-SKILL.md）：
//   - 哨兵值 NaN：0 是有效值，用 NaN 表示"无效"
//   - 零 panic：无效输入返回 NaN，不抛异常
// ============================================================================
package stats

import "math"

// Mean 计算算术均值。nil/空切片返回 NaN。
func Mean(values []float64) float64 {
	if values == nil || len(values) == 0 {
		return math.NaN()
	}
	sum, count := 0.0, 0
	for _, v := range values {
		if math.IsNaN(v) || math.IsInf(v, 0) {
			continue
		}
		sum += v
		count++
	}
	if count == 0 {
		return math.NaN()
	}
	result := sum / float64(count)
	if math.IsInf(result, 0) || math.IsNaN(result) {
		return math.NaN()
	}
	return result
}

// WeightedMean 计算加权均值。nil/空/长度不匹配/权重全零返回 NaN。
func WeightedMean(values, weights []float64) float64 {
	if values == nil || weights == nil ||
		len(values) == 0 || len(weights) == 0 ||
		len(values) != len(weights) {
		return math.NaN()
	}
	totalWeight := 0.0
	for _, w := range weights {
		totalWeight += w
	}
	if totalWeight == 0 {
		return math.NaN()
	}
	sum := 0.0
	for i, v := range values {
		sum += v * weights[i]
	}
	result := sum / totalWeight
	if math.IsInf(result, 0) || math.IsNaN(result) {
		return math.NaN()
	}
	return result
}
