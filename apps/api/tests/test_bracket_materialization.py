"""Tests for knockout schedule helpers and bracket materialization."""

from __future__ import annotations

from datetime import date

from app.models.domain import MatchResult, TournamentConfig
from app.services.bracket_materialization_service import (
    build_round_of_32_matches,
    compute_real_qualified_team_ids,
    has_knockout_fixtures,
    is_group_stage_complete,
    knockout_stage_label,
    materialize_round_of_32_if_ready,
)
from app.services.data_loader import load_tournament
from app.services.world_cup_schedule import (
    knockout_round_for_date,
    tournament_stage_label,
)
from app.simulation.knockout import WorldCup2026BracketBuilder
from app.simulation.third_place_allocation import assign_third_place_slots


def test_knockout_round_for_date_maps_official_windows() -> None:
    assert knockout_round_for_date(date(2026, 6, 28)) == "Round of 32"
    assert knockout_round_for_date(date(2026, 7, 4)) == "Round of 16"
    assert knockout_round_for_date(date(2026, 7, 10)) == "Quarter-finals"
    assert knockout_round_for_date(date(2026, 7, 15)) == "Semi-finals"
    assert knockout_round_for_date(date(2026, 7, 18)) == "Third-place match"
    assert knockout_round_for_date(date(2026, 7, 19)) == "Final"
    assert knockout_round_for_date(date(2026, 6, 27)) is None


def test_tournament_stage_label_prefers_group_then_knockout() -> None:
    assert tournament_stage_label(date(2026, 6, 12)) == "Matchday 1"
    assert tournament_stage_label(date(2026, 7, 19)) == "Final"
    assert knockout_stage_label(date(2026, 7, 4)) == "Round of 16"


def test_is_group_stage_complete_false_for_processed_snapshot() -> None:
    config = load_tournament("processed")
    assert not is_group_stage_complete(config)


def test_materialize_round_of_32_noop_when_group_incomplete() -> None:
    config = load_tournament("processed")
    assert materialize_round_of_32_if_ready(config) == []


def test_materialize_round_of_32_idempotent_after_first_run() -> None:
    config = _sample_config_with_completed_group_stage()
    first = materialize_round_of_32_if_ready(config)
    assert len(first) == 16
    extended = config.model_copy(update={"matches": [*config.matches, *first]})
    assert materialize_round_of_32_if_ready(extended) == []
    assert has_knockout_fixtures(extended)


def test_build_round_of_32_matches_uses_annex_c_allocation() -> None:
    config = _sample_config_with_completed_group_stage()
    matches = build_round_of_32_matches(config)
    assert len(matches) == 16
    assert all(match.stage == "Round of 32" for match in matches)
    assert all(match.result is None for match in matches)

    teams_by_id = {team.id: team for team in config.teams}
    qualified_team_ids = compute_real_qualified_team_ids(config)
    expected_pairs = WorldCup2026BracketBuilder().build_round_of_32(
        qualified_team_ids,
        teams_by_id,
    )
    actual_pairs = [(match.team_a_id, match.team_b_id) for match in matches]
    assert actual_pairs == expected_pairs

    third_groups = {
        teams_by_id[team_id].group_id for team_id in qualified_team_ids[24:]
    }
    assignments = assign_third_place_slots(third_groups)
    for slot_id, third_group in assignments.items():
        slot_index = {
            "1A": 6,
            "1B": 12,
            "1D": 8,
            "1E": 1,
            "1G": 9,
            "1I": 4,
            "1K": 14,
            "1L": 7,
        }[slot_id]
        third_team_id = actual_pairs[slot_index][1]
        assert teams_by_id[third_team_id].group_id == third_group


def _sample_config_with_completed_group_stage() -> TournamentConfig:
    config = load_tournament("sample")
    completed_matches = [
        match.model_copy(
            update={
                "result": MatchResult(
                    team_a_goals=2,
                    team_b_goals=1,
                    played=True,
                ),
                "winner_team_id": match.team_a_id,
            }
        )
        for match in config.matches
        if match.stage == "group"
    ]
    return config.model_copy(update={"matches": completed_matches})
