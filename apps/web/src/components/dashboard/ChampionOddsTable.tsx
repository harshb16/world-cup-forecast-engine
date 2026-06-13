import { ProbabilityBar } from "@/components/dashboard/ProbabilityBar";
import { SectionCard } from "@/components/ui/SectionCard";
import { formatPercent } from "@/lib/format";
import { TeamProbability } from "@/lib/api";

export function ChampionOddsTable({ teams }: { teams: TeamProbability[] }) {
  const rows = [...teams].sort((a, b) => b.champion - a.champion).slice(0, 12);

  return (
    <SectionCard>
      <h2 className="text-base font-semibold text-white">Champion odds</h2>
      <p className="mt-1 text-sm text-zinc-400">
        Chance each contender wins the tournament across the simulation run.
      </p>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-zinc-500">
            <tr>
              <th className="py-2 font-semibold">Team</th>
              <th className="py-2 font-semibold">Group</th>
              <th className="py-2 font-semibold">Champion</th>
              <th className="py-2 font-semibold">Average points</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {rows.map((team) => (
              <tr key={team.team_id}>
                <td className="py-3 font-medium text-zinc-100">
                  {team.team_name}
                </td>
                <td className="py-3 text-zinc-400">{team.group_id}</td>
                <td className="py-3">
                  <ProbabilityBar value={team.champion} />
                </td>
                <td className="py-3 text-zinc-400">
                  {team.average_points.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-zinc-500">
        Top 12 teams shown. Total champion probability:{" "}
        {formatPercent(teams.reduce((total, team) => total + team.champion, 0))}
      </p>
    </SectionCard>
  );
}
