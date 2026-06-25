"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Download,
  RotateCcw,
  Shuffle,
  Sparkles,
  Trophy,
  X,
  type LucideIcon,
} from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { ForecastRefreshControl } from "@/components/ForecastRefreshControl";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import {
  BracketMatch,
  BracketSimulation,
  DEFAULT_MODEL_TYPE,
  simulateBracket,
} from "@/lib/api";
import { formatModelLabel, formatNumber, formatPercent } from "@/lib/format";
import { useAutoForecast } from "@/hooks/useAutoForecast";

const ROUND_ORDER = [
  "Round of 32",
  "Round of 16",
  "Quarter-finals",
  "Semi-finals",
  "Final",
];

export default function BracketPage() {
  const [simulationMode, setSimulationMode] = useState<"favorite" | "random">(
    "favorite",
  );
  const [seed, setSeed] = useState(42);
  const [revealedMatchIds, setRevealedMatchIds] = useState<Set<string>>(
    () => new Set(),
  );
  const [selectedMatch, setSelectedMatch] = useState<BracketMatch | null>(null);

  const loadBracket = useCallback(
    () =>
      simulateBracket({
        model_type: DEFAULT_MODEL_TYPE,
        simulation_mode: simulationMode,
        seed,
      }),
    [seed, simulationMode],
  );
  const {
    data: trace,
    error,
    isRefreshing,
    lastRunAt,
    clear,
    refresh,
  } = useAutoForecast<BracketSimulation>(loadBracket);

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

  function revealHalf(side: "left" | "right") {
    if (!trace) {
      return;
    }
    const semifinals = trace.rounds["Semi-finals"] ?? [];
    const rootMatch = side === "left" ? semifinals[0] : semifinals[1];
    const matchIds = getAncestorMatchIds(trace, rootMatch);
    setRevealedMatchIds((current) => {
      const next = new Set(current);
      for (const round of ROUND_ORDER) {
        for (const match of trace.rounds[round] ?? []) {
          if (matchIds.has(match.id) && isMatchEligible(trace, match, next)) {
            next.add(match.id);
          }
        }
      }
      return next;
    });
  }

  function exportBracket() {
    if (!trace) {
      return;
    }
    const blob = new Blob([JSON.stringify(trace, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "world-cup-bracket.json";
    anchor.click();
    URL.revokeObjectURL(url);
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
                unresolved match. Random mode samples one seeded tournament
                trace.
              </p>
            </div>
            <div className="grid gap-2 sm:grid-cols-3 lg:min-w-[28rem]">
              <TraceStat
                icon={Sparkles}
                label="Model"
                value={formatModelLabel(DEFAULT_MODEL_TYPE)}
              />
              <TraceStat
                icon={Shuffle}
                label="Mode"
                value={
                  simulationMode === "favorite"
                    ? "Most likely"
                    : `Seed ${formatNumber(seed)}`
                }
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
                    clear();
                    setRevealedMatchIds(new Set());
                    setSelectedMatch(null);
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
                  clear();
                  setRevealedMatchIds(new Set());
                  setSelectedMatch(null);
                  setSimulationMode("random");
                  setSeed((current) => current + 1);
                }}
              />
              <ForecastRefreshControl
                isRefreshing={isRefreshing}
                lastRunAt={lastRunAt}
                onRefresh={refresh}
              />
              <ActionButton
                icon={Download}
                label="Export JSON"
                onClick={exportBracket}
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
        {!error && !trace ? (
          <LoadingState label="Building bracket trace" />
        ) : null}

        {!error && trace ? (
          <>
            <BracketWall
              trace={trace}
              revealedMatchIds={revealedMatchIds}
              onRevealMatch={revealMatch}
              onRevealRound={revealRound}
              onRevealHalf={revealHalf}
              onSelectMatch={setSelectedMatch}
            />
            {selectedMatch ? (
              <MatchDetailDrawer
                match={selectedMatch}
                onClose={() => setSelectedMatch(null)}
              />
            ) : null}
          </>
        ) : null}
      </div>
    </AppShell>
  );
}

function roundColumnWidth(round: string): string {
  return round === "Round of 32" ? "w-48" : "w-40";
}

function BracketWall({
  trace,
  revealedMatchIds,
  onRevealMatch,
  onRevealRound,
  onRevealHalf,
  onSelectMatch,
}: {
  trace: BracketSimulation;
  revealedMatchIds: Set<string>;
  onRevealMatch: (match: BracketMatch) => void;
  onRevealRound: (round: string) => void;
  onRevealHalf: (side: "left" | "right") => void;
  onSelectMatch: (match: BracketMatch) => void;
}) {
  const [mobileView, setMobileView] = useState<"left" | "final" | "right">(
    "left",
  );
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollRight, setCanScrollRight] = useState(false);

  useEffect(() => {
    const scroller = scrollRef.current;
    if (!scroller) {
      return;
    }

    function updateScrollState() {
      if (!scroller) {
        return;
      }
      const hasOverflow = scroller.scrollWidth > scroller.clientWidth + 1;
      const atEnd =
        scroller.scrollLeft + scroller.clientWidth >= scroller.scrollWidth - 1;
      setCanScrollRight(hasOverflow && !atEnd);
    }

    updateScrollState();
    scroller.addEventListener("scroll", updateScrollState, { passive: true });
    window.addEventListener("resize", updateScrollState);

    return () => {
      scroller.removeEventListener("scroll", updateScrollState);
      window.removeEventListener("resize", updateScrollState);
    };
  }, [trace]);
  const semifinals = trace.rounds["Semi-finals"] ?? [];
  const finalMatch = trace.rounds.Final?.[0] ?? null;
  const leftMatchIds = getAncestorMatchIds(trace, semifinals[0]);
  const rightMatchIds = getAncestorMatchIds(trace, semifinals[1]);
  const leftRounds = getHalfRounds(trace, leftMatchIds);
  const rightRounds = getHalfRounds(trace, rightMatchIds);

  return (
    <section className="rounded-lg border border-white/10 bg-[#05080b] p-3 shadow-[0_24px_80px_rgba(0,0,0,0.28)] sm:p-4">
      <div className="mb-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => onRevealHalf("left")}
          className="rounded-md border border-white/10 bg-white/[0.05] px-3 py-2 text-xs font-semibold text-zinc-300 transition hover:bg-white/[0.08]"
        >
          Reveal left half
        </button>
        <button
          type="button"
          onClick={() => onRevealHalf("right")}
          className="rounded-md border border-white/10 bg-white/[0.05] px-3 py-2 text-xs font-semibold text-zinc-300 transition hover:bg-white/[0.08]"
        >
          Reveal right half
        </button>
      </div>

      <div className="mb-4 flex rounded-md border border-white/10 bg-white/[0.03] p-1 lg:hidden">
        {(["left", "final", "right"] as const).map((view) => (
          <button
            key={view}
            type="button"
            onClick={() => setMobileView(view)}
            className={`flex-1 rounded px-3 py-2 text-xs font-semibold capitalize transition ${
              mobileView === view
                ? "bg-emerald-300 text-zinc-950"
                : "text-zinc-400 hover:bg-white/[0.06]"
            }`}
          >
            {view === "final" ? "Final" : `${view} half`}
          </button>
        ))}
      </div>

      <div className="lg:hidden">
        {mobileView === "left" ? (
          <MobileHalf
            trace={trace}
            rounds={leftRounds}
            revealedMatchIds={revealedMatchIds}
            onRevealMatch={onRevealMatch}
            onRevealRound={onRevealRound}
            onSelectMatch={onSelectMatch}
          />
        ) : null}
        {mobileView === "right" ? (
          <MobileHalf
            trace={trace}
            rounds={rightRounds}
            revealedMatchIds={revealedMatchIds}
            onRevealMatch={onRevealMatch}
            onRevealRound={onRevealRound}
            onSelectMatch={onSelectMatch}
          />
        ) : null}
        {mobileView === "final" && finalMatch ? (
          <BracketMatchCard
            trace={trace}
            match={finalMatch}
            revealed={revealedMatchIds.has(finalMatch.id)}
            eligible={isMatchEligible(trace, finalMatch, revealedMatchIds)}
            revealedMatchIds={revealedMatchIds}
            onReveal={() => onRevealMatch(finalMatch)}
            onSelect={() => onSelectMatch(finalMatch)}
          />
        ) : null}
      </div>

      <div className="relative hidden lg:block">
        <div
          ref={scrollRef}
          className="overflow-x-auto pb-2 [scrollbar-width:thin]"
        >
          <div className="flex min-h-[42rem] w-max gap-3 pr-2">
            {["Round of 32", "Round of 16", "Quarter-finals", "Semi-finals"].map(
              (round) => (
                <div
                  key={`left-${round}`}
                  className={`shrink-0 ${roundColumnWidth(round)}`}
                >
                  <BracketRoundColumn
                    trace={trace}
                    round={round}
                    matches={leftRounds[round] ?? []}
                    revealedMatchIds={revealedMatchIds}
                    onRevealMatch={onRevealMatch}
                    onRevealRound={onRevealRound}
                    onSelectMatch={onSelectMatch}
                  />
                </div>
              ),
            )}

            <div className="relative flex w-44 shrink-0 flex-col justify-center">
              <div className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-[linear-gradient(to_bottom,transparent,rgba(47,209,124,0.65),transparent)]" />
              <div className="relative rounded-lg border border-amber-300/25 bg-[#10100a] p-3 shadow-[0_0_40px_rgba(242,184,75,0.08)]">
                <p className="mb-3 text-center text-xs font-semibold uppercase text-amber-200">
                  Final
                </p>
                {finalMatch ? (
                  <BracketMatchCard
                    trace={trace}
                    match={finalMatch}
                    revealed={revealedMatchIds.has(finalMatch.id)}
                    eligible={isMatchEligible(trace, finalMatch, revealedMatchIds)}
                    revealedMatchIds={revealedMatchIds}
                    onReveal={() => onRevealMatch(finalMatch)}
                    onSelect={() => onSelectMatch(finalMatch)}
                  />
                ) : null}
              </div>
            </div>

            {["Semi-finals", "Quarter-finals", "Round of 16", "Round of 32"].map(
              (round) => (
                <div
                  key={`right-${round}`}
                  className={`shrink-0 ${roundColumnWidth(round)}`}
                >
                  <BracketRoundColumn
                    trace={trace}
                    round={round}
                    matches={rightRounds[round] ?? []}
                    revealedMatchIds={revealedMatchIds}
                    onRevealMatch={onRevealMatch}
                    onRevealRound={onRevealRound}
                    onSelectMatch={onSelectMatch}
                  />
                </div>
              ),
            )}
          </div>
        </div>
        {canScrollRight ? (
          <div
            className="pointer-events-none absolute inset-y-0 right-0 w-12 bg-gradient-to-l from-[#05080b] via-[#05080b]/80 to-transparent"
            aria-hidden="true"
          />
        ) : null}
      </div>
    </section>
  );
}

