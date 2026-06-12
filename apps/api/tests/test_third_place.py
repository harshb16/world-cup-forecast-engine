"""Tests for third-place qualification ranking."""

from app.models.domain import GroupStandingRow
from app.simulation.third_place import (
    get_best_third_place_qualifiers,
    get_third_place_rows,
    rank_third_place_teams,
)


def _row(team_id: str, points: int, goal_difference: int, goals_for: int) -> GroupStandingRow:
    wins = points // 3
    draws = points % 3
    played = wins + draws
    goals_against = goals_for - goal_difference
    if goals_against < 0:
        goals_for += abs(goals_against)
        goals_against = 0

    return GroupStandingRow(
        team_id=team_id,
        played=played,
        wins=wins,
        draws=draws,
        losses=0,
        goals_for=goals_for,
        goals_against=goals_against,
        goal_difference=goals_for - goals_against,
        points=points,
    )


def _group_tables() -> dict[str, list[GroupStandingRow]]:
    return {
        f"G{index:02d}": [
            _row(f"T{index:02d}A", 9, 5, 7),
            _row(f"T{index:02d}B", 6, 2, 5),
            _row(f"T{index:02d}C", index % 6, index - 6, index),
            _row(f"T{index:02d}D", 0, -5, 1),
        ]
        for index in range(1, 13)
    }


def test_extracts_exactly_one_third_place_row_per_group() -> None:
    rows = get_third_place_rows(_group_tables())

    assert len(rows) == 12
    assert all(row.team_id.endswith("C") for row in rows)


def test_ranks_twelve_third_place_teams() -> None:
    ranked = rank_third_place_teams(_group_tables())

    assert len(ranked) == 12


def test_returns_exactly_eight_qualifiers() -> None:
    qualifiers = get_best_third_place_qualifiers(_group_tables())

    assert len(qualifiers) == 8


def test_ranking_by_points_works() -> None:
    ranked = rank_third_place_teams(
        {
            "A": [_row("A1", 9, 4, 6), _row("A2", 6, 2, 4), _row("A3", 3, 0, 2)],
            "B": [_row("B1", 9, 4, 6), _row("B2", 6, 2, 4), _row("B3", 4, 0, 2)],
        }
    )

    assert [row.team_id for row in ranked] == ["B3", "A3"]


def test_ranking_by_goal_difference_works() -> None:
    ranked = rank_third_place_teams(
        {
            "A": [_row("A1", 9, 4, 6), _row("A2", 6, 2, 4), _row("A3", 4, 1, 3)],
            "B": [_row("B1", 9, 4, 6), _row("B2", 6, 2, 4), _row("B3", 4, 2, 3)],
        }
    )

    assert [row.team_id for row in ranked] == ["B3", "A3"]


def test_ranking_by_goals_for_works() -> None:
    ranked = rank_third_place_teams(
        {
            "A": [_row("A1", 9, 4, 6), _row("A2", 6, 2, 4), _row("A3", 4, 1, 3)],
            "B": [_row("B1", 9, 4, 6), _row("B2", 6, 2, 4), _row("B3", 4, 1, 4)],
        }
    )

    assert [row.team_id for row in ranked] == ["B3", "A3"]


def test_fallback_ordering_is_deterministic() -> None:
    ranked = rank_third_place_teams(
        {
            "A": [_row("A1", 9, 4, 6), _row("A2", 6, 2, 4), _row("T02", 4, 1, 3)],
            "B": [_row("B1", 9, 4, 6), _row("B2", 6, 2, 4), _row("T01", 4, 1, 3)],
        }
    )

    assert [row.team_id for row in ranked] == ["T01", "T02"]
