import type { TeamProbability } from "@/lib/api";

export function isTeamEliminated(probability: TeamProbability): boolean {
  return (
    probability.group_qualification_probability < 0.001 &&
    probability.round_of_32 < 0.001
  );
}

export function isGroupQualificationSaturated(
  probability: TeamProbability,
): boolean {
  return (
    probability.group_qualification_probability <= 0.001 ||
    probability.group_qualification_probability >= 0.999
  );
}

export function currentRoundLabel(probability: TeamProbability): string {
  if (isTeamEliminated(probability)) {
    return "Eliminated";
  }

  const rounds: Array<{ label: string; value: number }> = [
    { label: "Round of 32", value: probability.round_of_32 },
    { label: "Round of 16", value: probability.round_of_16 },
    { label: "Quarter-finals", value: probability.quarter_final },
    { label: "Semi-finals", value: probability.semi_final },
    { label: "Final", value: probability.final },
  ];

  for (let index = rounds.length - 1; index >= 0; index -= 1) {
    if (rounds[index].value < 0.95) {
      return rounds[Math.min(index + 1, rounds.length - 1)].label;
    }
  }

  if (probability.group_qualification_probability < 0.95) {
    return "Group stage";
  }

  return "Round of 32";
}

export type TournamentFilter = "still_in" | "eliminated" | "all";

export function matchesTournamentFilter(
  probability: TeamProbability | undefined,
  filter: TournamentFilter,
): boolean {
  if (filter === "all" || !probability) {
    return filter === "all" || probability !== undefined;
  }
  const eliminated = isTeamEliminated(probability);
  return filter === "eliminated" ? eliminated : !eliminated;
}
