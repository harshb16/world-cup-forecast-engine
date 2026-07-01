"use client";

import { useCallback, useMemo, useState } from "react";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { DataStatusCard } from "@/components/DataStatusCard";
import { TeamName } from "@/components/teams/TeamName";
import { TeamProbabilitySummary } from "@/components/teams/TeamProbabilitySummary";
import { TeamSearch } from "@/components/teams/TeamSearch";
import { EmptyState } from "@/components/ui/EmptyState";
import { HelpText } from "@/components/ui/HelpText";
import { SectionCard } from "@/components/ui/SectionCard";
import { usePublishedForecast } from "@/hooks/usePublishedForecast";
import {
  fetchGroups,
  fetchLatestForecast,
  fetchMetadata,
  fetchTeams,
  Group,
  SimulationSummary,
  Team,
  TeamProbability,
  DataMetadata,
} from "@/lib/api";
import {
  currentRoundLabel,
  matchesTournamentFilter,
  type TournamentFilter,
} from "@/lib/team-status";
import { formatPercent } from "@/lib/format";

type TeamIndexData = {
  groups: Group[];
  teams: Team[];
  simulation: SimulationSummary;
  metadata: DataMetadata;
};

export function TeamsDashboard() {
  const [query, setQuery] = useState("");
  const [selectedGroupId, setSelectedGroupId] = useState("all");
  const [tournamentFilter, setTournamentFilter] =
    useState<TournamentFilter>("all");

  const loadTeams = useCallback(async (): Promise<TeamIndexData> => {
    const [groups, teams, metadata, snapshot] = await Promise.all([
      fetchGroups(),
      fetchTeams(),
      fetchMetadata(),
      fetchLatestForecast(),
    ]);

    return {
      groups,
      teams,
      metadata,
      simulation: snapshot.summary,
    };
  }, []);

  const { data, error } = usePublishedForecast(loadTeams);

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
        .filter((team) =>
          matchesTournamentFilter(
            probabilitiesByTeamId.get(team.id),
            tournamentFilter,
          ),
        )
        .sort((a, b) => {
          const aProbability = probabilitiesByTeamId.get(a.id);
          const bProbability = probabilitiesByTeamId.get(b.id);
          const aChampion = aProbability?.champion ?? 0;
          const bChampion = bProbability?.champion ?? 0;

          return bChampion - aChampion || a.name.localeCompare(b.name);
        }) ?? []
    );
  }, [data, probabilitiesByTeamId, query, selectedGroupId, tournamentFilter]);

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

  if (error && !data) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <LoadingState label="Loading teams" />;
  }

  return (
    <div className="space-y-5">
      <SectionCard>
        <div className="grid gap-4">
          <div className="flex flex-wrap gap-2">
            {(
              [
                ["still_in", "Still in"],
                ["eliminated", "Eliminated"],
                ["all", "All teams"],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => setTournamentFilter(value)}
                className={`min-w-fit rounded-md border px-3 py-2 text-xs font-semibold transition ${
                  tournamentFilter === value
                    ? "border-primary/40 bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:bg-accent/60"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
            <TeamSearch value={query} onChange={setQuery} />
            <div className="flex max-w-full gap-2 overflow-x-auto">
            <button
              type="button"
              onClick={() => setSelectedGroupId("all")}
              className={`min-w-fit rounded-md border px-3 py-2 text-xs font-semibold transition ${
                selectedGroupId === "all"
                  ? "border-primary/40 bg-primary/10 text-primary"
                  : "border-border text-muted-foreground hover:bg-accent/60"
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
                    ? "border-primary/40 bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:bg-accent/60"
                }`}
              >
                {group.id}
              </button>
            ))}
          </div>
        </div>
        </div>
      </SectionCard>

      <HelpText>
        Team cards use the published forecast snapshot. Open a profile for a
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
              <p className="text-xs font-semibold uppercase text-primary">
                {group.id}
              </p>
              <h2 className="text-lg font-semibold text-foreground">{group.name}</h2>
            </div>
            <div className="grid gap-4 xl:grid-cols-2">
              {teams.map((team) => {
                const probability = probabilitiesByTeamId.get(team.id);
                const groupInfo = groupsById.get(team.group_id);

                return (
                  <SectionCard key={team.id}>
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <TeamName
                        team={team}
                        groupName={groupInfo?.name}
                        href={`/teams/${team.id}`}
                      />
                      {probability ? (
                        <TeamRoundBadge probability={probability} />
                      ) : null}
                    </div>
                    {probability ? (
                      <div className="mt-4">
                        <TeamProbabilitySummary probability={probability} compact />
                      </div>
                    ) : (
                      <p className="mt-3 text-sm text-muted-foreground">
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

function TeamRoundBadge({ probability }: { probability: TeamProbability }) {
  const label = currentRoundLabel(probability);
  const tone =
    label === "Eliminated"
      ? "border-signal-red/30 bg-signal-red/10 text-signal-red"
      : "border-primary/25 bg-primary/10 text-primary";

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-[0.65rem] font-semibold uppercase tracking-wide ${tone}`}
    >
      {label}
      {label !== "Eliminated" ? ` · ${formatPercent(probability.champion)}` : ""}
    </span>
  );
}
