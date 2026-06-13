import { formatPercent } from "@/lib/api";

export function ProbabilityBar({
  value,
  tone = "emerald",
}: {
  value: number;
  tone?: "emerald" | "amber" | "rose";
}) {
  const barClass = {
    emerald: "bg-emerald-600",
    amber: "bg-amber-500",
    rose: "bg-rose-500",
  }[tone];

  return (
    <div className="flex min-w-36 items-center gap-3">
      <div className="h-2 flex-1 rounded-full bg-zinc-100">
        <div
          className={`h-full rounded-full ${barClass}`}
          style={{ width: `${Math.max(0, Math.min(value, 1)) * 100}%` }}
        />
      </div>
      <span className="w-12 text-right text-xs font-semibold text-zinc-700">
        {formatPercent(value)}
      </span>
    </div>
  );
}