function MobileHalf({
  trace,
  rounds,
  revealedMatchIds,
  onRevealMatch,
  onRevealRound,
  onSelectMatch,
}: {
  trace: BracketSimulation;
  rounds: Record<string, BracketMatch[]>;
  revealedMatchIds: Set<string>;
  onRevealMatch: (match: BracketMatch) => void;
  onRevealRound: (round: string) => void;
  onSelectMatch: (match: BracketMatch) => void;
}) {
  return (
    <div className="space-y-4">
      {["Round of 32", "Round of 16", "Quarter-finals", "Semi-finals"].map(
        (round) => (
          <BracketRoundColumn
            key={round}
            trace={trace}
            round={round}
            matches={rounds[round] ?? []}
            revealedMatchIds={revealedMatchIds}
            onRevealMatch={onRevealMatch}
            onRevealRound={onRevealRound}
            onSelectMatch={onSelectMatch}
          />
        ),
      )}
    </div>
  );
}

function BracketRoundColumn({
  trace,
  round,
  matches,
  revealedMatchIds,
  onRevealMatch,
  onRevealRound,
  onSelectMatch,
}: {
  trace: BracketSimulation;
  round: string;
  matches: BracketMatch[];
  revealedMatchIds: Set<string>;
  onRevealMatch: (match: BracketMatch) => void;
  onRevealRound: (round: string) => void;
  onSelectMatch: (match: BracketMatch) => void;
}) {
  return (
    <div className="min-w-0 space-y-3">
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
          className="rounded-md border border-white/10 bg-white/[0.05] px-2 py-1.5 text-[0.68rem] font-semibold text-zinc-300 transition hover:bg-white/[0.08]"
        >
          Reveal
        </button>
      </div>
      <div className="space-y-3">
        {matches.map((match) => {
          const revealed = revealedMatchIds.has(match.id);
          const eligible = isMatchEligible(trace, match, revealedMatchIds);
          return (
            <BracketMatchCard
              key={match.id}
              trace={trace}
              match={match}
              revealed={revealed}
              eligible={eligible}
              revealedMatchIds={revealedMatchIds}
              onReveal={() => onRevealMatch(match)}
              onSelect={() => onSelectMatch(match)}
            />
          );
        })}
      </div>
    </div>
  );
}

