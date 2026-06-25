import { TeamProbability } from "@/lib/api";
import { formatPercent } from "@/lib/format";

export function calculateGroupChaosScore(teams: TeamProbability[]): number {
  const probabilities = teams.map((team) => team.group_qualification_probability);
  const total = probabilities.reduce((sum, probability) => sum + probability, 0);

  if (total <= 0 || probabilities.length <= 1) {
    return 0;
  }

  const entropy = probabilities.reduce((sum, probability) => {
    if (probability <= 0) {
      return sum;
    }
    const normalized = probability / total;
    return sum - normalized * Math.log(normalized);
  }, 0);

  return entropy / Math.log(probabilities.length);
}

export function GroupChaosScore({ teams }: { teams: TeamProbability[] }) {
  const score = calculateGroupChaosScore(teams);
  const label = score > 0.86 ? "High" : score > 0.72 ? "Medium" : "Low";

  return (
    <div className="rounded-md border border-border bg-accent/50 p-3">
      <div className="flex items-center justify-between gap-4">
        <span className="text-xs font-semibold uppercase text-muted-foreground">
          Group Chaos Score
        </span>
        <span className="text-xs font-semibold text-amber-200">
          {label} · {formatPercent(score, 0)}
        </span>
      </div>
      <div className="mt-2 h-2 rounded-full bg-muted/50">
        <div
          className="h-full rounded-full bg-amber-300"
          style={{ width: `${score * 100}%` }}
        />
      </div>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">
        Higher chaos means qualification odds are bunched together and the group
        is less settled.
      </p>
    </div>
  );
}
