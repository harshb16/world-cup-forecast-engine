import { formatPercent } from "@/lib/api";

export function DeltaBadge({ value }: { value: number }) {
  const isPositive = value > 0;
  const isNegative = value < 0;
  const className = isPositive
    ? "bg-emerald-50 text-emerald-700"
    : isNegative
      ? "bg-rose-50 text-rose-700"
      : "bg-zinc-100 text-zinc-600";
  const prefix = isPositive ? "+" : "";

  return (
    <span className={`rounded-md px-2 py-1 text-xs font-semibold ${className}`}>
      {prefix}
      {formatPercent(value)}
    </span>
  );
}
