"""Tests for knockout simulation."""

import numpy as np
import pytest

from app.models.domain import MatchResult
from app.services.data_loader import load_sample_tournament
from app.simulation.group_stage import simulate_group_stage
from app.simulation.knockout import (
    WorldCup2026BracketBuilder,
    simulate_knockout,
)
from app.simulation.match_models import EloWinDrawLossModel
from app.simulation.third_place_allocation import assign_third_place_slots


class AlwaysDrawModel(EloWinDrawLossModel):
    def simulate_result(self, *args, **kwargs) -> MatchResult:  # type: ignore[no-untyped-def]
        return MatchResult(team_a_goals=1, team_b_goals=1)


class FavoriteTeamModel(EloWinDrawLossModel):
    def __init__(self, favorite_team_ids: set[str]) -> None:
        super().__init__()
        self.favorite_team_ids = favorite_team_ids

    def simulate_result(self, team_a, team_b, rng) -> MatchResult:  # type: ignore[no-untyped-def]
        if team_b.id in self.favorite_team_ids and team_a.id not in self.favorite_team_ids:
            return MatchResult(team_a_goals=0, team_b_goals=1)
        return MatchResult(team_a_goals=1, team_b_goals=0)


def _qualified_team_ids() -> list[str]:
    config = load_sample_tournament()
    group_stage = simulate_group_stage(config, EloWinDrawLossModel(), np.random.default_rng(1))
    return group_stage.qualified_team_ids


def _teams_by_id():
    config = load_sample_tournament()
    return {team.id: team for team in config.teams}


def _rank_ordered_sample_qualifiers(third_place_groups: str = "EFGHIJKL") -> list[str]:
    config = load_sample_tournament()
    top_two = [
        team_id
        for group in sorted(config.groups, key=lambda item: item.id)
        for team_id in group.team_ids[:2]
    ]
    third_place = [
        next(group for group in config.groups if group.id == group_id).team_ids[2]
        for group_id in third_place_groups
    ]
    return top_two + third_place


def test_exactly_one_champion() -> None:
    result = simulate_knockout(
        _qualified_team_ids(),
        _teams_by_id(),
        EloWinDrawLossModel(),
        np.random.default_rng(1),
    )

    assert result.champion_team_id


def test_exactly_two_finalists() -> None:
    result = simulate_knockout(
        _qualified_team_ids(),
        _teams_by_id(),
        EloWinDrawLossModel(),
        np.random.default_rng(1),
    )

    assert len(result.finalists) == 2


def test_no_knockout_match_has_missing_winner() -> None:
    result = simulate_knockout(
        _qualified_team_ids(),
        _teams_by_id(),
        AlwaysDrawModel(),
        np.random.default_rng(1),
    )

    assert all(match.winner_team_id for matches in result.rounds.values() for match in matches)


def test_deterministic_with_fixed_seed() -> None:
    result_a = simulate_knockout(
        _qualified_team_ids(),
        _teams_by_id(),
        EloWinDrawLossModel(),
        np.random.default_rng(123),
    )
    result_b = simulate_knockout(
        _qualified_team_ids(),
        _teams_by_id(),
        EloWinDrawLossModel(),
        np.random.default_rng(123),
    )

    assert result_a == result_b


def test_every_qualified_team_receives_final_stage_status() -> None:
    qualified_team_ids = _qualified_team_ids()
    result = simulate_knockout(
        qualified_team_ids,
        _teams_by_id(),
        EloWinDrawLossModel(),
        np.random.default_rng(1),
    )

    assert set(result.eliminated_stage_by_team) == set(qualified_team_ids)


def test_round_of_32_uses_world_cup_2026_fixed_slots() -> None:
    pairs = WorldCup2026BracketBuilder().build_round_of_32(
        _rank_ordered_sample_qualifiers(),
        _teams_by_id(),
    )

    assert len(pairs) == 16
    assert pairs[0] == ("T02", "T06")  # 2A vs 2B
    assert pairs[2] == ("T21", "T10")  # 1F vs 2C
    assert pairs[3] == ("T09", "T22")  # 1C vs 2F
    assert pairs[5] == ("T18", "T34")  # 2E vs 2I
    assert pairs[10] == ("T42", "T46")  # 2K vs 2L
    assert pairs[11] == ("T29", "T38")  # 1H vs 2J
    assert pairs[13] == ("T37", "T30")  # 1J vs 2H
    assert pairs[15] == ("T14", "T26")  # 2D vs 2G


def test_official_advancement_places_group_h_and_i_winners_in_same_semifinal() -> None:
    result = simulate_knockout(
        _rank_ordered_sample_qualifiers(),
        _teams_by_id(),
        FavoriteTeamModel({"T29", "T33"}),  # 1H and 1I
        np.random.default_rng(1),
    )

    first_semifinal = result.rounds["Semi-finals"][0]

    assert {first_semifinal.team_a_id, first_semifinal.team_b_id} == {"T29", "T33"}


def test_round_of_32_assigns_thirds_to_fifa_slots() -> None:
    teams_by_id = _teams_by_id()
    qualified_team_ids = _rank_ordered_sample_qualifiers()
    pairs = WorldCup2026BracketBuilder().build_round_of_32(
        qualified_team_ids,
        teams_by_id,
    )
    third_groups = {
        teams_by_id[team_id].group_id for team_id in qualified_team_ids[24:]
    }
    assignments = assign_third_place_slots(third_groups)
    third_slot_pair_indexes = {
        "1E": 1,
        "1I": 4,
        "1A": 6,
        "1L": 7,
        "1D": 8,
        "1G": 9,
        "1B": 12,
        "1K": 14,
    }

    for slot_id, pair_index in third_slot_pair_indexes.items():
        third_team_id = pairs[pair_index][1]
        third_group_id = teams_by_id[third_team_id].group_id

        assert third_group_id == assignments[slot_id]


def test_round_of_32_rejects_wrong_group_rank_order() -> None:
    qualified_team_ids = _rank_ordered_sample_qualifiers()
    qualified_team_ids[0] = "T09"

    with pytest.raises(ValueError, match="not ranked in group A"):
        WorldCup2026BracketBuilder().build_round_of_32(
            qualified_team_ids,
            _teams_by_id(),
        )
