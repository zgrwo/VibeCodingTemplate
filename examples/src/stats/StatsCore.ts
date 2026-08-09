// ============================================================================
// StatsCore.ts — 统计均值计算核心层（TypeScript 示例）
//
// 对应模板：templates/NewModule/{Name}Core.ts.template
// 设计原则（见 skills/typescript-SKILL.md）：
//   - strict null check：null/undefined 显式守卫
//   - 哨兵契约：无效输入返回 NaN，不抛异常
//   - 零外部依赖：纯函数实现，可独立单元测试
// ============================================================================

/** 计算结果：成功返回值，失败返回 NaN（哨兵契约） */
type ComputeResult = number;

/**
 * 计算算术均值。
 *
 * @param values - 数值数组；null/undefined 或空数组返回 NaN
 * @returns 均值；无效输入返回 NaN
 */
export function mean(values: number[] | null | undefined): ComputeResult {
  if (values === null || values === undefined) {
    return NaN;
  }
  if (values.length === 0) {
    return NaN;
  }
  const clean = values.filter((v) => typeof v === "number" && Number.isFinite(v));
  if (clean.length === 0) {
    return NaN;
  }
  const result = clean.reduce((sum, v) => sum + v, 0) / clean.length;
  if (!Number.isFinite(result)) {
    return NaN;
  }
  return result;
}

/**
 * 计算加权均值。
 */
export function weightedMean(
  values: number[] | null | undefined,
  weights: number[] | null | undefined,
): ComputeResult {
  if (values === null || values === undefined || weights === null || weights === undefined) {
    return NaN;
  }
  if (values.length === 0 || weights.length === 0 || values.length !== weights.length) {
    return NaN;
  }
  const totalWeight = weights.reduce((sum, w) => sum + w, 0);
  if (totalWeight === 0) return NaN;
  const result = values.reduce((sum, v, i) => sum + v * weights[i], 0) / totalWeight;
  if (!Number.isFinite(result)) return NaN;
  return result;
}
