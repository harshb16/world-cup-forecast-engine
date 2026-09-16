"""Tests for sample data API endpoints."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_teams_returns_48_teams() -> None:
    response = client.get("/teams")

    assert response.status_code == 200
    assert len(response.json()) == 48


def test_groups_returns_12_groups() -> None:
    response = client.get("/groups")

    assert response.status_code == 200
    assert len(response.json()) == 12


def test_fixtures_returns_72_fixtures() -> None:
    response = client.get("/fixtures")

    assert response.status_code == 200
    assert len(response.json()) == 72


def test_fixture_team_ids_exist_in_teams_response() -> None:
    teams_response = client.get("/teams")
    fixtures_response = client.get("/fixtures")
    team_ids = {team["id"] for team in teams_response.json()}

    for fixture in fixtures_response.json():
        assert fixture["team_a_id"] in team_ids
        assert fixture["team_b_id"] in team_ids
