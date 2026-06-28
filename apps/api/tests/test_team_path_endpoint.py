"""Tests for team path explorer endpoint."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import TeamPathRequest
from app.services import forecast_snapshot_service
from app.services.team_path_service import (
    TEAM_PATHS_FILENAME,
    calculate_team_path,
)


client = TestClient(app)


def test_team_path_returns_stage_distribution() -> None:
    response = client.post(
        "/team-path",
        json={
            "team_id": "NORWAY",
            "model_type": "poisson",
            "n_simulations": 20,
            "seed": 42,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["team"]["team_id"] == "NORWAY"
    assert data["metadata"]["n_simulations"] == 20
    assert [stage["stage"] for stage in data["stages"]] == [
        "Round of 32",
        "Round of 16",
        "Quarter-finals",
        "Semi-finals",
        "Final",
    ]
    assert all(0 <= stage["reached_probability"] <= 1 for stage in data["stages"])


def test_team_path_is_deterministic_with_seed() -> None:
    request = TeamPathRequest(
        team_id="NORWAY",
        model_type="poisson",
        n_simulations=20,
        seed=7,
    )

    assert calculate_team_path(request, "processed") == calculate_team_path(
        request,
        "processed",
    )


def test_team_path_unknown_team_returns_400() -> None:
    response = client.post(
        "/team-path",
        json={
            "team_id": "NOPE",
            "model_type": "poisson",
            "n_simulations": 20,
            "seed": 42,
        },
    )

    assert response.status_code == 400


def test_get_team_path_uses_published_bank_not_live_mc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("WCO_SNAPSHOT_SIMULATIONS", "200")
    forecast_snapshot_service.publish_forecast_snapshot("processed")

    response = client.get("/team-path/NORWAY")

    assert response.status_code == 200
    data = response.json()
    assert data["team"]["team_id"] == "NORWAY"
    assert data["metadata"]["n_simulations"] == 200
    assert data["metadata"]["n_simulations"] != 500


def test_publish_writes_team_paths_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("WCO_SNAPSHOT_SIMULATIONS", "200")
    forecast_snapshot_service.publish_forecast_snapshot("processed")

    from app.services.runtime_store import get_active_forecast_directory

    forecast_dir = get_active_forecast_directory()
    assert forecast_dir is not None
    cache_path = forecast_dir / TEAM_PATHS_FILENAME
    assert cache_path.exists()
    payload = cache_path.read_text(encoding="utf-8")
    assert '"NORWAY"' in payload
    assert '"stages"' in payload


def test_get_team_path_reach_probability_matches_snapshot_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("WCO_SNAPSHOT_SIMULATIONS", "200")
    snapshot = forecast_snapshot_service.publish_forecast_snapshot("processed")
    team_id = "ARGENTINA"

    response = client.get(f"/team-path/{team_id}")
    assert response.status_code == 200
    team_path = response.json()
    summary_team = next(
        team for team in snapshot.summary.teams if team.team_id == team_id
    )
    final_stage = next(
        stage for stage in team_path["stages"] if stage["stage"] == "Final"
    )
    expected_final_reach = summary_team.final + summary_team.champion
    assert final_stage["reached_probability"] == pytest.approx(
        expected_final_reach,
        abs=1e-9,
    )


def test_get_team_path_unknown_team_returns_404(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("WCO_SNAPSHOT_SIMULATIONS", "200")
    forecast_snapshot_service.publish_forecast_snapshot("processed")

    response = client.get("/team-path/NOPE")

    assert response.status_code == 404
