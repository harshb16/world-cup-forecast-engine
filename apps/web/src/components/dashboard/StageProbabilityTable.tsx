import { TeamProbability } from "@/lib/api";
import { ProbabilityBar } from "@/components/dashboard/ProbabilityBar";

export function StageProbabilityTable({ teams }: { teams: TeamProbability[] }) {
  const rows = [...teams]
    .sort((a, b) => b.group_qualification_probability - a.group_qualification_probability)
    .slice(0, 12);

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-5">
      <h2 className="text-base font-semibold text-zinc-950">
        Stage probabilities
      </h2>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-zinc-500">
            <tr>
              <th className="py-2 font-semibold">Team</th>
              <th className="py-2 font-semibold">Qualify</th>
              <th className="py-2 font-semibold">Semi-final</th>
              <th className="py-2 font-semibold">Final</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {rows.map((team) => (
              <tr key={team.team_id}>
                <td className="py-3 font-medium text-zinc-800">
                  {team.team_name}
                </td>
                <td className="py-3">
                  <ProbabilityBar value={team.group_qualification_probability} />
                </td>
                <td className="py-3">
                  <ProbabilityBar value={team.semi_final} tone="amber" />
                </td>
                <td className="py-3">
                  <ProbabilityBar value={team.final} tone="rose" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