function BracketMatchCard({
  trace,
  match,
  revealed,
  eligible,
  revealedMatchIds,
  onReveal,
  onSelect,
}: {
  trace: BracketSimulation;
  match: BracketMatch;
  revealed: boolean;
  eligible: boolean;
  revealedMatchIds: Set<string>;
  onReveal: () => void;
  onSelect: () => void;
}) {
  const [teamASide, teamBSide] = getDisplaySides(
    trace,
    match,
    revealedMatchIds,
    revealed,
  );
  const teamAWins = match.winner_team_id === match.team_a.team_id;
  const teamBWins = match.winner_team_id === match.team_b.team_id;
  const showOdds = eligible || revealed;

  return (
    <article
      className={`rounded-md border p-2.5 transition sm:p-3 lg:p-2.5 xl:p-3 ${
        match.confirmed
          ? "border-emerald-400/50 bg-emerald-400/[0.08] ring-1 ring-emerald-400/30"
          : revealed
          ? "border-emerald-300/35 bg-emerald-300/[0.08]"
          : eligible
            ? "border-dashed border-white/20 bg-white/[0.04] hover:border-emerald-300/30"
            : "border-dashed border-white/8 bg-white/[0.02] opacity-60"
      }`}
    >
      <button
        type="button"
        onClick={onSelect}
        className="w-full text-left"
      >
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="text-[0.68rem] font-semibold uppercase text-zinc-500">
          {match.id}
        </span>
        <span className="text-right text-[0.68rem] font-semibold text-zinc-500">
          {match.confirmed ? (
            <span className="rounded border border-emerald-400/30 bg-emerald-400/10 px-1.5 py-0.5 text-emerald-200">
              Confirmed
            </span>
          ) : (
            <span className="rounded border border-white/10 bg-white/[0.05] px-1.5 py-0.5 text-zinc-400">
              Projected
            </span>
          )}
        </span>
      </div>
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="text-[0.68rem] font-semibold uppercase text-zinc-500">
          Advance odds
        </span>
        <span className="text-right text-[0.68rem] font-semibold text-zinc-500">
          {showOdds
            ? `${formatPercent(match.probabilities.team_a_advance, 0)} / ${formatPercent(match.probabilities.team_b_advance, 0)}`
            : "Path locked"}
        </span>
      </div>

      {showOdds ? (
        <div className="mb-2 flex items-center justify-between gap-2 text-[0.68rem] text-zinc-500">
          <span className="capitalize text-amber-200/80">
            {match.confidence_label ?? "projection"}
          </span>
          <span>
            xG {formatExpectedGoals(match.team_a_expected_goals)}-
            {formatExpectedGoals(match.team_b_expected_goals)}
          </span>
        </div>
      ) : null}

      <TeamLine
        name={teamASide.name}
        group={teamASide.group}
        score={match.result.team_a_goals}
        revealed={revealed}
        winner={!teamASide.placeholder && teamAWins}
        placeholder={teamASide.placeholder}
      />
      <TeamLine
        name={teamBSide.name}
        group={teamBSide.group}
        score={match.result.team_b_goals}
        revealed={revealed}
        winner={!teamBSide.placeholder && teamBWins}
        placeholder={teamBSide.placeholder}
      />

      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
        <div
          className={`h-full ${showOdds ? "bg-emerald-300" : "bg-zinc-700"}`}
          style={{
            width: showOdds
              ? `${Math.round(match.probabilities.team_a_advance * 100)}%`
              : "0%",
          }}
        />
      </div>
      </button>

      <button
        type="button"
        onClick={onReveal}
        disabled={!eligible || revealed}
        className="mt-3 w-full rounded-md border border-white/10 bg-white/[0.06] px-2.5 py-2 text-xs font-semibold text-zinc-100 transition hover:bg-white/[0.1] disabled:cursor-not-allowed disabled:text-zinc-500 xl:text-sm"
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
  placeholder,
}: {
  name: string;
  group: string | null;
  score: number;
  revealed: boolean;
  winner: boolean;
  placeholder: boolean;
}) {
  return (
    <div
      className={`mt-2 grid grid-cols-[minmax(0,1fr)_auto] items-center gap-2 rounded-md px-2.5 py-2 ${
        winner && revealed ? "bg-emerald-300 text-zinc-950" : "bg-black/20"
      }`}
    >
      <div className="min-w-0">
        <p
          className={`truncate text-xs font-semibold xl:text-sm ${
            winner && revealed
              ? "text-zinc-950"
              : placeholder
                ? "text-zinc-500"
                : "text-zinc-100"
          }`}
        >
          {name}
        </p>
        <p
          className={`text-[0.68rem] ${
            winner && revealed ? "text-zinc-800" : "text-zinc-500"
          }`}
        >
          {group ? `Group ${group}` : "Awaiting reveal"}
        </p>
      </div>
      <span className="font-mono text-lg font-semibold tabular-nums xl:text-xl">
        {revealed && !placeholder ? score : "-"}
      </span>
    </div>
  );
}

