import { formatPercent } from "@/lib/format";

export function ProbabilityBar({
  value,
  label,
  showLabel = true,
}: {
  value: number;
  label?: string;
  showLabel?: boolean;
}) {
  const safeValue = Math.max(0, Math.min(1, value));

  return (
    <div className="min-w-0">
      {showLabel ? (
        <div className="mb-1 flex items-center justify-between gap-3 text-xs">
          <span className="truncate text-zinc-400">{label ?? "Probability"}</span>
          <span className="font-semibold text-zinc-100">
            {formatPercent(safeValue)}
          </span>
        </div>
      ) : null}
      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-300 to-cyan-300"
          style={{ width: `${safeValue * 100}%` }}
        />
      </div>
    </div>
  );
}
