/** Chart line colors aligned with globals.css broadcast cobalt tokens */
export const CHART_LINE_COLORS = [
  "oklch(0.74 0.13 250)",
  "oklch(0.68 0.11 285)",
  "oklch(0.78 0.14 72)",
  "oklch(0.65 0.18 28)",
  "oklch(0.7 0.1 200)",
  "oklch(0.64 0.09 158)",
  "oklch(0.72 0.11 220)",
  "oklch(0.76 0.12 45)",
] as const;

export const CHART_TOOLTIP_STYLE = {
  background: "oklch(0.18 0.044 258)",
  border: "1px solid oklch(0.33 0.048 258 / 0.8)",
  borderRadius: "0.5rem",
  color: "oklch(0.93 0.012 95)",
} as const;
