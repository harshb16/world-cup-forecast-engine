"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { TeamName } from "@/components/teams/TeamName";
import { TeamProbabilitySummary } from "@/components/teams/TeamProbabilitySummary";
import { HelpText } from "@/components/ui/HelpText";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import {
  fetchGroups,
  fetchTeams,
  Group,
  simulateTournament,
  SimulationSummary,
  Team,
} from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";

type TeamDetailData = {
  groups: Group[];
  teams: Team[];
  simulation: SimulationSummary;
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
              : "Team detail request failed",
          );
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

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

      {probability ? (
        <HelpText>
          These chances are not predictions for a single match. They are the
          share of seeded sample simulations where {team.name} reaches each
          stage or wins the tournament.
        </HelpText>
      ) : null}
    </div>
  );
}
