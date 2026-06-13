import { formatDeltaPercent } from "@/lib/format";

export function DeltaBadge({ value }: { value: number }) {
  const className =
    value > 0
      ? "border-emerald-300/25 bg-emerald-300/10 text-emerald-200"
      : value < 0
        ? "border-rose-300/25 bg-rose-300/10 text-rose-200"
        : "border-white/10 bg-white/10 text-zinc-300";

  return (
    <span
      className={`inline-flex rounded-md border px-2 py-1 text-xs font-semibold ${className}`}
    >
      {formatDeltaPercent(value)}
    </span>
  );
}
