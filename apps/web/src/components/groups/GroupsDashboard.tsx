"use client";

import { useEffect, useMemo, useState } from "react";

import { ThirdPlaceTrackerPanel } from "@/components/analytics/ThirdPlaceTracker";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { DataStatusCard } from "@/components/DataStatusCard";
import { GroupProbabilityCard } from "@/components/groups/GroupProbabilityCard";
import { HelpText } from "@/components/ui/HelpText";
import {
  fetchGroupChaos,
  fetchGroups,
  fetchMetadata,
  fetchTeams,
  Group,
  GroupChaosScore,
  simulateTournament,
  SimulationSummary,
  Team,
  DataMetadata,
} from "@/lib/api";

type GroupData = {
  groups: Group[];
  teams: Team[];
  simulation: SimulationSummary;
  metadata: DataMetadata;
  chaosByGroupId: Map<string, GroupChaosScore>;
};

export function GroupsDashboard() {
  const [data, setData] = useState<GroupData | null>(null);
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
      fetchGroupChaos("oracle_v2", 500, 42),
    ])
      .then(([groups, teams, metadata, simulation, chaos]) => {
        if (isActive) {
          setData({
            groups,
            teams,
            metadata,
            simulation,
            chaosByGroupId: new Map(
              chaos.groups.map((group) => [group.group_id, group]),
            ),
          });
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
    <div className="space-y-5">
      <HelpText>
        Qualification probability combines finishing top two with the chance of
        advancing as one of the best third-place teams.
      </HelpText>
      <DataStatusCard metadata={data.metadata} />
      <div className="grid gap-5 xl:grid-cols-2">
        {data.groups.map((group) => (
          <GroupProbabilityCard
            key={group.id}
            group={group}
            teams={data.teams}
            probabilitiesByTeamId={probabilitiesByTeamId}
            chaos={data.chaosByGroupId.get(group.id)}
          />
        ))}
      </div>
      <ThirdPlaceTrackerPanel />
    </div>
  );
}
