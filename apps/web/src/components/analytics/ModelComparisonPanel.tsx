import { SectionCard } from "@/components/ui/SectionCard";
import { DeltaBadge } from "@/components/ui/DeltaBadge";
import { ModelComparison } from "@/lib/api";
import { formatModelLabel, formatPercent } from "@/lib/format";

export function ModelComparisonPanel({
  comparison,
  teamNames,
}: {
  comparison: ModelComparison;
  teamNames: Record<string, string>;
}) {
  return (
    <SectionCard>
      <p className="text-xs font-semibold uppercase text-primary">
        Model comparison
      </p>
      <h2 className="mt-1 text-lg font-semibold text-foreground">
        Where {formatModelLabel(comparison.baseline_model)} diverges
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Champion probability deltas versus the baseline model across{" "}
        {formatNumber(comparison.n_simulations)} seeded simulations.
      </p>

      <div className="mt-5 space-y-4">
        {comparison.model_deltas.map((delta) => (
          <div
            key={delta.model_type}
            className="rounded-md border border-border bg-muted/40 p-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="font-semibold text-foreground">
                {formatModelLabel(delta.model_type)}
              </h3>
              <span className="text-xs text-muted-foreground">
                vs {formatModelLabel(delta.baseline_model)}
              </span>
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <DeltaCard
                title="Largest positive delta"
                teamId={delta.largest_positive_delta_team_id}
                value={
                  delta.champion_probability_deltas[
                    delta.largest_positive_delta_team_id
                  ]
                }
                teamNames={teamNames}
              />
              <DeltaCard
                title="Largest negative delta"
                teamId={delta.largest_negative_delta_team_id}
                value={
                  delta.champion_probability_deltas[
                    delta.largest_negative_delta_team_id
                  ]
                }
                teamNames={teamNames}
              />
            </div>

            <div className="mt-4">
              <p className="text-xs font-semibold uppercase text-muted-foreground">
                Top-four champion deltas
              </p>
              <div className="mt-2 space-y-2">
                {comparison.top_four_team_ids.map((teamId) => (
                  <div
                    key={`${delta.model_type}-${teamId}`}
                    className="flex items-center justify-between gap-4 rounded-md bg-accent/50 px-3 py-2"
                  >
                    <span className="font-medium text-foreground">
                      {teamNames[teamId] ?? teamId}
                    </span>
                    <DeltaBadge
                      value={delta.top_four_probability_deltas[teamId] ?? 0}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

function DeltaCard({
  title,
  teamId,
  value,
  teamNames,
}: {
  title: string;
  teamId: string;
  value: number;
  teamNames: Record<string, string>;
}) {
  return (
    <div className="rounded-md bg-accent/50 px-3 py-3">
      <p className="text-xs uppercase text-muted-foreground">{title}</p>
      <div className="mt-2 flex items-center justify-between gap-3">
        <span className="font-semibold text-foreground">
          {teamNames[teamId] ?? teamId}
        </span>
        <DeltaBadge value={value} />
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        Champion delta {formatPercent(value)}
      </p>
    </div>
  );
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}
