"""Tests for the matchday endpoint."""

from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.services.matchday_service import calculate_matchday


client = TestClient(app)


def test_matchday_endpoint_returns_200() -> None:
    response = client.get("/matchday")
    assert response.status_code == 200


def test_matchday_response_has_required_fields() -> None:
    response = client.get("/matchday")
    data = response.json()

    assert "date" in data
    assert "matchday_label" in data
    assert data["model_type"] == "oracle_v3"
    assert "fixtures" in data
    assert "groups" in data
    assert isinstance(data["fixtures"], list)
    assert isinstance(data["groups"], list)


def test_matchday_groups_have_standings() -> None:
    response = client.get("/matchday")
    data = response.json()

    assert len(data["groups"]) > 0
    for group in data["groups"]:
        assert "group_id" in group
        assert "group_name" in group
        assert "standings" in group
        assert "is_complete" in group
        assert len(group["standings"]) == 4
        for row in group["standings"]:
            assert "position" in row
            assert "team_id" in row
            assert "team_name" in row
            assert "points" in row


def test_matchday_fixtures_have_probabilities() -> None:
    response = client.get("/matchday")
    data = response.json()

    for fixture in data["fixtures"]:
        assert "match_id" in fixture
        assert fixture["stage"] == "group"
        assert "team_a_id" in fixture
        assert "team_b_id" in fixture
        assert "team_a_win_probability" in fixture
        assert "draw_probability" in fixture
        assert "team_b_win_probability" in fixture
        assert "projected_team_a_goals" in fixture
        assert "projected_team_b_goals" in fixture
        assert "what_still_matters" in fixture
        # Probabilities should sum near 1
        total = (
            fixture["team_a_win_probability"]
            + fixture["draw_probability"]
            + fixture["team_b_win_probability"]
        )
        assert abs(total - 1.0) < 0.02


def test_matchday_service_returns_response_object() -> None:
    result = calculate_matchday("processed", "oracle_v2")
    assert result.date
    assert result.matchday_label
    assert isinstance(result.groups, list)
    assert len(result.groups) == 12  # 12 groups


def test_matchday_groups_are_sorted() -> None:
    result = calculate_matchday("processed", "oracle_v2")
    group_ids = [g.group_id for g in result.groups]
    assert group_ids == sorted(group_ids)


def test_matchday_group_standings_are_ranked() -> None:
    result = calculate_matchday("processed", "oracle_v2")
    for group in result.groups:
        points = [s.points for s in group.standings]
        # Points should be in descending order
        assert points == sorted(points, reverse=True)


def test_matchday_with_elo_model() -> None:
    response = client.get("/matchday?model_type=elo")
    assert response.status_code == 200
    data = response.json()
    assert "fixtures" in data


def test_matchday_sample_mode() -> None:
    result = calculate_matchday("sample", "oracle_v2")
    assert result.date
    assert len(result.groups) > 0
    assert all(fixture.kickoff_utc is None for fixture in result.fixtures)


def test_matchday_uses_official_world_cup_date_windows() -> None:
    matchday_two = calculate_matchday(
        "processed",
        "oracle_v2",
        as_of_date=date(2026, 6, 23),
    )
    matchday_three = calculate_matchday(
        "processed",
        "oracle_v2",
        as_of_date=date(2026, 6, 24),
    )

    assert matchday_two.matchday_label == "Matchday 2"
    assert matchday_three.matchday_label == "Matchday 3"


def test_matchday_idle_date_advances_to_next_fixture_date() -> None:
    result = calculate_matchday(
        "processed",
        "oracle_v2",
        as_of_date=date(2026, 6, 17),
    )

    assert result.date == "2026-06-18"
    assert result.matchday_label == "Matchday 2"
