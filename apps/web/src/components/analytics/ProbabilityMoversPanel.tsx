"use client";

import { TrendingDown, TrendingUp } from "lucide-react";

import { SectionCard } from "@/components/ui/SectionCard";
import { ProbabilityMovers } from "@/lib/api";
import { formatPercent } from "@/lib/format";

type ProbabilityMoversPanelProps = {
  movers: ProbabilityMovers;
};

export function ProbabilityMoversPanel({ movers }: ProbabilityMoversPanelProps) {
  if (movers.risers.length === 0 && movers.fallers.length === 0) {
    return (
      <SectionCard>
        <p className="text-xs font-semibold uppercase text-primary">
          What changed
        </p>
        <h2 className="mt-1 text-lg font-semibold text-foreground">
          Probability movers
        </h2>
        <p className="mt-3 text-sm text-muted-foreground">
          Sync at least twice to compare champion probability shifts between
          snapshots.
        </p>
      </SectionCard>
    );
  }

  return (
    <SectionCard>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-primary">
            What changed
          </p>
          <h2 className="mt-1 text-lg font-semibold text-foreground">
            Champion probability movers
          </h2>
        </div>
        {movers.previous_timestamp && movers.current_timestamp ? (
          <p className="text-xs text-muted-foreground">
            {movers.previous_timestamp.slice(0, 10)} →{" "}
            {movers.current_timestamp.slice(0, 10)}
          </p>
        ) : null}
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <MoverColumn
          title="Risers"
          icon={TrendingUp}
          tone="green"
          items={movers.risers}
        />
        <MoverColumn
          title="Fallers"
          icon={TrendingDown}
          tone="red"
          items={movers.fallers}
        />
      </div>
    </SectionCard>
  );
}

function MoverColumn({
  title,
  icon: Icon,
  tone,
  items,
}: {
  title: string;
  icon: typeof TrendingUp;
  tone: "green" | "red";
  items: ProbabilityMovers["risers"];
}) {
  const toneClass =
    tone === "green" ? "text-primary" : "text-destructive";
  const badgeClass =
    tone === "green"
      ? "border-emerald-400/30 bg-emerald-400/10 text-primary"
      : "border-red-400/30 bg-red-400/10 text-red-200";

  return (
    <div className="rounded-lg border border-border bg-black/15 p-4">
      <div className="flex items-center gap-2">
        <Icon size={16} className={toneClass} aria-hidden="true" />
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      </div>
      <ul className="mt-4 space-y-3">
        {items.length === 0 ? (
          <li className="text-sm text-muted-foreground">No movers in this bucket.</li>
        ) : (
          items.map((item) => (
            <li
              key={item.team_id}
              className="flex items-center justify-between gap-3"
            >
              <div>
                <p className="text-sm font-semibold text-foreground">
                  {item.team_name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatPercent(item.previous_probability)} →{" "}
                  {formatPercent(item.current_probability)}
                </p>
              </div>
              <span
                className={`rounded-md border px-2 py-1 text-xs font-semibold ${badgeClass}`}
              >
                {item.delta >= 0 ? "+" : ""}
                {formatPercent(item.delta)}
              </span>
            </li>
          ))
        )}
      </ul>
    </div>
  );
}
