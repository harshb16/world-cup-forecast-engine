"""Tests for team path explorer endpoint."""

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import TeamPathRequest
from app.services.team_path_service import calculate_team_path


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
