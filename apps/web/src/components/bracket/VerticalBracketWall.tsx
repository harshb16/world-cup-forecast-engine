"use client";

import { Trophy } from "lucide-react";

import type { BracketMatch, BracketSimulation } from "@/lib/api";
import { cn } from "@/lib/utils";

import { KNOCKOUT_ROUNDS, ROUND_SHORT_LABEL } from "./constants";
import { KnockoutMatchCard } from "./KnockoutMatchCard";
import {
  getAncestorMatchIds,
  getHalfRounds,
  gridClassForMatchCount,
  isMatchEligible,
} from "./utils";

type BracketWallProps = {
  trace: BracketSimulation;
  revealedMatchIds: Set<string>;
  onRevealMatch: (match: BracketMatch) => void;
  onRevealRound: (round: string) => void;
  onRevealHalf: (side: "left" | "right") => void;
  onSelectMatch: (match: BracketMatch) => void;
};

export function VerticalBracketWall({
  trace,
  revealedMatchIds,
  onRevealMatch,
  onRevealRound,
  onRevealHalf,
  onSelectMatch,
}: BracketWallProps) {
  const semifinals = trace.rounds["Semi-finals"] ?? [];
  const finalMatch = trace.rounds.Final?.[0] ?? null;
  const leftMatchIds = getAncestorMatchIds(trace, semifinals[0]);
  const rightMatchIds = getAncestorMatchIds(trace, semifinals[1]);
  const leftRounds = getHalfRounds(trace, leftMatchIds);
  const rightRounds = getHalfRounds(trace, rightMatchIds);
  const championRevealed =
    finalMatch !== null && revealedMatchIds.has(finalMatch.id);

  return (
    <section className="surface-panel overflow-hidden p-4 sm:p-5">
      <div className="mb-5 flex flex-wrap gap-2">
        <HalfRevealButton label="Reveal top half" onClick={() => onRevealHalf("left")} />
        <HalfRevealButton label="Reveal bottom half" onClick={() => onRevealHalf("right")} />
      </div>

      <div className="mx-auto w-full max-w-2xl overflow-x-hidden">
        <BracketHalf
          label="Top half"
          rounds={[...KNOCKOUT_ROUNDS]}
          roundMatches={leftRounds}
          trace={trace}
          revealedMatchIds={revealedMatchIds}
          onRevealMatch={onRevealMatch}
          onRevealRound={onRevealRound}
          onSelectMatch={onSelectMatch}
        />

        <FinalPodium
          trace={trace}
          finalMatch={finalMatch}
          championName={trace.champion_team_name}
          championRevealed={championRevealed}
          revealedMatchIds={revealedMatchIds}
          onRevealMatch={onRevealMatch}
          onSelectMatch={onSelectMatch}
        />

        <BracketHalf
          label="Bottom half"
          rounds={[...KNOCKOUT_ROUNDS].reverse()}
          roundMatches={rightRounds}
          trace={trace}
          revealedMatchIds={revealedMatchIds}
          onRevealMatch={onRevealMatch}
          onRevealRound={onRevealRound}
          onSelectMatch={onSelectMatch}
          className="mt-2"
        />
      </div>
    </section>
  );
}

function HalfRevealButton({
  label,
  onClick,
}: {
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-md border border-border bg-accent/50 px-3 py-2 text-xs font-semibold text-muted-foreground transition hover:bg-accent/80 hover:text-foreground"
    >
      {label}
    </button>
  );
}

function BracketHalf({
  label,
  rounds,
  roundMatches,
  trace,
  revealedMatchIds,
  onRevealMatch,
  onRevealRound,
  onSelectMatch,
  className,
}: {
  label: string;
  rounds: readonly string[];
  roundMatches: Record<string, BracketMatch[]>;
  trace: BracketSimulation;
  revealedMatchIds: Set<string>;
  onRevealMatch: (match: BracketMatch) => void;
  onRevealRound: (round: string) => void;
  onSelectMatch: (match: BracketMatch) => void;
  className?: string;
}) {
  const visibleRounds = rounds.filter(
    (round) => (roundMatches[round] ?? []).length > 0,
  );

  if (visibleRounds.length === 0) {
    return null;
  }

  return (
    <div className={cn("flex flex-col items-stretch", className)}>
      <p className="mb-3 text-center font-mono text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
        {label}
      </p>

      {visibleRounds.map((round, index) => {
        const matches = roundMatches[round] ?? [];
        return (
          <div key={`${label}-${round}`} className="w-full">
            <RoundSection
              round={round}
              matches={matches}
              trace={trace}
              revealedMatchIds={revealedMatchIds}
              onRevealRound={onRevealRound}
              onRevealMatch={onRevealMatch}
              onSelectMatch={onSelectMatch}
            />
            {index < visibleRounds.length - 1 ? <BracketConnector /> : null}
          </div>
        );
      })}
    </div>
  );
}

