"use client";

import { useCallback, useState } from "react";
import {
  Download,
  RotateCcw,
  Shuffle,
  Sparkles,
  Trophy,
  type LucideIcon,
} from "lucide-react";

import { ErrorState } from "@/components/ErrorState";
import { ForecastRefreshControl } from "@/components/ForecastRefreshControl";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { SyncResultsControl } from "@/components/SyncResultsControl";
import { Button } from "@/components/ui/button";
import {
  BracketMatch,
  DEFAULT_MODEL_TYPE,
  fetchLatestForecast,
  simulateBracket,
} from "@/lib/api";
import { formatModelLabel, formatNumber } from "@/lib/format";
import { usePublishedForecast } from "@/hooks/usePublishedForecast";
import { cn } from "@/lib/utils";

import { ROUND_ORDER } from "./constants";
import { MatchDetailDrawer } from "./MatchDetailDrawer";
import { VerticalBracketWall } from "./VerticalBracketWall";
import {
  getAncestorMatchIds,
  isMatchEligible,
} from "./utils";

export function BracketExperience() {
  const [simulationMode, setSimulationMode] = useState<"favorite" | "random">(
    "favorite",
  );
  const [seed, setSeed] = useState(42);
  const [revealedMatchIds, setRevealedMatchIds] = useState<Set<string>>(
    () => new Set(),
  );
  const [selectedMatch, setSelectedMatch] = useState<BracketMatch | null>(null);

  const loadBracket = useCallback(async () => {
    if (simulationMode === "favorite") {
      const snapshot = await fetchLatestForecast();
      return snapshot.bracket;
    }
    return simulateBracket({
      model_type: DEFAULT_MODEL_TYPE,
      simulation_mode: "random",
      seed,
    });
  }, [seed, simulationMode]);

  const {
    data: trace,
    error,
    isRefreshing,
    lastRunAt,
    clear,
    refresh,
  } = usePublishedForecast(loadBracket);

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
    <>
      <PageHeader
        eyebrow="Bracket lab"
        title="Reveal the most likely World Cup path"
        description="A vertical knockout tree — scroll down through the bracket, no sideways panning required."
      />

      <div className="flex flex-col gap-6">
        <section className="surface-hero overflow-hidden rounded-xl border border-border/80">
          <div className="grid gap-4 border-b border-border/80 p-5 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <p className="text-eyebrow">Simulation trace</p>
              <h2 className="mt-2 max-w-3xl text-2xl font-semibold text-foreground sm:text-3xl">
                {championRevealed && trace
                  ? `${trace.champion_team_name} wins this path.`
                  : simulationMode === "favorite"
                    ? "Most likely bracket locked. Start revealing."
                    : "Random bracket locked. Start revealing."}
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                Favorite mode picks the higher advance probability each match.
                Random mode samples one seeded tournament trace.
              </p>
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
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
                  className={cn(
                    "rounded-md border px-3 py-2 text-sm font-semibold transition",
                    simulationMode === mode
                      ? "border-chart-2/50 bg-chart-2/20 text-foreground"
                      : "border-border bg-accent/50 text-muted-foreground hover:bg-accent/80",
                  )}
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
              <SyncResultsControl onSynced={refresh} />
              <ActionButton
                icon={Download}
                label="Export"
                onClick={exportBracket}
              />
              <Button
                type="button"
                onClick={revealAll}
                disabled={!trace}
                size="sm"
              >
                Reveal all
              </Button>
            </div>
          </div>
        </section>

        {error ? <ErrorState message={error} /> : null}
        {!error && !trace ? (
          <LoadingState label="Loading forecast bracket" />
        ) : null}

        {!error && trace ? (
          <>
            <VerticalBracketWall
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
    </>
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
    <div className="rounded-lg border border-border/80 bg-card/60 p-3">
      <Icon className="text-primary" aria-hidden="true" />
      <p className="mt-2 text-xs font-semibold uppercase text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-lg font-semibold text-foreground">{value}</p>
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
      className="inline-flex items-center gap-2 rounded-md border border-border bg-accent/50 px-3 py-2 text-sm font-semibold text-muted-foreground transition hover:bg-accent/80 hover:text-foreground"
    >
      <Icon aria-hidden="true" />
      {label}
    </button>
  );
}
