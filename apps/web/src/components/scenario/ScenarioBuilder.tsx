"use client";

import { useMemo, useState } from "react";

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

  const selectedLabel = selectedMatch
    ? `${teamsById.get(selectedMatch.team_a_id)?.name ?? selectedMatch.team_a_id} vs ${
        teamsById.get(selectedMatch.team_b_id)?.name ?? selectedMatch.team_b_id
      }`
    : "Select match";

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-5">
      <h2 className="text-base font-semibold text-zinc-950">Scenario builder</h2>
      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_8rem_8rem_auto]">
        <label className="text-sm font-medium text-zinc-700">
          Match
          <select
            value={matchId}
            onChange={(event) => setMatchId(event.target.value)}
            className="mt-2 h-11 w-full rounded-md border border-zinc-300 bg-white px-3 text-sm text-zinc-950"
          >
            {fixtures.map((fixture) => {
              const teamA = teamsById.get(fixture.team_a_id)?.name ?? fixture.team_a_id;
              const teamB = teamsById.get(fixture.team_b_id)?.name ?? fixture.team_b_id;
              return (
                <option key={fixture.id} value={fixture.id}>
                  {fixture.id}: {teamA} vs {teamB}
                </option>
              );
            })}
          </select>
        </label>

        <label className="text-sm font-medium text-zinc-700">
          Team A
          <input
            value={teamAGoals}
            min={0}
            type="number"
            onChange={(event) => setTeamAGoals(Number(event.target.value))}
            className="mt-2 h-11 w-full rounded-md border border-zinc-300 px-3 text-sm text-zinc-950"
          />
        </label>

        <label className="text-sm font-medium text-zinc-700">
          Team B
          <input
            value={teamBGoals}
            min={0}
            type="number"
            onChange={(event) => setTeamBGoals(Number(event.target.value))}
            className="mt-2 h-11 w-full rounded-md border border-zinc-300 px-3 text-sm text-zinc-950"
          />
        </label>

        <button
          type="button"
          onClick={() =>
            onAddOverride({
              match_id: matchId,
              team_a_goals: Math.max(0, teamAGoals),
              team_b_goals: Math.max(0, teamBGoals),
            })
          }
          className="mt-7 h-11 rounded-md bg-emerald-600 px-4 text-sm font-semibold text-white transition hover:bg-emerald-700"
        >
          Add
        </button>
      </div>
      <p className="mt-3 text-xs text-zinc-500">{selectedLabel}</p>
    </section>
  );
}
