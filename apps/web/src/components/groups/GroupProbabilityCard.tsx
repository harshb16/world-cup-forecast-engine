import { GroupChaosScore } from "@/components/groups/GroupChaosScore";
import { ProbabilityBar } from "@/components/ui/ProbabilityBar";
import { SectionCard } from "@/components/ui/SectionCard";
import { Group, Team, TeamProbability } from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";

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
  const likelyWinner = groupTeams[0];

  return (
    <SectionCard>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-emerald-200">
            {group.id}
          </p>
          <h2 className="mt-1 text-xl font-semibold text-white">{group.name}</h2>
        </div>
        {likelyWinner ? (
          <div className="rounded-md border border-emerald-300/20 bg-emerald-300/10 px-3 py-2 text-sm text-emerald-100">
            <span className="block text-xs text-emerald-100/70">
              Most likely winner
            </span>
            <span className="font-semibold">
              {likelyWinner.team.name} ·{" "}
              {formatPercent(likelyWinner.probability.top_two_probability)}
            </span>
          </div>
        ) : null}
      </div>

      <div className="mt-5">
        <GroupChaosScore teams={groupTeams.map((item) => item.probability)} />
      </div>

      <div className="mt-5 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-white">Qualification race</h3>
          <span className="text-xs text-zinc-500">Sorted by qualify odds</span>
        </div>

        {groupTeams.map(({ team, probability }, index) => (
          <div
            key={team.id}
            className="rounded-md border border-white/10 bg-black/10 p-4"
          >
            <div className="grid gap-4 lg:grid-cols-[1fr_1.2fr] lg:items-center">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-md bg-white/10 text-xs font-semibold text-zinc-300">
                    {index + 1}
                  </span>
                  <div className="min-w-0">
                    <h4 className="truncate font-semibold text-white">
                      {team.name}
                    </h4>
                    <p className="text-xs text-zinc-500">
                      Rating {formatNumber(team.rating)} · Avg points{" "}
                      {probability.average_points.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
              <ProbabilityBar
                value={probability.group_qualification_probability}
                label="Overall qualification"
              />
            </div>

            <div className="mt-3 grid gap-3 text-xs text-zinc-400 sm:grid-cols-3">
              <div className="flex items-center justify-between gap-3 rounded-md bg-white/[0.035] px-3 py-2">
                <span>Average points</span>
                <span className="font-semibold text-zinc-100">
                  {probability.average_points.toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3 rounded-md bg-white/[0.035] px-3 py-2">
                <span>Top two</span>
                <span className="font-semibold text-zinc-100">
                  {formatPercent(probability.top_two_probability)}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>Third-place qualify</span>
                <span className="font-semibold text-zinc-100">
                  {formatPercent(
                    probability.third_place_qualification_probability,
                  )}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
