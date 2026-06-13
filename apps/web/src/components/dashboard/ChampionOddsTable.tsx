import { formatPercent, TeamProbability } from "@/lib/api";
import { ProbabilityBar } from "@/components/dashboard/ProbabilityBar";

export function ChampionOddsTable({ teams }: { teams: TeamProbability[] }) {
  const rows = [...teams].sort((a, b) => b.champion - a.champion).slice(0, 12);

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-5">
      <h2 className="text-base font-semibold text-zinc-950">
        Champion probability table
      </h2>
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
          <tbody className="divide-y divide-zinc-100">
            {rows.map((team) => (
              <tr key={team.team_id}>
                <td className="py-3 font-medium text-zinc-800">
                  {team.team_name}
                </td>
                <td className="py-3 text-zinc-600">{team.group_id}</td>
                <td className="py-3">
                  <ProbabilityBar value={team.champion} />
                </td>
                <td className="py-3 text-zinc-600">
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
    </section>
  );
}
