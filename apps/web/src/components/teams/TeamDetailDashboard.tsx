"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { TeamName } from "@/components/teams/TeamName";
import { TeamProbabilitySummary } from "@/components/teams/TeamProbabilitySummary";
import {
  fetchGroups,
  fetchTeams,
  Group,
  simulateTournament,
  SimulationSummary,
  Team,
} from "@/lib/api";

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
        className="inline-flex text-sm font-semibold text-emerald-700 transition hover:text-emerald-800"
      >
        Back to teams
      </Link>

      <section className="rounded-lg border border-zinc-200 bg-white p-5">
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
      </section>
    </div>
  );
}
