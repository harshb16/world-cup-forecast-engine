"""Coherence tests for published forecast snapshots."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_snapshot_bracket_final_matches_featured_final() -> None:
    with patch(
        "app.services.forecast_snapshot_service.publish_forecast_snapshot",
        side_effect=AssertionError("snapshot should already exist"),
    ):
        snapshot = client.get("/forecast/latest").json()

    featured = snapshot["featured_final"]
    bracket_final = snapshot["bracket"]["rounds"]["Final"][0]
    assert {featured["team_a"]["team_id"], featured["team_b"]["team_id"]} == {
        bracket_final["team_a"]["team_id"],
        bracket_final["team_b"]["team_id"],
    }
    assert featured["winner_team_id"] == bracket_final["winner_team_id"]


def test_snapshot_read_does_not_publish_or_simulate() -> None:
    with patch(
        "app.services.forecast_snapshot_service.publish_forecast_snapshot",
        side_effect=AssertionError("read path must not publish"),
    ), patch(
        "app.services.forecast_snapshot_service.run_bracket_simulation",
        side_effect=AssertionError("read path must not simulate"),
    ):
        response = client.get("/forecast/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["bracket"]["rounds"]["Final"]
    assert payload["model_version"]
    assert payload["uncertainty"]["n_simulations"] > 0


def test_snapshot_bracket_matchups_are_internally_consistent() -> None:
    snapshot = client.get("/forecast/latest").json()
    rounds = snapshot["bracket"]["rounds"]
    r32 = rounds["Round of 32"]
    r16 = rounds["Round of 16"]
    assert len(r32) == 16
    assert len(r16) == 8
    for match in r16:
        assert match["team_a"]["team_id"]
        assert match["team_b"]["team_id"]