type DisplaySide = {
  name: string;
  group: string | null;
  placeholder: boolean;
};

function getAncestorMatchIds(
  trace: BracketSimulation,
  rootMatch?: BracketMatch,
): Set<string> {
  const matchesById = getMatchesById(trace);
  const ids = new Set<string>();

  function visit(match?: BracketMatch) {
    if (!match || ids.has(match.id)) {
      return;
    }
    ids.add(match.id);
    for (const sourceId of match.source_match_ids) {
      visit(matchesById.get(sourceId));
    }
  }

  visit(rootMatch);
  return ids;
}

function getHalfRounds(
  trace: BracketSimulation,
  matchIds: Set<string>,
): Record<string, BracketMatch[]> {
  return Object.fromEntries(
    ROUND_ORDER.filter((round) => round !== "Final").map((round) => [
      round,
      (trace.rounds[round] ?? []).filter((match) => matchIds.has(match.id)),
    ]),
  );
}

function getMatchesById(trace: BracketSimulation): Map<string, BracketMatch> {
  return new Map(
    ROUND_ORDER.flatMap((round) => trace.rounds[round] ?? []).map(
      (sourceMatch) => [sourceMatch.id, sourceMatch],
    ),
  );
}

function getDisplaySides(
  trace: BracketSimulation,
  match: BracketMatch,
  revealedMatchIds: Set<string>,
  revealed: boolean,
): [DisplaySide, DisplaySide] {
  const roundIndex = ROUND_ORDER.indexOf(match.stage);
  if (roundIndex === 0 || revealed) {
    return [toDisplaySide(match.team_a), toDisplaySide(match.team_b)];
  }

  const [firstFeeder, secondFeeder] = getFeederMatches(trace, match);
  return [
    getFeederSide(firstFeeder, match.team_a, revealedMatchIds),
    getFeederSide(secondFeeder, match.team_b, revealedMatchIds),
  ];
}

