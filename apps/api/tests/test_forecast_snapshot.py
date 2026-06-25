"""Tests for published forecast snapshot serving."""

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services import forecast_snapshot_service


client = TestClient(app)


def test_latest_forecast_reads_published_snapshot_without_simulating() -> None:
    with patch(
        "app.services.forecast_snapshot_service.publish_forecast_snapshot",
        side_effect=AssertionError("snapshot should already exist"),
    ):
        response = client.get("/forecast/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["snapshot_id"]
    assert payload["summary"]["metadata"]["n_simulations"] == 5_000
    assert len(payload["summary"]["teams"]) == 48
    assert len(payload["group_chaos"]["groups"]) == 12
    assert payload["upsets"]["fixtures"]
    assert payload["third_place"]["teams"]
    assert payload["featured_final"]["stage"] == "Final"
    assert payload["bracket"]["rounds"]["Final"]
    assert payload["model_version"]


def test_forecast_status_matches_latest_snapshot_pointer() -> None:
    with patch(
        "app.services.forecast_snapshot_service.publish_forecast_snapshot",
        side_effect=AssertionError("snapshot should already exist"),
    ):
        status = client.get("/forecast/status").json()
        snapshot = client.get("/forecast/latest").json()

    assert status["snapshot_id"] == snapshot["snapshot_id"]
    assert status["forecast_generated_at"] == snapshot["generated_at"]
    assert status["completed_result_count"] == 54
    assert status["n_simulations"] == 5_000


def test_snapshot_featured_final_matches_favorite_bracket_trace() -> None:
    snapshot = client.get("/forecast/latest").json()
    featured = snapshot["featured_final"]
    bracket_final = snapshot["bracket"]["rounds"]["Final"][0]

    assert {featured["team_a"]["team_id"], featured["team_b"]["team_id"]} == {
        bracket_final["team_a"]["team_id"],
        bracket_final["team_b"]["team_id"],
    }
    assert featured["winner_team_id"] == bracket_final["winner_team_id"]
    assert featured["winner_team_id"] in {
        featured["team_a"]["team_id"],
        featured["team_b"]["team_id"],
    }


def test_snapshot_title_contenders_include_featured_finalists() -> None:
    snapshot = client.get("/forecast/latest").json()
    top_eight = {
        team["team_id"]
        for team in sorted(
            snapshot["summary"]["teams"],
            key=lambda team: team["champion"],
            reverse=True,
        )[:8]
    }
    featured = snapshot["featured_final"]

    assert {featured["team_a"]["team_id"], featured["team_b"]["team_id"]}.issubset(
        top_eight
    )


def test_missing_snapshot_does_not_trigger_page_load_simulation(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        forecast_snapshot_service,
        "BOOTSTRAP_SNAPSHOT_PATH",
        tmp_path / "missing.json",
    )
    monkeypatch.setattr(
        forecast_snapshot_service,
        "get_active_forecast_payload_path",
        lambda: None,
    )

    with patch(
        "app.services.forecast_snapshot_service.publish_forecast_snapshot",
        side_effect=AssertionError("page load must not simulate"),
    ):
        response = client.get("/forecast/latest")

    assert response.status_code == 503
