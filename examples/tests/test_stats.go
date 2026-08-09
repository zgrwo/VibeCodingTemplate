// ============================================================================
// test_stats.go — StatsCore 单元测试（Go 示例）
// 对应模板：templates/NewModule/{Name}Core_test.go.template
// 运行：cd examples && go test ./tests/... -v
// ============================================================================
package tests

import (
	"math"
	"testing"

	"examples/src/stats"
)

func TestMean(t *testing.T) {
	tests := []struct {
		name  string
		input []float64
		want  float64
		isNaN bool
	}{
		{"normal positive", []float64{1, 2, 3, 4, 5}, 3.0, false},
		{"normal negative", []float64{-1, -2, -3}, -2.0, false},
		{"mixed signs", []float64{-1, 1}, 0.0, false},
		{"all zeros is valid", []float64{0, 0, 0}, 0.0, false},
		{"single element", []float64{42}, 42.0, false},
		{"nil returns NaN", nil, 0, true},
		{"empty returns NaN", []float64{}, 0, true},
		{"NaN elements filtered", []float64{1, math.NaN(), 3}, 2.0, false},
		{"Inf elements filtered", []float64{1, math.Inf(1), 3}, 2.0, false},
		{"all invalid returns NaN", []float64{math.NaN(), math.Inf(1)}, 0, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := stats.Mean(tt.input)
			if tt.isNaN {
				if !math.IsNaN(got) {
					t.Errorf("Mean() = %v, want NaN", got)
				}
			} else if got != tt.want {
				t.Errorf("Mean() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestWeightedMean(t *testing.T) {
	tests := []struct {
		name    string
		values  []float64
		weights []float64
		want    float64
		isNaN   bool
	}{
		{"equal weights", []float64{1, 2, 3}, []float64{1, 1, 1}, 2.0, false},
		{"weighted", []float64{1, 2, 3}, []float64{0, 0, 1}, 3.0, false},
		{"nil values", nil, []float64{1, 2}, 0, true},
		{"nil weights", []float64{1, 2}, nil, 0, true},
		{"length mismatch", []float64{1, 2}, []float64{1}, 0, true},
		{"zero total weight", []float64{1, 2}, []float64{0, 0}, 0, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := stats.WeightedMean(tt.values, tt.weights)
			if tt.isNaN {
				if !math.IsNaN(got) {
					t.Errorf("WeightedMean() = %v, want NaN", got)
				}
			} else if got != tt.want {
				t.Errorf("WeightedMean() = %v, want %v", got, tt.want)
			}
		})
	}
}
