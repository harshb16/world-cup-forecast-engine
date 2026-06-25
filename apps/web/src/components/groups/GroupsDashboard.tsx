"use client";

import { useCallback, useMemo } from "react";

import { ThirdPlaceTrackerPanel } from "@/components/analytics/ThirdPlaceTracker";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { DataStatusCard } from "@/components/DataStatusCard";
import { GroupProbabilityCard } from "@/components/groups/GroupProbabilityCard";
import { HelpText } from "@/components/ui/HelpText";
import { usePublishedForecast } from "@/hooks/usePublishedForecast";
import { THIRD_PLACE_QUALIFIER_COUNT } from "@/lib/tournament";
import {
  fetchGroups,
  fetchLatestForecast,
  fetchMetadata,
  fetchTeams,
  Group,
  GroupChaosScore,
  SimulationSummary,
  Team,
  DataMetadata,
  ThirdPlaceTracker,
} from "@/lib/api";

type GroupData = {
  groups: Group[];
  teams: Team[];
  simulation: SimulationSummary;
  metadata: DataMetadata;
  chaosByGroupId: Map<string, GroupChaosScore>;
  thirdPlace: ThirdPlaceTracker;
};

export function GroupsDashboard() {
  const loadGroups = useCallback(async (): Promise<GroupData> => {
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
      chaosByGroupId: new Map(
        snapshot.group_chaos.groups.map((group) => [group.group_id, group]),
      ),
      thirdPlace: snapshot.third_place,
    };
  }, []);

  const { data, error } = usePublishedForecast(loadGroups);

  const probabilitiesByTeamId = useMemo(() => {
    return new Map(
      data?.simulation.teams.map((team) => [team.team_id, team]) ?? [],
    );
  }, [data]);

  if (error && !data) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <LoadingState label="Loading group probabilities" />;
  }

  return (
    <div className="space-y-5">
      <HelpText>
        Qualification probability combines finishing top two with the chance of
        advancing as one of the best {THIRD_PLACE_QUALIFIER_COUNT} third-place
        teams.
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
      <ThirdPlaceTrackerPanel tracker={data.thirdPlace} />
    </div>
  );
}
