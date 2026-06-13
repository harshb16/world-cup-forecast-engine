import { ProbabilityBar } from "@/components/dashboard/ProbabilityBar";
import { GroupChaosScore } from "@/components/groups/GroupChaosScore";
import { Group, Team, TeamProbability } from "@/lib/api";

export function GroupProbabilityCard({
  group,
  teams,
  probabilitiesByTeamId,
}: {
  group: Group;
  teams: Team[];
  probabilitiesByTeamId: Map<string, TeamProbability>;
}) {
  const groupTeams = group.team_ids
    .map((teamId) => {
      const team = teams.find((candidate) => candidate.id === teamId);
      const probability = probabilitiesByTeamId.get(teamId);
      return team && probability ? { team, probability } : null;
    })
    .filter((item): item is { team: Team; probability: TeamProbability } =>
      Boolean(item),
    )
    .sort(
      (a, b) =>
        b.probability.group_qualification_probability -
        a.probability.group_qualification_probability,
    );

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-zinc-950">{group.name}</h2>
          <p className="text-sm text-zinc-500">{group.id}</p>
        </div>
        <GroupChaosScore teams={groupTeams.map((item) => item.probability)} />
      </div>

      <div className="mt-5 space-y-4">
        {groupTeams.map(({ team, probability }) => (
          <div key={team.id} className="rounded-md border border-zinc-100 p-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h3 className="font-semibold text-zinc-900">{team.name}</h3>
                <p className="text-xs text-zinc-500">
                  Rating {team.rating.toFixed(0)} · Avg points{" "}
                  {probability.average_points.toFixed(2)}
                </p>
              </div>
              <ProbabilityBar
                value={probability.group_qualification_probability}
              />
            </div>
            <div className="mt-3 grid gap-3 text-xs text-zinc-600 sm:grid-cols-2">
              <div className="flex items-center justify-between gap-3">
                <span>Top two</span>
                <span className="font-semibold">
                  {(probability.top_two_probability * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>Third-place qualify</span>
                <span className="font-semibold">
                  {(
                    probability.third_place_qualification_probability * 100
                  ).toFixed(1)}
                  %
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
