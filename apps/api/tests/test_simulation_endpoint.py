"""Tests for the simulation API endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_simulate_returns_200() -> None:
    response = client.post(
        "/simulate",
        json={"n_simulations": 5, "model_type": "elo", "seed": 1},
    )

    assert response.status_code == 200


def test_simulate_contains_all_48_teams() -> None:
    response = client.post(
        "/simulate",
        json={"n_simulations": 5, "model_type": "elo", "seed": 1},
    )

    assert len(response.json()["teams"]) == 48


def test_simulate_champion_probabilities_exist() -> None:
    response = client.post(
        "/simulate",
        json={"n_simulations": 5, "model_type": "elo", "seed": 1},
    )

    champion_probabilities = response.json()["champion_probabilities"]

    assert len(champion_probabilities) == 48
    assert any(probability > 0 for probability in champion_probabilities.values())


def test_simulate_champion_probabilities_sum_to_one() -> None:
    response = client.post(
        "/simulate",
        json={"n_simulations": 8, "model_type": "elo", "seed": 1},
    )

    champion_total = sum(response.json()["champion_probabilities"].values())

    assert champion_total == pytest.approx(1.0)


def test_simulate_invalid_model_type_returns_validation_error() -> None:
    response = client.post(
        "/simulate",
        json={"n_simulations": 5, "model_type": "not-real", "seed": 1},
    )

    assert response.status_code == 422


def test_simulate_n_simulations_limit_works() -> None:
    response = client.post(
        "/simulate",
        json={"n_simulations": 10_001, "model_type": "elo", "seed": 1},
    )

    assert response.status_code == 422


def test_simulate_supports_calibrated_elo() -> None:
    response = client.post(
        "/simulate",
        json={"n_simulations": 3, "model_type": "calibrated_elo", "seed": 1},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["model_type"] == "calibrated_elo"
