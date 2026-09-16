"""Tests for the FIFA 2026 third-place allocation lookup table."""

from __future__ import annotations

import json
from itertools import combinations

import pytest

from app.services.data_loader import load_tournament
from app.simulation.group_table import calculate_group_table
from app.simulation.knockout import GROUP_ORDER, WorldCup2026BracketBuilder
from app.simulation.match_models import EloWinDrawLossModel
from app.simulation.third_place import get_best_third_place_qualifiers
from app.simulation.third_place_allocation import (
    SLOT_IDS,
    TABLE_PATH,
    assign_third_place_slots,
    load_allocation_table,
    reset_allocation_table_cache_for_tests,
)


@pytest.fixture(autouse=True)
def _clear_allocation_cache() -> None:
    reset_allocation_table_cache_for_tests()


def test_allocation_table_has_495_rows() -> None:
    payload = json.loads(TABLE_PATH.read_text(encoding="utf-8"))
    assert payload["row_count"] == 495
    assert len(payload["rows"]) == 495


def test_every_row_assigns_each_qualified_group_once() -> None:
    for row in load_allocation_table().values():
        assert len(row) == len(SLOT_IDS)
        assert len(set(row.values())) == 8


@pytest.mark.parametrize(
    "qualified_groups",
    ["".join(groups) for groups in combinations(GROUP_ORDER, 8)],
)
def test_every_combination_has_lookup_row(qualified_groups: str) -> None:
    assignments = assign_third_place_slots(set(qualified_groups))
    assert set(assignments.values()) == set(qualified_groups)
    assert set(assignments) == set(SLOT_IDS)


@pytest.mark.parametrize(
    ("qualified_groups", "expected"),
    [
        (
            "BDEFIJKL",
            {
                "1A": "E",
                "1B": "J",
                "1D": "B",
                "1E": "D",
                "1G": "I",
                "1I": "F",
                "1K": "L",
                "1L": "K",
            },
        ),
        (
            "EFGHIJKL",
            {
                "1A": "E",
                "1B": "J",
                "1D": "I",
                "1E": "F",
                "1G": "H",
                "1I": "G",
                "1K": "L",
                "1L": "K",
            },
        ),
        (
            "DEFGHIJK",
            {
                "1A": "E",
                "1B": "G",
                "1D": "J",
                "1E": "D",
                "1G": "H",
                "1I": "F",
                "1K": "I",
                "1L": "K",
            },
        ),
    ],
)
def test_annex_c_golden_rows(
    qualified_groups: str,
    expected: dict[str, str],
) -> None:
    assert assign_third_place_slots(set(qualified_groups)) == expected


def test_no_third_place_team_faces_same_group_winner() -> None:
    for assignments in load_allocation_table().values():
        for slot_id, third_group in assignments.items():
            winner_group = slot_id[1]
            assert third_group != winner_group


def test_allocation_rows_produce_no_same_group_round_of_32_pairings() -> None:
    config = load_tournament("sample")
    teams_by_id = {team.id: team for team in config.teams}

    for qualified_groups in load_allocation_table():
        top_two: list[str] = []
        third_place: list[str] = []
        for group in sorted(config.groups, key=lambda item: item.id):
            top_two.extend([group.team_ids[0], group.team_ids[1]])
            if group.id in qualified_groups:
                third_place.append(group.team_ids[2])
        qualified_team_ids = top_two + third_place
        pairs = WorldCup2026BracketBuilder().build_round_of_32(
            qualified_team_ids,
            teams_by_id,
        )
        for team_a_id, team_b_id in pairs:
            group_a = teams_by_id[team_a_id].group_id
            group_b = teams_by_id[team_b_id].group_id
            assert group_a != group_b


def test_processed_standings_use_matching_fifa_allocation_row() -> None:
    config = load_tournament("processed")
    teams_by_id = {team.id: team for team in config.teams}
    played_matches = [
        match
        for match in config.matches
        if match.stage == "group"
        and match.result is not None
        and match.result.played
    ]
    group_tables = {
        group.id: calculate_group_table(group, teams_by_id, played_matches)
        for group in sorted(config.groups, key=lambda item: item.id)
    }
    top_two_qualifiers = [
        row.team_id
        for group_id in sorted(group_tables)
        for row in group_tables[group_id][:2]
    ]
    third_place_qualifiers = [
        row.team_id
        for row in get_best_third_place_qualifiers(group_tables, count=8)
    ]
    qualified_team_ids = top_two_qualifiers + third_place_qualifiers
    third_groups = {
        teams_by_id[team_id].group_id for team_id in third_place_qualifiers
    }
    assert len(third_groups) == 8

    pairs = WorldCup2026BracketBuilder().build_round_of_32(
        qualified_team_ids,
        teams_by_id,
    )
    pair_labels = {
        (teams_by_id[team_a_id].group_id, teams_by_id[team_b_id].group_id)
        for team_a_id, team_b_id in pairs
    }

    assert ("A", "B") in pair_labels  # 2A vs 2B

    assignments = assign_third_place_slots(third_groups)
    third_slot_pair_indexes = {
        "1A": 6,
        "1B": 12,
        "1D": 8,
        "1E": 1,
        "1G": 9,
        "1I": 4,
        "1K": 14,
        "1L": 7,
    }
    for slot_id, pair_index in third_slot_pair_indexes.items():
        third_team_id = pairs[pair_index][1]
        assert teams_by_id[third_team_id].group_id == assignments[slot_id]
