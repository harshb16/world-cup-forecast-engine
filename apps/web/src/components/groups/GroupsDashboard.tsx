"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ThirdPlaceTrackerPanel } from "@/components/analytics/ThirdPlaceTracker";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { DataStatusCard } from "@/components/DataStatusCard";
import { GroupProbabilityCard } from "@/components/groups/GroupProbabilityCard";
import { HelpText } from "@/components/ui/HelpText";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { useTimeMachine } from "@/components/time-machine/TimeMachineProvider";

type GroupData = {
  groups: Group[];
  teams: Team[];
  simulation: SimulationSummary;
  metadata: DataMetadata;
  chaosByGroupId: Map<string, GroupChaosScore>;
  thirdPlace: ThirdPlaceTracker;
  groupTables?: Record<string, Array<Record<string, unknown>>>;
};

export function GroupsDashboard() {
  const replay = useTimeMachine();
  const loadGroups = useCallback(async (): Promise<GroupData> => {
    const [groups, teams, metadata, liveSnapshot] = await Promise.all([
      fetchGroups(),
      fetchTeams(),
      fetchMetadata(),
      replay.isReplay ? Promise.resolve(null) : fetchLatestForecast(),
    ]);
    const snapshot = replay.isReplay ? replay.snapshot?.forecast : liveSnapshot;
    if (!snapshot) throw new Error("Replay snapshot is still loading.");

    return {
      groups,
      teams,
      metadata,
      simulation: snapshot.summary,
      chaosByGroupId: new Map(
        snapshot.group_chaos.groups.map((group) => [group.group_id, group]),
      ),
      thirdPlace: snapshot.third_place,
      groupTables: replay.snapshot?.group_tables,
    };
  }, [replay.isReplay, replay.snapshot]);

  const { data, error } = usePublishedForecast(loadGroups);

  const probabilitiesByTeamId = useMemo(() => {
    return new Map(
      data?.simulation.teams.map((team) => [team.team_id, team]) ?? [],
    );
  }, [data]);

  const [activeGroup, setActiveGroup] = useState<string>("A");

  useEffect(() => {
    if (data?.groups[0] && !data.groups.some((g) => g.id === activeGroup)) {
      setActiveGroup(data.groups[0].id);
    }
  }, [data, activeGroup]);

  if (error && !data) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <LoadingState label="Loading group probabilities" />;
  }

  const selectedGroup =
    data.groups.find((group) => group.id === activeGroup) ?? data.groups[0];

  return (
    <div className="flex flex-col gap-6">
      <HelpText>
        Qualification probability combines finishing top two with the chance of
        advancing as one of the best {THIRD_PLACE_QUALIFIER_COUNT} third-place
        teams.
      </HelpText>
      {replay.isReplay ? (
        <p className="rounded-md border border-primary/20 bg-primary/10 px-4 py-3 text-sm">Observed standings and forecast odds at {replay.snapshot?.milestone.label}.</p>
      ) : <DataStatusCard metadata={data.metadata} />}

      <Tabs
        value={activeGroup}
        onValueChange={(value) => value && setActiveGroup(value)}
      >
        <TabsList className="flex h-auto flex-wrap gap-1">
          {data.groups.map((group) => (
            <TabsTrigger key={group.id} value={group.id} className="px-3">
              {group.id}
            </TabsTrigger>
          ))}
        </TabsList>
        {data.groups.map((group) => (
          <TabsContent key={group.id} value={group.id} className="pt-4">
            {group.id === selectedGroup.id ? (
              <GroupProbabilityCard
                group={group}
                teams={data.teams}
                probabilitiesByTeamId={probabilitiesByTeamId}
                chaos={data.chaosByGroupId.get(group.id)}
                standings={data.groupTables?.[group.id]}
              />
            ) : null}
          </TabsContent>
        ))}
      </Tabs>

      <ThirdPlaceTrackerPanel tracker={data.thirdPlace} />
    </div>
  );
}
