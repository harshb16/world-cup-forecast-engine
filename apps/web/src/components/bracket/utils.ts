import type { BracketMatch, BracketSimulation } from "@/lib/api";

import { ROUND_ORDER } from "./constants";

export type DisplaySide = {
  name: string;
  group: string | null;
  placeholder: boolean;
};

export function getMatchesById(
  trace: BracketSimulation,
): Map<string, BracketMatch> {
  return new Map(
    ROUND_ORDER.flatMap((round) => trace.rounds[round] ?? []).map((match) => [
      match.id,
      match,
    ]),
  );
}

export function getAncestorMatchIds(
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

export function getHalfRounds(
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

export function getFeederMatches(
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

export function isMatchEligible(
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

export function toDisplaySide(team: BracketMatch["team_a"]): DisplaySide {
  return {
    name: team.team_name,
    group: team.group_id,
    placeholder: false,
  };
}

export function getDisplaySides(
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

export function teamInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return `${parts[0][0] ?? ""}${parts[parts.length - 1][0] ?? ""}`.toUpperCase();
  }
  return name.slice(0, 3).toUpperCase();
}

export function gridClassForMatchCount(count: number): string {
  if (count <= 1) {
    return "grid-cols-1 max-w-xs mx-auto";
  }
  if (count === 2) {
    return "grid-cols-2 max-w-md mx-auto";
  }
  if (count <= 4) {
    return "grid-cols-2 sm:grid-cols-2";
  }
  return "grid-cols-2 sm:grid-cols-4";
}

export function formatExpectedGoals(value: number | null): string {
  return value === null ? "-" : value.toFixed(1);
}
