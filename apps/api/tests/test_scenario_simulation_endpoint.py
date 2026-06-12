"""Tests for scenario simulation API endpoint."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _payload(seed: int = 1) -> dict:
    return {
        "n_simulations": 5,
        "model_type": "elo",
        "seed": seed,
        "result_overrides": [
            {"match_id": "A1", "team_a_goals": 3, "team_b_goals": 0},
        ],
    }


def test_scenario_simulate_returns_200() -> None:
    response = client.post("/scenario/simulate", json=_payload())

    assert response.status_code == 200


def test_override_result_is_preserved_in_metadata() -> None:
    response = client.post("/scenario/simulate", json=_payload())

    metadata = response.json()["metadata"]

    assert metadata["overrides_applied"] == _payload()["result_overrides"]


def test_invalid_match_id_returns_clear_400_error() -> None:
    payload = _payload()
    payload["result_overrides"][0]["match_id"] = "missing"

    response = client.post("/scenario/simulate", json=payload)

    assert response.status_code == 400
    assert "unknown match_id" in response.json()["detail"]


def test_same_seed_and_same_override_is_deterministic() -> None:
    response_a = client.post("/scenario/simulate", json=_payload(seed=123))
    response_b = client.post("/scenario/simulate", json=_payload(seed=123))

    assert response_a.status_code == 200
    assert response_a.json() == response_b.json()
