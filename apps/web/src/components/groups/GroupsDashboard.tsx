"use client";

import { useEffect, useMemo, useState } from "react";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { GroupProbabilityCard } from "@/components/groups/GroupProbabilityCard";
import {
  fetchGroups,
  fetchTeams,
  Group,
  simulateTournament,
  SimulationSummary,
  Team,
} from "@/lib/api";

type GroupData = {
  groups: Group[];
  teams: Team[];
  simulation: SimulationSummary;
};

export function GroupsDashboard() {
  const [data, setData] = useState<GroupData | null>(null);
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
              : "Group data request failed",
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

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <LoadingState label="Loading group probabilities" />;
  }

  return (
    <div className="grid gap-5 xl:grid-cols-2">
      {data.groups.map((group) => (
        <GroupProbabilityCard
          key={group.id}
          group={group}
          teams={data.teams}
          probabilitiesByTeamId={probabilitiesByTeamId}
        />
      ))}
    </div>
  );
}
