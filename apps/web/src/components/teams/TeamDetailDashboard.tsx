"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { DataStatusCard } from "@/components/DataStatusCard";
import { TeamName } from "@/components/teams/TeamName";
import { TeamProbabilitySummary } from "@/components/teams/TeamProbabilitySummary";
import { HelpText } from "@/components/ui/HelpText";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import {
  fetchGroups,
  fetchMetadata,
  fetchTeams,
  fetchTeamPath,
  Group,
  simulateTournament,
  SimulationSummary,
  Team,
  DataMetadata,
  TeamPath,
  TeamPathStage,
} from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";

type TeamDetailData = {
  groups: Group[];
  teams: Team[];
  simulation: SimulationSummary;
  metadata: DataMetadata;
  path: TeamPath;
};

export function TeamDetailDashboard() {
  const params = useParams<{ teamId: string }>();
  const teamId = params.teamId;
  const [data, setData] = useState<TeamDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    Promise.all([
      fetchGroups(),
      fetchTeams(),
      fetchMetadata(),
      fetchTeamPath(teamId),
      simulateTournament({
        n_simulations: 1000,
        model_type: "poisson",
        seed: 42,
      }),
    ])
      .then(([groups, teams, metadata, path, simulation]) => {
        if (isActive) {
          setData({ groups, teams, metadata, path, simulation });
        }
      })
      .catch((caughtError: unknown) => {
        if (isActive) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Team detail request failed",
          );
        }
      });

    return () => {
      isActive = false;
    };
  }, [teamId]);

  const team = useMemo(
    () => data?.teams.find((candidate) => candidate.id === teamId),
    [data, teamId],
  );
  const group = useMemo(
    () => data?.groups.find((candidate) => candidate.id === team?.group_id),
    [data, team],
  );
  const probability = useMemo(
    () => data?.simulation.teams.find((candidate) => candidate.team_id === teamId),
    [data, teamId],
  );

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <LoadingState label="Loading team profile" />;
  }

  if (!team) {
    return <ErrorState message="Team not found." />;
  }

  return (
    <div className="space-y-5">
      <Link
        href="/teams"
        className="inline-flex text-sm font-semibold text-emerald-200 transition hover:text-emerald-100"
      >
        Back to teams
      </Link>

      <section className="rounded-lg border border-white/10 bg-gradient-to-br from-white/[0.12] to-white/[0.04] p-6">
        <div className="grid gap-6 xl:grid-cols-[1fr_1.2fr] xl:items-end">
          <div>
            <p className="text-xs font-semibold uppercase text-emerald-200">
              Team dashboard
            </p>
            <h2 className="mt-2 text-4xl font-semibold text-white">
              {team.name}
            </h2>
            <p className="mt-3 text-sm text-zinc-400">
              {group?.name ?? team.group_id} · Rating {formatNumber(team.rating)}
            </p>
          </div>
          {probability ? (
            <div className="grid gap-3 sm:grid-cols-3">
              <StatCard
                label="Champion chance"
                value={formatPercent(probability.champion)}
                detail="Wins the tournament"
                tone="green"
              />
              <StatCard
                label="Qualification"
                value={formatPercent(
                  probability.group_qualification_probability,
                )}
                detail="Reaches knockouts"
              />
              <StatCard
                label="Average points"
                value={probability.average_points.toFixed(2)}
                detail="Group stage"
                tone="amber"
              />
            </div>
          ) : null}
        </div>
      </section>

      <SectionCard>
        <TeamName team={team} groupName={group?.name} />
        {probability ? (
          <div className="mt-5">
            <TeamProbabilitySummary probability={probability} />
          </div>
        ) : (
          <p className="mt-3 text-sm text-zinc-500">
            Simulation probabilities unavailable.
          </p>
        )}
      </SectionCard>
      <DataStatusCard metadata={data.metadata} />

      <TeamPathExplorer path={data.path} />

      {probability ? (
        <HelpText>
          These chances are not predictions for a single match. They are the
          share of seeded World Cup simulations where {team.name} reaches each
          stage or wins the tournament.
        </HelpText>
      ) : null}
    </div>
  );
}

function TeamPathExplorer({ path }: { path: TeamPath }) {
  return (
    <SectionCard>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-emerald-200">
            Path explorer
          </p>
          <h2 className="mt-1 text-lg font-semibold text-white">
            Likely knockout road
          </h2>
        </div>
        <p className="text-xs text-zinc-500">
          {formatNumber(path.metadata.n_simulations)} simulations ·{" "}
          {path.metadata.model_type.toUpperCase()}
        </p>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-5">
        {path.stages.map((stage) => (
          <PathStageCard key={stage.stage} stage={stage} />
        ))}
      </div>
    </SectionCard>
  );
}

function PathStageCard({ stage }: { stage: TeamPathStage }) {
  const topOpponent = stage.opponents[0];

  return (
    <div className="rounded-lg border border-white/10 bg-black/15 p-3">
      <p className="text-xs font-semibold uppercase text-zinc-500">
        {stage.stage}
      </p>
      <p className="mt-2 text-2xl font-semibold text-white">
        {formatPercent(stage.reached_probability)}
      </p>
      <p className="mt-1 text-xs text-zinc-500">Reach probability</p>

      <div className="mt-4 space-y-2">
        {topOpponent ? (
          stage.opponents.slice(0, 3).map((opponent) => (
            <div key={opponent.team_id}>
              <div className="flex items-center justify-between gap-2 text-xs">
                <span className="truncate font-semibold text-zinc-200">
                  {opponent.team_name}
                </span>
                <span className="text-zinc-500">
                  {formatPercent(opponent.probability)}
                </span>
              </div>
              <div className="mt-1 h-1 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full bg-emerald-300"
                  style={{
                    width: `${Math.round(opponent.probability * 100)}%`,
                  }}
                />
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-zinc-500">No common opponent yet.</p>
        )}
      </div>
    </div>
  );
}
