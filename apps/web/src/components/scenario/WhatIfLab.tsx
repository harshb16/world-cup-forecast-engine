"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { DataStatusCard } from "@/components/DataStatusCard";
import { ScenarioBuilder } from "@/components/scenario/ScenarioBuilder";
import { ScenarioOverridesList } from "@/components/scenario/ScenarioOverridesList";
import { ScenarioResultDeltaTable } from "@/components/scenario/ScenarioResultDeltaTable";
import { DeltaBadge } from "@/components/ui/DeltaBadge";
import { HelpText } from "@/components/ui/HelpText";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import {
  compareScenario,
  DEFAULT_MODEL_TYPE,
  fetchFixtures,
  fetchMetadata,
  fetchTeams,
  Match,
  MatchResultOverride,
  ScenarioCompareResponse,
  Team,
  DataMetadata,
} from "@/lib/api";

function encodeOverrides(overrides: MatchResultOverride[]): string {
  if (overrides.length === 0) {
    return "";
  }
  return overrides
    .map(
      (override) =>
        `${override.match_id}:${override.team_a_goals}-${override.team_b_goals}`,
    )
    .join(",");
}

function decodeOverrides(value: string | null): MatchResultOverride[] {
  if (!value) {
    return [];
  }

  return value
    .split(",")
    .map((entry) => {
      const [matchId, score] = entry.split(":");
      const [teamAGoals, teamBGoals] = (score ?? "").split("-").map(Number);
      if (!matchId || Number.isNaN(teamAGoals) || Number.isNaN(teamBGoals)) {
        return null;
      }
      return {
        match_id: matchId,
        team_a_goals: teamAGoals,
        team_b_goals: teamBGoals,
      };
    })
    .filter((item): item is MatchResultOverride => Boolean(item));
}

export function WhatIfLab() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [fixtures, setFixtures] = useState<Match[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [overrides, setOverrides] = useState<MatchResultOverride[]>(() =>
    decodeOverrides(searchParams.get("overrides")),
  );
  const [result, setResult] = useState<ScenarioCompareResponse | null>(null);
  const [metadata, setMetadata] = useState<DataMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let isActive = true;
    Promise.all([fetchFixtures(), fetchTeams(), fetchMetadata()])
      .then(([nextFixtures, nextTeams, nextMetadata]) => {
        if (isActive) {
          setFixtures(nextFixtures);
          setTeams(nextTeams);
          setMetadata(nextMetadata);
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

  useEffect(() => {
    const encoded = encodeOverrides(overrides);
    const next = encoded ? `/what-if?overrides=${encoded}` : "/what-if";
    router.replace(next, { scroll: false });
  }, [overrides, router]);

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
      model_type: DEFAULT_MODEL_TYPE,
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

  async function copyScenarioLink() {
    await navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
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
            <span className="flex size-7 items-center justify-center rounded-md bg-[var(--turf)]/10 text-sm font-semibold text-[var(--turf)]">
              {index + 1}
            </span>
            <p className="mt-3 text-sm font-semibold text-white">{step}</p>
          </div>
        ))}
      </section>
      {metadata ? <DataStatusCard metadata={metadata} /> : null}

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
            <p className="text-xs font-semibold uppercase text-[var(--turf)]">
              Step 3
            </p>
            <h2 className="mt-1 text-lg font-semibold text-white">
              Run the scenario
            </h2>
            <p className="mt-1 text-sm text-zinc-400">
              The backend compares this scenario against the same seeded
              baseline simulation. Scenario state is stored in the URL for
              sharing.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={copyScenarioLink}
              className="h-12 rounded-md border border-white/10 bg-white/[0.05] px-4 text-sm font-semibold text-zinc-100 transition hover:bg-white/[0.08]"
            >
              {copied ? "Link copied" : "Copy scenario link"}
            </button>
            <button
              type="button"
              onClick={runScenario}
              disabled={isRunning}
              className="h-12 rounded-md bg-[var(--turf)] px-6 text-sm font-semibold text-zinc-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-400"
            >
              {isRunning ? "Running scenario" : "Run scenario"}
            </button>
          </div>
        </div>
        {error ? <p className="mt-3 text-sm text-[var(--risk-red)]">{error}</p> : null}
      </SectionCard>

      {result ? (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <StatCard
              label="Baseline champion"
              value={
                [...result.baseline.teams].sort(
                  (a, b) => b.champion - a.champion,
                )[0]?.team_name ?? "-"
              }
              detail="Before overrides"
            />
            <StatCard
              label="Scenario champion"
              value={
                [...result.scenario.teams].sort(
                  (a, b) => b.champion - a.champion,
                )[0]?.team_name ?? "-"
              }
              detail="After overrides"
              tone="green"
            />
            <StatCard
              label="Overrides applied"
              value={String(overrides.length)}
              detail="Manual result changes"
              tone="amber"
            />
          </div>

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
