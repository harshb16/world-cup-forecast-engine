"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { HeadToHeadPanel } from "@/components/teams/HeadToHeadPanel";
import { TeamProbabilitySummary } from "@/components/teams/TeamProbabilitySummary";
import { SectionCard } from "@/components/ui/SectionCard";
import {
  fetchLatestForecast,
  fetchTeamPath,
  fetchTeams,
  Team,
  TeamPath,
  TeamProbability,
} from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";
import { useTimeMachine } from "@/components/time-machine/TimeMachineProvider";

export function TeamCompareDashboard() {
  const replay = useTimeMachine();
  const { isReplay, loadTeamPath, snapshot } = replay;
  const searchParams = useSearchParams();
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamAId, setTeamAId] = useState(searchParams.get("a") ?? "");
  const [teamBId, setTeamBId] = useState(searchParams.get("b") ?? "");
  const [probabilities, setProbabilities] = useState<Map<string, TeamProbability>>(
    new Map(),
  );
  const [paths, setPaths] = useState<Record<string, TeamPath | null>>({
    a: null,
    b: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTeams()
      .then((loadedTeams) => {
        setTeams(loadedTeams);
        setTeamAId((current) => current || loadedTeams[0]?.id || "");
        setTeamBId((current) => current || loadedTeams[1]?.id || "");
      })
      .catch((caught: unknown) => {
        setError(
          caught instanceof Error ? caught.message : "Failed to load teams",
        );
      });
  }, []);

  useEffect(() => {
    if (!teamAId || !teamBId || teamAId === teamBId) {
      setLoading(false);
      return;
    }

    let isActive = true;
    setLoading(true);
    setError(null);

    Promise.all([
      isReplay ? Promise.resolve(snapshot?.forecast ?? null) : fetchLatestForecast(),
      isReplay ? loadTeamPath(teamAId) : fetchTeamPath(teamAId),
      isReplay ? loadTeamPath(teamBId) : fetchTeamPath(teamBId),
    ])
      .then(([snapshot, pathA, pathB]) => {
        if (!isActive) {
          return;
        }
        if (!snapshot) throw new Error("Replay snapshot is still loading.");
        setProbabilities(
          new Map(snapshot.summary.teams.map((team) => [team.team_id, team])),
        );
        setPaths({ a: pathA, b: pathB });
      })
      .catch((caught: unknown) => {
        if (isActive) {
          setError(
            caught instanceof Error ? caught.message : "Compare request failed",
          );
        }
      })
      .finally(() => {
        if (isActive) {
          setLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [isReplay, loadTeamPath, snapshot, teamAId, teamBId]);

  const teamA = useMemo(
    () => teams.find((team) => team.id === teamAId) ?? null,
    [teams, teamAId],
  );
  const teamB = useMemo(
    () => teams.find((team) => team.id === teamBId) ?? null,
    [teams, teamBId],
  );
  const probabilityA = probabilities.get(teamAId);
  const probabilityB = probabilities.get(teamBId);

  if (error && !teamA) {
    return <ErrorState message={error} />;
  }

  if (loading && !probabilityA) {
    return <LoadingState label="Loading team comparison" />;
  }

  return (
    <div className="space-y-6">
      <SectionCard>
        <div className="grid gap-4 md:grid-cols-2">
          <TeamPicker
            label="Team A"
            teams={teams}
            value={teamAId}
            onChange={setTeamAId}
            excludeId={teamBId}
          />
          <TeamPicker
            label="Team B"
            teams={teams}
            value={teamBId}
            onChange={setTeamBId}
            excludeId={teamAId}
          />
        </div>
      </SectionCard>

      {teamAId === teamBId ? (
        <p className="text-sm text-destructive">Pick two different teams.</p>
      ) : null}

      {teamA && teamB && probabilityA && probabilityB ? (
        <>
          <div className="grid gap-4 xl:grid-cols-2">
            <CompareColumn
              team={teamA}
              probability={probabilityA}
              path={paths.a}
            />
            <CompareColumn
              team={teamB}
              probability={probabilityB}
              path={paths.b}
            />
          </div>

          <SectionCard>
            <p className="text-xs font-semibold uppercase text-primary">
              Rating gap
            </p>
            <p className="mt-2 text-sm text-foreground">
              {teamA.name} {formatNumber(teamA.rating)} vs {teamB.name}{" "}
              {formatNumber(teamB.rating)} (
              {formatNumber(Math.abs(teamA.rating - teamB.rating))} Elo gap)
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Champion odds: {formatPercent(probabilityA.champion)} vs{" "}
              {formatPercent(probabilityB.champion)}
            </p>
          </SectionCard>

          <HeadToHeadPanel
            teamAId={teamAId}
            teamBId={teamBId}
            title={`${teamA.name} vs ${teamB.name} meeting odds`}
          />
        </>
      ) : null}
    </div>
  );
}

function TeamPicker({
  label,
  teams,
  value,
  onChange,
  excludeId,
}: {
  label: string;
  teams: Team[];
  value: string;
  onChange: (teamId: string) => void;
  excludeId: string;
}) {
  return (
    <label className="text-sm font-medium text-muted-foreground">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 h-11 w-full rounded-md border border-border bg-card px-3 text-sm text-foreground outline-none focus:border-primary/50"
      >
        {teams
          .filter((team) => team.id !== excludeId)
          .map((team) => (
            <option key={team.id} value={team.id}>
              {team.name}
            </option>
          ))}
      </select>
    </label>
  );
}

function CompareColumn({
  team,
  probability,
  path,
}: {
  team: Team;
  probability: TeamProbability;
  path: TeamPath | null;
}) {
  const replay = useTimeMachine();
  return (
    <SectionCard>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase text-primary">
            {team.group_id}
          </p>
          <h2 className="mt-1 text-2xl font-semibold text-foreground">
            {team.name}
          </h2>
        </div>
        <Link
          href={replay.hrefFor(`/teams/${team.id}`)}
          className="text-sm font-semibold text-primary"
        >
          Open profile
        </Link>
      </div>
      <div className="mt-4">
        <TeamProbabilitySummary probability={probability} />
      </div>
      {path ? (
        <div className="mt-4 space-y-2 text-sm text-muted-foreground">
          {path.stages
            .filter((stage) => stage.most_likely_opponent)
            .map((stage) => (
              <div
                key={stage.stage}
                className="flex items-center justify-between gap-3 rounded-md border border-border bg-muted/40 px-3 py-2"
              >
                <span>{stage.stage}</span>
                <span className="font-medium text-foreground">
                  {stage.most_likely_opponent?.team_name}
                </span>
              </div>
            ))}
        </div>
      ) : null}
    </SectionCard>
  );
}