function RoundSection({
  round,
  matches,
  trace,
  revealedMatchIds,
  onRevealRound,
  onRevealMatch,
  onSelectMatch,
}: {
  round: string;
  matches: BracketMatch[];
  trace: BracketSimulation;
  revealedMatchIds: Set<string>;
  onRevealRound: (round: string) => void;
  onRevealMatch: (match: BracketMatch) => void;
  onSelectMatch: (match: BracketMatch) => void;
}) {
  return (
    <div className="w-full">
      <div className="mb-2 flex items-center justify-between gap-2 px-1">
        <div>
          <p className="font-mono text-[0.65rem] font-semibold uppercase tracking-widest text-primary">
            {ROUND_SHORT_LABEL[round] ?? round}
          </p>
          <h3 className="text-sm font-semibold text-foreground">{round}</h3>
        </div>
        <button
          type="button"
          onClick={() => onRevealRound(round)}
          className="rounded-md border border-border bg-accent/40 px-2 py-1 text-[0.65rem] font-semibold text-muted-foreground transition hover:bg-accent/70 hover:text-foreground"
        >
          Reveal round
        </button>
      </div>

      <div className={cn("grid gap-2", gridClassForMatchCount(matches.length))}>
        {matches.map((match) => {
          const revealed = revealedMatchIds.has(match.id);
          const eligible = isMatchEligible(trace, match, revealedMatchIds);
          return (
            <KnockoutMatchCard
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

function BracketConnector() {
  return (
    <div className="flex justify-center py-2" aria-hidden="true">
      <div className="flex flex-col items-center">
        <div className="h-3 w-px bg-border" />
        <div className="size-1.5 rounded-full bg-border" />
        <div className="h-3 w-px bg-border" />
      </div>
    </div>
  );
}

function FinalPodium({
  trace,
  finalMatch,
  championName,
  championRevealed,
  revealedMatchIds,
  onRevealMatch,
  onSelectMatch,
}: {
  trace: BracketSimulation;
  finalMatch: BracketMatch | null;
  championName: string;
  championRevealed: boolean;
  revealedMatchIds: Set<string>;
  onRevealMatch: (match: BracketMatch) => void;
  onSelectMatch: (match: BracketMatch) => void;
}) {
  if (!finalMatch) {
    return null;
  }

  const revealed = revealedMatchIds.has(finalMatch.id);
  const eligible = isMatchEligible(trace, finalMatch, revealedMatchIds);

  return (
    <div className="relative my-6 py-4">
      <div
        className="pointer-events-none absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-gradient-to-b from-transparent via-primary/45 to-transparent"
        aria-hidden="true"
      />

      <div className="mx-auto flex max-w-lg flex-col items-center gap-5 sm:flex-row sm:items-stretch sm:justify-center">
        <div className="w-full max-w-xs sm:flex-1">
          <KnockoutMatchCard
            trace={trace}
            match={finalMatch}
            revealed={revealed}
            eligible={eligible}
            revealedMatchIds={revealedMatchIds}
            onReveal={() => onRevealMatch(finalMatch)}
            onSelect={() => onSelectMatch(finalMatch)}
            variant="final"
          />
        </div>

        <div className="flex w-full max-w-[10rem] flex-col items-center justify-center rounded-xl border border-border/80 bg-muted/30 px-4 py-5 text-center sm:w-auto">
          <div
            className={cn(
              "flex size-14 items-center justify-center rounded-full border",
              championRevealed
                ? "border-signal-amber/40 bg-signal-amber/10 text-signal-amber"
                : "border-border bg-muted text-muted-foreground",
            )}
          >
            <Trophy className="size-7" aria-hidden="true" />
          </div>
          <p className="mt-3 font-mono text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Champion
          </p>
          <p
            className={cn(
              "mt-1 text-sm font-semibold leading-snug",
              championRevealed ? "text-foreground" : "text-muted-foreground",
            )}
          >
            {championRevealed ? championName : "Reveal the final"}
          </p>
        </div>
      </div>
    </div>
  );
}
