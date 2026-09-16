import type { BracketMatch, Match, MatchResultOverride } from "@/lib/api";

const KNOCKOUT_STAGE_ORDER = [
  "Round of 32",
  "Round of 16",
  "Quarter-finals",
  "Semi-finals",
  "Final",
] as const;

export function encodeOverrides(overrides: MatchResultOverride[]): string {
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

export function buildWhatIfUrl(overrides: MatchResultOverride[]): string {
  const encoded = encodeOverrides(overrides);
  return encoded ? `/what-if?overrides=${encoded}` : "/what-if";
}

export function isUnplayedFixture(fixture: Match): boolean {
  return fixture.result === null || !fixture.result.played;
}

export function sortFixturesForScenario(fixtures: Match[]): Match[] {
  return [...fixtures].sort((left, right) => {
    const leftKnockout = left.stage !== "group";
    const rightKnockout = right.stage !== "group";
    if (leftKnockout !== rightKnockout) {
      return leftKnockout ? -1 : 1;
    }
    if (leftKnockout && rightKnockout) {
      const leftIndex = KNOCKOUT_STAGE_ORDER.indexOf(
        left.stage as (typeof KNOCKOUT_STAGE_ORDER)[number],
      );
      const rightIndex = KNOCKOUT_STAGE_ORDER.indexOf(
        right.stage as (typeof KNOCKOUT_STAGE_ORDER)[number],
      );
      if (leftIndex !== rightIndex) {
        return leftIndex - rightIndex;
      }
    }
    return left.id.localeCompare(right.id);
  });
}

export function scenarioFixtures(fixtures: Match[]): Match[] {
  return sortFixturesForScenario(fixtures.filter(isUnplayedFixture));
}

export function favoriteWinsOverride(match: BracketMatch): MatchResultOverride {
  const favoriteIsTeamA =
    match.probabilities.team_a_advance >= match.probabilities.team_b_advance;
  return {
    match_id: match.id,
    team_a_goals: favoriteIsTeamA ? 2 : 0,
    team_b_goals: favoriteIsTeamA ? 1 : 2,
  };
}

export function upsetOverride(match: BracketMatch): MatchResultOverride {
  const favoriteIsTeamA =
    match.probabilities.team_a_advance >= match.probabilities.team_b_advance;
  return {
    match_id: match.id,
    team_a_goals: favoriteIsTeamA ? 0 : 2,
    team_b_goals: favoriteIsTeamA ? 2 : 0,
  };
}

export function underdogWinsNextMatchPreset(
  fixtures: Match[],
): MatchResultOverride[] {
  const nextFixture = scenarioFixtures(fixtures)[0];
  if (!nextFixture) {
    return [];
  }
  return [underdogWinsFixtureOverride(nextFixture)];
}

export function allFavoritesAdvancePreset(
  fixtures: Match[],
): MatchResultOverride[] {
  return scenarioFixtures(fixtures)
    .filter((fixture) => fixture.stage !== "group")
    .map((fixture) => favoriteWinsFixtureOverride(fixture));
}

export function chaosRoundPreset(fixtures: Match[]): MatchResultOverride[] {
  const unplayedKnockout = scenarioFixtures(fixtures).filter(
    (fixture) => fixture.stage !== "group",
  );
  if (unplayedKnockout.length === 0) {
    return [];
  }
  const targetStage = unplayedKnockout[0].stage;
  return unplayedKnockout
    .filter((fixture) => fixture.stage === targetStage)
    .map((fixture) => underdogWinsFixtureOverride(fixture));
}

function favoriteWinsFixtureOverride(fixture: Match): MatchResultOverride {
  return {
    match_id: fixture.id,
    team_a_goals: 2,
    team_b_goals: 1,
  };
}

function underdogWinsFixtureOverride(fixture: Match): MatchResultOverride {
  return {
    match_id: fixture.id,
    team_a_goals: 0,
    team_b_goals: 1,
  };
}
