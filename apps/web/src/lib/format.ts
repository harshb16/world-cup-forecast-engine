export function formatPercent(value: number, maximumFractionDigits = 1): string {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits,
  }).format(value);
}

export function formatDeltaPercent(value: number): string {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${formatPercent(value)}`;
}

export function formatNumber(value: number, maximumFractionDigits = 0): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits,
  }).format(value);
}

export function formatModelLabel(modelType: string): string {
  if (modelType === "oracle_v3") {
    return "Forecast v3";
  }
  if (modelType === "oracle_v2") {
    return "Forecast v2";
  }
  if (modelType === "calibrated_elo") {
    return "Calibrated Elo";
  }
  return modelType.toUpperCase();
}
