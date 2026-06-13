"use client";

import { useEffect, useState } from "react";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { MetricCard } from "@/components/MetricCard";
import { ChampionOddsTable } from "@/components/dashboard/ChampionOddsTable";
import { StageProbabilityTable } from "@/components/dashboard/StageProbabilityTable";
import { TopWinnersCards } from "@/components/dashboard/TopWinnersCards";
import { formatPercent, simulateTournament, SimulationSummary } from "@/lib/api";

export function HomeDashboard() {
  const [summary, setSummary] = useState<SimulationSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    simulateTournament({
      n_simulations: 1000,
      model_type: "poisson",
      seed: 42,
    })
      .then((data) => {
        if (isActive) {
          setSummary(data);
        }
      })
      .catch((caughtError: unknown) => {
        if (isActive) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Simulation request failed",
          );
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!summary) {
    return <LoadingState label="Running simulation" />;
  }

  const teams = summary.teams;
  const topChampion = [...teams].sort((a, b) => b.champion - a.champion)[0];
  const averageQualification =
    teams.reduce(
      (total, team) => total + team.group_qualification_probability,
      0,
    ) / teams.length;

  return (
    <div className="space-y-6">
      <TopWinnersCards teams={teams} />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          label="Model"
          value={summary.metadata.model_type.toUpperCase()}
          detail={`${summary.metadata.n_simulations.toLocaleString()} simulations`}
        />
        <MetricCard
          label="Top champion"
          value={topChampion.team_name}
          detail={formatPercent(topChampion.champion)}
          tone="green"
        />
        <MetricCard
          label="Average qualification"
          value={formatPercent(averageQualification)}
          detail="Across all teams"
          tone="amber"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_1fr]">
        <ChampionOddsTable teams={teams} />
        <StageProbabilityTable teams={teams} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-lg border border-zinc-200 bg-white p-5">
          <h2 className="text-base font-semibold text-zinc-950">
            Group qualification overview
          </h2>
          <p className="mt-3 text-sm leading-6 text-zinc-600">
            Full group cards arrive next with top-two, third-place, and average
            points views.
          </p>
        </section>

        <section className="rounded-lg border border-zinc-200 bg-white p-5">
          <h2 className="text-base font-semibold text-zinc-950">
            Upset radar
          </h2>
          <p className="mt-3 text-sm leading-6 text-zinc-600">
            Match-level volatility will appear after fixture scenario controls
            are connected.
          </p>
        </section>
      </div>
    </div>
  );
}
