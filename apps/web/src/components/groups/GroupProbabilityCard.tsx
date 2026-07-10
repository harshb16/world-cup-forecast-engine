import { GroupChaosScore as GroupChaosScoreComponent } from "@/components/groups/GroupChaosScore";
import { ProbabilityBar } from "@/components/ui/ProbabilityBar";
import { SectionCard } from "@/components/ui/SectionCard";
import { Group, GroupChaosScore, Team, TeamProbability } from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";

export function GroupProbabilityCard({
  group,
  teams,
  probabilitiesByTeamId,
  chaos,
  standings,
}: {
  group: Group;
  teams: Team[];
  probabilitiesByTeamId: Map<string, TeamProbability>;
  chaos?: GroupChaosScore;
  standings?: Array<Record<string, unknown>>;
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
          <p className="text-xs font-semibold uppercase text-primary">
            {group.id}
          </p>
          <h2 className="mt-1 text-xl font-semibold text-foreground">{group.name}</h2>
        </div>
        {likelyWinner ? (
          <div className="rounded-md border border-primary/20 bg-primary/10 px-3 py-2 text-sm text-primary">
            <span className="block text-xs text-primary/70">
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
        <GroupChaosScoreComponent
          teams={groupTeams.map((item) => item.probability)}
        />
        {chaos?.key_swing_match_label ? (
          <p className="mt-3 text-sm text-muted-foreground">
            Key swing match:{" "}
            <span className="font-semibold text-signal-amber">
              {chaos.key_swing_match_label}
            </span>
          </p>
        ) : null}
      </div>

      {standings ? (
        <div className="mt-5 overflow-x-auto rounded-md border border-border">
          <table className="w-full min-w-[34rem] text-sm">
            <thead className="bg-muted/60 text-xs uppercase text-muted-foreground">
              <tr><th className="px-3 py-2 text-left">Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th></tr>
            </thead>
            <tbody>
              {standings.map((row) => {
                const team = teams.find((candidate) => candidate.id === row.team_id);
                return <tr key={String(row.team_id)} className="border-t border-border text-center">
                  <td className="px-3 py-2 text-left font-semibold">{team?.name ?? String(row.team_id)}</td>
                  <td>{String(row.played)}</td><td>{String(row.wins)}</td><td>{String(row.draws)}</td><td>{String(row.losses)}</td>
                  <td>{String(row.goals_for)}</td><td>{String(row.goals_against)}</td><td>{String(row.goal_difference)}</td><td className="font-semibold">{String(row.points)}</td>
                </tr>;
              })}
            </tbody>
          </table>
        </div>
      ) : null}

      <div className="mt-5 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-foreground">Qualification race</h3>
          <span className="text-xs text-muted-foreground">Sorted by qualify odds</span>
        </div>

        {groupTeams.map(({ team, probability }, index) => (
          <div
            key={team.id}
            className="rounded-md border border-border bg-black/10 p-4"
          >
            <div className="grid gap-4 lg:grid-cols-[1fr_1.2fr] lg:items-center">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-md bg-muted/50 text-xs font-semibold text-muted-foreground">
                    {index + 1}
                  </span>
                  <div className="min-w-0">
                    <h4 className="truncate font-semibold text-foreground">
                      {team.name}
                    </h4>
                    <p className="text-xs text-muted-foreground">
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

            <div className="mt-3 grid gap-3 text-xs text-muted-foreground sm:grid-cols-3">
              <div className="flex items-center justify-between gap-3 rounded-md bg-white/[0.035] px-3 py-2">
                <span>Average points</span>
                <span className="font-semibold text-foreground">
                  {probability.average_points.toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3 rounded-md bg-white/[0.035] px-3 py-2">
                <span>Top two</span>
                <span className="font-semibold text-foreground">
                  {formatPercent(probability.top_two_probability)}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>Third-place qualify</span>
                <span className="font-semibold text-foreground">
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
