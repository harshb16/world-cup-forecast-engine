"""Knockout simulation module."""

import numpy as np

from app.models.domain import KnockoutResult, Match, MatchResult, Team
from app.simulation.match_models import MatchModel

ROUND_NAMES = [
    "Round of 32",
    "Round of 16",
    "Quarter-finals",
    "Semi-finals",
    "Final",
]


class PlaceholderBracketBuilder:
    """Temporary, non-official bracket builder for early simulation work."""

    def build_round_of_32(self, qualified_team_ids: list[str]) -> list[tuple[str, str]]:
        """Pair teams in current qualification order.

        This is intentionally a placeholder and is not the official FIFA bracket.
        """
        if len(qualified_team_ids) != 32:
            raise ValueError("round of 32 requires exactly 32 teams")
        return _pair_sequentially(qualified_team_ids)


def simulate_knockout(
    qualified_team_ids: list[str],
    teams_by_id: dict[str, Team],
    match_model: MatchModel,
    rng: np.random.Generator,
    bracket_builder: PlaceholderBracketBuilder | None = None,
) -> KnockoutResult:
    """Simulate a placeholder knockout bracket from 32 teams to champion."""
    builder = bracket_builder or PlaceholderBracketBuilder()
    current_team_ids = list(qualified_team_ids)
    rounds: dict[str, list[Match]] = {}
    eliminated_stage_by_team: dict[str, str] = {}
    finalists: list[str] = []

    for round_name in ROUND_NAMES:
        if round_name == "Round of 32":
            pairs = builder.build_round_of_32(current_team_ids)
        else:
            pairs = _pair_sequentially(current_team_ids)

        if round_name == "Final":
            finalists = list(current_team_ids)

        round_matches: list[Match] = []
        winners: list[str] = []
        for index, (team_a_id, team_b_id) in enumerate(pairs, start=1):
            team_a = teams_by_id[team_a_id]
            team_b = teams_by_id[team_b_id]
            result = match_model.simulate_result(team_a, team_b, rng)
            winner_team_id = _winner_from_result(team_a, team_b, result, rng)
            loser_team_id = team_b_id if winner_team_id == team_a_id else team_a_id
            eliminated_stage_by_team[loser_team_id] = round_name
            winners.append(winner_team_id)
            round_matches.append(
                Match(
                    id=f"KO-{_round_code(round_name)}-{index:02d}",
                    stage=round_name,
                    team_a_id=team_a_id,
                    team_b_id=team_b_id,
                    result=result,
                    winner_team_id=winner_team_id,
                )
            )

        rounds[round_name] = round_matches
        current_team_ids = winners

    champion_team_id = current_team_ids[0]
    eliminated_stage_by_team[champion_team_id] = "Champion"

    return KnockoutResult(
        rounds=rounds,
        eliminated_stage_by_team=eliminated_stage_by_team,
        finalists=finalists,
        champion_team_id=champion_team_id,
    )


def _pair_sequentially(team_ids: list[str]) -> list[tuple[str, str]]:
    if len(team_ids) % 2 != 0:
        raise ValueError("knockout rounds require an even number of teams")
    return [
        (team_ids[index], team_ids[index + 1])
        for index in range(0, len(team_ids), 2)
    ]


def _winner_from_result(
    team_a: Team,
    team_b: Team,
    result: MatchResult,
    rng: np.random.Generator,
) -> str:
    if result.team_a_goals > result.team_b_goals:
        return team_a.id
    if result.team_b_goals > result.team_a_goals:
        return team_b.id

    team_a_probability = 1 / (1 + 10 ** (-(team_a.rating - team_b.rating) / 400))
    return team_a.id if rng.random() < team_a_probability else team_b.id


def _round_code(round_name: str) -> str:
    return (
        round_name.upper()
        .replace("ROUND OF ", "R")
        .replace("QUARTER-FINALS", "QF")
        .replace("SEMI-FINALS", "SF")
        .replace("FINAL", "F")
        .replace(" ", "-")
    )
