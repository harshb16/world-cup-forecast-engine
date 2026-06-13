import { Trophy } from "lucide-react";

import { formatPercent, TeamProbability } from "@/lib/api";

export function TopWinnersCards({ teams }: { teams: TeamProbability[] }) {
  const topTeams = [...teams]
    .sort((a, b) => b.champion - a.champion)
    .slice(0, 4);

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {topTeams.map((team, index) => (
        <section
          key={team.team_id}
          className="rounded-lg border border-zinc-200 bg-white p-4"
        >
          <div className="flex items-center justify-between gap-3">
            <span className="flex size-9 items-center justify-center rounded-md bg-emerald-50 text-emerald-700">
              <Trophy size={18} aria-hidden="true" />
            </span>
            <span className="text-xs font-semibold text-zinc-400">
              #{index + 1}
            </span>
          </div>
          <p className="mt-4 text-sm font-medium text-zinc-500">
            Champion probability
          </p>
          <h2 className="mt-1 text-lg font-semibold text-zinc-950">
            {team.team_name}
          </h2>
          <p className="mt-2 text-2xl font-semibold text-emerald-700">
            {formatPercent(team.champion)}
          </p>
        </section>
      ))}
    </div>
  );
}
