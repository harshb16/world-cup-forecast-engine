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
  fetchLatestForecast,
  fetchMetadata,
  fetchTeams,
  fetchTeamPath,
  Group,
  SimulationSummary,
  Team,
  DataMetadata,
  TeamPath,
  TeamPathStage,
} from "@/lib/api";
import { formatModelLabel, formatNumber, formatPercent } from "@/lib/format";

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
      fetchLatestForecast(),
    ])
      .then(([groups, teams, metadata, path, snapshot]) => {
        if (isActive) {
          setData({
            groups,
            teams,
            metadata,
            path,
            simulation: snapshot.summary,
          });
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
        className="inline-flex text-sm font-semibold text-primary transition hover:text-primary"
      >
        Back to teams
      </Link>

      <section className="rounded-lg border border-border bg-gradient-to-br from-white/[0.12] to-white/[0.04] p-6">
        <div className="grid gap-6 xl:grid-cols-[1fr_1.2fr] xl:items-end">
          <div>
            <p className="text-xs font-semibold uppercase text-primary">
              Team dashboard
            </p>
            <h2 className="mt-2 text-4xl font-semibold text-foreground">
              {team.name}
            </h2>
            <p className="mt-3 text-sm text-muted-foreground">
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
          <p className="mt-3 text-sm text-muted-foreground">
            Simulation probabilities unavailable.
          </p>
        )}
      </SectionCard>
      <DataStatusCard metadata={data.metadata} />

      <TeamPathExplorer path={data.path} />

      <SectionCard>
        <p className="text-xs font-semibold uppercase text-primary">
          Likely road to final
        </p>
        <h2 className="mt-1 text-lg font-semibold text-foreground">
          Most common opponents by round
        </h2>
        <ul className="mt-4 space-y-3">
          {data.path.stages
            .filter((stage) => stage.most_likely_opponent)
            .map((stage) => (
              <li
                key={stage.stage}
                className="flex items-center justify-between gap-3 rounded-md border border-border bg-black/15 px-3 py-2"
              >
                <span className="text-sm font-semibold text-muted-foreground">
                  {stage.stage}
                </span>
                <span className="text-sm text-foreground">
                  {stage.most_likely_opponent?.team_name ?? "—"}
                </span>
                <span className="text-xs text-muted-foreground">
                  {formatPercent(stage.most_likely_opponent?.probability ?? 0)}
                </span>
              </li>
            ))}
        </ul>
      </SectionCard>

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
          <p className="text-xs font-semibold uppercase text-primary">
            Path explorer
          </p>
          <h2 className="mt-1 text-lg font-semibold text-foreground">
            Likely knockout road
          </h2>
        </div>
        <p className="text-xs text-muted-foreground">
          {formatNumber(path.metadata.n_simulations)} simulations ·{" "}
          {formatModelLabel(path.metadata.model_type)}
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
    <div className="rounded-lg border border-border bg-black/15 p-3">
      <p className="text-xs font-semibold uppercase text-muted-foreground">
        {stage.stage}
      </p>
      <p className="mt-2 text-2xl font-semibold text-foreground">
        {formatPercent(stage.reached_probability)}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">Reach probability</p>

      <div className="mt-4 space-y-2">
        {topOpponent ? (
          stage.opponents.slice(0, 3).map((opponent) => (
            <div key={opponent.team_id}>
              <div className="flex items-center justify-between gap-2 text-xs">
                <span className="truncate font-semibold text-foreground">
                  {opponent.team_name}
                </span>
                <span className="text-muted-foreground">
                  {formatPercent(opponent.probability)}
                </span>
              </div>
              <div className="mt-1 h-1 overflow-hidden rounded-full bg-muted/50">
                <div
                  className="h-full bg-primary"
                  style={{
                    width: `${Math.round(opponent.probability * 100)}%`,
                  }}
                />
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">No common opponent yet.</p>
        )}
      </div>
    </div>
  );
}
