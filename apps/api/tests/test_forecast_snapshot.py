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
    assert payload["summary"]["metadata"]["n_simulations"] == 5_000
    assert len(payload["summary"]["teams"]) == 48
    assert len(payload["group_chaos"]["groups"]) == 12
    assert payload["upsets"]["fixtures"]


def test_snapshot_title_contenders_include_favorite_finalists() -> None:
    snapshot = client.get("/forecast/latest").json()
    bracket = client.post(
        "/bracket/simulate",
        json={
            "model_type": "calibrated_elo",
            "simulation_mode": "favorite",
            "seed": 42,
        },
    ).json()
    top_eight = {
        team["team_id"]
        for team in sorted(
            snapshot["summary"]["teams"],
            key=lambda team: team["champion"],
            reverse=True,
        )[:8]
    }
    final = bracket["rounds"]["Final"][0]

    assert {final["team_a"]["team_id"], final["team_b"]["team_id"]}.issubset(
        top_eight
    )


def test_missing_snapshot_does_not_trigger_page_load_simulation(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        forecast_snapshot_service,
        "SNAPSHOT_PATH",
        tmp_path / "missing.json",
    )

    with patch(
        "app.services.forecast_snapshot_service.publish_forecast_snapshot",
        side_effect=AssertionError("page load must not simulate"),
    ):
        response = client.get("/forecast/latest")

    assert response.status_code == 503
