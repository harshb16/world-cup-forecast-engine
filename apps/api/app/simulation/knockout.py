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
ADVANCEMENT_PAIRINGS = {
    "Round of 16": [
        (0, 2),  # Match 89: winner 73 vs winner 75
        (1, 4),  # Match 90: winner 74 vs winner 77
        (3, 5),  # Match 91: winner 76 vs winner 78
        (6, 7),  # Match 92: winner 79 vs winner 80
        (10, 11),  # Match 93: winner 83 vs winner 84
        (8, 9),  # Match 94: winner 81 vs winner 82
        (13, 15),  # Match 95: winner 86 vs winner 88
        (12, 14),  # Match 96: winner 85 vs winner 87
    ],
    "Quarter-finals": [
        (0, 1),  # Match 97: winner 89 vs winner 90
        (4, 5),  # Match 98: winner 93 vs winner 94
        (2, 3),  # Match 99: winner 91 vs winner 92
        (6, 7),  # Match 100: winner 95 vs winner 96
    ],
    "Semi-finals": [
        (0, 1),  # Match 101: winner 97 vs winner 98
        (2, 3),  # Match 102: winner 99 vs winner 100
    ],
    "Final": [
        (0, 1),  # Match 104: winner 101 vs winner 102
    ],
}

GROUP_ORDER = tuple("ABCDEFGHIJKL")
THIRD_PLACE_SLOT_ALLOWED_GROUPS = {
    "1E": {"A", "B", "C", "D", "F"},
    "1I": {"C", "D", "F", "G", "H"},
    "1A": {"C", "E", "F", "H", "I"},
    "1L": {"E", "H", "I", "J", "K"},
    "1D": {"B", "E", "F", "I", "J"},
    "1G": {"A", "E", "H", "I", "J"},
    "1B": {"E", "F", "G", "I", "J"},
    "1K": {"D", "E", "I", "J", "L"},
}


class WorldCup2026BracketBuilder:
    """FIFA World Cup 2026 round-of-32 slot builder."""

    def build_round_of_32(
        self,
        qualified_team_ids: list[str],
        teams_by_id: dict[str, Team],
    ) -> list[tuple[str, str]]:
        """Build the 2026 round-of-32 match order from group ranks.

        The group-stage module passes group winners and runners-up first,
        ordered by group A-L, followed by the eight best third-placed teams.
        """
        if len(qualified_team_ids) != 32:
            raise ValueError("round of 32 requires exactly 32 teams")

        winners: dict[str, str] = {}
        runners_up: dict[str, str] = {}
        for index, group_id in enumerate(GROUP_ORDER):
            winner_team_id = qualified_team_ids[index * 2]
            runner_up_team_id = qualified_team_ids[index * 2 + 1]
            _validate_team_group(winner_team_id, group_id, teams_by_id)
            _validate_team_group(runner_up_team_id, group_id, teams_by_id)
            winners[group_id] = winner_team_id
            runners_up[group_id] = runner_up_team_id

        third_by_group = _third_place_qualifiers_by_group(
            qualified_team_ids[24:],
            teams_by_id,
        )
        third_slot_assignments = _assign_third_place_slots(set(third_by_group))

        return [
            (runners_up["A"], runners_up["B"]),  # Match 73
            (winners["E"], third_by_group[third_slot_assignments["1E"]]),  # Match 74
            (winners["F"], runners_up["C"]),  # Match 75
            (winners["C"], runners_up["F"]),  # Match 76
            (winners["I"], third_by_group[third_slot_assignments["1I"]]),  # Match 77
            (runners_up["E"], runners_up["I"]),  # Match 78
            (winners["A"], third_by_group[third_slot_assignments["1A"]]),  # Match 79
            (winners["L"], third_by_group[third_slot_assignments["1L"]]),  # Match 80
            (winners["D"], third_by_group[third_slot_assignments["1D"]]),  # Match 81
            (winners["G"], third_by_group[third_slot_assignments["1G"]]),  # Match 82
            (runners_up["K"], runners_up["L"]),  # Match 83
            (winners["H"], runners_up["J"]),  # Match 84
            (winners["B"], third_by_group[third_slot_assignments["1B"]]),  # Match 85
            (winners["J"], runners_up["H"]),  # Match 86
            (winners["K"], third_by_group[third_slot_assignments["1K"]]),  # Match 87
            (runners_up["D"], runners_up["G"]),  # Match 88
        ]


