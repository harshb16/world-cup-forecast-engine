import { formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

export function ProbabilityBar({
  value,
  label,
  showLabel = true,
  interactive = false,
}: {
  value: number;
  label?: string;
  showLabel?: boolean;
  interactive?: boolean;
}) {
  const safeValue = Math.max(0, Math.min(1, value));

  return (
    <div className="min-w-0">
      {showLabel ? (
        <div className="mb-1 flex items-center justify-between gap-3 text-xs">
          <span className="truncate text-muted-foreground">
            {label ?? "Probability"}
          </span>
          <span className="font-semibold tabular-nums text-foreground">
            {formatPercent(safeValue)}
          </span>
        </div>
      ) : null}
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          data-fill
          className={cn(
            "h-full rounded-full bg-primary transition-[width] duration-300",
            interactive && "hover:shadow-[0_0_12px_color-mix(in_oklch,var(--primary)_40%,transparent)]",
          )}
          style={{ width: `${safeValue * 100}%` }}
        />
      </div>
    </div>
  );
}