function getFeederSide(
  feeder: BracketMatch | null,
  team: BracketMatch["team_a"],
  revealedMatchIds: Set<string>,
): DisplaySide {
  if (feeder && revealedMatchIds.has(feeder.id)) {
    return toDisplaySide(team);
  }

  return {
    name: feeder ? `Winner ${feeder.id}` : "Winner previous match",
    group: null,
    placeholder: true,
  };
}

function toDisplaySide(team: BracketMatch["team_a"]): DisplaySide {
  return {
    name: team.team_name,
    group: team.group_id,
    placeholder: false,
  };
}

function formatExpectedGoals(value: number | null): string {
  return value === null ? "-" : value.toFixed(1);
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

  const [firstFeeder, secondFeeder] = getFeederMatches(trace, match);

  return Boolean(
    firstFeeder &&
    secondFeeder &&
    revealedMatchIds.has(firstFeeder.id) &&
    revealedMatchIds.has(secondFeeder.id),
  );
}

function getFeederMatches(
  trace: BracketSimulation,
  match: BracketMatch,
): [BracketMatch | null, BracketMatch | null] {
  if (match.source_match_ids.length === 0) {
    return [null, null];
  }

  const matchesById = getMatchesById(trace);
  const [firstSourceId, secondSourceId] = match.source_match_ids;
  return [
    firstSourceId ? matchesById.get(firstSourceId) ?? null : null,
    secondSourceId ? matchesById.get(secondSourceId) ?? null : null,
  ];
}