def simulate_knockout(
    qualified_team_ids: list[str],
    teams_by_id: dict[str, Team],
    match_model: MatchModel,
    rng: np.random.Generator,
    bracket_builder: WorldCup2026BracketBuilder | None = None,
) -> KnockoutResult:
    """Simulate the knockout bracket from 32 teams to champion."""
    builder = bracket_builder or WorldCup2026BracketBuilder()
    current_team_ids = list(qualified_team_ids)
    rounds: dict[str, list[Match]] = {}
    eliminated_stage_by_team: dict[str, str] = {}
    finalists: list[str] = []

    for round_name in ROUND_NAMES:
        if round_name == "Round of 32":
            pairs = builder.build_round_of_32(current_team_ids, teams_by_id)
        else:
            pairs = _pair_by_indices(current_team_ids, ADVANCEMENT_PAIRINGS[round_name])

        if round_name == "Final":
            finalists = list(current_team_ids)

        round_matches: list[Match] = []
        winners: list[str] = []
        for index, (team_a_id, team_b_id) in enumerate(pairs, start=1):
            team_a = teams_by_id[team_a_id]
            team_b = teams_by_id[team_b_id]
            result = _simulate_knockout_result(match_model, team_a, team_b, rng)
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


def _pair_by_indices(
    team_ids: list[str],
    pair_indices: list[tuple[int, int]],
) -> list[tuple[str, str]]:
    max_index = max(index for pair in pair_indices for index in pair)
    if len(team_ids) <= max_index:
        raise ValueError("knockout advancement map references missing teams")
    return [
        (team_ids[first_index], team_ids[second_index])
        for first_index, second_index in pair_indices
    ]


def _validate_team_group(
    team_id: str,
    expected_group_id: str,
    teams_by_id: dict[str, Team],
) -> None:
    if team_id not in teams_by_id:
        raise ValueError(f"qualified team {team_id} is not in teams_by_id")
    if teams_by_id[team_id].group_id != expected_group_id:
        raise ValueError(
            f"qualified team {team_id} is not ranked in group {expected_group_id}"
        )


def _third_place_qualifiers_by_group(
    third_place_team_ids: list[str],
    teams_by_id: dict[str, Team],
) -> dict[str, str]:
    third_by_group: dict[str, str] = {}
    for team_id in third_place_team_ids:
        if team_id not in teams_by_id:
            raise ValueError(f"qualified team {team_id} is not in teams_by_id")
        group_id = teams_by_id[team_id].group_id
        if group_id in third_by_group:
            raise ValueError(f"multiple third-place qualifiers from group {group_id}")
        third_by_group[group_id] = team_id

    if len(third_by_group) != 8:
        raise ValueError("round of 32 requires exactly eight third-place qualifiers")
    return third_by_group


def _assign_third_place_slots(
    qualified_third_groups: set[str],
) -> dict[str, str]:
    slot_ids = sorted(
        THIRD_PLACE_SLOT_ALLOWED_GROUPS,
        key=lambda slot_id: (
            len(THIRD_PLACE_SLOT_ALLOWED_GROUPS[slot_id] & qualified_third_groups),
            slot_id,
        ),
    )
    assignments = _search_third_place_assignments(
        slot_ids,
        qualified_third_groups,
        {},
    )
    if assignments is None:
        groups = ", ".join(sorted(qualified_third_groups))
        raise ValueError(f"unsupported third-place group combination: {groups}")
    return assignments


def _search_third_place_assignments(
    remaining_slots: list[str],
    remaining_groups: set[str],
    assignments: dict[str, str],
) -> dict[str, str] | None:
    if not remaining_slots:
        return assignments

    slot_id = remaining_slots[0]
    eligible_groups = sorted(
        THIRD_PLACE_SLOT_ALLOWED_GROUPS[slot_id] & remaining_groups
    )
    for group_id in eligible_groups:
        result = _search_third_place_assignments(
            remaining_slots[1:],
            remaining_groups - {group_id},
            {**assignments, slot_id: group_id},
        )
        if result is not None:
            return result
    return None


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


def _simulate_knockout_result(
    match_model: MatchModel,
    team_a: Team,
    team_b: Team,
    rng: np.random.Generator,
) -> MatchResult:
    if hasattr(match_model, "knockout_lambda_scale"):
        return match_model.simulate_result(team_a, team_b, rng, stage="knockout")
    return match_model.simulate_result(team_a, team_b, rng)


def _round_code(round_name: str) -> str:
    return (
        round_name.upper()
        .replace("ROUND OF ", "R")
        .replace("QUARTER-FINALS", "QF")
        .replace("SEMI-FINALS", "SF")
        .replace("FINAL", "F")
        .replace(" ", "-")
    )
