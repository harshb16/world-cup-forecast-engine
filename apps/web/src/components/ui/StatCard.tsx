import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  detail,
  tone = "default",
}: {
  label: string;
  value: string;
  detail?: string;
  tone?: "default" | "green" | "amber" | "red";
}) {
  const toneClass = {
    default: "text-foreground",
    green: "text-primary",
    amber: "text-signal-amber",
    red: "text-destructive-foreground",
  }[tone];

  return (
    <div className="rounded-lg border border-border bg-card/80 p-4">
      <p className="font-mono text-xs font-medium uppercase tracking-widest text-muted-foreground">
        {label}
      </p>
      <p className={cn("mt-2 text-2xl font-semibold tabular-nums", toneClass)}>
        {value}
      </p>
      {detail ? (
        <p className="mt-1 text-sm text-muted-foreground">{detail}</p>
      ) : null}
    </div>
  );
}
