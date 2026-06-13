import { ProbabilityBar } from "@/components/dashboard/ProbabilityBar";
import { formatPercent, TeamProbability } from "@/lib/api";

const stageRows = [
  { label: "Round of 32", key: "round_of_32" },
  { label: "Round of 16", key: "round_of_16" },
  { label: "Quarter-final", key: "quarter_final" },
  { label: "Semi-final", key: "semi_final" },
  { label: "Final", key: "final" },
] as const;

export function TeamProbabilitySummary({
  probability,
  compact = false,
}: {
  probability: TeamProbability;
  compact?: boolean;
}) {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-md border border-zinc-100 p-3">
          <span className="text-xs font-medium text-zinc-500">Champion</span>
          <div className="mt-2">
            <ProbabilityBar value={probability.champion} />
          </div>
        </div>
        <div className="rounded-md border border-zinc-100 p-3">
          <span className="text-xs font-medium text-zinc-500">
            Group qualification
          </span>
          <div className="mt-2">
            <ProbabilityBar
              value={probability.group_qualification_probability}
            />
          </div>
        </div>
      </div>

      {!compact ? (
        <div className="rounded-md border border-zinc-100 p-3">
          <div className="grid gap-3 text-sm md:grid-cols-2">
            {stageRows.map((row) => (
              <div
                key={row.key}
                className="flex items-center justify-between gap-4"
              >
                <span className="text-zinc-600">{row.label}</span>
                <span className="font-semibold text-zinc-950">
                  {formatPercent(probability[row.key])}
                </span>
              </div>
            ))}
            <div className="flex items-center justify-between gap-4">
              <span className="text-zinc-600">Average points</span>
              <span className="font-semibold text-zinc-950">
                {probability.average_points.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
