"use client";

import { useEffect, useMemo, useState } from "react";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { DataStatusCard } from "@/components/DataStatusCard";
import { TeamName } from "@/components/teams/TeamName";
import { TeamProbabilitySummary } from "@/components/teams/TeamProbabilitySummary";
import { TeamSearch } from "@/components/teams/TeamSearch";
import { EmptyState } from "@/components/ui/EmptyState";
import { HelpText } from "@/components/ui/HelpText";
import { SectionCard } from "@/components/ui/SectionCard";
import {
  fetchGroups,
  fetchMetadata,
  fetchTeams,
  Group,
  simulateTournament,
  SimulationSummary,
  Team,
  DataMetadata,
} from "@/lib/api";

type TeamIndexData = {
  groups: Group[];
  teams: Team[];
  simulation: SimulationSummary;
  metadata: DataMetadata;
};

export function TeamsDashboard() {
  const [data, setData] = useState<TeamIndexData | null>(null);
  const [query, setQuery] = useState("");
  const [selectedGroupId, setSelectedGroupId] = useState("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    Promise.all([
      fetchGroups(),
      fetchTeams(),
      fetchMetadata(),
      simulateTournament({
        n_simulations: 1000,
        model_type: "oracle_v2",
        seed: 42,
      }),
    ])
      .then(([groups, teams, metadata, simulation]) => {
        if (isActive) {
          setData({ groups, teams, metadata, simulation });
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
        .filter((team) =>
          selectedGroupId === "all" ? true : team.group_id === selectedGroupId,
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
  }, [data, probabilitiesByTeamId, query, selectedGroupId]);

  const teamsByGroup = useMemo(() => {
    if (!data) {
      return [];
    }

    return data.groups
      .map((group) => ({
        group,
        teams: filteredTeams.filter((team) => team.group_id === group.id),
      }))
      .filter((groupData) => groupData.teams.length > 0);
  }, [data, filteredTeams]);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <LoadingState label="Loading teams" />;
  }

  return (
    <div className="space-y-5">
      <SectionCard>
        <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
          <TeamSearch value={query} onChange={setQuery} />
          <div className="flex max-w-full gap-2 overflow-x-auto">
            <button
              type="button"
              onClick={() => setSelectedGroupId("all")}
              className={`min-w-fit rounded-md border px-3 py-2 text-xs font-semibold transition ${
                selectedGroupId === "all"
                  ? "border-emerald-300/40 bg-emerald-300/10 text-emerald-100"
                  : "border-white/10 text-zinc-400 hover:bg-white/[0.06]"
              }`}
            >
              All groups
            </button>
            {data.groups.map((group) => (
              <button
                key={group.id}
                type="button"
                onClick={() => setSelectedGroupId(group.id)}
                className={`min-w-fit rounded-md border px-3 py-2 text-xs font-semibold transition ${
                  selectedGroupId === group.id
                    ? "border-emerald-300/40 bg-emerald-300/10 text-emerald-100"
                    : "border-white/10 text-zinc-400 hover:bg-white/[0.06]"
                }`}
              >
                {group.id}
              </button>
            ))}
          </div>
        </div>
      </SectionCard>

      <HelpText>
        Team cards use latest seeded World Cup data. Open a profile for a
        fuller stage-by-stage ladder.
      </HelpText>
      <DataStatusCard metadata={data.metadata} />

      {teamsByGroup.length === 0 ? (
        <EmptyState
          title="No teams match that filter"
          description="Try a different search term or show all groups."
        />
      ) : null}

      <div className="space-y-6">
        {teamsByGroup.map(({ group, teams }) => (
          <section key={group.id} className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase text-emerald-200">
                {group.id}
              </p>
              <h2 className="text-lg font-semibold text-white">{group.name}</h2>
            </div>
            <div className="grid gap-4 xl:grid-cols-2">
              {teams.map((team) => {
                const probability = probabilitiesByTeamId.get(team.id);
                const groupInfo = groupsById.get(team.group_id);

                return (
                  <SectionCard key={team.id}>
                    <TeamName
                      team={team}
                      groupName={groupInfo?.name}
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
                  </SectionCard>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
