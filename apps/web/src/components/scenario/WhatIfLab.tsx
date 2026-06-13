"use client";

import { useEffect, useMemo, useState } from "react";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { ScenarioBuilder } from "@/components/scenario/ScenarioBuilder";
import { ScenarioOverridesList } from "@/components/scenario/ScenarioOverridesList";
import { ScenarioResultDeltaTable } from "@/components/scenario/ScenarioResultDeltaTable";
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

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <button
          type="button"
          onClick={runScenario}
          disabled={isRunning}
          className="h-11 rounded-md bg-emerald-600 px-5 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-zinc-300"
        >
          {isRunning ? "Running" : "Run scenario"}
        </button>
        {error ? <span className="text-sm text-rose-700">{error}</span> : null}
      </div>

      {result ? (
        <div className="space-y-6">
          <div className="grid gap-6 xl:grid-cols-2">
            <ScenarioResultDeltaTable
              title="Biggest risers"
              rows={result.biggest_risers}
            />
            <ScenarioResultDeltaTable
              title="Biggest fallers"
              rows={result.biggest_fallers}
            />
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
