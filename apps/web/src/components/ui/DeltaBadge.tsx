import { formatDeltaPercent } from "@/lib/format";

export function DeltaBadge({ value }: { value: number }) {
  const className =
    value > 0
      ? "border-primary/25 bg-primary/10 text-primary"
      : value < 0
        ? "border-rose-300/25 bg-rose-300/10 text-rose-200"
        : "border-border bg-muted/50 text-muted-foreground";

  return (
    <span
      className={`inline-flex rounded-md border px-2 py-1 text-xs font-semibold ${className}`}
    >
      {formatDeltaPercent(value)}
    </span>
  );
}
