"use client";

import type { BracketMatch, BracketSimulation } from "@/lib/api";
import { formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

import { Badge } from "@/components/ui/badge";

import {
  type DisplaySide,
  formatExpectedGoals,
  getDisplaySides,
  teamInitials,
} from "./utils";

export function KnockoutMatchCard({
  trace,
  match,
  revealed,
  eligible,
  revealedMatchIds,
  onReveal,
  onSelect,
  variant = "default",
}: {
  trace: BracketSimulation;
  match: BracketMatch;
  revealed: boolean;
  eligible: boolean;
  revealedMatchIds: Set<string>;
  onReveal: () => void;
  onSelect: () => void;
  variant?: "default" | "final";
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
  const locked = !eligible && !revealed;

  return (
    <article
      className={cn(
        "relative overflow-hidden rounded-xl border bg-card/90 transition",
        match.confirmed && "border-primary/40 ring-1 ring-primary/20",
        variant === "final" && "border-signal-amber/35 ring-1 ring-signal-amber/15",
        revealed && variant !== "final" && "border-primary/30",
        locked && "border-border/70 opacity-75",
        !locked && !revealed && "border-border hover:border-primary/25",
      )}
    >
      <button
        type="button"
        onClick={onSelect}
        className="w-full px-3 py-2.5 text-left"
      >
        {variant === "final" ? (
          <div className="mb-2 flex justify-center">
            <Badge className="bg-signal-amber/15 text-signal-amber hover:bg-signal-amber/15">
              FINAL
            </Badge>
          </div>
        ) : null}

        <TeamRow
          side={teamASide}
          score={match.result.team_a_goals}
          revealed={revealed}
          winner={!teamASide.placeholder && teamAWins}
        />
        <div className="my-1.5 border-t border-border/50" />
        <TeamRow
          side={teamBSide}
          score={match.result.team_b_goals}
          revealed={revealed}
          winner={!teamBSide.placeholder && teamBWins}
        />

        {showOdds ? (
          <p className="mt-2 text-center font-mono text-[0.65rem] tabular-nums text-muted-foreground">
            {formatPercent(match.probabilities.team_a_advance, 0)} ·{" "}
            {formatPercent(match.probabilities.team_b_advance, 0)}
            {match.team_a_expected_goals !== null ? (
              <>
                {" "}
                · xG {formatExpectedGoals(match.team_a_expected_goals)}-
                {formatExpectedGoals(match.team_b_expected_goals)}
              </>
            ) : null}
          </p>
        ) : (
          <p className="mt-2 text-center text-[0.65rem] text-muted-foreground">
            Awaiting feeder matches
          </p>
        )}
      </button>

      {!match.confirmed ? (
        <button
          type="button"
          onClick={onReveal}
          disabled={!eligible || revealed}
          className="w-full border-t border-border/60 bg-accent/30 px-3 py-2 text-xs font-semibold text-foreground transition hover:bg-accent/60 disabled:cursor-not-allowed disabled:text-muted-foreground"
        >
          {revealed ? "Revealed" : eligible ? "Reveal" : "Locked"}
        </button>
      ) : (
        <div className="border-t border-border/60 bg-primary/10 px-3 py-1.5 text-center text-[0.65rem] font-semibold uppercase tracking-wider text-primary">
          Confirmed
        </div>
      )}
    </article>
  );
}

function TeamRow({
  side,
  score,
  revealed,
  winner,
}: {
  side: DisplaySide;
  score: number;
  revealed: boolean;
  winner: boolean;
}) {
  const displayName = side.placeholder ? "TBD" : side.name;

  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-lg px-1.5 py-1",
        winner && revealed && "bg-primary text-primary-foreground",
      )}
    >
      <span
        className={cn(
          "flex size-7 shrink-0 items-center justify-center rounded-full text-[0.6rem] font-bold uppercase",
          winner && revealed
            ? "bg-primary-foreground/15 text-primary-foreground"
            : "bg-muted text-muted-foreground",
        )}
      >
        {side.placeholder ? "?" : teamInitials(side.name)}
      </span>
      <div className="min-w-0 flex-1">
        <p
          className={cn(
            "truncate text-xs font-semibold",
            winner && revealed ? "text-primary-foreground" : "text-foreground",
            side.placeholder && "text-muted-foreground",
          )}
        >
          {displayName}
        </p>
        {side.group ? (
          <p
            className={cn(
              "text-[0.6rem] uppercase tracking-wide",
              winner && revealed
                ? "text-primary-foreground/80"
                : "text-muted-foreground",
            )}
          >
            {side.group}
          </p>
        ) : null}
      </div>
      <span
        className={cn(
          "font-mono text-sm font-semibold tabular-nums",
          winner && revealed ? "text-primary-foreground" : "text-foreground",
        )}
      >
        {revealed && !side.placeholder ? score : "-"}
      </span>
    </div>
  );
}
