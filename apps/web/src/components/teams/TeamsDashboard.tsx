"use client";

import { useEffect, useMemo, useState } from "react";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { TeamName } from "@/components/teams/TeamName";
import { TeamProbabilitySummary } from "@/components/teams/TeamProbabilitySummary";
import { TeamSearch } from "@/components/teams/TeamSearch";
import {
  fetchGroups,
  fetchTeams,
  Group,
  simulateTournament,
  SimulationSummary,
  Team,
} from "@/lib/api";

type TeamIndexData = {
  groups: Group[];
  teams: Team[];
  simulation: SimulationSummary;
};

export function TeamsDashboard() {
  const [data, setData] = useState<TeamIndexData | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    Promise.all([
      fetchGroups(),
      fetchTeams(),
      simulateTournament({
        n_simulations: 1000,
        model_type: "poisson",
        seed: 42,
      }),
    ])
      .then(([groups, teams, simulation]) => {
        if (isActive) {
          setData({ groups, teams, simulation });
        }
      })
      .catch((caughtError: unknown) => {
        if (isActive) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Team data request failed",
          );
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  const probabilitiesByTeamId = useMemo(() => {
    return new Map(
      data?.simulation.teams.map((team) => [team.team_id, team]) ?? [],
    );
  }, [data]);

  const groupsById = useMemo(() => {
    return new Map(data?.groups.map((group) => [group.id, group]) ?? []);
  }, [data]);

  const filteredTeams = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return (
      data?.teams
        .filter((team) =>
          normalizedQuery
            ? team.name.toLowerCase().includes(normalizedQuery) ||
              team.group_id.toLowerCase().includes(normalizedQuery)
            : true,
        )
        .sort((a, b) => {
          const aProbability =
            probabilitiesByTeamId.get(a.id)?.group_qualification_probability ??
            0;
          const bProbability =
            probabilitiesByTeamId.get(b.id)?.group_qualification_probability ??
            0;

          return bProbability - aProbability || a.name.localeCompare(b.name);
        }) ?? []
    );
  }, [data, probabilitiesByTeamId, query]);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <LoadingState label="Loading teams" />;
  }

  return (
    <div className="space-y-5">
      <TeamSearch value={query} onChange={setQuery} />

      <div className="grid gap-5 xl:grid-cols-2">
        {filteredTeams.map((team) => {
          const probability = probabilitiesByTeamId.get(team.id);
          const group = groupsById.get(team.group_id);

          return (
            <section
              key={team.id}
              className="rounded-lg border border-zinc-200 bg-white p-5"
            >
              <TeamName
                team={team}
                groupName={group?.name}
                href={`/teams/${team.id}`}
              />
              {probability ? (
                <div className="mt-4">
                  <TeamProbabilitySummary probability={probability} compact />
                </div>
              ) : (
                <p className="mt-3 text-sm text-zinc-500">
                  Simulation probabilities unavailable.
                </p>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}
