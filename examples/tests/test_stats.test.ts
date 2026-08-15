// ============================================================================
// test_stats.test.ts — StatsCore 单元测试（TypeScript 示例）
// 对应模板：templates/NewModule/{Name}Core.test.ts.template
// 运行：npx vitest run examples/tests/
// 注意：文件名后缀 .test.ts 为 vitest/Jest 默认 glob（**/*.{test,spec}.*）要求
// ============================================================================
import { describe, it, expect } from "vitest";
import { mean, weightedMean } from "../src/stats/StatsCore";

describe("mean", () => {
  it("normal positive", () => expect(mean([1, 2, 3, 4, 5])).toBe(3));
  it("negative", () => expect(mean([-1, -2, -3])).toBe(-2));
  it("mixed signs", () => expect(mean([-1, 1])).toBe(0));
  it("all zeros is valid (0 is valid value)", () => expect(mean([0, 0, 0])).toBe(0));
  it("single element", () => expect(mean([42])).toBe(42));
  it("null returns NaN", () => expect(Number.isNaN(mean(null))).toBe(true));
  it("undefined returns NaN", () => expect(Number.isNaN(mean(undefined))).toBe(true));
  it("empty returns NaN", () => expect(Number.isNaN(mean([]))).toBe(true));
  it("NaN elements filtered", () => expect(mean([1, NaN, 3])).toBe(2));
  it("Infinity elements filtered", () => expect(mean([1, Infinity, 3])).toBe(2));
  it("all invalid returns NaN", () => expect(Number.isNaN(mean([NaN, Infinity]))).toBe(true));
  it("overflow returns NaN", () => expect(Number.isNaN(mean([1e308, 1e308]))).toBe(true));
});

describe("weightedMean", () => {
  it("equal weights", () => expect(weightedMean([1, 2, 3], [1, 1, 1])).toBe(2));
  it("weighted", () => expect(weightedMean([1, 2, 3], [0, 0, 1])).toBe(3));
  it("null values", () => expect(Number.isNaN(weightedMean(null, [1, 2]))).toBe(true));
  it("null weights", () => expect(Number.isNaN(weightedMean([1, 2], null))).toBe(true));
  it("length mismatch", () => expect(Number.isNaN(weightedMean([1, 2], [1]))).toBe(true));
  it("zero total weight", () => expect(Number.isNaN(weightedMean([1, 2], [0, 0]))).toBe(true));
});
