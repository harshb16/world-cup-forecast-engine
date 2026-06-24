"""Tests for head-to-head meeting probability endpoint."""

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
