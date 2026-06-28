"""Coherence tests for published forecast snapshots."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import forecast_snapshot_service

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
        "app.services.forecast_snapshot_service.plurality_bracket_from_bank",
        side_effect=AssertionError("read path must not simulate"),
    ):
        response = client.get("/forecast/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["bracket"]["rounds"]["Final"]
    assert payload["model_version"]
    assert payload["uncertainty"]["n_simulations"] > 0
    n_simulations = payload["summary"]["metadata"]["n_simulations"]
    assert payload["uncertainty"]["n_simulations"] == n_simulations


def test_snapshot_coherence_on_published_bank_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("WCO_SNAPSHOT_SIMULATIONS", "500")

    snapshot = forecast_snapshot_service.publish_forecast_snapshot("processed")
    n_simulations = snapshot.summary.metadata.n_simulations

    assert snapshot.uncertainty.n_simulations == n_simulations
    assert snapshot.third_place.n_simulations == n_simulations
    assert snapshot.bracket.metadata.n_simulations == n_simulations
    assert snapshot.bracket.simulation_mode == "bank_plurality"
    from app.services.simulation_bank_service import (
        champion_probabilities_match_summary,
        load_bank_arrays,
        modal_champion_and_final_pairing,
    )
    from app.services.runtime_store import get_active_forecast_bank_path

    assert champion_probabilities_match_summary(snapshot.summary)
    bank_path = get_active_forecast_bank_path()
    assert bank_path is not None
    bank = load_bank_arrays(bank_path)
    modal_champion_id, modal_runner_id = modal_champion_and_final_pairing(bank)
    assert snapshot.bracket.champion_team_id == modal_champion_id
    final_match = snapshot.bracket.rounds["Final"][0]
    assert {final_match.team_a.team_id, final_match.team_b.team_id} == {
        modal_champion_id,
        modal_runner_id,
    }


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
