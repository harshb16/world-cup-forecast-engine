"use client";

import { useEffect, useMemo, useState } from "react";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { ScenarioBuilder } from "@/components/scenario/ScenarioBuilder";
import { ScenarioOverridesList } from "@/components/scenario/ScenarioOverridesList";
import { ScenarioResultDeltaTable } from "@/components/scenario/ScenarioResultDeltaTable";
import { DeltaBadge } from "@/components/ui/DeltaBadge";
import { HelpText } from "@/components/ui/HelpText";
import { SectionCard } from "@/components/ui/SectionCard";
import {
  compareScenario,
  fetchFixtures,
  fetchTeams,
  Match,
  MatchResultOverride,
  ScenarioCompareResponse,
  Team,
} from "@/lib/api";

export function WhatIfLab() {
  const [fixtures, setFixtures] = useState<Match[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [overrides, setOverrides] = useState<MatchResultOverride[]>([]);
  const [result, setResult] = useState<ScenarioCompareResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;
    Promise.all([fetchFixtures(), fetchTeams()])
      .then(([nextFixtures, nextTeams]) => {
        if (isActive) {
          setFixtures(nextFixtures);
          setTeams(nextTeams);
          setIsLoading(false);
        }
      })
      .catch((caughtError: unknown) => {
        if (isActive) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Scenario data request failed",
          );
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  const teamsById = useMemo(
    () => new Map(teams.map((team) => [team.id, team])),
    [teams],
  );
  const fixturesById = useMemo(
    () => new Map(fixtures.map((fixture) => [fixture.id, fixture])),
    [fixtures],
  );

  function addOverride(override: MatchResultOverride) {
    setOverrides((current) => [
      ...current.filter((item) => item.match_id !== override.match_id),
      override,
    ]);
  }

  function runScenario() {
    setIsRunning(true);
    setError(null);
    compareScenario({
      n_simulations: 1000,
      model_type: "poisson",
      seed: 42,
      result_overrides: overrides,
    })
      .then(setResult)
      .catch((caughtError: unknown) => {
        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "Scenario comparison failed",
        );
      })
      .finally(() => setIsRunning(false));
  }

  if (isLoading) {
    return <LoadingState label="Loading scenario fixtures" />;
  }

  if (error && !result) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-3 md:grid-cols-4">
        {scenarioSteps.map((step, index) => (
          <div
            key={step}
            className="rounded-lg border border-white/10 bg-white/[0.05] p-4"
          >
            <span className="flex size-7 items-center justify-center rounded-md bg-emerald-300/10 text-sm font-semibold text-emerald-200">
              {index + 1}
            </span>
            <p className="mt-3 text-sm font-semibold text-white">{step}</p>
          </div>
        ))}
      </section>

      <ScenarioBuilder
        fixtures={fixtures}
        teamsById={teamsById}
        onAddOverride={addOverride}
      />
      <ScenarioOverridesList
        overrides={overrides}
        fixturesById={fixturesById}
        teamsById={teamsById}
        onRemove={(matchId) =>
          setOverrides((current) =>
            current.filter((override) => override.match_id !== matchId),
          )
        }
        onClear={() => {
          setOverrides([]);
          setResult(null);
        }}
      />

      <SectionCard>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase text-emerald-200">
              Step 3
            </p>
            <h2 className="mt-1 text-lg font-semibold text-white">
              Run the scenario
            </h2>
            <p className="mt-1 text-sm text-zinc-400">
              The backend compares this scenario against the same seeded
              baseline simulation.
            </p>
          </div>
          <button
            type="button"
            onClick={runScenario}
            disabled={isRunning}
            className="h-12 rounded-md bg-emerald-300 px-6 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-400"
          >
            {isRunning ? "Running scenario" : "Run scenario"}
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-rose-200">{error}</p> : null}
      </SectionCard>

      {result ? (
        <div className="space-y-6">
          <HelpText>
            These deltas compare two Monte Carlo runs. Tiny movements can be
            sampling noise; focus on larger, directional shifts.
          </HelpText>
          <div className="grid gap-4 xl:grid-cols-2">
            <DeltaSummary title="Biggest risers" rows={result.biggest_risers} />
            <DeltaSummary title="Biggest fallers" rows={result.biggest_fallers} />
          </div>
          <ScenarioResultDeltaTable
            title="Champion and stage probability changes"
            rows={[...result.deltas]
              .sort(
                (a, b) =>
                  Math.abs(b.champion_probability_delta) -
                  Math.abs(a.champion_probability_delta),
              )
              .slice(0, 16)}
          />
        </div>
      ) : null}
    </div>
  );
}

const scenarioSteps = [
  "Pick matches",
  "Set scores",
  "Run scenario",
  "Compare movement",
];

function DeltaSummary({
  title,
  rows,
}: {
  title: string;
  rows: ScenarioCompareResponse["biggest_risers"];
}) {
  return (
    <SectionCard>
      <h2 className="text-base font-semibold text-white">{title}</h2>
      <div className="mt-4 space-y-3">
        {rows.slice(0, 5).map((row) => (
          <div
            key={row.team_id}
            className="flex items-center justify-between gap-4 rounded-md border border-white/10 bg-white/[0.035] p-3"
          >
            <span className="font-semibold text-zinc-100">{row.team_name}</span>
            <DeltaBadge value={row.champion_probability_delta} />
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
