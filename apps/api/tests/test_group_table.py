"""Tests for group table calculation."""

from app.models.domain import Group, Match, MatchResult, Team
from app.simulation.group_table import calculate_group_table


def _teams_by_id() -> dict[str, Team]:
    return {
        "T1": Team(id="T1", name="Team 1", group_id="A", rating=1600),
        "T2": Team(id="T2", name="Team 2", group_id="A", rating=1500),
        "T3": Team(id="T3", name="Team 3", group_id="A", rating=1400),
        "T4": Team(id="T4", name="Team 4", group_id="A", rating=1300),
    }


def _group() -> Group:
    return Group(id="A", name="Group A", team_ids=["T1", "T2", "T3", "T4"])


def test_win_gives_three_points_and_loss_zero_points() -> None:
    matches = [
        Match(
            id="M1",
            stage="group",
            group_id="A",
            team_a_id="T1",
            team_b_id="T2",
            result=MatchResult(team_a_goals=2, team_b_goals=0),
        )
    ]

    table = calculate_group_table(_group(), _teams_by_id(), matches)
    rows = {row.team_id: row for row in table}

    assert rows["T1"].points == 3
    assert rows["T2"].points == 0


def test_draw_gives_one_point_each() -> None:
    matches = [
        Match(
            id="M1",
            stage="group",
            group_id="A",
            team_a_id="T1",
            team_b_id="T2",
            result=MatchResult(team_a_goals=1, team_b_goals=1),
        )
    ]

    table = calculate_group_table(_group(), _teams_by_id(), matches)
    rows = {row.team_id: row for row in table}

    assert rows["T1"].points == 1
    assert rows["T2"].points == 1


def test_goal_totals_are_calculated() -> None:
    matches = [
        Match(
            id="M1",
            stage="group",
            group_id="A",
            team_a_id="T1",
            team_b_id="T2",
            result=MatchResult(team_a_goals=3, team_b_goals=1),
        )
    ]

    table = calculate_group_table(_group(), _teams_by_id(), matches)
    row = {row.team_id: row for row in table}["T1"]

    assert row.goals_for == 3
    assert row.goals_against == 1
    assert row.goal_difference == 2


def test_ranking_order_uses_points_goal_difference_and_goals_for() -> None:
    matches = [
        Match(
            id="M1",
            stage="group",
            group_id="A",
            team_a_id="T1",
            team_b_id="T2",
            result=MatchResult(team_a_goals=2, team_b_goals=0),
        ),
        Match(
            id="M2",
            stage="group",
            group_id="A",
            team_a_id="T3",
            team_b_id="T4",
            result=MatchResult(team_a_goals=3, team_b_goals=2),
        ),
        Match(
            id="M3",
            stage="group",
            group_id="A",
            team_a_id="T1",
            team_b_id="T4",
            result=MatchResult(team_a_goals=2, team_b_goals=2),
        ),
        Match(
            id="M4",
            stage="group",
            group_id="A",
            team_a_id="T2",
            team_b_id="T3",
            result=MatchResult(team_a_goals=0, team_b_goals=0),
        ),
    ]

    table = calculate_group_table(_group(), _teams_by_id(), matches)

    assert [row.team_id for row in table] == ["T1", "T3", "T4", "T2"]


def test_fallback_ordering_is_deterministic_by_team_id() -> None:
    table = calculate_group_table(_group(), _teams_by_id(), [])

    assert [row.team_id for row in table] == ["T1", "T2", "T3", "T4"]


def test_ignores_matches_without_result() -> None:
    matches = [
        Match(id="M1", stage="group", group_id="A", team_a_id="T1", team_b_id="T2"),
    ]

    table = calculate_group_table(_group(), _teams_by_id(), matches)

    assert all(row.played == 0 for row in table)
