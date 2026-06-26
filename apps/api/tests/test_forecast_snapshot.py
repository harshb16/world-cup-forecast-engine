"""Tests for published forecast snapshot serving."""

from pathlib import Path
from unittest.mock import patch

import pytest
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
    n_simulations = payload["summary"]["metadata"]["n_simulations"]
    assert payload["snapshot_id"]
    assert n_simulations > 0
    assert payload["summary"]["metadata"]["n_simulations"] == payload["uncertainty"]["n_simulations"]
    assert payload["third_place"]["n_simulations"] > 0
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
    assert status["completed_result_count"] == snapshot["summary"]["metadata"]["completed_result_count"]
    assert status["n_simulations"] == snapshot["summary"]["metadata"]["n_simulations"]


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


def test_publish_forecast_snapshot_uses_single_bank(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("WCO_SNAPSHOT_SIMULATIONS", "80")

    with patch(
        "app.services.simulation_service.run_simulation",
        side_effect=AssertionError("publish must not run standalone MC"),
    ):
        snapshot = forecast_snapshot_service.publish_forecast_snapshot("processed")

    n_simulations = snapshot.summary.metadata.n_simulations
    assert n_simulations == 80
    assert snapshot.uncertainty.n_simulations == n_simulations
    assert snapshot.third_place.n_simulations == n_simulations
    assert snapshot.snapshot_id.endswith(f":{n_simulations}")
    from app.services.simulation_bank_service import champion_probabilities_match_summary

    assert champion_probabilities_match_summary(snapshot.summary)


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