function MatchDetailDrawer({
  match,
  onClose,
}: {
  match: BracketMatch;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-4 sm:items-center">
      <div className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-lg border border-white/10 bg-[#101722] p-5 shadow-[0_24px_80px_rgba(0,0,0,0.45)]">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase text-[var(--var-blue)]">
              {match.stage} · {match.id}
            </p>
            <h2 className="mt-1 text-xl font-semibold text-white">
              {match.team_a.team_name} vs {match.team_b.team_name}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-white/10 p-2 text-zinc-300 hover:bg-white/[0.06]"
            aria-label="Close match details"
          >
            <X size={16} />
          </button>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <DetailMetric
            label="Team A advance"
            value={formatPercent(match.probabilities.team_a_advance)}
          />
          <DetailMetric
            label="Team B advance"
            value={formatPercent(match.probabilities.team_b_advance)}
          />
          <DetailMetric
            label="Expected goals"
            value={`${formatExpectedGoals(match.team_a_expected_goals)} - ${formatExpectedGoals(match.team_b_expected_goals)}`}
          />
          <DetailMetric
            label="Confidence"
            value={match.confidence_label ?? "Projection"}
          />
        </div>

        {match.drivers.length > 0 ? (
          <div className="mt-5">
            <h3 className="text-xs font-semibold uppercase text-zinc-500">
              Model drivers
            </h3>
            <ul className="mt-2 space-y-2 text-sm leading-6 text-zinc-300">
              {match.drivers.map((driver) => (
                <li key={driver}>• {driver}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="mt-5 rounded-md border border-white/10 bg-black/20 p-3 text-sm text-zinc-300">
          Ratings: {match.team_a.team_name} {formatNumber(match.team_a.rating)} ·{" "}
          {match.team_b.team_name} {formatNumber(match.team_b.rating)}
        </div>
      </div>
    </div>
  );
}

function DetailMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-white/[0.04] px-3 py-3">
      <p className="text-xs uppercase text-zinc-500">{label}</p>
      <p className="mt-1 font-semibold text-white">{value}</p>
    </div>
  );
}
