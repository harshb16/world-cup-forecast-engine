"use client";

import { useEffect, useState } from "react";
import {
  RotateCcw,
  Shuffle,
  Sparkles,
  Trophy,
  type LucideIcon,
} from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import {
  BracketMatch,
  BracketSimulation,
  ModelType,
  simulateBracket,
} from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";

const ROUND_ORDER = [
  "Round of 32",
  "Round of 16",
  "Quarter-finals",
  "Semi-finals",
  "Final",
];

export default function BracketPage() {
  const [modelType, setModelType] = useState<ModelType>("poisson");
  const [simulationMode, setSimulationMode] = useState<"favorite" | "random">(
    "favorite",
  );
  const [seed, setSeed] = useState(42);
  const [trace, setTrace] = useState<BracketSimulation | null>(null);
  const [revealedMatchIds, setRevealedMatchIds] = useState<Set<string>>(
    () => new Set(),
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    simulateBracket({ model_type: modelType, simulation_mode: simulationMode, seed })
      .then((data) => {
        if (isActive) {
          setTrace(data);
          setRevealedMatchIds(new Set());
          setError(null);
        }
      })
      .catch((caughtError: unknown) => {
        if (isActive) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Bracket simulation failed",
          );
        }
      });

    return () => {
      isActive = false;
    };
  }, [modelType, simulationMode, seed]);

  const finalMatch = trace?.rounds.Final?.[0] ?? null;
  const championRevealed =
    finalMatch !== null && revealedMatchIds.has(finalMatch.id);
  const revealedCount = revealedMatchIds.size;
  const totalMatches = trace
    ? ROUND_ORDER.reduce(
        (total, round) => total + (trace.rounds[round]?.length ?? 0),
        0,
      )
    : 0;

  function revealMatch(match: BracketMatch) {
    setRevealedMatchIds((current) => new Set(current).add(match.id));
  }

  function revealRound(round: string) {
    if (!trace) {
      return;
    }
    setRevealedMatchIds((current) => {
      const next = new Set(current);
      for (const match of trace.rounds[round] ?? []) {
        if (isMatchEligible(trace, match, next)) {
          next.add(match.id);
        }
      }
      return next;
    });
  }

  function revealAll() {
    if (!trace) {
      return;
    }
    setRevealedMatchIds(
      new Set(
        ROUND_ORDER.flatMap((round) =>
          (trace.rounds[round] ?? []).map((match) => match.id),
        ),
      ),
    );
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Bracket lab"
        title="Reveal the most likely World Cup path"
        description="Click through a deterministic favorite path by default, or switch to seeded random mode when you want chaos."
      />

      <div className="space-y-6">
        <section className="overflow-hidden rounded-lg border border-white/10 bg-[#080c13] shadow-[0_24px_80px_rgba(0,0,0,0.28)]">
          <div className="grid gap-4 border-b border-white/10 bg-[linear-gradient(135deg,rgba(57,255,136,0.12),rgba(110,168,255,0.06)_38%,rgba(8,12,19,0)_70%)] p-5 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <p className="text-xs font-semibold uppercase text-emerald-200">
                Simulation trace
              </p>
              <h2 className="mt-2 max-w-3xl text-3xl font-semibold text-white sm:text-4xl">
                {championRevealed && trace
                  ? `${trace.champion_team_name} wins this path.`
                  : simulationMode === "favorite"
                    ? "Most likely bracket locked. Start revealing."
                    : "Random bracket locked. Start revealing."}
              </h2>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-400">
                Favorite mode chooses the higher advance probability at every
                unresolved match. Random mode samples one seeded tournament trace.
              </p>
            </div>
            <div className="grid gap-2 sm:grid-cols-3 lg:min-w-[28rem]">
              <TraceStat
                icon={Sparkles}
                label="Model"
                value={modelType.toUpperCase()}
              />
              <TraceStat
                icon={Shuffle}
                label="Mode"
                value={simulationMode === "favorite" ? "Most likely" : `Seed ${formatNumber(seed)}`}
              />
              <TraceStat
                icon={Trophy}
                label="Revealed"
                value={`${revealedCount}/${totalMatches}`}
              />
            </div>
          </div>

          <div className="flex flex-col gap-3 p-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap gap-2">
              {(["favorite", "random"] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => {
                    if (mode === simulationMode) {
                      return;
                    }
                    setTrace(null);
                    setError(null);
                    setSimulationMode(mode);
                  }}
                  className={`rounded-md border px-3 py-2 text-sm font-semibold transition ${
                    simulationMode === mode
                      ? "border-sky-300/50 bg-sky-300 text-zinc-950"
                      : "border-white/10 bg-white/[0.05] text-zinc-300 hover:bg-white/[0.08]"
                  }`}
                >
                  {mode === "favorite" ? "Most likely" : "Random"}
                </button>
              ))}
              {(["poisson", "elo"] as ModelType[]).map((model) => (
                <button
                  key={model}
                  type="button"
                  onClick={() => {
                    if (model === modelType) {
                      return;
                    }
                    setTrace(null);
                    setError(null);
                    setModelType(model);
                  }}
                  className={`rounded-md border px-3 py-2 text-sm font-semibold transition ${
                    modelType === model
                      ? "border-emerald-300/50 bg-emerald-300 text-zinc-950"
                      : "border-white/10 bg-white/[0.05] text-zinc-300 hover:bg-white/[0.08]"
                  }`}
                >
                  {model.toUpperCase()}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              <ActionButton
                icon={RotateCcw}
                label="Reset"
                onClick={() => setRevealedMatchIds(new Set())}
              />
              <ActionButton
                icon={Shuffle}
                label="New seed"
                onClick={() => {
                  setTrace(null);
                  setError(null);
                  setSimulationMode("random");
                  setSeed((current) => current + 1);
                }}
              />
              <button
                type="button"
                onClick={revealAll}
                disabled={!trace}
                className="rounded-md bg-emerald-300 px-3 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-400"
              >
                Reveal all
              </button>
            </div>
          </div>
        </section>

        {error ? <ErrorState message={error} /> : null}
        {!error && !trace ? <LoadingState label="Building bracket trace" /> : null}

        {!error && trace ? (
          <BracketWall
            trace={trace}
            revealedMatchIds={revealedMatchIds}
            onRevealMatch={revealMatch}
            onRevealRound={revealRound}
          />
        ) : null}
      </div>
    </AppShell>
  );
}

function BracketWall({
  trace,
  revealedMatchIds,
  onRevealMatch,
  onRevealRound,
}: {
  trace: BracketSimulation;
  revealedMatchIds: Set<string>;
  onRevealMatch: (match: BracketMatch) => void;
  onRevealRound: (round: string) => void;
}) {
  return (
    <section className="overflow-x-auto rounded-lg border border-white/10 bg-[#070a10] p-4">
      <div className="grid min-w-[88rem] grid-cols-[repeat(5,minmax(16rem,1fr))] gap-4">
        {ROUND_ORDER.map((round) => {
          const matches = trace.rounds[round] ?? [];
          return (
            <div key={round} className="space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase text-zinc-500">
                    {matches.length} matches
                  </p>
                  <h2 className="text-sm font-semibold text-white">{round}</h2>
                </div>
                <button
                  type="button"
                  onClick={() => onRevealRound(round)}
                  className="rounded-md border border-white/10 bg-white/[0.05] px-2.5 py-1.5 text-xs font-semibold text-zinc-300 transition hover:bg-white/[0.08]"
                >
                  Reveal round
                </button>
              </div>
              <div className="space-y-3">
                {matches.map((match) => {
                  const revealed = revealedMatchIds.has(match.id);
                  const eligible = isMatchEligible(trace, match, revealedMatchIds);
                  return (
                    <BracketMatchCard
                      key={match.id}
                      match={match}
                      revealed={revealed}
                      eligible={eligible}
                      onReveal={() => onRevealMatch(match)}
                    />
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function BracketMatchCard({
  match,
  revealed,
  eligible,
  onReveal,
}: {
  match: BracketMatch;
  revealed: boolean;
  eligible: boolean;
  onReveal: () => void;
}) {
  const teamAWins = match.winner_team_id === match.team_a.team_id;
  const teamBWins = match.winner_team_id === match.team_b.team_id;

  return (
    <article
      className={`rounded-lg border p-3 transition ${
        revealed
          ? "border-emerald-300/35 bg-emerald-300/[0.08]"
          : eligible
            ? "border-white/15 bg-white/[0.055] hover:border-emerald-300/30"
            : "border-white/8 bg-white/[0.025] opacity-60"
      }`}
    >
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="text-xs font-semibold uppercase text-zinc-500">
          {match.id}
        </span>
        <span className="text-xs font-semibold text-zinc-500">
          {formatPercent(match.probabilities.team_a_advance, 0)} /{" "}
          {formatPercent(match.probabilities.team_b_advance, 0)}
        </span>
      </div>

      <TeamLine
        name={match.team_a.team_name}
        group={match.team_a.group_id}
        score={match.result.team_a_goals}
        revealed={revealed}
        winner={teamAWins}
      />
      <TeamLine
        name={match.team_b.team_name}
        group={match.team_b.group_id}
        score={match.result.team_b_goals}
        revealed={revealed}
        winner={teamBWins}
      />

      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full bg-emerald-300"
          style={{
            width: `${Math.round(match.probabilities.team_a_advance * 100)}%`,
          }}
        />
      </div>

      <button
        type="button"
        onClick={onReveal}
        disabled={!eligible || revealed}
        className="mt-3 w-full rounded-md border border-white/10 bg-white/[0.06] px-3 py-2 text-sm font-semibold text-zinc-100 transition hover:bg-white/[0.1] disabled:cursor-not-allowed disabled:text-zinc-500"
      >
        {revealed ? "Revealed" : eligible ? "Reveal match" : "Locked"}
      </button>
    </article>
  );
}

function TeamLine({
  name,
  group,
  score,
  revealed,
  winner,
}: {
  name: string;
  group: string;
  score: number;
  revealed: boolean;
  winner: boolean;
}) {
  return (
    <div
      className={`mt-2 grid grid-cols-[1fr_auto] items-center gap-3 rounded-md px-3 py-2 ${
        winner && revealed ? "bg-emerald-300 text-zinc-950" : "bg-black/20"
      }`}
    >
      <div className="min-w-0">
        <p
          className={`truncate text-sm font-semibold ${
            winner && revealed ? "text-zinc-950" : "text-zinc-100"
          }`}
        >
          {name}
        </p>
        <p
          className={`text-xs ${
            winner && revealed ? "text-zinc-800" : "text-zinc-500"
          }`}
        >
          Group {group}
        </p>
      </div>
      <span className="font-mono text-xl font-semibold tabular-nums">
        {revealed ? score : "-"}
      </span>
    </div>
  );
}

function TraceStat({
  icon: Icon,
  label,
  value,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-black/20 p-3">
      <Icon size={16} className="text-emerald-200" aria-hidden="true" />
      <p className="mt-2 text-xs font-semibold uppercase text-zinc-500">
        {label}
      </p>
      <p className="mt-1 text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

function ActionButton({
  icon: Icon,
  label,
  onClick,
}: {
  icon: LucideIcon;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.05] px-3 py-2 text-sm font-semibold text-zinc-300 transition hover:bg-white/[0.08]"
    >
      <Icon size={16} aria-hidden="true" />
      {label}
    </button>
  );
}

function isMatchEligible(
  trace: BracketSimulation,
  match: BracketMatch,
  revealedMatchIds: Set<string>,
): boolean {
  const roundIndex = ROUND_ORDER.indexOf(match.stage);
  if (roundIndex === 0) {
    return true;
  }

  const previousRound = ROUND_ORDER[roundIndex - 1];
  const previousMatches = trace.rounds[previousRound] ?? [];
  const firstFeeder = previousMatches[(match.match_number - 1) * 2];
  const secondFeeder = previousMatches[(match.match_number - 1) * 2 + 1];

  return Boolean(
    firstFeeder &&
      secondFeeder &&
      revealedMatchIds.has(firstFeeder.id) &&
      revealedMatchIds.has(secondFeeder.id),
  );
}
