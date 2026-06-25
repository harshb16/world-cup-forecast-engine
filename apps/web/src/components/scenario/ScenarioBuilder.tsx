"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SectionCard } from "@/components/ui/SectionCard";
import { Match, MatchResultOverride, Team } from "@/lib/api";

export function ScenarioBuilder({
  fixtures,
  teamsById,
  onAddOverride,
}: {
  fixtures: Match[];
  teamsById: Map<string, Team>;
  onAddOverride: (override: MatchResultOverride) => void;
}) {
  const [matchId, setMatchId] = useState(fixtures[0]?.id ?? "");
  const [teamAGoals, setTeamAGoals] = useState(1);
  const [teamBGoals, setTeamBGoals] = useState(0);

  const selectedMatch = useMemo(
    () => fixtures.find((fixture) => fixture.id === matchId),
    [fixtures, matchId],
  );

  const selectedLabel = selectedMatch ? formatFixture(selectedMatch, teamsById) : "";

  return (
    <SectionCard>
      <div>
        <p className="text-xs font-semibold uppercase text-primary">
          Step 1 and 2
        </p>
        <h2 className="mt-1 text-lg font-semibold text-foreground">
          Pick a match and set the score
        </h2>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_8rem_8rem_auto]">
        <label className="text-sm font-medium text-muted-foreground">
          Match
          <select
            value={matchId}
            onChange={(event) => setMatchId(event.target.value)}
            className="mt-2 h-11 w-full rounded-md border border-border bg-card px-3 text-sm text-foreground outline-none focus:border-primary/50"
          >
            {fixtures.map((fixture) => {
              return (
                <option key={fixture.id} value={fixture.id}>
                  {formatFixture(fixture, teamsById)}
                </option>
              );
            })}
          </select>
        </label>

        <label className="text-sm font-medium text-muted-foreground">
          Team A
          <Input
            value={teamAGoals}
            min={0}
            type="number"
            onChange={(event) => setTeamAGoals(Number(event.target.value))}
            className="mt-2 h-11"
          />
        </label>

        <label className="text-sm font-medium text-muted-foreground">
          Team B
          <Input
            value={teamBGoals}
            min={0}
            type="number"
            onChange={(event) => setTeamBGoals(Number(event.target.value))}
            className="mt-2 h-11"
          />
        </label>

        <Button
          type="button"
          disabled={!matchId}
          className="mt-7 h-11"
          onClick={() =>
            onAddOverride({
              match_id: matchId,
              team_a_goals: Math.max(0, teamAGoals),
              team_b_goals: Math.max(0, teamBGoals),
            })
          }
        >
          Add result
        </Button>
      </div>
      {selectedLabel ? (
        <p className="mt-3 text-xs text-muted-foreground">Selected: {selectedLabel}</p>
      ) : null}
    </SectionCard>
  );
}

function formatFixture(fixture: Match, teamsById: Map<string, Team>): string {
  const teamA = teamsById.get(fixture.team_a_id)?.name ?? fixture.team_a_id;
  const teamB = teamsById.get(fixture.team_b_id)?.name ?? fixture.team_b_id;
  const groupLabel = fixture.group_id ? `${fixture.group_id} · ` : "";
  const score = fixture.result
    ? ` · ${fixture.result.team_a_goals}-${fixture.result.team_b_goals}`
    : "";
  return `${groupLabel}${teamA} vs ${teamB}${score}`;
}
