"""Tests for tournament domain models."""

import pytest
from pydantic import ValidationError

from app.models.domain import (
    Group,
    GroupStandingRow,
    Match,
    MatchResult,
    Team,
    TournamentConfig,
)
from app.services.data_loader import load_sample_tournament


def test_team_requires_positive_rating() -> None:
    with pytest.raises(ValidationError):
        Team(id="T1", name="Team 1", group_id="A", rating=0)


def test_match_requires_distinct_teams() -> None:
    with pytest.raises(ValidationError):
        Match(id="M1", stage="group", team_a_id="T1", team_b_id="T1")


def test_match_result_defaults_to_played() -> None:
    result = MatchResult(team_a_goals=2, team_b_goals=1)

    assert result.played is True


def test_group_rejects_duplicate_team_ids() -> None:
    with pytest.raises(ValidationError):
        Group(id="A", name="Group A", team_ids=["T1", "T1"])


def test_group_standing_row_validates_totals() -> None:
    with pytest.raises(ValidationError):
        GroupStandingRow(
            team_id="T1",
            played=2,
            wins=1,
            draws=0,
            losses=0,
            goals_for=3,
            goals_against=1,
            goal_difference=2,
            points=3,
        )


def test_group_standing_row_accepts_consistent_values() -> None:
    row = GroupStandingRow(
        team_id="T1",
        played=2,
        wins=1,
        draws=1,
        losses=0,
        goals_for=3,
        goals_against=1,
        goal_difference=2,
        points=4,
    )

    assert row.team_id == "T1"


def test_tournament_config_validates_references() -> None:
    teams = [
        Team(id="T1", name="Team 1", group_id="A", rating=1500),
        Team(id="T2", name="Team 2", group_id="A", rating=1450),
    ]
    groups = [Group(id="A", name="Group A", team_ids=["T1", "T2"])]
    matches = [Match(id="M1", stage="group", group_id="A", team_a_id="T1", team_b_id="T2")]

    config = TournamentConfig(teams=teams, groups=groups, matches=matches)

    assert len(config.teams) == 2


def test_tournament_config_rejects_unknown_match_team() -> None:
    teams = [Team(id="T1", name="Team 1", group_id="A", rating=1500)]
    groups = [Group(id="A", name="Group A", team_ids=["T1"])]
    matches = [Match(id="M1", stage="group", group_id="A", team_a_id="T1", team_b_id="T2")]

    with pytest.raises(ValidationError):
        TournamentConfig(teams=teams, groups=groups, matches=matches)


def test_tournament_config_rejects_invalid_team_group_id() -> None:
    teams = [
        Team(id="T1", name="Team 1", group_id="B", rating=1500),
        Team(id="T2", name="Team 2", group_id="A", rating=1450),
    ]
    groups = [Group(id="A", name="Group A", team_ids=["T2"])]

    with pytest.raises(ValidationError):
        TournamentConfig(teams=teams, groups=groups)


def test_tournament_config_rejects_group_with_unknown_team() -> None:
    teams = [Team(id="T1", name="Team 1", group_id="A", rating=1500)]
    groups = [Group(id="A", name="Group A", team_ids=["T1", "T2"])]

    with pytest.raises(ValidationError):
        TournamentConfig(teams=teams, groups=groups)


def test_tournament_config_rejects_team_listed_in_wrong_group() -> None:
    teams = [
        Team(id="T1", name="Team 1", group_id="A", rating=1500),
        Team(id="T2", name="Team 2", group_id="A", rating=1450),
    ]
    groups = [
        Group(id="A", name="Group A", team_ids=["T1"]),
        Group(id="B", name="Group B", team_ids=["T2"]),
    ]

    with pytest.raises(ValidationError):
        TournamentConfig(teams=teams, groups=groups)


def test_tournament_config_rejects_team_in_multiple_groups() -> None:
    teams = [
        Team(id="T1", name="Team 1", group_id="A", rating=1500),
        Team(id="T2", name="Team 2", group_id="A", rating=1450),
    ]
    groups = [
        Group(id="A", name="Group A", team_ids=["T1", "T2"]),
        Group(id="B", name="Group B", team_ids=["T1"]),
    ]

    with pytest.raises(ValidationError):
        TournamentConfig(teams=teams, groups=groups)


def test_tournament_config_rejects_group_stage_fixture_with_team_group_mismatch() -> None:
    teams = [
        Team(id="T1", name="Team 1", group_id="A", rating=1500),
        Team(id="T2", name="Team 2", group_id="A", rating=1450),
        Team(id="T3", name="Team 3", group_id="B", rating=1400),
    ]
    groups = [
        Group(id="A", name="Group A", team_ids=["T1", "T2"]),
        Group(id="B", name="Group B", team_ids=["T3"]),
    ]
    matches = [Match(id="M1", stage="group", group_id="A", team_a_id="T1", team_b_id="T3")]

    with pytest.raises(ValidationError):
        TournamentConfig(teams=teams, groups=groups, matches=matches)


def test_tournament_config_rejects_group_stage_fixture_without_group_id() -> None:
    teams = [
        Team(id="T1", name="Team 1", group_id="A", rating=1500),
        Team(id="T2", name="Team 2", group_id="A", rating=1450),
    ]
    groups = [Group(id="A", name="Group A", team_ids=["T1", "T2"])]
    matches = [Match(id="M1", stage="group", team_a_id="T1", team_b_id="T2")]

    with pytest.raises(ValidationError):
        TournamentConfig(teams=teams, groups=groups, matches=matches)


def test_valid_sample_tournament_still_loads_successfully() -> None:
    config = load_sample_tournament()

    assert len(config.teams) == 48
    assert len(config.groups) == 12
    assert len(config.matches) == 72
