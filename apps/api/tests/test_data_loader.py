"""Tests for sample tournament data loading."""

from app.services.data_loader import load_sample_tournament


def test_loads_48_teams() -> None:
    config = load_sample_tournament()

    assert len(config.teams) == 48


def test_loads_12_groups() -> None:
    config = load_sample_tournament()

    assert len(config.groups) == 12


def test_every_group_has_four_teams() -> None:
    config = load_sample_tournament()

    assert all(len(group.team_ids) == 4 for group in config.groups)


def test_loads_72_group_fixtures() -> None:
    config = load_sample_tournament()

    assert len(config.matches) == 72
    assert all(match.stage == "group" for match in config.matches)


def test_every_fixture_references_valid_team_ids() -> None:
    config = load_sample_tournament()
    team_ids = {team.id for team in config.teams}

    for match in config.matches:
        assert match.team_a_id in team_ids
        assert match.team_b_id in team_ids
