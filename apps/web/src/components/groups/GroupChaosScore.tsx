import { TeamProbability } from "@/lib/api";

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
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 rounded-full bg-zinc-100">
        <div
          className="h-full rounded-full bg-amber-500"
          style={{ width: `${score * 100}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-zinc-600">
        {label} chaos
      </span>
    </div>
  );
}
