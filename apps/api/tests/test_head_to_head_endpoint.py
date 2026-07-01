"""Tests for head-to-head meeting probability endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_head_to_head_returns_complete_probability_fields() -> None:
    response = client.get(
        "/team-path/head-to-head"
        "?team_a=MEXICO&team_b=RSA&model_type=oracle_v2&n_simulations=20&seed=7"
    )

    assert response.status_code == 200
    payload = response.json()
    assert 0.0 <= payload["probability"] <= 1.0
    assert isinstance(payload["stages_they_could_meet"], list)
    assert payload["meet_before_final_probability"] <= payload["probability"]
    assert payload["meet_in_final_probability"] <= payload["probability"]


def test_head_to_head_rejects_same_team() -> None:
    response = client.get(
        "/team-path/head-to-head"
        "?team_a=MEXICO&team_b=MEXICO&model_type=oracle_v2&n_simulations=20"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "team ids must be different"


def test_head_to_head_rejects_zero_simulations() -> None:
    response = client.get(
        "/team-path/head-to-head"
        "?team_a=MEXICO&team_b=RSA&model_type=oracle_v2&n_simulations=0"
    )

    assert response.status_code == 422


def test_head_to_head_from_bank_is_deterministic(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.head_to_head_service import calculate_head_to_head_from_bank
    from app.services.simulation_bank_service import build_simulation_bank

    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("WCO_SNAPSHOT_SIMULATIONS", "120")
    bank_path, _ = build_simulation_bank(
        data_version="h2h-test",
        n_simulations=120,
        master_seed=17,
        max_workers=1,
    )

    first = calculate_head_to_head_from_bank(
        bank_path,
        "MEXICO",
        "RSA",
        "processed",
        model_type="calibrated_elo",
    )
    second = calculate_head_to_head_from_bank(
        bank_path,
        "MEXICO",
        "RSA",
        "processed",
        model_type="calibrated_elo",
    )

    assert first == second
    assert first.n_simulations == 120
